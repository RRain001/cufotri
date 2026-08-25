"""Immutable V3 P6.5 harvest and food-product inventory records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..leaf_exchange_resistance import ForcingProvenance
from .validation import (
    FOOD_INVENTORY_UNIT,
    HARVEST_FRACTION_UNIT,
    require_finite,
    validate_food_inventory,
    validate_harvest_state,
)


@dataclass(frozen=True)
class FoodInventory:
    """Total food-product activity with explicit OBT and TFWT components."""

    food_product_identifier: str
    food_inventory_bq: float
    obt_inventory_bq: float
    tfwt_inventory_bq: float
    timestamp: datetime
    provenance: ForcingProvenance
    inventory_unit: str = FOOD_INVENTORY_UNIT
    version: str = "v3-p6-5"

    def __post_init__(self) -> None:
        validate_food_inventory(self)

    @classmethod
    def from_components(
        cls,
        *,
        food_product_identifier: str,
        obt_inventory_bq: float,
        tfwt_inventory_bq: float,
        timestamp: datetime,
        provenance: ForcingProvenance,
    ) -> "FoodInventory":
        """Construct a total inventory from checked source components."""

        obt = require_finite(obt_inventory_bq, field="obt_inventory_bq")
        tfwt = require_finite(tfwt_inventory_bq, field="tfwt_inventory_bq")
        return cls(
            food_product_identifier=food_product_identifier,
            food_inventory_bq=obt + tfwt,
            obt_inventory_bq=obt,
            tfwt_inventory_bq=tfwt,
            timestamp=timestamp,
            provenance=provenance,
        )

    def inventory(self) -> float:
        """Return the total food-product inventory in Bq."""

        return self.food_inventory_bq

    def product(self) -> str:
        """Return the stable food-product identifier."""

        return self.food_product_identifier


@dataclass(frozen=True)
class HarvestState:
    """Plant-to-food transfer state, not a dose or ingestion state."""

    plant_identifier: str
    crop_identifier: str
    growth_stage: str
    harvest_fraction: float
    harvest_inventory_bq: float
    food_product_identifier: str
    timestamp: datetime
    provenance: ForcingProvenance
    inventory_unit: str = FOOD_INVENTORY_UNIT
    harvest_fraction_unit: str = HARVEST_FRACTION_UNIT
    version: str = "v3-p6-5"

    def __post_init__(self) -> None:
        validate_harvest_state(self)

    @classmethod
    def from_inventory(
        cls,
        *,
        plant_identifier: str,
        crop_identifier: str,
        growth_stage: str,
        harvest_fraction: float,
        harvest_inventory_bq: float,
        food_product_identifier: str,
        timestamp: datetime,
        provenance: ForcingProvenance,
    ) -> "HarvestState":
        """Construct a checked immutable harvest record."""

        return cls(
            plant_identifier=plant_identifier,
            crop_identifier=crop_identifier,
            growth_stage=growth_stage,
            harvest_fraction=require_finite(
                harvest_fraction,
                field="harvest_fraction",
            ),
            harvest_inventory_bq=require_finite(
                harvest_inventory_bq,
                field="harvest_inventory_bq",
            ),
            food_product_identifier=food_product_identifier,
            timestamp=timestamp,
            provenance=provenance,
        )

    def inventory(self) -> float:
        """Return the transferred harvest inventory in Bq."""

        return self.harvest_inventory_bq

    def product(self) -> str:
        """Return the stable food-product identifier."""

        return self.food_product_identifier


__all__ = ["FoodInventory", "HarvestState"]
