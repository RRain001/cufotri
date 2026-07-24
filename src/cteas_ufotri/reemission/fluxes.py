from __future__ import annotations

import math


def basic_reemission_fluxes(
    soil_evaporation_m_s: float,
    soil_concentration_bq_m3: float,
    plant_transpiration_m_s: float,
    plant_concentration_bq_m3: float,
) -> tuple[float, float, float]:
    soil = max(soil_evaporation_m_s, 0.0) * max(soil_concentration_bq_m3, 0.0)
    plant = max(plant_transpiration_m_s, 0.0) * max(plant_concentration_bq_m3, 0.0)
    return soil, plant, soil + plant
def ufotri_empirical_soil_reemission_bq_m2_s(
    soil_inventory_bq_m2: float,
    soil_evaporation_m_s: float,
    soil_water_m: float,
    drainage_fraction: float,
    elapsed_since_release_s: float,
    is_day: bool,
    *,
    reference_evaporation_m_s: float,
    reference_water_m: float,
    radiative_reference_fraction_h: float,
    diffusive_fraction_h: float,
    zt_half_life_h: float,
    ht_correction: float = 1.0,
) -> float:
    """Configurable Eq. (44-1)/(44-2) engineering reconstruction.

    ``radiative_reference_fraction_h`` is calibrated at the configured
    evaporation/water reference. ``diffusive_fraction_h`` applies day and night.
    ZT is an exponential post-release decrease. All fractional rates are per hour.
    """
    if soil_inventory_bq_m2 <= 0:
        return 0.0
    positive_required = (
        reference_evaporation_m_s,
        reference_water_m,
        zt_half_life_h,
    )
    if min(positive_required) <= 0:
        raise ValueError("Empirical re-emission reference values must be positive")
    if min(radiative_reference_fraction_h, diffusive_fraction_h, ht_correction) < 0:
        raise ValueError("Empirical re-emission factors must be non-negative")
    water = max(soil_water_m, 1.0e-15)
    evaporation_fraction_s = max(soil_evaporation_m_s, 0.0) / water
    reference_fraction_s = reference_evaporation_m_s / reference_water_m
    radiative_rate_s = 0.0
    if is_day:
        radiative_rate_s = (
            radiative_reference_fraction_h
            / 3600.0
            * evaporation_fraction_s
            / reference_fraction_s
            * max(1.0 - drainage_fraction, 0.0)
            * ht_correction
        )
    diffusive_rate_s = diffusive_fraction_h / 3600.0
    zt = math.exp(
        -math.log(2.0)
        * max(elapsed_since_release_s, 0.0)
        / (zt_half_life_h * 3600.0)
    )
    return soil_inventory_bq_m2 * (radiative_rate_s + diffusive_rate_s) * zt
