from __future__ import annotations

from dataclasses import dataclass
import math

from .derived_variables import saturation_curve_slope_pa_k, vapour_pressure_deficit_pa


@dataclass(frozen=True)
class WaterFluxes:
    potential_total_m_s: float
    potential_soil_m_s: float
    soil_evaporation_m_s: float
    plant_transpiration_m_s: float
    root_uptake_m_s: float
    moisture_factor: float


def moisture_reduction(water_m: float, maximum_water_m: float) -> float:
    """UFOTRI Eq. (41), capped at one as a physical reduction factor."""
    if maximum_water_m <= 0:
        raise ValueError("maximum_water_m must be positive")
    ratio = max(water_m, 0.0) / maximum_water_m
    return min(1.0, 1.26 * (1.0 - math.exp(-10.56 * ratio)))


def penman_ufotri_m_s(
    temperature_k: float,
    dewpoint_k: float,
    wind_m_s: float,
    net_radiation_w_m2: float,
    latent_heat_j_kg: float,
    water_density_kg_m3: float,
    psychrometric_constant_pa_k: float,
    aerodynamic_coefficient_w_m2_pa: float,
) -> float:
    """UFOTRI Eq. (38) in SI.

    The manual's empirical aerodynamic term is dimensionally incomplete.
    ``aerodynamic_coefficient_w_m2_pa`` is therefore explicit and provisional.
    Setting it to zero yields the manual's Eq. (39) equilibrium form.
    """
    delta = float(saturation_curve_slope_pa_k(temperature_k))
    vpd = float(vapour_pressure_deficit_pa(temperature_k, dewpoint_k))
    wind_km_day = max(wind_m_s, 0.0) * 86.4
    radiation = max(net_radiation_w_m2, 0.0)
    aerodynamic = (
        aerodynamic_coefficient_w_m2_pa
        * (1.0 + 0.0061 * wind_km_day)
        * vpd
    )
    latent_flux = (delta * radiation + psychrometric_constant_pa_k * aerodynamic) / (
        delta + psychrometric_constant_pa_k
    )
    return max(latent_flux, 0.0) / latent_heat_j_kg / water_density_kg_m3


def partition_evapotranspiration(
    potential_total_m_s: float,
    lai: float,
    water_m: float,
    maximum_water_m: float,
    wilting_water_m: float,
) -> WaterFluxes:
    shade = math.exp(-0.398 * max(lai, 0.0))
    potential_soil = potential_total_m_s * shade
    factor = moisture_reduction(water_m, maximum_water_m)
    soil = potential_soil * factor
    plant = max(potential_total_m_s - potential_soil, 0.0) * factor
    if water_m <= wilting_water_m:
        plant = 0.0
    return WaterFluxes(potential_total_m_s, potential_soil, soil, plant, plant, factor)
