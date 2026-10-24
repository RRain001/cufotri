"""P2 R16: independent conditional area/time accounting; no production closure."""

from pathlib import Path
import math

import pytest
import yaml

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_photo_r2_audit import (
    audit_kfk5194_1993_eq28_canopy, audit_kfk5194_1993_eq30_respiration,
)
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    CO2_TO_DRY_MATTER_FACTOR,
    KFK5194CropOrgan, KFK5194OBTFormationMode, KFK5194SolarPeriod,
    KFK5194PhotoOBTError,
    kfk5194_1993_photo_rates, kfk5194_1993_obt_formation_rate,
)


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"
A = 0.36
B = 1.67e-4


@pytest.fixture(scope="module")
def profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


@pytest.fixture(scope="module")
def gates():
    y = yaml.safe_load((DOC / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    row = next(r for r in y["rows"] if r["id"] == "UF93-13")
    return y, row, row["p2_r16_eq28_eq30_area_time_closure"]


def gross(profile, lai, par):
    source = audit_kfk5194_1993_eq28_canopy(
        profile=profile,
        incident_par_w_m2_ground=par,
        lai_m2_leaf_per_m2_ground=lai,
        maximum_co2_g_m2_leaf_h=5.0,
        initial_light_efficiency_g_co2_per_w_h=0.012,
        respiration_g_co2_m2_leaf_h=0.0,
    )
    assert source.provenance()["production_runtime_activated"] is False
    return source.printed_eq28_pc_g_co2_m2_ground_h, source.integrated_eq26_27_pc_g_co2_m2_ground_h


def ground_simultaneous(g, biomass):
    """Only under a Pground/Rground/Wground common-area convention."""
    p = (g - B * biomass) / (1 + A)
    r = (A * g + B * biomass) / (1 + A)
    return p, r


@pytest.mark.parametrize("lai,par,biomass", [
    (0.2, 800.0, 200.0),
    (0.5, 100.0, 20.0),
    (1.0, 400.0, 500.0),
    (2.0, 800.0, 1200.0),
    (4.0, 300.0, 150.0),
])
def test_r16_both_unselected_gross_branches_balance_on_ground_area(profile, lai, par, biomass):
    printed, integrated = gross(profile, lai, par)
    for g in (printed, integrated):
        p, r = ground_simultaneous(g, biomass)
        assert math.fsum((p, r)) == pytest.approx(g, rel=2e-14, abs=1e-13)
        assert r == pytest.approx(A * p + B * biomass, rel=2e-14, abs=1e-13)
        # For positive P, compare against the production-independent Eq30 audit API.
        if p >= 0.0:
            source_r = audit_kfk5194_1993_eq30_respiration(
                profile=profile,
                canopy_pc_g_co2_m2_ground_h=p,
                accumulated_biomass_g_co2_equiv_m2_ground=biomass,
            )
            assert source_r.total_respiration_g_co2_m2_ground_h == pytest.approx(r)
            assert source_r.provenance()["implicit_eq28_coupling"] == "NOT_RECONSTRUCTED"


@pytest.mark.parametrize("lai", [0.3, 0.7, 1.0, 2.0, 3.5])
def test_r16_uniform_leaf_area_normalization_yields_ground_budget_if_lai_positive(lai):
    # Leaf-uniform assumption only. No biological heterogeneity assertion.
    gross_ground, biomass_ground = 3.0, 200.0
    p_ground, r_ground = ground_simultaneous(gross_ground, biomass_ground)
    p_leaf = p_ground / lai
    w_leaf = biomass_ground / lai
    r_leaf = A * p_leaf + B * w_leaf
    assert lai * r_leaf == pytest.approx(r_ground)
    assert p_ground + lai * r_leaf == pytest.approx(gross_ground)


@pytest.mark.parametrize("lai", [0.2, 0.6, 2.0, 4.0])
def test_r16_mixed_area_r8_scale_is_only_a_negative_control(lai):
    gross_ground, biomass_ground = 4.0, 220.0
    coherent_p, _ = ground_simultaneous(gross_ground, biomass_ground)
    mixed_p = (gross_ground - lai * B * biomass_ground) / (1 + lai * A)
    assert abs(mixed_p - coherent_p) > 1e-4
    # The two numerical results do NOT represent competing calibrated physics:
    # the mixed branch reuses ground-normalized P and W as leaf densities.


def test_r16_zero_lai_cannot_define_uniform_leaf_density(profile, gates):
    _, _, gate = gates
    printed, integrated = gross(profile, 0.0, 500.0)
    assert integrated == pytest.approx(0.0, abs=1e-13)
    assert printed > 0.0  # Printed Eq28 inconsistency remains
    # No fabricated epsilon or numerical P_leaf=P_ground/LAI at LAI==0.
    assert gate["lai_zero_leaf_normalization"] == "UNDEFINED_NEEDS_SEPARATE_SOURCE_BRANCH"
    assert gate["coupled_1993_obt_production_eligible"] is False


def test_r16_zero_light_signed_negative_net_is_rejected_by_daytime_interfaces(profile):
    printed, integrated = gross(profile, 2.0, 0.0)
    assert printed == pytest.approx(0.0) and integrated == pytest.approx(0.0)
    pc, _ = ground_simultaneous(integrated, 800.0)
    assert pc < 0
    with pytest.raises(KFK5194PhotoOBTError):
        audit_kfk5194_1993_eq30_respiration(
            profile=profile,
            canopy_pc_g_co2_m2_ground_h=pc,
            accumulated_biomass_g_co2_equiv_m2_ground=800.0,
        )
    with pytest.raises(KFK5194PhotoOBTError):
        kfk5194_1993_photo_rates(
            profile=profile, incident_par_w_m2_ground=0.0,
            leaf_depth_lai=0.5, total_leaf_area_index=2.0,
            maximum_co2_g_m2_leaf_h=5.0,
            initial_light_efficiency_g_co2_per_w_h=0.012,
            respiration_g_co2_m2_leaf_h=0.2,
            externally_integrated_canopy_co2_g_m2_ground_h=pc,
            externally_determined_stomatal_stress_fraction=0.8,
        )


def test_r16_sequential_lag_and_simultaneous_current_hour_are_distinct():
    biomass = 300.0
    previous_gross = 0.8
    current_gross = 3.0
    previous_p, _ = ground_simultaneous(previous_gross, biomass)
    simultaneous_p, _ = ground_simultaneous(current_gross, biomass)
    sequential_p = current_gross - (A * previous_p + B * biomass)
    assert sequential_p != pytest.approx(simultaneous_p)
    assert current_gross - sequential_p == pytest.approx(A * previous_p + B * biomass)
    # Neither formula is selected by printed historical source or this test.


def test_r16_mitchell_biomass_factor_not_eq31_drymatter_factor(gates):
    _, _, g = gates
    assert CO2_TO_DRY_MATTER_FACTOR == g["eq31_dry_matter_multiplier"] == 1.5
    mitchell_dry_per_co2_eq = 30 / 44
    mitchell_co2_eq_per_dry = 44 / 30
    assert mitchell_dry_per_co2_eq == pytest.approx(g["mitchell_co2_equiv_to_dry_matter_multiplier"])
    assert mitchell_co2_eq_per_dry == pytest.approx(g["mitchell_dry_matter_to_co2_equiv_multiplier"])
    assert (mitchell_dry_per_co2_eq * mitchell_co2_eq_per_dry) == pytest.approx(1.0)
    # Only the same conversion orientation is numerically comparable.
    assert CO2_TO_DRY_MATTER_FACTOR / mitchell_dry_per_co2_eq == pytest.approx(2.2)
    assert g["eq31_vs_mitchell_converter_interchangeability"] == (
        "OPPOSITE_CONVERSION_DIRECTION_FOR_44_DIV_30_NOT_SUBSTITUTABLE"
    )


def test_r16_l2_rate_only_interface_requires_explicit_external_canopy_input(profile):
    # Exercise the genuine opt-in Eq31/33 boundary, not fake 1993 model coupling.
    positive_net_ground = 2.0  # explicitly synthetic, externally declared
    photo = kfk5194_1993_photo_rates(
        profile=profile,
        incident_par_w_m2_ground=400.0,
        leaf_depth_lai=0.5,
        total_leaf_area_index=2.0,
        maximum_co2_g_m2_leaf_h=5.0,
        initial_light_efficiency_g_co2_per_w_h=0.012,
        respiration_g_co2_m2_leaf_h=0.1,
        externally_integrated_canopy_co2_g_m2_ground_h=positive_net_ground,
        externally_determined_stomatal_stress_fraction=0.8,
    )
    assert photo.actual_dry_matter_g_m2_ground_h == pytest.approx(positive_net_ground * 1.5 * .8)
    assert photo.provenance()["canopy_integral_eq28"] == "EXTERNAL_INPUT_NOT_RECONSTRUCTED"
    formation = kfk5194_1993_obt_formation_rate(
        profile=profile,
        crop_organ=KFK5194CropOrgan.LEAFY_VEGETABLE_WHOLE,
        mode=KFK5194OBTFormationMode.ADVANCED_EQ33_DAYLIGHT_ONLY,
        solar_period=KFK5194SolarPeriod.DAY,
        mean_uniform_transfer_d_1=0.024,  # synthetic transfer rate: NOT site input
        photosynthesis=photo,
        external_mean_dry_matter_g_m2_ground_h=1.2,
        external_nonuniform_distribution_fraction=0.5,
    )
    assert formation.actual_transfer_h_1 == pytest.approx(
        (2.4 / 1.2) * (.024 / 24) * 1.75 * .5
    )
    assert formation.provenance()["production_runtime_activated"] is False
    assert formation.provenance()["obs_or_fortran_validation"] == "NOT_ESTABLISHED"


def test_r16_source_branch_and_scientific_gates_fail_closed(gates):
    y, row, g = gates
    assert y["baseline_version"] == "KFK4605_1990"
    assert y["runtime_1993_profile_activated"] is False
    assert g["historical_eq28_choice"] == "NOT_ESTABLISHED"
    assert g["original_eq30_iteration_and_time"] == "NOT_ESTABLISHED"
    assert g["temporal_lag_source_assumption"] == "NOT_ESTABLISHED"
    assert g["eq29_pm_conversion_to_eq26"] == "NOT_ESTABLISHED"
    assert g["mixed_ground_inputs_as_leaf_rates"] == "PROHIBITED_AREA_DIMENSION_MISMATCH"
    assert g["lai_zero_leaf_normalization"] == "UNDEFINED_NEEDS_SEPARATE_SOURCE_BRANCH"
    assert g["zero_par_with_biomass"] == "SIGNED_NEGATIVE_PC_NOT_OBT_FORMATION"
    assert g["eq33_pm_mean_dry_matter_vs_eq29_pm_leaf_maximum"] == (
        "DISTINCT_QUANTITIES_DO_NOT_CONFLATE"
    )
    assert g["coupled_1993_obt_production_eligible"] is False
    assert g["original_executable_parity"] == "NOT_RUN"
    assert g["independent_scientific_review"] == "NOT_RUN"
    assert g["production_coupling_allowed"] is False
    assert row["p2_r15_table3_table7_uncertainty_discrimination"]["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False
    packet = ROOT / g["audit_packet"]
    assert packet.is_file()
    packet_text = packet.read_text(encoding="utf-8")
    for token in ("NOT_IDENTIFIED", "NOT_RUN", "PROHIBITED"):
        assert token.lower() in packet_text.lower()
    assert "do not" in packet_text.lower()
    assert packet.name in (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
