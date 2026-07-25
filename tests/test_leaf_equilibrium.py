from __future__ import annotations

from copy import deepcopy
import math

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from cteas_ufotri.plant.leaf_exchange import bidirectional_leaf_exchange


TEMPERATURE_K = 293.15
PLANT_WATER_BQ_M3 = 5.0e10
ISOTOPE_FRACTIONATION = 1.1
WATER_DENSITY_KG_M3 = 1000.0


def _dewpoint_for_rh(relative_humidity: float) -> float:
    temperature_c = TEMPERATURE_K - 273.15
    saturated_pa = 610.78 * math.exp(
        17.2694 * temperature_c / (temperature_c + 237.29)
    )
    log_ratio = math.log(relative_humidity * saturated_pa / 610.78)
    dewpoint_c = 237.29 * log_ratio / (17.2694 - log_ratio)
    return dewpoint_c + 273.15


def _exchange(relative_humidity: float):
    return bidirectional_leaf_exchange(
        1.0e6,
        PLANT_WATER_BQ_M3,
        TEMPERATURE_K,
        _dewpoint_for_rh(relative_humidity),
        3.0,
        True,
        wind_speed_m_s=2.0,
        stability_class="D",
        roughness_length_m=0.1,
        canopy_height_m=0.5,
        wind_measurement_height_m=10.0,
        leaf_characteristic_length_m=0.05,
        air_kinematic_viscosity_m2_s=1.5e-5,
        water_vapour_diffusivity_m2_s=2.5e-5,
        stomatal_resistance_day_s_m=400.0,
        stomatal_resistance_night_s_m=6000.0,
        vpd_sensitivity_per_kpa=0.5,
        isotope_fractionation_liquid_to_vapour=ISOTOPE_FRACTIONATION,
        water_density_kg_m3=WATER_DENSITY_KG_M3,
    )


def test_eq27_uses_saturated_vapour_density_independent_of_rh():
    temperature_c = TEMPERATURE_K - 273.15
    saturated_pressure_pa = 610.78 * math.exp(
        17.2694 * temperature_c / (temperature_c + 237.29)
    )
    rho_v_sat = saturated_pressure_pa / (461.5 * TEMPERATURE_K)
    expected_bq_m3 = (
        PLANT_WATER_BQ_M3
        * rho_v_sat
        / (ISOTOPE_FRACTIONATION * WATER_DENSITY_KG_M3)
    )

    equilibria = [
        _exchange(relative_humidity).equilibrium_air_concentration_bq_m3
        for relative_humidity in (0.3, 0.6, 0.9)
    ]

    assert equilibria == pytest.approx([expected_bq_m3] * 3, rel=1.0e-14)


@pytest.mark.parametrize("relative_humidity", (0.3, 0.6, 0.9))
def test_eq27_leaf_path_reaches_flux_tfwt_obt_and_dose(relative_humidity: float):
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_leaf_exchange_food_dose_72h.yaml",
    )
    config = deepcopy(config)
    config["synthetic_forcing"]["mean_temperature_k"] = TEMPERATURE_K
    config["synthetic_forcing"]["temperature_amplitude_k"] = 0.0
    config["synthetic_forcing"]["dewpoint_depression_k"] = (
        TEMPERATURE_K - _dewpoint_for_rh(relative_humidity)
    )

    frame = run_short_case(config)
    final = frame.iloc[-1]

    assert frame["leaf_uptake_flux"].max() > 0.0
    assert final["plant_tfwt_inventory"] > 0.0
    assert final["plant_obt_inventory"] > 0.0
    assert final["plant_ingestion_dose_sv"] > 0.0
    assert frame["surface_box_relative_residual"].abs().max() < 1.0e-12
