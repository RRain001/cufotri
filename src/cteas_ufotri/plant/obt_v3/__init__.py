"""V3-P6.2C isolated TFWT-to-OBT inventory pathway.

This package is provisional and opt-in. V4 may select the controlled UFOTRI
baseline profile explicitly; no hidden runtime default is introduced here.
"""

from .obt_solver import (
    OBTParameters,
    OBTStepResult,
    OBTStorageBalance,
    OBTSolver,
    PlantBiologicalForcing,
)
from .obt_state import OBTState
from .ufotri_baseline import (
    SECONDS_PER_HOUR,
    UFOTRI_OBT_DAYLIGHT_MULTIPLIER,
    UFOTRI_OBT_FORMATION_PER_HOUR,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    UFOTRI_OBT_LOSS_PER_HOUR,
    UFOTRI_OBT_NIGHTTIME_MULTIPLIER,
    ufotri_obt_baseline_parameters,
)
from .validation import (
    INTEGRATED_ACTIVITY_UNIT,
    OBT_CONCENTRATION_UNIT,
    OBT_INVENTORY_UNIT,
    OBTInputError,
    OBTParameterError,
    OBTStateError,
    OBTUnitError,
    OBTValidationError,
    PLANT_MASS_UNIT,
    RATE_UNIT,
)

__all__ = [
    "INTEGRATED_ACTIVITY_UNIT",
    "OBT_CONCENTRATION_UNIT",
    "OBT_INVENTORY_UNIT",
    "OBTInputError",
    "OBTParameterError",
    "OBTState",
    "OBTStateError",
    "OBTStepResult",
    "OBTStorageBalance",
    "OBTSolver",
    "OBTUnitError",
    "OBTValidationError",
    "OBTParameters",
    "PLANT_MASS_UNIT",
    "PlantBiologicalForcing",
    "RATE_UNIT",
    "SECONDS_PER_HOUR",
    "UFOTRI_OBT_DAYLIGHT_MULTIPLIER",
    "UFOTRI_OBT_FORMATION_PER_HOUR",
    "UFOTRI_OBT_KF_S",
    "UFOTRI_OBT_KR_S",
    "UFOTRI_OBT_LOSS_PER_HOUR",
    "UFOTRI_OBT_NIGHTTIME_MULTIPLIER",
    "ufotri_obt_baseline_parameters",
]
