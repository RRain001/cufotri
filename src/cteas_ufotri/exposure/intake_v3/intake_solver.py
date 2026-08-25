"""V3 P6.6A food-consumption to annual-intake inventory solver."""

from __future__ import annotations

from dataclasses import dataclass

from ...plant.leaf_exchange_resistance import ForcingProvenance
from ...plant.food_v3 import FoodInventory
from .intake_state import IntakeState
from .validation import (
    IntakeInputError,
    IntakeParameterError,
    require_finite,
    validate_consumption_parameters,
)


@dataclass(frozen=True)
class ConsumptionParameters:
    """Explicit provisional annual consumption and food-mass parameters.

    ``FoodInventory`` is a total activity inventory in Bq. The explicit food
    mass is therefore required to derive the product concentration in Bq/kg
    before applying the annual consumption amount in kg/year.
    """

    food_product_identifier: str
    age_group_identifier: str
    annual_consumption_amount: float
    consumption_unit: str
    provenance: ForcingProvenance
    food_product_mass_kg: float
    food_product_mass_unit: str = "kg"
    parameter_status: str = "provisional"
    time_period: str = "annual"

    def __post_init__(self) -> None:
        validate_consumption_parameters(self)


class FoodIntakeSolver:
    """Convert one food-product inventory into one annual intake state."""

    def __init__(self, *, consumer_identifier: str | None = None) -> None:
        self._consumer_identifier = consumer_identifier

    def _resolve_consumer(self, consumer_identifier: str | None) -> str:
        if (
            self._consumer_identifier is not None
            and consumer_identifier is not None
        ):
            raise IntakeParameterError(
                "consumer_identifier cannot be supplied both at construction "
                "and advance"
            )
        resolved = (
            self._consumer_identifier
            if self._consumer_identifier is not None
            else consumer_identifier
        )
        if not isinstance(resolved, str) or not resolved.strip():
            raise IntakeParameterError(
                "an explicit consumer_identifier is required"
            )
        return resolved

    def advance(
        self,
        food_inventory: FoodInventory,
        consumption_parameters: ConsumptionParameters,
        *,
        consumer_identifier: str | None = None,
    ) -> IntakeState:
        """Advance one explicit FoodInventory -> IntakeState transfer.

        The dimensional equation is:

            I_food [Bq/year]
              = C_food [Bq/kg] * R_consumption [kg/year]
            C_food [Bq/kg]
              = M_food [Bq] / m_food [kg]
        """

        if not isinstance(food_inventory, FoodInventory):
            raise IntakeInputError("food_inventory must be a V3 FoodInventory")
        if not isinstance(consumption_parameters, ConsumptionParameters):
            raise IntakeParameterError(
                "consumption_parameters must be ConsumptionParameters"
            )
        validate_consumption_parameters(consumption_parameters)
        if (
            food_inventory.product()
            != consumption_parameters.food_product_identifier
        ):
            raise IntakeInputError(
                "food product identifiers do not match"
            )

        food_activity_bq = require_finite(
            food_inventory.inventory(),
            field="food_inventory.inventory()",
        )
        if food_activity_bq < 0.0:
            raise IntakeInputError(
                "food inventory must be non-negative"
            )
        food_mass_kg = require_finite(
            consumption_parameters.food_product_mass_kg,
            field="food_product_mass_kg",
        )
        food_concentration_bq_kg = food_activity_bq / food_mass_kg
        intake_inventory_bq = require_finite(
            food_concentration_bq_kg
            * consumption_parameters.annual_consumption_amount,
            field="intake_inventory_bq",
        )
        return IntakeState.from_annual_inventory(
            consumer_identifier=self._resolve_consumer(consumer_identifier),
            age_group_identifier=consumption_parameters.age_group_identifier,
            food_product_identifier=consumption_parameters.food_product_identifier,
            consumption_rate=consumption_parameters.annual_consumption_amount,
            intake_inventory_bq=intake_inventory_bq,
            time_period=consumption_parameters.time_period,
            timestamp=food_inventory.timestamp,
            provenance=consumption_parameters.provenance,
        )

    def step(
        self,
        food_inventory: FoodInventory,
        consumption_parameters: ConsumptionParameters,
        *,
        consumer_identifier: str | None = None,
    ) -> IntakeState:
        """Alias for the public one-event intake operation."""

        return self.advance(
            food_inventory,
            consumption_parameters,
            consumer_identifier=consumer_identifier,
        )


__all__ = ["ConsumptionParameters", "FoodIntakeSolver"]
