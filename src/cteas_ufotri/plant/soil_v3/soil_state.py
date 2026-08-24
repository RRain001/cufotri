"""Inventory-based V3 P6.3 soil HTO state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from .validation import (
    LAYER_DEPTH_UNIT,
    SOIL_CONCENTRATION_UNIT,
    SOIL_INVENTORY_UNIT,
    SOIL_WATER_CONTENT_UNIT,
    SoilStateError,
    require_finite,
    validate_provenance,
    validate_state,
)


@dataclass(frozen=True)
class SoilProvenance:
    """Immutable provenance for a soil state source artifact."""

    source_id: str
    source_version: str
    artifact_sha256: str
    spatial_reference: str
    temporal_resolution_s: float

    def __post_init__(self) -> None:
        validate_provenance(self)


@dataclass(frozen=True)
class SoilState:
    """One soil layer whose authoritative quantity is HTO inventory."""

    soil_identifier: str
    layer_id: str
    layer_depth_m: float
    soil_water_content: float
    soil_water_inventory_bq_m2: float
    soil_water_concentration: float
    timestamp: datetime
    provenance: SoilProvenance
    area_basis: str = "soil_layer_area"
    inventory_unit: str = SOIL_INVENTORY_UNIT
    concentration_unit: str = SOIL_CONCENTRATION_UNIT
    water_content_unit: str = SOIL_WATER_CONTENT_UNIT
    layer_depth_unit: str = LAYER_DEPTH_UNIT
    version: str = "v3-p6-3"

    def __post_init__(self) -> None:
        validate_state(self)

    @classmethod
    def from_inventory(
        cls,
        *,
        soil_identifier: str,
        layer_id: str,
        layer_depth_m: float,
        soil_water_content: float,
        soil_water_inventory_bq_m2: float,
        timestamp: datetime,
        provenance: SoilProvenance,
        area_basis: str = "soil_layer_area",
    ) -> "SoilState":
        """Construct a consistent state from layer inventory and water content."""

        layer_depth = require_finite(layer_depth_m, field="layer_depth_m")
        water_content = require_finite(
            soil_water_content,
            field="soil_water_content",
        )
        inventory = require_finite(
            soil_water_inventory_bq_m2,
            field="soil_water_inventory_bq_m2",
        )
        if layer_depth <= 0.0:
            raise SoilStateError("layer_depth_m must be strictly positive")
        if water_content <= 0.0:
            raise SoilStateError("soil_water_content must be strictly positive")
        if inventory < 0.0:
            raise SoilStateError("soil_water_inventory_bq_m2 must be non-negative")
        return cls(
            soil_identifier=soil_identifier,
            layer_id=layer_id,
            layer_depth_m=layer_depth,
            soil_water_content=water_content,
            soil_water_inventory_bq_m2=inventory,
            soil_water_concentration=inventory / water_content,
            timestamp=timestamp,
            provenance=provenance,
            area_basis=area_basis,
        )

    def with_inventory(
        self,
        *,
        soil_water_inventory_bq_m2: float,
        timestamp: datetime,
    ) -> "SoilState":
        """Return a new state with a checked inventory/concentration pair."""

        inventory = require_finite(
            soil_water_inventory_bq_m2,
            field="soil_water_inventory_bq_m2",
        )
        if inventory < 0.0:
            raise SoilStateError("soil_water_inventory_bq_m2 must be non-negative")
        return replace(
            self,
            soil_water_inventory_bq_m2=inventory,
            soil_water_concentration=inventory / self.soil_water_content,
            timestamp=timestamp,
        )

    def inventory(self) -> float:
        """Return public HTO inventory in ``Bq m^-2``."""

        return self.soil_water_inventory_bq_m2

    def concentration(self) -> float:
        """Return public soil-water HTO concentration in ``Bq m^-3``."""

        return self.soil_water_concentration

    def advance(
        self,
        interval_seconds: float,
        forcing: object,
        *,
        parameters: object | None = None,
        tritium_half_life_s: float | None = None,
    ) -> "SoilState":
        """Advance through an explicitly parameterized soil storage solver."""

        from .soil_solver import SoilStorageSolver

        return SoilStorageSolver(
            parameters=parameters,
            tritium_half_life_s=tritium_half_life_s,
        ).step(self, forcing, interval_seconds)


__all__ = ["SoilProvenance", "SoilState"]
