"""Independent calculations/discriminating tests for KfK5194 p.20 Eq28-30.

Tests are source arithmetic, not original 1993 FORTRAN parity or scientific
endorsement of either inconsistent Eq28 rendering.
"""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_r2_audit import (
    KFK5194PhotoOBTError,
    audit_kfk5194_1993_eq28_canopy,
    audit_kfk5194_1993_eq29_temperature,
    audit_kfk5194_1993_eq30_respiration,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _eq28(**changes):
    args = dict(
        profile=_profile(), incident_par_w_m2_ground=500.0,
        lai_m2_leaf_per_m2_ground=3.0,
        maximum_co2_g_m2_leaf_h=5.0,
        initial_light_efficiency_g_co2_per_w_h=0.012,
        respiration_g_co2_m2_leaf_h=0.1,
    )
    return audit_kfk5194_1993_eq28_canopy(**(args | changes))


def _eq29(**changes):
    args = dict(
        profile=_profile(), temperature_kelvin=298.15,
        co_source_mg_co2_m2_h=40.0,
        activation_energy_dh1_cal_mol=18000.0,
        denaturation_energy_dh2_cal_mol=40000.0,
        entropy_change_ds_cal_mol_kelvin=-10.0,
        gas_constant_r_cal_mol_kelvin=1.987,
    )
    return audit_kfk5194_1993_eq29_temperature(**(args | changes))


def _eq30(**changes):
    args = dict(
        profile=_profile(), canopy_pc_g_co2_m2_ground_h=6.0,
        accumulated_biomass_g_co2_equiv_m2_ground=1200.0,
    )
    return audit_kfk5194_1993_eq30_respiration(**(args | changes))


def test_r2_eq28_literal_transcription_vs_independent_direct_algebra():
    v = _eq28()
    par_bottom = 500.*0.6*math.exp(-0.6*3.)
    top = 5.+0.012*0.6*500.
    printed = 5./0.6*math.log(top/(5.+0.012*0.6*par_bottom)) - 0.1
    calculus = 5./0.6*math.log(top/(5.+0.012*par_bottom)) - 0.1*3.
    assert v.bottom_absorbed_par_w_m2_leaf == pytest.approx(par_bottom)
    assert v.printed_eq28_pc_g_co2_m2_ground_h == pytest.approx(printed)
    assert v.integrated_eq26_27_pc_g_co2_m2_ground_h == pytest.approx(calculus)
    assert v.printed_minus_integrated_g_co2_m2_ground_h == pytest.approx(
        printed-calculus
    )
    assert abs(v.printed_minus_integrated_g_co2_m2_ground_h) > 0.01
    assert v.provenance()["disposition"] == "FORMULAE_NOT_EQUIVALENT_DO_NOT_AUTO_SELECT"


@pytest.mark.parametrize("lai", [0.25, 0.8, 2.0, 4.0])
def test_r2_eq26_eq27_independent_midpoint_quadrature_agrees_only_with_calculus(lai):
    v = _eq28(lai_m2_leaf_per_m2_ground=lai)
    # Independent 10000-point canopy integral of Eq.(26) with Eq.(27):
    # gross hyperbolic CO2 saturation, minus respiration at each leaf depth.
    n = 10000
    delta = lai/n
    integrand = (
        5. * (0.012*500.*0.6*math.exp(-0.6*(j+.5)*delta))
        / (5. + (0.012*500.*0.6*math.exp(-0.6*(j+.5)*delta))) - 0.1
        for j in range(n)
    )
    independent = delta*math.fsum(integrand)
    assert v.integrated_eq26_27_pc_g_co2_m2_ground_h == pytest.approx(
        independent, rel=2e-9, abs=1e-10
    )
    assert v.printed_eq28_pc_g_co2_m2_ground_h != pytest.approx(
        independent, rel=1e-5, abs=1e-6
    )


def test_r2_eq28_zero_lai_exposes_nonzero_printed_result():
    z = _eq28(lai_m2_leaf_per_m2_ground=0., respiration_g_co2_m2_leaf_h=0.)
    assert z.integrated_eq26_27_pc_g_co2_m2_ground_h == pytest.approx(0., abs=1e-13)
    assert z.printed_eq28_pc_g_co2_m2_ground_h > 0.
    assert z.provenance()["exact_1993_fortran_or_empirical_equivalence"] == "NOT_ESTABLISHED"


def test_r2_eq28_zero_light_retains_distinct_respiration_basis():
    z = _eq28(incident_par_w_m2_ground=0.)
    assert z.printed_eq28_pc_g_co2_m2_ground_h == pytest.approx(-0.1)
    assert z.integrated_eq26_27_pc_g_co2_m2_ground_h == pytest.approx(-0.3)
    # Negative net potential is NOT a nonnegative OBT formation flux.


def test_r2_eq28_weak_light_and_zero_respiration_safe():
    z = _eq28(incident_par_w_m2_ground=0., respiration_g_co2_m2_leaf_h=0.)
    assert z.printed_eq28_pc_g_co2_m2_ground_h == 0.
    assert z.integrated_eq26_27_pc_g_co2_m2_ground_h == 0.


def test_r2_eq29_literal_direct_numerator_denominator_oracle_and_units_flag():
    r = _eq29()
    temperature = 298.15
    R = 1.987
    numerator = (0.158*40.*(10.**9)*temperature
                 * math.exp(-18000./(R*temperature)))
    denominator = (1. + math.exp(-40000./(R*temperature))
                   * math.exp(-(-10.)/R))
    assert r.printed_pm_raw == pytest.approx(numerator/denominator, rel=2e-13)
    assert r.provenance()["co_unit_printed"] == "MG_CO2_M2_H"
    assert r.provenance()["eq26_pm_unit_printed"] == "G_CO2_M2_H"
    assert r.provenance()["use_as_eq26_pm"] == (
        "PROHIBITED_WITHOUT_INDEPENDENT_UNIT_AUDIT"
    )


def test_r2_eq29_high_stress_exponent_stays_finite():
    # A direct exp(-deltaH2/(RT)-deltaS/R) would overflow.
    r = _eq29(
        co_source_mg_co2_m2_h=1.0,
        entropy_change_ds_cal_mol_kelvin=-2000.0,
        denaturation_energy_dh2_cal_mol=1.0,
    )
    assert r.printed_pm_raw >= 0.
    assert math.isfinite(r.printed_pm_raw)


def test_r2_eq29_co_zero_source_gives_zero_pm_and_no_synthetic_co2():
    assert _eq29(co_source_mg_co2_m2_h=0.).printed_pm_raw == 0.


def test_r2_eq30_independent_co2_equivalent_respiration_budget():
    r = _eq30()
    expected = 0.36*6.0 + 1.67e-4*1200.0
    assert r.total_respiration_g_co2_m2_ground_h == pytest.approx(expected)
    assert r.provenance()["biomass_basis"] == "CO2_EQUIVALENTS_NOT_RAW_DRY_MATTER"
    assert r.provenance()["implicit_eq28_coupling"] == "NOT_RECONSTRUCTED"


def test_r2_eq30_zero_pc_still_respiration_from_biomass():
    r = _eq30(canopy_pc_g_co2_m2_ground_h=0.)
    assert r.total_respiration_g_co2_m2_ground_h == pytest.approx(1.67e-4*1200.)


@pytest.mark.parametrize("key,value", [
    ("incident_par_w_m2_ground", -1.),
    ("lai_m2_leaf_per_m2_ground", float("nan")),
    ("lai_m2_leaf_per_m2_ground", True),
    ("maximum_co2_g_m2_leaf_h", 0.),
    ("initial_light_efficiency_g_co2_per_w_h", -1.),
    ("respiration_g_co2_m2_leaf_h", float("inf")),
])
def test_r2_invalid_eq28_inputs_fail_closed(key, value):
    with pytest.raises(KFK5194PhotoOBTError):
        _eq28(**{key: value})


@pytest.mark.parametrize("key,value", [
    ("temperature_kelvin", 0.),
    ("temperature_kelvin", float("nan")),
    ("co_source_mg_co2_m2_h", -1.),
    ("activation_energy_dh1_cal_mol", -1.),
    ("denaturation_energy_dh2_cal_mol", -1.),
    ("gas_constant_r_cal_mol_kelvin", 0.),
    ("entropy_change_ds_cal_mol_kelvin", float("inf")),
])
def test_r2_invalid_eq29_input_fails_closed(key, value):
    with pytest.raises(KFK5194PhotoOBTError):
        _eq29(**{key: value})


@pytest.mark.parametrize("key,value", [
    ("canopy_pc_g_co2_m2_ground_h", -1.),
    ("accumulated_biomass_g_co2_equiv_m2_ground", -1.),
    ("canopy_pc_g_co2_m2_ground_h", "6.0"),
    ("accumulated_biomass_g_co2_equiv_m2_ground", True),
])
def test_r2_invalid_eq30_input_fails_closed(key, value):
    with pytest.raises(KFK5194PhotoOBTError):
        _eq30(**{key: value})


def test_r2_explicit_profile_and_no_prod_imports():
    with pytest.raises(KFK5194PhotoOBTError):
        _eq28(profile=replace(_profile(), profile_id="KFK4605_1990"))
    with pytest.raises(KFK5194PhotoOBTError):
        _eq29(profile=replace(_profile(), profile_id="KFK4605_1990"))
    with pytest.raises(KFK5194PhotoOBTError):
        _eq30(profile=replace(_profile(), profile_id="KFK4605_1990"))
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        assert "kfk5194_1993_photo_r2_audit" not in (
            ROOT/path
        ).read_text(encoding="utf-8")
