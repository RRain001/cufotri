"""Independent hand-oracles for opt-in KfK5194 1993 P2 source-rate R1.

Software/dimensional checks only. No Eq28 canopy integration, physical
nighttime Eq33 reconstruction or original FORTRAN/field validation.
"""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    CO2_TO_DRY_MATTER_FACTOR, PAR_EXTINCTION_K,
    KFK5194CropOrgan as Crop, KFK5194OBTFormationMode as Mode,
    KFK5194SolarPeriod as Period, KFK5194PhotoOBTError,
    kfk5194_1993_photo_rates, kfk5194_1993_obt_formation_rate,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _photo(**overrides):
    data = {
        "profile": _profile(),
        "incident_par_w_m2_ground": 300.,
        "leaf_depth_lai": 0.8,
        "total_leaf_area_index": 2.0,
        "maximum_co2_g_m2_leaf_h": 6.0,
        "initial_light_efficiency_g_co2_per_w_h": 0.01,
        "respiration_g_co2_m2_leaf_h": 0.1,
        "externally_integrated_canopy_co2_g_m2_ground_h": 2.0,
        "externally_determined_stomatal_stress_fraction": 0.8,
    }
    return kfk5194_1993_photo_rates(**{**data, **overrides})


def _rate(**overrides):
    data = {
        "profile": _profile(),
        "crop_organ": Crop.LEAFY_VEGETABLE_WHOLE,
        "mode": Mode.SIMPLE_EQ32,
        "solar_period": Period.DAY,
        "mean_uniform_transfer_d_1": 0.024,
        "external_fig11_phenology_factor": 1.2,
    }
    return kfk5194_1993_obt_formation_rate(**{**data, **overrides})


def test_eq26_eq27_eq31_independent_hand_oracle_and_units():
    result = _photo()
    par = 300.0 * 0.6 * math.exp(-0.6 * 0.8)
    expected_co2 = (6.0 * (0.01 * par)) / (6.0 + (0.01 * par)) - 0.1
    assert PAR_EXTINCTION_K == 0.6
    assert CO2_TO_DRY_MATTER_FACTOR == 1.5
    assert result.absorbed_par_w_m2_leaf == pytest.approx(par, rel=1e-13)
    assert result.potential_co2_g_m2_leaf_h == pytest.approx(expected_co2)
    assert result.actual_dry_matter_g_m2_ground_h == pytest.approx(
        2.0 * 1.5 * 0.8
    )
    assert result.provenance()["canopy_integral_eq28"] == "EXTERNAL_INPUT_NOT_RECONSTRUCTED"
    assert result.provenance()["fortran_parity"] == "NOT_ESTABLISHED"


def test_zero_light_is_negative_net_due_to_respiration_not_silent_zero():
    result = _photo(
        incident_par_w_m2_ground=0.,
        externally_integrated_canopy_co2_g_m2_ground_h=0.,
    )
    assert result.absorbed_par_w_m2_leaf == 0.
    assert result.potential_co2_g_m2_leaf_h == pytest.approx(-0.1)
    assert result.actual_dry_matter_g_m2_ground_h == 0.


@pytest.mark.parametrize("depth", [0., 0.5, 2.])
def test_eq27_par_monotonically_attenuates_at_source_extinction(depth):
    result = _photo(leaf_depth_lai=depth)
    surface = _photo(leaf_depth_lai=0.).absorbed_par_w_m2_leaf
    assert result.absorbed_par_w_m2_leaf == pytest.approx(
        surface * math.exp(-0.6 * depth)
    )


def test_explicit_external_stress_zero_and_one_are_bounded():
    off = _photo(externally_determined_stomatal_stress_fraction=0.)
    on = _photo(externally_determined_stomatal_stress_fraction=1.)
    assert off.actual_dry_matter_g_m2_ground_h == 0.
    assert on.actual_dry_matter_g_m2_ground_h == pytest.approx(3.0)
    # The temperature/stomatal law is not invented: f(r) is only an input.
    assert off.provenance()["stomatal_stress"] == "EXPLICIT_INPUT_NOT_CALIBRATED"


@pytest.mark.parametrize("crop", list(Crop))
def test_eq32_all_four_printed_1993_organ_roles_and_empirical_daynight(crop):
    day = _rate(crop_organ=crop)
    night = _rate(crop_organ=crop, solar_period=Period.NIGHT)
    mean_h = 0.024 / 24.
    assert day.actual_transfer_h_1 == pytest.approx(mean_h * 1.2 * 1.75)
    assert night.actual_transfer_h_1 == pytest.approx(mean_h * 1.2 * 0.25)
    assert (day.actual_transfer_h_1 + night.actual_transfer_h_1) / 2. == (
        pytest.approx(mean_h * 1.2)
    )  # Only with an explicit 12-hour daytime/12-hour night partition
    assert day.actual_transfer_s_1 == pytest.approx(day.actual_transfer_h_1 / 3600.)
    assert day.provenance()["mean_transfer_rate"] == (
        "CALLER_SUPPLIED_DAILY_CROP_SPECIFIC_NOT_1990_DEFAULT"
    )


