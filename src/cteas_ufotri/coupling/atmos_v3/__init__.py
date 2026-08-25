"""V3 P7 atmospheric forcing coupling interface.

This package is a typed, immutable interface layer. It accepts atmospheric
forcing and adapts it only to the existing leaf-resistance and soil forcing
inputs. It does not implement atmospheric dispersion, hydrology, downstream
compartment or assessment solvers, parameter loading, or external-model
integration.
"""

from .forcing import AtmosphericHTOForcing
from .metadata import AtmosphericForcingMetadata
from .validation import (
    AIR_CONCENTRATION_UNIT,
    DEPOSITION_FLUX_UNIT,
    HUMIDITY_UNIT,
    PRECIPITATION_UNIT,
    TEMPERATURE_UNIT,
    TIME_RESOLUTION_UNIT,
    WIND_SPEED_UNIT,
    AtmosV3ValidationError,
    AtmosphericForcingError,
    AtmosphericMetadataError,
    AtmosphericUnitError,
)


__all__ = [
    "AIR_CONCENTRATION_UNIT",
    "AtmosV3ValidationError",
    "AtmosphericForcingError",
    "AtmosphericForcingMetadata",
    "AtmosphericHTOForcing",
    "AtmosphericMetadataError",
    "AtmosphericUnitError",
    "DEPOSITION_FLUX_UNIT",
    "HUMIDITY_UNIT",
    "PRECIPITATION_UNIT",
    "TEMPERATURE_UNIT",
    "TIME_RESOLUTION_UNIT",
    "WIND_SPEED_UNIT",
]
