"""Immutable typed results and provenance for the V4 root flux core."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .validation import (
    HTO_CONCENTRATION_UNIT,
    HTO_FLUX_UNIT,
    HTO_TRANSFER_UNIT,
    INTERVAL_UNIT,
    WATER_FLUX_UNIT,
    WATER_TRANSFER_UNIT,
    RootV4InputError,
    require_finite,
    require_layer_ids,
    require_text,
    require_unit,
    validate_interval,
    validate_provenance,
    validate_utc_timestamp,
)


@dataclass(frozen=True)
class RootWaterFluxProvenanceV4:
    source_id: str
    source_locator: str
    revision: str
    artifact_sha256: str
    profile_context: str

    def __post_init__(self) -> None:
        validate_provenance(self)


@dataclass(frozen=True)
class LayerRootTransferV4:
    layer_id: str
    water_uptake_flux_m_s: float
    soil_hto_concentration_bq_m3_water: float
    hto_uptake_flux_bq_m2_s: float
    water_transfer_m: float
    hto_transfer_bq_m2: float
    source_water_inventory_m: float
    source_hto_inventory_bq_m2: float
    remaining_water_if_applied_m: float
    remaining_hto_if_applied_bq_m2: float
    water_balance_residual_m: float
    hto_balance_residual_bq_m2: float
    water_flux_unit: str = WATER_FLUX_UNIT
    concentration_unit: str = HTO_CONCENTRATION_UNIT
    hto_flux_unit: str = HTO_FLUX_UNIT
    water_transfer_unit: str = WATER_TRANSFER_UNIT
    hto_transfer_unit: str = HTO_TRANSFER_UNIT

    def __post_init__(self) -> None:
        require_text(self.layer_id, field="layer_id")
        require_unit(self.water_flux_unit, WATER_FLUX_UNIT, field="water_uptake_flux")
        require_unit(self.concentration_unit, HTO_CONCENTRATION_UNIT, field="soil_hto_concentration")
        require_unit(self.hto_flux_unit, HTO_FLUX_UNIT, field="hto_uptake_flux")
        require_unit(self.water_transfer_unit, WATER_TRANSFER_UNIT, field="water_transfer")
        require_unit(self.hto_transfer_unit, HTO_TRANSFER_UNIT, field="hto_transfer")
        nonnegative = (
            "water_uptake_flux_m_s",
            "soil_hto_concentration_bq_m3_water",
            "hto_uptake_flux_bq_m2_s",
            "water_transfer_m",
            "hto_transfer_bq_m2",
            "source_water_inventory_m",
            "source_hto_inventory_bq_m2",
            "remaining_water_if_applied_m",
            "remaining_hto_if_applied_bq_m2",
        )
        for field in nonnegative:
            if require_finite(getattr(self, field), field=field) < 0.0:
                raise RootV4InputError(f"{field} must be non-negative")
        require_finite(self.water_balance_residual_m, field="water_balance_residual_m")
        require_finite(self.hto_balance_residual_bq_m2, field="hto_balance_residual_bq_m2")


@dataclass(frozen=True)
class ThreeLayerRootFluxPlanV4:
    plant_identifier: str
    soil_identifier: str
    timestamp_start: datetime
    timestamp_end: datetime
    interval_seconds: float
    layer_transfers: tuple[LayerRootTransferV4, LayerRootTransferV4, LayerRootTransferV4]
    provenance: RootWaterFluxProvenanceV4
    area_basis: str = "soil_surface_area"
    interval_semantics: str = "start"
    interval_unit: str = INTERVAL_UNIT
    version: str = "v4-three-layer-root-flux-r1"

    def __post_init__(self) -> None:
        require_text(self.plant_identifier, field="plant_identifier")
        require_text(self.soil_identifier, field="soil_identifier")
        require_text(self.area_basis, field="area_basis")
        validate_utc_timestamp(self.timestamp_start, field="timestamp_start")
        validate_utc_timestamp(self.timestamp_end, field="timestamp_end")
        interval = validate_interval(self.interval_seconds)
        require_unit(self.interval_unit, INTERVAL_UNIT, field="interval")
        if self.interval_semantics != "start":
            raise RootV4InputError("interval_semantics must be 'start'")
        if (self.timestamp_end - self.timestamp_start).total_seconds() != interval:
            raise RootV4InputError("timestamp_end must equal timestamp_start + interval_seconds")
        if not isinstance(self.layer_transfers, tuple) or len(self.layer_transfers) != 3:
            raise RootV4InputError("layer_transfers must contain exactly L1, L2, L3")
        if not all(isinstance(item, LayerRootTransferV4) for item in self.layer_transfers):
            raise RootV4InputError("all layer_transfers must be LayerRootTransferV4")
        require_layer_ids(item.layer_id for item in self.layer_transfers)
        if not isinstance(self.provenance, RootWaterFluxProvenanceV4):
            raise RootV4InputError("provenance must be RootWaterFluxProvenanceV4")
        validate_provenance(self.provenance)

    @property
    def water_uptake_fluxes_m_s(self) -> tuple[float, float, float]:
        return tuple(item.water_uptake_flux_m_s for item in self.layer_transfers)  # type: ignore[return-value]

    @property
    def hto_uptake_fluxes_bq_m2_s(self) -> tuple[float, float, float]:
        return tuple(item.hto_uptake_flux_bq_m2_s for item in self.layer_transfers)  # type: ignore[return-value]

    @property
    def total_water_transfer_m(self) -> float:
        return sum(item.water_transfer_m for item in self.layer_transfers)

    @property
    def total_hto_transfer_bq_m2(self) -> float:
        return sum(item.hto_transfer_bq_m2 for item in self.layer_transfers)

    @property
    def max_abs_water_balance_residual_m(self) -> float:
        return max(abs(item.water_balance_residual_m) for item in self.layer_transfers)

    @property
    def max_abs_hto_balance_residual_bq_m2(self) -> float:
        return max(abs(item.hto_balance_residual_bq_m2) for item in self.layer_transfers)


__all__ = [
    "LayerRootTransferV4",
    "RootWaterFluxProvenanceV4",
    "ThreeLayerRootFluxPlanV4",
]