def test_eq33_daylight_mean_biomass_is_not_eq26_maximum_co2():
    photo = _photo()
    result = _rate(
        mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
        external_fig11_phenology_factor=None,
        photosynthesis=photo,
        external_mean_dry_matter_g_m2_ground_h=1.2,
        external_nonuniform_distribution_fraction=0.5,
    )
    # P_act=2.4 g dry matter / m2 ground / h, mean P_m=1.2 of SAME
    # quantity (not Eq26 P_m=6 g CO2 / m2 leaf / h).
    expected = (2.4/1.2) * (0.024/24.) * 1.75 * 0.5
    assert result.actual_transfer_h_1 == pytest.approx(expected)
    assert result.distribution_factor == 0.5
    assert result.factor_phenology is None
    assert result.provenance()["eq33_night_branch"] == "NOT_ESTABLISHED"


def test_eq33_zero_assimilation_gives_zero_daylight_formation():
    photo = _photo(
        incident_par_w_m2_ground=0.,
        externally_integrated_canopy_co2_g_m2_ground_h=0.,
        externally_determined_stomatal_stress_fraction=0.,
    )
    r = _rate(
        mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
        external_fig11_phenology_factor=None,
        photosynthesis=photo,
        external_mean_dry_matter_g_m2_ground_h=0.8,
        external_nonuniform_distribution_fraction=0.5,
    )
    assert r.actual_transfer_h_1 == 0.


def test_eq33_night_fails_closed_instead_of_inventing_25_percent_physics():
    with pytest.raises(KFK5194PhotoOBTError, match="night"):
        _rate(
            mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
            solar_period=Period.NIGHT,
            external_fig11_phenology_factor=None,
            photosynthesis=_photo(),
            external_mean_dry_matter_g_m2_ground_h=0.8,
            external_nonuniform_distribution_fraction=0.5,
        )


@pytest.mark.parametrize("key,bad", [
    ("crop_organ", None),
    ("crop_organ", "LEAFY_VEGETABLE_WHOLE"),
    ("mode", None),
    ("mode", "SIMPLE_EQ32"),
    ("solar_period", None),
    ("solar_period", "DAY"),
    ("mean_uniform_transfer_d_1", -0.01),
    ("mean_uniform_transfer_d_1", float("nan")),
    ("mean_uniform_transfer_d_1", True),
    ("external_fig11_phenology_factor", None),
    ("external_fig11_phenology_factor", -1.),
    ("external_fig11_phenology_factor", "1.0"),
])
def test_invalid_or_missing_explicit_source_rate_selection_rejected(key, bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _rate(**{key: bad})


@pytest.mark.parametrize("key,bad", [
    ("incident_par_w_m2_ground", -1.),
    ("incident_par_w_m2_ground", "300"),
    ("total_leaf_area_index", -1.),
    ("leaf_depth_lai", 2.01),
    ("maximum_co2_g_m2_leaf_h", 0.),
    ("initial_light_efficiency_g_co2_per_w_h", 0.),
    ("respiration_g_co2_m2_leaf_h", -0.1),
    ("externally_integrated_canopy_co2_g_m2_ground_h", -0.01),
    ("externally_determined_stomatal_stress_fraction", 1.01),
    ("externally_determined_stomatal_stress_fraction", float("inf")),
])
def test_invalid_or_dimensional_mixed_photosynthetic_inputs_rejected(key, bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _photo(**{key: bad})


def test_1993_profile_and_advanced_gate_fail_closed():
    with pytest.raises(KFK5194PhotoOBTError):
        _photo(profile=replace(_profile(), profile_id="KFK4605_1990"))
    with pytest.raises(KFK5194PhotoOBTError):
        _rate(mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
              external_fig11_phenology_factor=None)
    with pytest.raises(KFK5194PhotoOBTError):
        _rate(mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
              external_fig11_phenology_factor=None,
              photosynthesis=_photo(),
              external_mean_dry_matter_g_m2_ground_h=0.,
              external_nonuniform_distribution_fraction=0.5)
    with pytest.raises(KFK5194PhotoOBTError):
        _rate(mode=Mode.ADVANCED_EQ33_DAYLIGHT_ONLY,
              external_fig11_phenology_factor=None,
              photosynthesis=_photo(),
              external_mean_dry_matter_g_m2_ground_h=1.,
              external_nonuniform_distribution_fraction=1.1)


def test_no_default_solver_import_or_1990_parameter_replacement():
    for name in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        assert "kfk5194_1993_photo_obt_rates" not in (
            ROOT / name
        ).read_text(encoding="utf-8")
