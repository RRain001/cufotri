"""V3-P6.3 isolated soil HTO inventory and transport pathway.

This package is provisional and opt-in. It consumes deposition and signed
layer-transport fluxes only; it does not alter V1/V2 runtime behavior or
connect root uptake, plant, foodchain, dose, CTEAS-Atmos, or UFOTRI parameters.
"""

from .soil_solver import (
    SoilForcing,
    SoilParameters,
    SoilStepResult,
    SoilStorageBalance,
    SoilStorageSolver,
)
from .soil_state import SoilProvenance, SoilState
from .validation import (
    FLUX_UNIT,
    HALF_LIFE_UNIT,
    INTEGRATED_ACTIVITY_UNIT,
    LAYER_DEPTH_UNIT,
    RATE_UNIT,
    SOIL_CONCENTRATION_UNIT,
    SOIL_INVENTORY_UNIT,
    SOIL_WATER_CONTENT_UNIT,
    SoilInputError,
    SoilParameterError,
    SoilStateError,
    SoilUnitError,
    SoilValidationError,
)

__all__ = [
    "FLUX_UNIT",
    "HALF_LIFE_UNIT",
    "INTEGRATED_ACTIVITY_UNIT",
    "LAYER_DEPTH_UNIT",
    "RATE_UNIT",
    "SOIL_CONCENTRATION_UNIT",
    "SOIL_INVENTORY_UNIT",
    "SOIL_WATER_CONTENT_UNIT",
    "SoilForcing",
    "SoilInputError",
    "SoilParameterError",
    "SoilParameters",
    "SoilProvenance",
    "SoilState",
    "SoilStateError",
    "SoilStepResult",
    "SoilStorageBalance",
    "SoilStorageSolver",
    "SoilUnitError",
    "SoilValidationError",
]
