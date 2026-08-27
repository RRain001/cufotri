"""Opt-in V4 three-layer root water/HTO flux core."""

from .reference import UFOTRIRootReferenceEvidenceV4, UFOTRI_ROOT_REFERENCE_EVIDENCE_V4
from .root_solver import ThreeLayerRootFluxSolverV4, ThreeLayerRootWaterFluxForcingV4
from .root_state import LayerRootTransferV4, RootWaterFluxProvenanceV4, ThreeLayerRootFluxPlanV4
from .ufotri_eq39 import (
    EQ39_MODE,
    LAI_UNIT,
    LATENT_HEAT_UNIT,
    NET_RADIATION_UNIT,
    PSYCHROMETRIC_CONSTANT_UNIT,
    TEMPERATURE_UNIT,
    UFOTRIEq39RootUptakeInputV4,
    UFOTRIEq39RootUptakeResultV4,
    WATER_DENSITY_UNIT,
    WATER_STORAGE_UNIT,
    ufotri_eq39_potential_total_m_s,
    ufotri_eq39_root_uptake,
)
from .ufotri_profile import (
    UFOTRI_ROOT_LAYER_IDS,
    UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_root_water_uptake_fluxes,
    ufotri_three_layer_root_water_flux_forcing,
)
from .validation import (
    HTO_CONCENTRATION_UNIT,
    HTO_FLUX_UNIT,
    HTO_TRANSFER_UNIT,
    INTERVAL_UNIT,
    RootV4InputError,
    RootV4ProvenanceError,
    RootV4UnitError,
    RootV4ValidationError,
    WATER_FLUX_UNIT,
    WATER_TRANSFER_UNIT,
)

__all__ = [
    "EQ39_MODE",
    "HTO_CONCENTRATION_UNIT",
    "HTO_FLUX_UNIT",
    "HTO_TRANSFER_UNIT",
    "INTERVAL_UNIT",
    "LAI_UNIT",
    "LATENT_HEAT_UNIT",
    "LayerRootTransferV4",
    "NET_RADIATION_UNIT",
    "PSYCHROMETRIC_CONSTANT_UNIT",
    "RootV4InputError",
    "RootV4ProvenanceError",
    "RootV4UnitError",
    "RootV4ValidationError",
    "RootWaterFluxProvenanceV4",
    "TEMPERATURE_UNIT",
    "ThreeLayerRootFluxPlanV4",
    "ThreeLayerRootFluxSolverV4",
    "ThreeLayerRootWaterFluxForcingV4",
    "UFOTRIEq39RootUptakeInputV4",
    "UFOTRIEq39RootUptakeResultV4",
    "UFOTRIRootReferenceEvidenceV4",
    "UFOTRI_ROOT_REFERENCE_EVIDENCE_V4",
    "UFOTRI_ROOT_LAYER_IDS",
    "UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS",
    "WATER_DENSITY_UNIT",
    "WATER_FLUX_UNIT",
    "WATER_STORAGE_UNIT",
    "WATER_TRANSFER_UNIT",
    "ufotri_eq39_potential_total_m_s",
    "ufotri_eq39_root_uptake",
    "ufotri_root_water_uptake_fluxes",
    "ufotri_three_layer_root_water_flux_forcing",
]
