"""Opt-in V4 UFOTRI-style three-layer soil core."""

from .soil_solver import (
    GlobalSoilBalanceV4,
    LayerSoilBalanceV4,
    ThreeLayerSoilForcing,
    ThreeLayerSoilParameters,
    ThreeLayerSoilStepResult,
    ThreeLayerSoilStorageSolver,
)
from .soil_state import SoilLayerStateV4, SoilV4Provenance, ThreeLayerSoilState
from .validation import (
    CANONICAL_LAYER_GEOMETRY,
    SoilV4InputError,
    SoilV4ParameterError,
    SoilV4StateError,
    SoilV4UnitError,
    SoilV4ValidationError,
)

__all__ = [
    "CANONICAL_LAYER_GEOMETRY",
    "GlobalSoilBalanceV4",
    "LayerSoilBalanceV4",
    "SoilLayerStateV4",
    "SoilV4InputError",
    "SoilV4ParameterError",
    "SoilV4Provenance",
    "SoilV4StateError",
    "SoilV4UnitError",
    "SoilV4ValidationError",
    "ThreeLayerSoilForcing",
    "ThreeLayerSoilParameters",
    "ThreeLayerSoilState",
    "ThreeLayerSoilStepResult",
    "ThreeLayerSoilStorageSolver",
]
