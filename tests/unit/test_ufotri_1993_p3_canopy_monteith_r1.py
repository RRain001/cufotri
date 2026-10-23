"""KfK5194 P3 R1 source-anchored opt-in stomatal/canopy/Monteith tests."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    KFK5194P3InputError,
    kfk5194_1993_daylight_canopy,
    kfk5194_1993_monteith_et,
)
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs" / "ufotri_1993_manual_source_profile.yaml"


def _canopy_kwargs(**changes):
    p = load_1993_source_profile(CONFIG, selected_profile=PROFILE_ID)
    v = dict(
        profile=p,
        regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.0,
        radiation_balance_w_m2=300.0,
        half_response_radiation_w_m2=60.0,
        vapour_pressure_deficit_hpa=5.0,
        humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8,
        temperature_c=25.0,
        minimum_temperature_c=10.0,
        optimal_temperature_c=25.0,
        maximum_temperature_c=40.0,
        leaf_area_index=2.0,
        wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4,
        stanton_number=0.2,
    )
    v.update(changes)
    return v


def _et_kwargs(**changes):
    state = kfk5194_1993_daylight_canopy(**_canopy_kwargs())
    v = dict(
        profile=_canopy_kwargs()["profile"], canopy=state,
        net_radiation_w_m2=300.0,
        soil_surface_resistance_s_m=150.0,
        vapour_pressure_slope_pa_k=180.0,
        psychrometric_constant_pa_k=65.0,
        air_volumetric_heat_capacity_j_m3_k=1200.0,
        latent_heat_vaporization_j_kg=2.45e6,
    )
    v.update(changes)
    return v


def test_equations_4_to_10_reproduce_independent_hand_calculation():
    r = kfk5194_1993_daylight_canopy(**_canopy_kwargs())
    assert r.temperature_exponent == 1.0
    assert r.temperature_factor == 1.0
    assert r.humidity_factor == 0.8
    assert r.stomatal_resistance_s_m == pytest.approx(187.5)
    assert r.canopy_resistance_s_m == pytest.approx(93.75)
    assert r.aerodynamic_resistance_s_m == pytest.approx(25.0)
    assert r.boundary_resistance_s_m == pytest.approx(12.5)
    assert r.leaf_total_resistance_s_m == pytest.approx(225.0)
    assert r.canopy_total_resistance_s_m == pytest.approx(131.25)
    assert r.atmosphere_resistance_s_m == pytest.approx(37.5)
    assert r.provenance()["whole_1993_runtime_activated"] is False


@pytest.mark.parametrize("temp", [13.0, 20.0, 30.0, 37.0])
def test_eq8_temperature_factor_reduces_resistance_at_optimum(temp):
    optimal = kfk5194_1993_daylight_canopy(**_canopy_kwargs())
    other = kfk5194_1993_daylight_canopy(**_canopy_kwargs(temperature_c=temp))
    assert other.temperature_factor < optimal.temperature_factor
    assert other.stomatal_resistance_s_m > optimal.stomatal_resistance_s_m


def test_source_radiation_humidity_soil_water_and_lai_sensitivities():
    base = kfk5194_1993_daylight_canopy(**_canopy_kwargs())
    more_light = kfk5194_1993_daylight_canopy(
        **_canopy_kwargs(radiation_balance_w_m2=600.0))
    drier_air = kfk5194_1993_daylight_canopy(
        **_canopy_kwargs(vapour_pressure_deficit_hpa=10.0))
    drought = kfk5194_1993_daylight_canopy(
        **_canopy_kwargs(soil_water_factor=0.4))
    large_lai = kfk5194_1993_daylight_canopy(
        **_canopy_kwargs(leaf_area_index=4.0))
    assert more_light.stomatal_resistance_s_m < base.stomatal_resistance_s_m
    assert drier_air.stomatal_resistance_s_m > base.stomatal_resistance_s_m
    assert drought.stomatal_resistance_s_m > base.stomatal_resistance_s_m
    assert large_lai.canopy_resistance_s_m == pytest.approx(
        base.canopy_resistance_s_m / 2)


def test_eq11_radiation_partition_and_explicit_dimensional_water_mass_flux():
    r = kfk5194_1993_monteith_et(**_et_kwargs())
    attenuation = math.exp(-0.398 * 2.0)
    assert r.soil_radiation_w_m2 == pytest.approx(300 * attenuation)
    assert r.plant_radiation_w_m2 == pytest.approx(300 * (1 - attenuation))
    assert r.net_radiation_partition_residual_w_m2 == pytest.approx(0, abs=1e-12)
    denominator_leaf = 180 + 65 * (1 + 93.75 / 37.5)
    denominator_soil = 180 + 65 * (1 + 150 / 37.5)
    aerodynamics = 1200 * 500 / 37.5
    assert r.plant_latent_heat_flux_w_m2 == pytest.approx(
        (180 * r.plant_radiation_w_m2 + aerodynamics) / denominator_leaf)
    assert r.soil_latent_heat_flux_w_m2 == pytest.approx(
        (180 * r.soil_radiation_w_m2 + aerodynamics) / denominator_soil)
    assert r.total_water_flux_kg_m2_s == pytest.approx(
        (r.plant_latent_heat_flux_w_m2 + r.soil_latent_heat_flux_w_m2) / 2.45e6)
    assert r.provenance()["original_executable_equivalence"] == "NOT_ESTABLISHED"


@pytest.mark.parametrize("lai", [0.1, 1.0, 3.0, 10.0])
def test_lai_shading_energy_conserves_and_finite(lai):
    state = kfk5194_1993_daylight_canopy(**_canopy_kwargs(leaf_area_index=lai))
    r = kfk5194_1993_monteith_et(**_et_kwargs(canopy=state))
    assert r.net_radiation_partition_residual_w_m2 == pytest.approx(0, abs=1e-10)
    assert all(math.isfinite(x) and x >= 0 for x in (
        r.plant_latent_heat_flux_w_m2, r.soil_latent_heat_flux_w_m2,
        r.plant_water_flux_kg_m2_s, r.soil_water_flux_kg_m2_s))


@pytest.mark.parametrize("updates", [
    {"regime": "NIGHT"}, {"regime": "DAYLIGHT_RAIN"},
    {"radiation_balance_w_m2": 0}, {"half_response_radiation_w_m2": -1},
    {"minimum_stomatal_resistance_s_m": 0},
    {"vapour_pressure_deficit_hpa": -1},
    {"humidity_sensitivity_per_hpa": 0.2},
    {"soil_water_factor": 0},
    {"soil_water_factor": 1.5},
    {"temperature_c": 10}, {"temperature_c": 40},
    {"optimal_temperature_c": 41}, {"leaf_area_index": 0},
    {"friction_velocity_m_s": 0}, {"stanton_number": 0},
    {"wind_speed_at_reference_m_s": float("inf")},
    {"temperature_c": float("nan")},
])
def test_inadmissible_canopy_inputs_fail_closed(updates):
    with pytest.raises(KFK5194P3InputError):
        kfk5194_1993_daylight_canopy(**_canopy_kwargs(**updates))


@pytest.mark.parametrize("updates", [
    {"net_radiation_w_m2": -1},
    {"soil_surface_resistance_s_m": 0},
    {"vapour_pressure_slope_pa_k": 0},
    {"psychrometric_constant_pa_k": -1},
    {"air_volumetric_heat_capacity_j_m3_k": 0},
    {"latent_heat_vaporization_j_kg": float("nan")},
])
def test_monteith_nonphysical_inputs_fail_closed(updates):
    with pytest.raises(KFK5194P3InputError):
        kfk5194_1993_monteith_et(**_et_kwargs(**updates))


def test_version_identity_and_legacy_runtime_isolation():
    d = _canopy_kwargs()
    for altered in (
        replace(d["profile"], profile_id="KFK4605_1990"),
        replace(d["profile"], flag_defaults=tuple(
            (k, 0 if k == "IMONT" else v)
            for k, v in d["profile"].flag_defaults)),
    ):
        with pytest.raises(KFK5194P3InputError):
            kfk5194_1993_daylight_canopy(**_canopy_kwargs(profile=altered))
    for file in ("src/cteas_ufotri/config.py", "src/cteas_ufotri/cli.py",
                 "src/cteas_ufotri/plant/leaf_ufotri_v4/model.py"):
        assert "kfk5194_1993_canopy_et" not in (ROOT / file).read_text(encoding="utf-8")


def test_monteith_zero_radiation_still_has_aerodynamic_evaporation():
    r = kfk5194_1993_monteith_et(**_et_kwargs(net_radiation_w_m2=0))
    assert r.plant_radiation_w_m2 == 0
    assert r.soil_radiation_w_m2 == 0
    assert r.plant_water_flux_kg_m2_s > 0
    assert r.soil_water_flux_kg_m2_s > 0
