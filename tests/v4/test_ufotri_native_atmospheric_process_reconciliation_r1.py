from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode,
    kfk4332_liftoff_evidence,
    kfk4332_source_depletion_integral_m,
    kfk5194_species_policy,
    kfk5194_washout,
    source_depletion_kfk4332,
    transport_straight_segment_reconciled,
)
from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    MOL_SMOOTH_TERRAIN_COEFFICIENTS,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    UFOTRINativeAtmosphereError,
    source_depletion_compatibility,
)


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_native_atmospheric_process_reconciliation_r1.py"
    )
    spec = importlib.util.spec_from_file_location("native_atmos_h4_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION"
    assert all(result["recovered_checks"].values())
    assert all(result["boundary_checks"].values())
    assert not any(result["forbidden_claims"].values())


def test_kfk5194_iwash0_coefficients_and_regtim_are_exact() -> None:
    mode = KFK5194HTOWashoutMode.PRECALCULATED_CLASSES
    cases = [
        (0.5, 6.0e-5, 0.5),
        (1.0, 1.0e-4, 0.75),
        (2.999999, 1.0e-4, 0.75),
        (3.0, 4.0e-4, 0.72),
        (8.0, 4.0e-4, 0.72),
    ]
    for intensity, expected_lambda, expected_duration in cases:
        result = kfk5194_washout(
            species=TritiumAtmosphericForm.HTO,
            precipitation_mm_h=intensity,
            mode=mode,
        )
        assert result.coefficient_s_1 == expected_lambda
        assert result.mean_relative_precipitation_duration == expected_duration
        assert result.source_status == "RECOVERED_KFK5194_IWASH0"


def test_kfk5194_iwash0_zero_rain_disables_current_washout() -> None:
    result = kfk5194_washout(
        species=TritiumAtmosphericForm.HTO,
        precipitation_mm_h=0.0,
        mode=KFK5194HTOWashoutMode.PRECALCULATED_CLASSES,
    )
    assert result.coefficient_s_1 == 0.0
    assert result.mean_relative_precipitation_duration == 0.5


def test_kfk5194_iwash1_power_law_is_exact_and_regtim_is_not_invented() -> None:
    intensity = 4.0
    result = kfk5194_washout(
        species=TritiumAtmosphericForm.HTO,
        precipitation_mm_h=intensity,
        mode=KFK5194HTOWashoutMode.POWER_LAW,
    )
    assert result.coefficient_s_1 == pytest.approx(9.0e-5 * intensity**0.6)
    assert result.mean_relative_precipitation_duration is None
    assert "REGTIM_SOURCE_LIMITED" in result.source_status


def test_ht_washout_remains_zero_in_both_kfk5194_modes() -> None:
    for mode in KFK5194HTOWashoutMode:
        result = kfk5194_washout(
            species=TritiumAtmosphericForm.HT,
            precipitation_mm_h=10.0,
            mode=mode,
        )
        assert result.coefficient_s_1 == 0.0
        policy = kfk5194_species_policy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
            precipitation_mm_h=10.0,
            mode=mode,
        )
        assert policy.wet_scavenging_rate_s_1 == 0.0


def test_ground_release_eq220_integral_matches_power_law_analytic_identity() -> None:
    x = 1000.0
    c = MOL_SMOOTH_TERRAIN_COEFFICIENTS["D"]
    expected = x ** (1.0 - c.q_z) / (c.p_z * (1.0 - c.q_z))
    actual = kfk4332_source_depletion_integral_m(
        downwind_m=x,
        effective_release_height_m=0.0,
        stability_class="D",
        mixing_lid_m=10000.0,
    )
    assert actual == pytest.approx(expected, rel=2.0e-13)


def test_elevated_release_has_smaller_eq220_dry_depletion_integral() -> None:
    ground = kfk4332_source_depletion_integral_m(
        downwind_m=5000.0,
        effective_release_height_m=0.0,
        stability_class="D",
        mixing_lid_m=560.0,
    )
    elevated = kfk4332_source_depletion_integral_m(
        downwind_m=5000.0,
        effective_release_height_m=60.0,
        stability_class="D",
        mixing_lid_m=560.0,
    )
    assert 0.0 < elevated < ground


def test_kfk4332_wet_eq227_matches_exponential_factor() -> None:
    source = 1.0e8
    x = 5000.0
    u = 5.0
    wet = 1.0e-4
    policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=0.0,
        hto_washout_coefficient_s_1=wet,
    )
    result = source_depletion_kfk4332(
        source_bq_s=source,
        downwind_m=x,
        wind_speed_m_s=u,
        effective_release_height_m=20.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )
    assert result.source_after_bq_s == pytest.approx(source * math.exp(-wet * x / u))
    assert result.dry_loss_bq_s == 0.0
    assert result.wet_loss_bq_s > 0.0
    assert result.residual_bq_s == pytest.approx(0.0, abs=1.0e-8)


def test_h4_source_depletion_supersedes_h1_controlled_approximation() -> None:
    policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HT,
        dry_deposition_velocity_m_s=5.0e-4,
    )
    h4 = source_depletion_kfk4332(
        source_bq_s=1.0e8,
        downwind_m=5000.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )
    h1 = source_depletion_compatibility(1.0e8, 5000.0, 5.0, 560.0, policy)
    assert h4.source_after_bq_s != pytest.approx(h1.source_after_bq_s, rel=1.0e-10)
    assert h4.residual_bq_s == pytest.approx(0.0, abs=1.0e-8)


def test_reconciled_transport_uses_recovered_source_strength() -> None:
    policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HT,
        dry_deposition_velocity_m_s=5.0e-4,
    )
    depletion = source_depletion_kfk4332(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )
    result = transport_straight_segment_reconciled(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=policy,
    )
    assert result.effective_source_bq_s == depletion.source_after_bq_s
    assert result.air_concentration_bq_m3 > 0.0
    assert result.dry_surface_flux_bq_m2_s == pytest.approx(
        result.air_concentration_bq_m3 * policy.dry_deposition_velocity_m_s
    )
    assert result.source_depletion_residual_bq_s == pytest.approx(0.0, abs=1.0e-8)
    assert result.atmospheric_ht_to_hto_generated_bq_s == 0.0


def test_liftoff_wake_and_plume_rise_numeric_gaps_remain_source_limited() -> None:
    evidence = kfk4332_liftoff_evidence()
    assert evidence.threshold_lp == 30.0
    assert evidence.thermal_buoyancy_dominates_above_threshold
    assert not evidence.numeric_equation_322_recovered
    assert not evidence.building_wake_complete_numerics_recovered
    assert not evidence.plume_rise_complete_numerics_recovered
    assert evidence.status == "SOURCE_LIMITED_EQ322_OCR_AMBIGUOUS"


def test_invalid_h4_inputs_fail_closed() -> None:
    with pytest.raises(UFOTRINativeAtmosphereError):
        kfk5194_washout(
            species=TritiumAtmosphericForm.HTO,
            precipitation_mm_h=-1.0,
            mode=KFK5194HTOWashoutMode.POWER_LAW,
        )
    with pytest.raises(UFOTRINativeAtmosphereError):
        kfk4332_source_depletion_integral_m(
            downwind_m=1000.0,
            effective_release_height_m=-1.0,
            stability_class="D",
            mixing_lid_m=560.0,
        )
