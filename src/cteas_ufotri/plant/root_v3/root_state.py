"""Immutable V3 P6.4 root-transfer state and public flux record."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..leaf_exchange_resistance import ForcingProvenance
from .validation import (
    ROOT_FLUX_UNIT,
    ROOT_INVENTORY_UNIT,
    require_finite,
    validate_state,
)


@dataclass(frozen=True)
class RootState:
    """One interval of root transfer, not a TFWT or whole-plant compartment."""

    plant_identifier: str
    root_zone_identifier: str
    uptake_inventory_bq_m2: float
    uptake_flux_bq_m2_s: float
    timestamp: datetime
    provenance: ForcingProvenance
    inventory_unit: str = ROOT_INVENTORY_UNIT
    flux_unit: str = ROOT_FLUX_UNIT
    version: str = "v3-p6-4"

    def __post_init__(self) -> None:
        validate_state(self)

    @classmethod
    def from_transfer(
        cls,
        *,
        plant_identifier: str,
        root_zone_identifier: str,
        uptake_inventory_bq_m2: float,
        uptake_flux_bq_m2_s: float,
        timestamp: datetime,
        provenance: ForcingProvenance,
    ) -> "RootState":
        """Construct a checked immutable transfer record."""

        return cls(
            plant_identifier=plant_identifier,
            root_zone_identifier=root_zone_identifier,
            uptake_inventory_bq_m2=require_finite(
                uptake_inventory_bq_m2,
                field="uptake_inventory_bq_m2",
            ),
            uptake_flux_bq_m2_s=require_finite(
                uptake_flux_bq_m2_s,
                field="uptake_flux_bq_m2_s",
            ),
            timestamp=timestamp,
            provenance=provenance,
        )

    def inventory(self) -> float:
        """Return the integrated root transfer in Bq m^-2."""

        return self.uptake_inventory_bq_m2

    def flux(self) -> float:
        """Return the root transfer flux in Bq m^-2 s^-1."""

        return self.uptake_flux_bq_m2_s

    def as_flux(self) -> "RootFlux":
        """Return this immutable record through the semantic RootFlux alias."""

        return self


# RootState is the state-bearing representation of the public root flux. The
# alias keeps the Soil -> Root -> TFWT seam typed without introducing plant
# storage fields into this module.
RootFlux = RootState


__all__ = ["RootFlux", "RootState"]
