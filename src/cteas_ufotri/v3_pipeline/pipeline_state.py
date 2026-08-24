"""Immutable V3 P7.5 pipeline state, ledgers, and restart serialization."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
import json
from typing import Any, Mapping

from ..coupling.atmos_v3 import AtmosphericForcingMetadata, AtmosphericHTOForcing
from ..plant.food_v3 import (
    FoodInventory,
    FoodTransferBalance,
    HarvestState,
)
from ..plant.leaf_exchange_resistance import ForcingProvenance
from ..plant.obt_v3 import OBTState, OBTStorageBalance
from ..plant.root_v3 import RootState, RootUptakeBalance
from ..plant.soil_v3 import SoilProvenance, SoilState, SoilStorageBalance
from ..plant.tfwt_v3 import TFWTState, TFWTStorageBalance
from ..exposure.dose_v3 import DoseState
from ..exposure.intake_v3 import IntakeState
from .validation import (
    PipelineSerializationError,
    PipelineStateError,
    validate_forcing,
    validate_utc_timestamp,
)


@dataclass(frozen=True)
class V3PipelineLedger:
    """Auditable balances returned by the last controlled pipeline step."""

    soil_balance: SoilStorageBalance
    root_balance: RootUptakeBalance
    tfwt_balance: TFWTStorageBalance
    obt_balance: OBTStorageBalance
    food_balance: FoodTransferBalance

    def __post_init__(self) -> None:
        if not isinstance(self.soil_balance, SoilStorageBalance):
            raise PipelineStateError("soil_balance must be SoilStorageBalance")
        if not isinstance(self.root_balance, RootUptakeBalance):
            raise PipelineStateError("root_balance must be RootUptakeBalance")
        if not isinstance(self.tfwt_balance, TFWTStorageBalance):
            raise PipelineStateError("tfwt_balance must be TFWTStorageBalance")
        if not isinstance(self.obt_balance, OBTStorageBalance):
            raise PipelineStateError("obt_balance must be OBTStorageBalance")
        if not isinstance(self.food_balance, FoodTransferBalance):
            raise PipelineStateError("food_balance must be FoodTransferBalance")


@dataclass(frozen=True)
class V3SimulationState:
    """Complete immutable state emitted by one V3 pipeline step."""

    timestamp: datetime
    atmospheric_state: AtmosphericHTOForcing
    soil_state: SoilState
    tfwt_state: TFWTState
    obt_state: OBTState
    root_state: RootState
    harvest_state: HarvestState
    food_state: FoodInventory
    intake_state: IntakeState
    dose_state: DoseState
    provenance: ForcingProvenance
    ledger: V3PipelineLedger | None = None

    def __post_init__(self) -> None:
        validate_utc_timestamp(
            self.timestamp,
            field="simulation_state.timestamp",
            error_type=PipelineStateError,
        )
        validate_forcing(self.atmospheric_state)
        if self.atmospheric_state.timestamp > self.timestamp:
            raise PipelineStateError(
                "atmospheric_state.timestamp cannot be after state.timestamp"
            )
        for field, expected_type in (
            ("soil_state", SoilState),
            ("tfwt_state", TFWTState),
            ("obt_state", OBTState),
            ("root_state", RootState),
            ("harvest_state", HarvestState),
            ("food_state", FoodInventory),
            ("intake_state", IntakeState),
            ("dose_state", DoseState),
            ("provenance", ForcingProvenance),
        ):
            if not isinstance(getattr(self, field), expected_type):
                raise PipelineStateError(
                    f"{field} must be {expected_type.__name__}"
                )

        component_timestamps = {
            "soil_state.timestamp": self.soil_state.timestamp,
            "tfwt_state.time": self.tfwt_state.time,
            "obt_state.timestamp": self.obt_state.timestamp,
            "root_state.timestamp": self.root_state.timestamp,
            "harvest_state.timestamp": self.harvest_state.timestamp,
            "food_state.timestamp": self.food_state.timestamp,
            "intake_state.timestamp": self.intake_state.timestamp,
            "dose_state.timestamp": self.dose_state.timestamp,
        }
        if any(value != self.timestamp for value in component_timestamps.values()):
            raise PipelineStateError(
                "all downstream component timestamps must equal state.timestamp"
            )
        if self.tfwt_state.plant_identifier != self.obt_state.plant_identifier:
            raise PipelineStateError("TFWT and OBT plant identifiers must match")
        if self.tfwt_state.plant_identifier != self.root_state.plant_identifier:
            raise PipelineStateError("root plant identifier must match TFWT")
        if self.tfwt_state.plant_identifier != self.harvest_state.plant_identifier:
            raise PipelineStateError("harvest plant identifier must match TFWT")
        if self.harvest_state.food_product_identifier != self.food_state.product():
            raise PipelineStateError("harvest and food product identifiers must match")
        if self.food_state.product() != self.intake_state.food_product():
            raise PipelineStateError("food and intake product identifiers must match")
        if self.intake_state.age_group() != self.dose_state.age_group_identifier:
            raise PipelineStateError("intake and dose age groups must match")
        if self.ledger is not None and not isinstance(self.ledger, V3PipelineLedger):
            raise PipelineStateError("ledger must be V3PipelineLedger or None")

    def to_mapping(self) -> dict[str, Any]:
        """Return a JSON-compatible mapping without writing files."""

        encoded = _encode(self)
        if not isinstance(encoded, dict):
            raise PipelineSerializationError("pipeline state did not encode to a mapping")
        return encoded

    def to_json(self) -> str:
        """Serialize the immutable state for an explicit restart boundary."""

        return json.dumps(self.to_mapping(), sort_keys=True)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "V3SimulationState":
        """Reconstruct and revalidate one serialized pipeline state."""

        try:
            mapping = _require_mapping(payload, field="pipeline_state")
            return cls(
                timestamp=_parse_datetime(mapping["timestamp"], "timestamp"),
                atmospheric_state=_decode_atmospheric(mapping["atmospheric_state"]),
                soil_state=_decode_soil(mapping["soil_state"]),
                tfwt_state=_decode_tfwt(mapping["tfwt_state"]),
                obt_state=_decode_obt(mapping["obt_state"]),
                root_state=_decode_root(mapping["root_state"]),
                harvest_state=_decode_harvest(mapping["harvest_state"]),
                food_state=_decode_food(mapping["food_state"]),
                intake_state=_decode_intake(mapping["intake_state"]),
                dose_state=_decode_dose(mapping["dose_state"]),
                provenance=_decode_forcing_provenance(mapping["provenance"]),
                ledger=_decode_ledger(mapping.get("ledger")),
            )
        except PipelineSerializationError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise PipelineSerializationError(
                f"invalid serialized V3SimulationState: {exc}"
            ) from exc

    @classmethod
    def from_json(cls, payload: str) -> "V3SimulationState":
        """Decode JSON and re-run the complete state validation contract."""

        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise PipelineSerializationError(
                f"invalid serialized pipeline JSON: {exc}"
            ) from exc
        if not isinstance(decoded, Mapping):
            raise PipelineSerializationError("serialized pipeline JSON must be an object")
        return cls.from_mapping(decoded)


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            field.name: _encode(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    return value


def _require_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise PipelineSerializationError(f"{field} must be an object")
    return dict(value)


def _parse_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise PipelineSerializationError(f"{field} must be an ISO timestamp")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PipelineSerializationError(f"{field} is not a valid ISO timestamp") from exc
    validate_utc_timestamp(
        timestamp,
        field=field,
        error_type=PipelineSerializationError,
    )
    return timestamp


def _decode_forcing_provenance(value: Any) -> ForcingProvenance:
    return ForcingProvenance(**_require_mapping(value, field="provenance"))


def _decode_atmospheric(value: Any) -> AtmosphericHTOForcing:
    payload = _require_mapping(value, field="atmospheric_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "atmospheric_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        metadata_payload = dict(metadata)
        metadata_payload["creation_time"] = _parse_datetime(
            metadata_payload["creation_time"],
            "atmospheric_state.metadata.creation_time",
        )
        payload["metadata"] = AtmosphericForcingMetadata(**metadata_payload)
    return AtmosphericHTOForcing(**payload)


def _decode_soil(value: Any) -> SoilState:
    payload = _require_mapping(value, field="soil_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "soil_state.timestamp",
    )
    payload["provenance"] = SoilProvenance(**payload["provenance"])
    return SoilState(**payload)


def _decode_tfwt(value: Any) -> TFWTState:
    payload = _require_mapping(value, field="tfwt_state")
    payload["time"] = _parse_datetime(payload["time"], "tfwt_state.time")
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return TFWTState(**payload)


def _decode_obt(value: Any) -> OBTState:
    payload = _require_mapping(value, field="obt_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "obt_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return OBTState(**payload)


def _decode_root(value: Any) -> RootState:
    payload = _require_mapping(value, field="root_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "root_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return RootState(**payload)


def _decode_harvest(value: Any) -> HarvestState:
    payload = _require_mapping(value, field="harvest_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "harvest_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return HarvestState(**payload)


def _decode_food(value: Any) -> FoodInventory:
    payload = _require_mapping(value, field="food_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "food_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return FoodInventory(**payload)


def _decode_intake(value: Any) -> IntakeState:
    payload = _require_mapping(value, field="intake_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "intake_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return IntakeState(**payload)


def _decode_dose(value: Any) -> DoseState:
    payload = _require_mapping(value, field="dose_state")
    payload["timestamp"] = _parse_datetime(
        payload["timestamp"],
        "dose_state.timestamp",
    )
    payload["provenance"] = _decode_forcing_provenance(payload["provenance"])
    return DoseState(**payload)


def _decode_ledger(value: Any) -> V3PipelineLedger | None:
    if value is None:
        return None
    payload = _require_mapping(value, field="ledger")
    return V3PipelineLedger(
        soil_balance=SoilStorageBalance(**payload["soil_balance"]),
        root_balance=RootUptakeBalance(**payload["root_balance"]),
        tfwt_balance=TFWTStorageBalance(**payload["tfwt_balance"]),
        obt_balance=OBTStorageBalance(**payload["obt_balance"]),
        food_balance=FoodTransferBalance(**payload["food_balance"]),
    )


__all__ = ["V3PipelineLedger", "V3SimulationState"]
