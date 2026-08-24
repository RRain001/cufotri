"""V3-P6.4 isolated Soil -> Root -> TFWT transfer boundary.

The coefficient is an explicit provisional test parameter. This package does
not import the UFOTRI parameter database, alter V1/V2 runtime behavior, or
create TFWT, OBT, foodchain, dose, or CTEAS-Atmos state.
"""

from .root_solver import (
    RootParameters,
    RootUptakeBalance,
    RootUptakeForcing,
    RootUptakeSolver,
    RootUptakeStepResult,
)
from .root_state import RootFlux, RootState
from .validation import (
    INTEGRATED_ACTIVITY_UNIT,
    ROOT_COEFFICIENT_UNIT,
    ROOT_FLUX_UNIT,
    ROOT_INVENTORY_UNIT,
    RootInputError,
    RootParameterError,
    RootStateError,
    RootUnitError,
    RootValidationError,
)

__all__ = [
    "INTEGRATED_ACTIVITY_UNIT",
    "ROOT_COEFFICIENT_UNIT",
    "ROOT_FLUX_UNIT",
    "ROOT_INVENTORY_UNIT",
    "RootFlux",
    "RootInputError",
    "RootParameterError",
    "RootParameters",
    "RootState",
    "RootStateError",
    "RootUnitError",
    "RootUptakeBalance",
    "RootUptakeForcing",
    "RootUptakeSolver",
    "RootUptakeStepResult",
    "RootValidationError",
]
