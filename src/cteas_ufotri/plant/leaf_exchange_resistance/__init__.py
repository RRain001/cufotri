"""V3-P6.2B-1 leaf-exchange resistance subsystem.

This package is intentionally separate from the existing V1/V2
``plant.leaf_exchange`` module. It exposes only resistance, forcing validation,
and a signed flux placeholder; it does not implement TFWT, OBT, roots, soil,
or dose.
"""

from .resistance import (
    DEFAULT_PARAMETER_NAMES,
    ParameterDatabaseProtocol,
    ResistanceChain,
    build_resistance_chain,
    exchange_coefficient,
    leaf_exchange_flux,
    signed_leaf_exchange_flux,
    total_resistance,
)
from .types import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    LeafExchangeFlux,
    ResistanceCoordinates,
    ResistanceState,
)
from .validation import (
    CONCENTRATION_UNIT,
    EXCHANGE_VELOCITY_UNIT,
    FLUX_UNIT,
    InvalidForcingError,
    InvalidResistanceError,
    MissingParameterError,
    ParameterUseNotAllowedError,
    RESISTANCE_UNIT,
    ResistanceSubsystemError,
    UnitMismatchError,
)

__all__ = [
    "AtmosphericHTOForcing",
    "CONCENTRATION_UNIT",
    "DEFAULT_PARAMETER_NAMES",
    "EXCHANGE_VELOCITY_UNIT",
    "FLUX_UNIT",
    "ForcingProvenance",
    "InvalidForcingError",
    "InvalidResistanceError",
    "LeafExchangeFlux",
    "MissingParameterError",
    "ParameterDatabaseProtocol",
    "ParameterUseNotAllowedError",
    "ResistanceChain",
    "ResistanceCoordinates",
    "ResistanceState",
    "RESISTANCE_UNIT",
    "ResistanceSubsystemError",
    "UnitMismatchError",
    "build_resistance_chain",
    "exchange_coefficient",
    "leaf_exchange_flux",
    "signed_leaf_exchange_flux",
    "total_resistance",
]
