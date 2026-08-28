"""Opt-in UFOTRI grass/pasture 40/60/0 root-uptake distribution profile."""

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

# KfK 4605 grass/pasture role in the second ingestion system. The existing
# V2 parameter-source audit records this as a manual-direct root-fraction
# table: 40%, 60%, 0% in the 0-5, 5-15 and 15-30 cm layers.
UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS = (0.4, 0.6, 0.0)
UFOTRI_PASTURE_ROOT_LAYER_IDS = ("L1", "L2", "L3")
UFOTRI_PASTURE_ROOT_PROFILE_ID = "UFOTRI_PASTURE_40_60_0"


def ufotri_pasture_root_water_uptake_fluxes(
    total_water_uptake_flux_m_s: float,
    *,
    water_flux_unit: str = WATER_FLUX_UNIT,
) -> tuple[float, float, float]:
    """Distribute explicit total grass/pasture water uptake by 40/60/0.

    The total uptake remains an explicit upstream input. This profile performs
    only layer allocation and does not infer evapotranspiration, hydrology,
    plant demand, or a production parameter.
    """

    require_unit(water_flux_unit, WATER_FLUX_UNIT, field="total_water_uptake_flux")
    total = require_finite(
        total_water_uptake_flux_m_s,
        field="total_water_uptake_flux_m_s",
    )
    if total < 0.0:
        raise RootV4InputError("total_water_uptake_flux_m_s must be non-negative")
    return tuple(
        total * fraction for fraction in UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS
    )  # type: ignore[return-value]


def ufotri_pasture_three_layer_root_water_flux_forcing(
    *,
    total_water_uptake_flux_m_s: float,
    plant_identifier: str,
    timestamp: datetime,
    provenance: RootWaterFluxProvenanceV4,
    water_flux_unit: str = WATER_FLUX_UNIT,
) -> ThreeLayerRootWaterFluxForcingV4:
    """Build typed V4 root forcing for the opt-in pasture fidelity profile."""

    layer_fluxes = ufotri_pasture_root_water_uptake_fluxes(
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
    "UFOTRI_PASTURE_ROOT_LAYER_IDS",
    "UFOTRI_PASTURE_ROOT_PROFILE_ID",
    "UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS",
    "ufotri_pasture_root_water_uptake_fluxes",
    "ufotri_pasture_three_layer_root_water_flux_forcing",
]
