"""Immutable V3 P6.6A human food-intake inventory state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ...plant.leaf_exchange_resistance import ForcingProvenance
from .validation import (
    ANNUAL_TIME_PERIOD,
    CONSUMPTION_RATE_UNIT,
    INTAKE_INVENTORY_UNIT,
    require_finite,
    validate_intake_state,
)


@dataclass(frozen=True)
class IntakeState:
    """Annual food-to-human activity inventory, without a downstream result."""

    consumer_identifier: str
    age_group_identifier: str
    food_product_identifier: str
    consumption_rate: float
    consumption_rate_unit: str
    intake_inventory_bq: float
    time_period: str
    timestamp: datetime
    provenance: ForcingProvenance
    inventory_unit: str = INTAKE_INVENTORY_UNIT
    version: str = "v3-p6-6a"

    def __post_init__(self) -> None:
        validate_intake_state(self)

    @classmethod
    def from_annual_inventory(
        cls,
        *,
        consumer_identifier: str,
        age_group_identifier: str,
        food_product_identifier: str,
        consumption_rate: float,
        intake_inventory_bq: float,
        timestamp: datetime,
        provenance: ForcingProvenance,
        time_period: str = ANNUAL_TIME_PERIOD,
    ) -> "IntakeState":
        """Construct a checked annual intake state."""

        return cls(
            consumer_identifier=consumer_identifier,
            age_group_identifier=age_group_identifier,
            food_product_identifier=food_product_identifier,
            consumption_rate=require_finite(
                consumption_rate,
                field="consumption_rate",
            ),
            consumption_rate_unit=CONSUMPTION_RATE_UNIT,
            intake_inventory_bq=require_finite(
                intake_inventory_bq,
                field="intake_inventory_bq",
            ),
            time_period=time_period,
            timestamp=timestamp,
            provenance=provenance,
        )

    def inventory(self) -> float:
        """Return annual intake activity in ``Bq/year``."""

        return self.intake_inventory_bq

    def consumer(self) -> str:
        """Return the stable consumer identifier."""

        return self.consumer_identifier

    def food_product(self) -> str:
        """Return the stable food-product identifier."""

        return self.food_product_identifier

    def age_group(self) -> str:
        """Return the stable age-group identifier."""

        return self.age_group_identifier

    def period(self) -> str:
        """Return the explicit intake time-period identifier."""

        return self.time_period

    def time(self) -> datetime:
        """Return the UTC timestamp of the intake record."""

        return self.timestamp


__all__ = ["IntakeState"]
