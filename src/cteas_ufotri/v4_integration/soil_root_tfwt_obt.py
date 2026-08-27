"""Opt-in V4 three-layer soil -> root -> TFWT -> OBT integration.

R1 freezes only the selected explicit operator semantics. Root water fluxes are
external forcing. The root transfer is planned from the interval-start soil
state, applied once as the soil sink, and added once to endpoint TFWT after OBT
formation has consumed interval-start TFWT. No plant-water storage, hydrology,
area conversion, parameter activation, or V3 pipeline change is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import json
import math
from typing import Any, Mapping

from cteas_ufotri.plant.leaf_exchange_resistance.types import ForcingProvenance
from cteas_ufotri.plant.obt_v3.obt_solver import (
    OBTSolver,
    OBTStepResult,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.obt_v3.obt_state import OBTState
from cteas_ufotri.plant.root_v4.root_solver import (
    ThreeLayerRootFluxSolverV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.root_v4.root_state import ThreeLayerRootFluxPlanV4
from cteas_ufotri.plant.soil_v4.soil_solver import (
    ThreeLayerSoilForcing,
    ThreeLayerSoilStepResult,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.soil_v4.soil_state import ThreeLayerSoilState
from cteas_ufotri.plant.tfwt_v3.tfwt_state import TFWTState


SELECTED_OPERATOR_SPLIT = "PRESERVE_V3_POST_OBT_ROOT_GAIN"


class V4IntegrationError(ValueError):
    """Fail-closed error for the isolated V4 integration boundary."""


def _require_finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise V4IntegrationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise V4IntegrationError(f"{field} must be finite")
    return result


def _provenance_to_mapping(provenance: ForcingProvenance) -> dict[str, Any]:
    return {
        "source_id": provenance.source_id,
        "source_version": provenance.source_version,
        "artifact_sha256": provenance.artifact_sha256,
        "spatial_reference": provenance.spatial_reference,
        "temporal_resolution_s": provenance.temporal_resolution_s,
    }


def _provenance_from_mapping(payload: Mapping[str, Any]) -> ForcingProvenance:
    try:
        return ForcingProvenance(
            source_id=str(payload["source_id"]),
            source_version=str(payload["source_version"]),
            artifact_sha256=str(payload["artifact_sha256"]),
            spatial_reference=str(payload["spatial_reference"]),
            temporal_resolution_s=float(payload["temporal_resolution_s"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise V4IntegrationError(f"invalid plant provenance: {exc}") from exc


@dataclass(frozen=True)
class V4SoilRootTFWTOBTState:
    """Restartable composite state for the isolated four-module integration."""

    soil_state: ThreeLayerSoilState
    tfwt_state: TFWTState
    obt_state: OBTState
    version: str = "v4-soil-root-tfwt-obt-integration-r1"

    def __post_init__(self) -> None:
        if not isinstance(self.soil_state, ThreeLayerSoilState):
            raise V4IntegrationError("soil_state must be ThreeLayerSoilState")
        if not isinstance(self.tfwt_state, TFWTState):
            raise V4IntegrationError("tfwt_state must be TFWTState")
        if not isinstance(self.obt_state, OBTState):
            raise V4IntegrationError("obt_state must be OBTState")
        if not isinstance(self.version, str) or not self.version.strip():
            raise V4IntegrationError("version is required")

        timestamp = self.soil_state.timestamp
        if self.tfwt_state.time != timestamp or self.obt_state.timestamp != timestamp:
            raise V4IntegrationError("soil, TFWT, and OBT states must share one interval-start timestamp")
        if self.tfwt_state.plant_identifier != self.obt_state.plant_identifier:
            raise V4IntegrationError("TFWT and OBT plant_identifier must match")
        if self.tfwt_state.crop != self.obt_state.crop:
            raise V4IntegrationError("TFWT and OBT crop must match")
        if self.tfwt_state.growth_stage != self.obt_state.growth_stage:
            raise V4IntegrationError("TFWT and OBT growth_stage must match")

        bases = {
            self.soil_state.area_basis,
            self.tfwt_state.area_basis,
            self.obt_state.area_basis,
        }
        if len(bases) != 1:
            raise V4IntegrationError(
                "soil, TFWT, and OBT area_basis must be identical; an explicit area adapter is required otherwise"
            )

    @property
    def timestamp(self) -> datetime:
        return self.soil_state.timestamp

    @property
    def plant_identifier(self) -> str:
        return self.tfwt_state.plant_identifier

    @property
    def area_basis(self) -> str:
        return self.soil_state.area_basis

    def to_mapping(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "soil_state": self.soil_state.to_mapping(),
            "tfwt_state": {
                "plant_identifier": self.tfwt_state.plant_identifier,
                "crop": self.tfwt_state.crop,
                "growth_stage": self.tfwt_state.growth_stage,
                "tfwt_inventory_bq_m2": self.tfwt_state.tfwt_inventory_bq_m2,
                "water_content_kg_m2": self.tfwt_state.water_content_kg_m2,
                "time": self.tfwt_state.time.isoformat(),
                "provenance": _provenance_to_mapping(self.tfwt_state.provenance),
                "area_basis": self.tfwt_state.area_basis,
                "state_version": self.tfwt_state.version,
            },
            "obt_state": {
                "plant_identifier": self.obt_state.plant_identifier,
                "crop": self.obt_state.crop,
                "growth_stage": self.obt_state.growth_stage,
                "obt_inventory_bq_m2": self.obt_state.obt_inventory_bq_m2,
                "plant_mass_kg_m2": self.obt_state.plant_mass_kg_m2,
                "timestamp": self.obt_state.timestamp.isoformat(),
                "provenance": _provenance_to_mapping(self.obt_state.provenance),
                "area_basis": self.obt_state.area_basis,
                "state_version": self.obt_state.version,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "V4SoilRootTFWTOBTState":
        try:
            soil_payload = payload["soil_state"]
            tfwt_payload = payload["tfwt_state"]
            obt_payload = payload["obt_state"]
            if not isinstance(soil_payload, Mapping):
                raise V4IntegrationError("soil_state mapping is required")
            if not isinstance(tfwt_payload, Mapping):
                raise V4IntegrationError("tfwt_state mapping is required")
            if not isinstance(obt_payload, Mapping):
                raise V4IntegrationError("obt_state mapping is required")

            soil_state = ThreeLayerSoilState.from_mapping(soil_payload)
            tfwt_inventory = float(tfwt_payload["tfwt_inventory_bq_m2"])
            water_content = float(tfwt_payload["water_content_kg_m2"])
            tfwt_state = TFWTState(
                plant_identifier=str(tfwt_payload["plant_identifier"]),
                crop=str(tfwt_payload["crop"]),
                growth_stage=str(tfwt_payload["growth_stage"]),
                tfwt_concentration_bq_kg_water=tfwt_inventory / water_content,
                tfwt_inventory_bq_m2=tfwt_inventory,
                water_content_kg_m2=water_content,
                time=datetime.fromisoformat(str(tfwt_payload["time"])),
                provenance=_provenance_from_mapping(tfwt_payload["provenance"]),
                area_basis=str(tfwt_payload["area_basis"]),
                version=str(tfwt_payload.get("state_version", "v3-p6-2b-2")),
            )
            obt_inventory = float(obt_payload["obt_inventory_bq_m2"])
            plant_mass = float(obt_payload["plant_mass_kg_m2"])
            obt_state = OBTState(
                plant_identifier=str(obt_payload["plant_identifier"]),
                crop=str(obt_payload["crop"]),
                growth_stage=str(obt_payload["growth_stage"]),
                obt_inventory_bq_m2=obt_inventory,
                obt_concentration=obt_inventory / plant_mass,
                plant_mass_kg_m2=plant_mass,
                timestamp=datetime.fromisoformat(str(obt_payload["timestamp"])),
                provenance=_provenance_from_mapping(obt_payload["provenance"]),
                area_basis=str(obt_payload["area_basis"]),
                version=str(obt_payload.get("state_version", "v3-p6-2c")),
            )
            return cls(
                soil_state=soil_state,
                tfwt_state=tfwt_state,
                obt_state=obt_state,
                version=str(payload.get("version", "v4-soil-root-tfwt-obt-integration-r1")),
            )
        except V4IntegrationError:
            raise
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise V4IntegrationError(f"invalid composite state mapping: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "V4SoilRootTFWTOBTState":
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise V4IntegrationError(f"invalid composite state JSON: {exc}") from exc
        if not isinstance(decoded, Mapping):
            raise V4IntegrationError("composite state JSON must decode to an object")
        return cls.from_mapping(decoded)


@dataclass(frozen=True)
class V4SoilRootTFWTOBTBalance:
    root_water_transfer_m: float
    root_hto_transfer_bq_m2: float
    soil_root_water_identity_residual_m: float
    soil_root_hto_identity_residual_bq_m2: float
    obt_tfwt_transfer_bq_m2: float
    obt_external_loss_bq_m2: float
    plant_storage_change_bq_m2: float
    plant_residual_bq_m2: float
    soil_nonroot_external_hto_loss_bq_m2: float
    soil_decay_loss_bq_m2: float
    coupled_storage_change_bq_m2: float
    coupled_residual_bq_m2: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _require_finite(getattr(self, field), field=field)


@dataclass(frozen=True)
class V4SoilRootTFWTOBTStepResult:
    state: V4SoilRootTFWTOBTState
    root_plan: ThreeLayerRootFluxPlanV4
    soil_result: ThreeLayerSoilStepResult
    obt_result: OBTStepResult
    applied_soil_forcing: ThreeLayerSoilForcing
    balance: V4SoilRootTFWTOBTBalance
    selected_operator_split: str = SELECTED_OPERATOR_SPLIT


class V4SoilRootTFWTOBTIntegrator:
    """Apply the selected post-OBT root-gain order on an isolated V4 path."""

    def __init__(
        self,
        *,
        soil_solver: ThreeLayerSoilStorageSolver,
        obt_solver: OBTSolver,
        root_solver: ThreeLayerRootFluxSolverV4 | None = None,
    ) -> None:
        if not isinstance(soil_solver, ThreeLayerSoilStorageSolver):
            raise V4IntegrationError("explicit ThreeLayerSoilStorageSolver is required")
        if not isinstance(obt_solver, OBTSolver):
            raise V4IntegrationError("explicit OBTSolver is required")
        if root_solver is not None and not isinstance(root_solver, ThreeLayerRootFluxSolverV4):
            raise V4IntegrationError("root_solver must be ThreeLayerRootFluxSolverV4")
        self.soil_solver = soil_solver
        self.obt_solver = obt_solver
        self.root_solver = ThreeLayerRootFluxSolverV4() if root_solver is None else root_solver

    @staticmethod
    def _require_zero_root_slots(soil_forcing: ThreeLayerSoilForcing) -> None:
        if any(value != 0.0 for value in soil_forcing.root_water_extraction_m_s):
            raise V4IntegrationError(
                "base soil_forcing.root_water_extraction_m_s must be zero; root_v4 owns the single root transfer plan"
            )
        if any(value != 0.0 for value in soil_forcing.root_hto_extraction_bq_m2_s):
            raise V4IntegrationError(
                "base soil_forcing.root_hto_extraction_bq_m2_s must be zero; root_v4 owns the single root transfer plan"
            )

    @staticmethod
    def _require_closed(value: float, *, field: str, scale: float) -> None:
        tolerance = 1.0e-10 * max(1.0, abs(scale))
        if abs(value) > tolerance:
            raise V4IntegrationError(f"{field} failed conservation closure: {value}")

    def advance(
        self,
        state: V4SoilRootTFWTOBTState,
        *,
        soil_forcing: ThreeLayerSoilForcing,
        root_forcing: ThreeLayerRootWaterFluxForcingV4,
        biological_forcing: PlantBiologicalForcing,
        interval_seconds: float,
    ) -> V4SoilRootTFWTOBTStepResult:
        if not isinstance(state, V4SoilRootTFWTOBTState):
            raise V4IntegrationError("state must be V4SoilRootTFWTOBTState")
        if not isinstance(soil_forcing, ThreeLayerSoilForcing):
            raise V4IntegrationError("soil_forcing must be ThreeLayerSoilForcing")
        if not isinstance(root_forcing, ThreeLayerRootWaterFluxForcingV4):
            raise V4IntegrationError("root_forcing must be ThreeLayerRootWaterFluxForcingV4")
        if not isinstance(biological_forcing, PlantBiologicalForcing):
            raise V4IntegrationError("biological_forcing must be PlantBiologicalForcing")
        interval = _require_finite(interval_seconds, field="interval_seconds")
        if interval <= 0.0:
            raise V4IntegrationError("interval_seconds must be strictly positive")
        if soil_forcing.timestamp != state.timestamp:
            raise V4IntegrationError("soil_forcing.timestamp must equal the composite interval-start timestamp")
        if root_forcing.timestamp != state.timestamp:
            raise V4IntegrationError("root_forcing.timestamp must equal the composite interval-start timestamp")
        if root_forcing.plant_identifier != state.plant_identifier:
            raise V4IntegrationError("root_forcing.plant_identifier must match the composite plant")
        self._require_zero_root_slots(soil_forcing)

        # Root is planned from S_n before any interval soil update.
        root_plan = self.root_solver.plan(state.soil_state, root_forcing, interval)
        if root_plan.area_basis != state.area_basis:
            raise V4IntegrationError("root plan and composite state must share one area_basis")

        # Selected split: OBT consumes interval-start TFWT; root gain is not yet present.
        obt_result = self.obt_solver.advance(
            state.tfwt_state,
            state.obt_state,
            interval,
            biological_forcing,
        )
        tfwt_after_obt = state.tfwt_state.inventory() - obt_result.balance.tfwt_loss_bq_m2
        if tfwt_after_obt < -1.0e-12:
            raise V4IntegrationError(
                "OBT formation exceeds interval-start TFWT inventory under the selected post-OBT split"
            )
        tfwt_after_obt = max(tfwt_after_obt, 0.0)

        # Apply exactly the same transfer plan as the soil root sink.
        applied_soil_forcing = replace(
            soil_forcing,
            root_water_extraction_m_s=root_plan.water_uptake_fluxes_m_s,
            root_hto_extraction_bq_m2_s=root_plan.hto_uptake_fluxes_bq_m2_s,
        )
        soil_result = self.soil_solver.advance(state.soil_state, applied_soil_forcing, interval)

        # Root HTO enters endpoint TFWT only after OBT reconciliation.
        endpoint_tfwt_inventory = tfwt_after_obt + root_plan.total_hto_transfer_bq_m2
        endpoint_tfwt = state.tfwt_state.with_inventory(
            tfwt_inventory_bq_m2=endpoint_tfwt_inventory,
            time=root_plan.timestamp_end,
        )
        next_state = V4SoilRootTFWTOBTState(
            soil_state=soil_result.state,
            tfwt_state=endpoint_tfwt,
            obt_state=obt_result.state,
        )

        applied_root_water = sum(applied_soil_forcing.root_water_extraction_m_s) * interval
        applied_root_hto = sum(applied_soil_forcing.root_hto_extraction_bq_m2_s) * interval
        water_identity_residual = root_plan.total_water_transfer_m - applied_root_water
        hto_identity_residual = root_plan.total_hto_transfer_bq_m2 - applied_root_hto

        initial_plant = state.tfwt_state.inventory() + state.obt_state.inventory()
        final_plant = endpoint_tfwt.inventory() + obt_result.state.inventory()
        plant_change = final_plant - initial_plant
        plant_residual = (
            root_plan.total_hto_transfer_bq_m2
            - obt_result.balance.other_loss_bq_m2
            - plant_change
        )

        soil_global = soil_result.global_balance
        nonroot_soil_loss = (
            soil_global.external_hto_loss_bq_m2 - root_plan.total_hto_transfer_bq_m2
        )
        if nonroot_soil_loss < -1.0e-10:
            raise V4IntegrationError("soil external HTO loss is smaller than the applied root transfer")
        nonroot_soil_loss = max(nonroot_soil_loss, 0.0)
        initial_coupled = state.soil_state.total_hto_inventory_bq_m2 + initial_plant
        final_coupled = soil_result.state.total_hto_inventory_bq_m2 + final_plant
        coupled_change = final_coupled - initial_coupled
        coupled_residual = (
            soil_global.external_hto_input_bq_m2
            - nonroot_soil_loss
            - soil_global.decay_loss_bq_m2
            - obt_result.balance.other_loss_bq_m2
            - coupled_change
        )

        balance = V4SoilRootTFWTOBTBalance(
            root_water_transfer_m=root_plan.total_water_transfer_m,
            root_hto_transfer_bq_m2=root_plan.total_hto_transfer_bq_m2,
            soil_root_water_identity_residual_m=water_identity_residual,
            soil_root_hto_identity_residual_bq_m2=hto_identity_residual,
            obt_tfwt_transfer_bq_m2=obt_result.balance.tfwt_loss_bq_m2,
            obt_external_loss_bq_m2=obt_result.balance.other_loss_bq_m2,
            plant_storage_change_bq_m2=plant_change,
            plant_residual_bq_m2=plant_residual,
            soil_nonroot_external_hto_loss_bq_m2=nonroot_soil_loss,
            soil_decay_loss_bq_m2=soil_global.decay_loss_bq_m2,
            coupled_storage_change_bq_m2=coupled_change,
            coupled_residual_bq_m2=coupled_residual,
        )

        scale = max(
            state.soil_state.total_hto_inventory_bq_m2,
            initial_plant,
            root_plan.total_hto_transfer_bq_m2,
            1.0,
        )
        self._require_closed(water_identity_residual, field="soil_root_water_identity_residual_m", scale=root_plan.total_water_transfer_m)
        self._require_closed(hto_identity_residual, field="soil_root_hto_identity_residual_bq_m2", scale=scale)
        self._require_closed(plant_residual, field="plant_residual_bq_m2", scale=scale)
        self._require_closed(coupled_residual, field="coupled_residual_bq_m2", scale=scale)
        self._require_closed(soil_global.hto_residual_bq_m2, field="soil_global.hto_residual_bq_m2", scale=scale)
        self._require_closed(soil_global.water_residual_m, field="soil_global.water_residual_m", scale=state.soil_state.total_water_inventory_m)

        return V4SoilRootTFWTOBTStepResult(
            state=next_state,
            root_plan=root_plan,
            soil_result=soil_result,
            obt_result=obt_result,
            applied_soil_forcing=applied_soil_forcing,
            balance=balance,
        )

    def step(
        self,
        state: V4SoilRootTFWTOBTState,
        *,
        soil_forcing: ThreeLayerSoilForcing,
        root_forcing: ThreeLayerRootWaterFluxForcingV4,
        biological_forcing: PlantBiologicalForcing,
        interval_seconds: float,
    ) -> V4SoilRootTFWTOBTState:
        return self.advance(
            state,
            soil_forcing=soil_forcing,
            root_forcing=root_forcing,
            biological_forcing=biological_forcing,
            interval_seconds=interval_seconds,
        ).state


__all__ = [
    "SELECTED_OPERATOR_SPLIT",
    "V4IntegrationError",
    "V4SoilRootTFWTOBTBalance",
    "V4SoilRootTFWTOBTIntegrator",
    "V4SoilRootTFWTOBTState",
    "V4SoilRootTFWTOBTStepResult",
]
