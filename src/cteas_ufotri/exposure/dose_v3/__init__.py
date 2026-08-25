"""V3-P6.6B isolated intake-to-dose assessment boundary.

The package consumes a typed IntakeState and emits an immutable DoseState.
Dose coefficients remain explicit and provisional; no upstream transport
state or downstream assessment state is activated.
"""

from .dose_solver import DoseParameters, DoseSolver
from .dose_state import DoseState
from .validation import (
    ANNUAL_TIME_PERIOD,
    COMMITTED_DOSE_UNIT,
    DOSE_COEFFICIENT_UNIT,
    INTAKE_INVENTORY_UNIT,
    DoseInputError,
    DoseParameterError,
    DoseStateError,
    DoseUnitError,
    DoseValidationError,
)

__all__ = [
    "ANNUAL_TIME_PERIOD",
    "COMMITTED_DOSE_UNIT",
    "DOSE_COEFFICIENT_UNIT",
    "DoseInputError",
    "DoseParameterError",
    "DoseParameters",
    "DoseSolver",
    "DoseState",
    "DoseStateError",
    "DoseUnitError",
    "DoseValidationError",
    "INTAKE_INVENTORY_UNIT",
]
