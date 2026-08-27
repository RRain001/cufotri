"""Controlled UFOTRI three-layer root water-uptake distribution profile."""

from __future__ import annotations

from datetime import datetime

from .root_solver import ThreeLayerRootWaterFluxForcingV4
from .root_state import RootWaterFluxProvenanceV4
from .validation import (
    WATER_FLUX_UNIT,
    RootV4InputError,
    require_finite,
    require_unit,
)

# KfK 4605 chapter 3.3.2: 20%, 40%, 40% of total plant water uptake
# are assigned to the 0-5, 5-15 and 15-30 cm root-zone layers.
UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS = (0.2, 0.4, 0.4)
UFOTRI_ROOT_LAYER_IDS = ("L1", "L2", "L3")


def ufotri_root_water_uptake_fluxes(
    total_water_uptake_flux_m_s: float,
    *,
    water_flux_unit: str = WATER_FLUX_UNIT,
) -> tuple[float, float, float]:
    """Distribute an explicit total plant-water uptake flux by UFOTRI 20/40/40.

    This function does not infer the total uptake from meteorology, soil state,
    a transfer-rate constant, or a hidden hydrology/transpiration model.
    """

    require_unit(water_flux_unit, WATER_FLUX_UNIT, field="total_water_uptake_flux")
    total = require_finite(
        total_water_uptake_flux_m_s,
        field="total_water_uptake_flux_m_s",
    )
    if total < 0.0:
        raise RootV4InputError("total_water_uptake_flux_m_s must be non-negative")
    return tuple(total * fraction for fraction in UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS)  # type: ignore[return-value]


def ufotri_three_layer_root_water_flux_forcing(
    *,
    total_water_uptake_flux_m_s: float,
    plant_identifier: str,
    timestamp: datetime,
    provenance: RootWaterFluxProvenanceV4,
    water_flux_unit: str = WATER_FLUX_UNIT,
) -> ThreeLayerRootWaterFluxForcingV4:
    """Build typed V4 root forcing from an explicit total flux and UFOTRI fractions."""

    layer_fluxes = ufotri_root_water_uptake_fluxes(
        total_water_uptake_flux_m_s,
        water_flux_unit=water_flux_unit,
    )
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=plant_identifier,
        timestamp=timestamp,
        water_uptake_fluxes_m_s=layer_fluxes,
        provenance=provenance,
        water_flux_unit=water_flux_unit,
    )


__all__ = [
    "UFOTRI_ROOT_LAYER_IDS",
    "UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS",
    "ufotri_root_water_uptake_fluxes",
    "ufotri_three_layer_root_water_flux_forcing",
]
