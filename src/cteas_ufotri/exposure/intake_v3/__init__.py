"""V3-P6.6A isolated food-consumption and annual-intake boundary.

The package consumes a typed FoodInventory and emits an immutable annual
IntakeState. Consumption and food-mass parameters remain explicit and
provisional; no downstream radiological-result or assessment state is made.
"""

from .intake_solver import ConsumptionParameters, FoodIntakeSolver
from .intake_state import IntakeState
from .validation import (
    ANNUAL_TIME_PERIOD,
    CONSUMPTION_RATE_UNIT,
    FOOD_ACTIVITY_CONCENTRATION_UNIT,
    FOOD_MASS_UNIT,
    INTAKE_INVENTORY_UNIT,
    IntakeInputError,
    IntakeParameterError,
    IntakeStateError,
    IntakeUnitError,
    IntakeValidationError,
)

__all__ = [
    "ANNUAL_TIME_PERIOD",
    "CONSUMPTION_RATE_UNIT",
    "ConsumptionParameters",
    "FOOD_ACTIVITY_CONCENTRATION_UNIT",
    "FOOD_MASS_UNIT",
    "FoodIntakeSolver",
    "INTAKE_INVENTORY_UNIT",
    "IntakeInputError",
    "IntakeParameterError",
    "IntakeState",
    "IntakeStateError",
    "IntakeUnitError",
    "IntakeValidationError",
]
