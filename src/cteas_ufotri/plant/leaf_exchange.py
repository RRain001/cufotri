from __future__ import annotations

from dataclasses import dataclass

from ..meteorology.derived_variables import (
    relative_humidity,
    saturation_vapour_pressure_pa,
    vapour_pressure_deficit_pa,
)


@dataclass(frozen=True)
class LeafExchange:
    net_to_plant_bq_m2_s: float
    conductance_m_s: float
    equilibrium_air_concentration_bq_m3: float
    relative_humidity: float
    vapour_pressure_deficit_pa: float


def bidirectional_leaf_exchange(
    air_concentration_bq_m3: float,
    plant_water_concentration_bq_m3: float,
    temperature_k: float,
    dewpoint_k: float,
    lai: float,
    is_day: bool,
    *,
    aerodynamic_resistance_s_m: float,
    boundary_resistance_s_m: float,
    stomatal_resistance_day_s_m: float,
    stomatal_resistance_night_s_m: float,
    vpd_sensitivity_per_kpa: float,
    isotope_fractionation_liquid_to_vapour: float,
    water_density_kg_m3: float,
) -> LeafExchange:
    """Manual-derived net HTO exchange through canopy resistance.

    Plant-water activity is converted to equilibrium air activity using actual
    atmospheric water-vapour density and the configured liquid/vapour isotope
    fractionation. Positive flux is air to plant; negative flux is re-release.
    """
    if lai <= 0:
        return LeafExchange(0.0, 0.0, 0.0, 0.0, 0.0)
    if min(
        aerodynamic_resistance_s_m,
        boundary_resistance_s_m,
        stomatal_resistance_day_s_m,
        stomatal_resistance_night_s_m,
        isotope_fractionation_liquid_to_vapour,
        water_density_kg_m3,
    ) <= 0:
        raise ValueError("Leaf-exchange resistances and conversion factors must be positive")
    if vpd_sensitivity_per_kpa < 0:
        raise ValueError("VPD sensitivity must be non-negative")
    rh = float(relative_humidity(temperature_k, dewpoint_k))
    vpd = float(vapour_pressure_deficit_pa(temperature_k, dewpoint_k))
    stomatal = (
        stomatal_resistance_day_s_m
        if is_day
        else stomatal_resistance_night_s_m
    )
    canopy = stomatal * (1.0 + vpd_sensitivity_per_kpa * vpd / 1000.0) / lai
    total_resistance = (
        aerodynamic_resistance_s_m + boundary_resistance_s_m + canopy
    )
    conductance = 1.0 / total_resistance
    actual_vapour_pressure = rh * float(saturation_vapour_pressure_pa(temperature_k))
    vapour_density = actual_vapour_pressure / (461.5 * temperature_k)
    equilibrium_air = (
        max(plant_water_concentration_bq_m3, 0.0)
        * vapour_density
        / (
            isotope_fractionation_liquid_to_vapour
            * water_density_kg_m3
        )
    )
    net = conductance * (
        max(air_concentration_bq_m3, 0.0) - equilibrium_air
    )
    return LeafExchange(net, conductance, equilibrium_air, rh, vpd)

