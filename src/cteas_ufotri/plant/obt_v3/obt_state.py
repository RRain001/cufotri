"""Inventory-based V3 P6.2C OBT state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ..leaf_exchange_resistance import ForcingProvenance
from .validation import (
    OBT_CONCENTRATION_UNIT,
    OBT_INVENTORY_UNIT,
    PLANT_MASS_UNIT,
    OBTStateError,
    require_finite,
    validate_state,
)


@dataclass(frozen=True)
class OBTState:
    """Plant OBT state with inventory as the authoritative quantity.

    ``obt_concentration`` is a derived concentration diagnostic on the
    explicitly declared fresh-plant-mass basis. It is stored alongside the
    inventory only to mirror the TFWT public state contract and is checked
    against that inventory at construction. No TFWT/OBT ratio is stored.
    """

    plant_identifier: str
    crop: str
    growth_stage: str
    obt_inventory_bq_m2: float
    obt_concentration: float
    plant_mass_kg_m2: float
    timestamp: datetime
    provenance: ForcingProvenance
    area_basis: str = "plant_area"
    inventory_unit: str = OBT_INVENTORY_UNIT
    concentration_unit: str = OBT_CONCENTRATION_UNIT
    plant_mass_unit: str = PLANT_MASS_UNIT
    version: str = "v3-p6-2c"

    def __post_init__(self) -> None:
        validate_state(self)

    @classmethod
    def from_inventory(
        cls,
        *,
        plant_identifier: str,
        crop: str,
        growth_stage: str,
        obt_inventory_bq_m2: float,
        plant_mass_kg_m2: float,
        timestamp: datetime,
        provenance: ForcingProvenance,
        area_basis: str = "plant_area",
    ) -> "OBTState":
        """Construct a consistent OBT state from its inventory."""

        inventory = require_finite(
            obt_inventory_bq_m2,
            field="obt_inventory_bq_m2",
        )
        plant_mass = require_finite(
            plant_mass_kg_m2,
            field="plant_mass_kg_m2",
        )
        if inventory < 0.0:
            raise OBTStateError("obt_inventory_bq_m2 must be non-negative")
        if plant_mass <= 0.0:
            raise OBTStateError("plant_mass_kg_m2 must be strictly positive")
        return cls(
            plant_identifier=plant_identifier,
            crop=crop,
            growth_stage=growth_stage,
            obt_inventory_bq_m2=inventory,
            obt_concentration=inventory / plant_mass,
            plant_mass_kg_m2=plant_mass,
            timestamp=timestamp,
            provenance=provenance,
            area_basis=area_basis,
        )

    def with_inventory(
        self,
        *,
        obt_inventory_bq_m2: float,
        timestamp: datetime,
    ) -> "OBTState":
        """Return a new state while preserving its mass and provenance basis."""

        inventory = require_finite(
            obt_inventory_bq_m2,
            field="obt_inventory_bq_m2",
        )
        if inventory < 0.0:
            raise OBTStateError("obt_inventory_bq_m2 must be non-negative")
        return replace(
            self,
            obt_inventory_bq_m2=inventory,
            obt_concentration=inventory / self.plant_mass_kg_m2,
            timestamp=timestamp,
        )

    def inventory(self) -> float:
        """Return the public OBT inventory in ``Bq m^-2``."""

        return self.obt_inventory_bq_m2

    def activity_concentration(self) -> float:
        """Return the public OBT concentration in ``Bq kg^-1 fresh``."""

        return self.obt_concentration


__all__ = ["OBTState"]
