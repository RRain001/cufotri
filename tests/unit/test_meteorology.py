import numpy as np

from cteas_ufotri.meteorology.derived_variables import (
    accumulated_to_flux,
    kelvin_to_celsius,
    relative_humidity,
    saturation_curve_slope_pa_k,
    vapour_pressure_deficit_pa,
    wind_speed_direction,
)
from cteas_ufotri.meteorology.fallback_fluxes import (
    partition_evapotranspiration,
    penman_ufotri_m_s,
)


def test_saturated_air_and_wind():
    assert np.isclose(kelvin_to_celsius(273.15), 0.0)
    assert np.isclose(relative_humidity(293.15, 293.15), 1.0)
    assert np.isclose(vapour_pressure_deficit_pa(293.15, 293.15), 0.0)
    assert saturation_curve_slope_pa_k(293.15) > 0
    speed, _ = wind_speed_direction(3.0, 4.0)
    assert np.isclose(speed, 5.0)
    assert np.isclose(accumulated_to_flux(3_600_000.0, 3600), 1000.0)


def test_penman_is_finite_positive_and_zero_without_energy_or_vpd():
    wet = penman_ufotri_m_s(
        293.15, 293.15, 3.0, 200.0, 2.45e6, 1000.0, 66.0, 0.001
    )
    zero = penman_ufotri_m_s(
        293.15, 293.15, 3.0, 0.0, 2.45e6, 1000.0, 66.0, 0.001
    )
    assert np.isfinite(wet) and wet > 0
    assert zero == 0.0


def test_lai_and_dryness_reduce_flux():
    wet0 = partition_evapotranspiration(1e-7, 0, 0.02, 0.02, 0.004)
    wet3 = partition_evapotranspiration(1e-7, 3, 0.02, 0.02, 0.004)
    dry3 = partition_evapotranspiration(1e-7, 3, 0.001, 0.02, 0.004)
    assert wet0.potential_soil_m_s > wet3.potential_soil_m_s
    assert wet0.potential_soil_m_s == wet0.potential_total_m_s
    assert dry3.soil_evaporation_m_s < wet3.soil_evaporation_m_s
    assert dry3.plant_transpiration_m_s == dry3.root_uptake_m_s == 0
