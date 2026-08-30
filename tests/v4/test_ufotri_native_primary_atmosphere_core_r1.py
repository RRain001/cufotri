from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import math
from pathlib import Path

import pytest

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    KFK4605_ITER_AIR_OXIDATION_FRACTION_D_1,
    KFK4605_ITER_HT_DRY_DEPOSITION_VELOCITY_M_S,
    KFK4605_ITER_HTO_DRY_DEPOSITION_VELOCITY_M_S,
    MOL_SMOOTH_TERRAIN_COEFFICIENTS,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    UFOTRINativeAtmosphereError,
    atmospheric_oxidation_evidence,
    gaussian_concentration_bq_m3,
    kfk4605_iter_benchmark_policy,
    mol_sigma_m,
    source_depletion_compatibility,
    split_release_into_hourly_slices,
    transport_straight_segment,
    wind_speed_power_law_m_s,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_native_primary_atmosphere_core_r1.py"
    )
    spec = importlib.util.spec_from_file_location("native_atmos_core_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE"
    assert all(result["manual_semantics"].values())
    assert all(result["numerical_checks"].values())
    assert not any(result["forbidden_claims"].values())


def test_table9_mol_coefficients_are_exactly_recovered_for_a_to_f() -> None:
    expected = {
        "A": (0.946, 0.796, 1.321, 0.711),
        "B": (0.826, 0.796, 0.950, 0.711),
        "C": (0.586, 0.796, 0.700, 0.711),
        "D": (0.418, 0.796, 0.520, 0.711),
        "E": (0.297, 0.796, 0.382, 0.711),
        "F": (0.235, 0.796, 0.311, 0.711),
    }
    assert set(MOL_SMOOTH_TERRAIN_COEFFICIENTS) == set(expected)
    for stability, values in expected.items():
        c = MOL_SMOOTH_TERRAIN_COEFFICIENTS[stability]
        assert (c.p_y, c.q_y, c.p_z, c.q_z) == values


def test_mol_sigma_uses_power_law_and_08_mixing_lid_cap() -> None:
    x = 1000.0
    sy, sz = mol_sigma_m(x, "D")
    assert sy == pytest.approx(0.418 * x**0.796, rel=1e-15)
    assert sz == pytest.approx(0.520 * x**0.711, rel=1e-15)

    _, capped = mol_sigma_m(1.0e6, "A", mixing_lid_m=100.0)
    assert capped == pytest.approx(80.0, rel=0.0, abs=1e-12)


def test_appendix_b_wind_power_law_is_literal() -> None:
    assert wind_speed_power_law_m_s(5.0, 60.0, 60.0, 0.34) == 5.0
    expected = 5.0 * (10.0 / 60.0) ** 0.34
    assert wind_speed_power_law_m_s(5.0, 60.0, 10.0, 0.34) == pytest.approx(expected)


def test_gaussian_concentration_matches_independent_image_source_identity() -> None:
    q = 1.2e8
    x = 1200.0
    y = 35.0
    u = 5.0
    h = 20.0
    z = 1.0
    sy, sz = mol_sigma_m(x, "D", mixing_lid_m=560.0)
    expected = (
        q
        / (2.0 * math.pi * u * sy * sz)
        * math.exp(-0.5 * (y / sy) ** 2)
        * (
            math.exp(-0.5 * ((z - h) / sz) ** 2)
            + math.exp(-0.5 * ((z + h) / sz) ** 2)
        )
    )
    actual = gaussian_concentration_bq_m3(
        q, x, y, u, h, z, "D", mixing_lid_m=560.0
    )
    assert actual == pytest.approx(expected, rel=1e-15)


def test_long_release_is_split_into_hourly_slices_without_activity_change() -> None:
    slices = split_release_into_hourly_slices(
        start_utc=T0,
        duration_s=9000.0,
        total_activity_bq=9.0e9,
        species=TritiumAtmosphericForm.HT,
        source_id="LONG_HT",
    )
    assert [item.duration_s for item in slices] == [3600.0, 3600.0, 1800.0]
    assert sum(item.released_activity_bq for item in slices) == pytest.approx(
        9.0e9, rel=0.0, abs=1e-6
    )
    assert len({item.emission_rate_bq_s for item in slices}) == 1


def test_kfk4605_species_policies_preserve_ht_hto_difference() -> None:
    ht = kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT)
    hto = kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HTO)
    assert ht.dry_deposition_velocity_m_s == KFK4605_ITER_HT_DRY_DEPOSITION_VELOCITY_M_S
    assert hto.dry_deposition_velocity_m_s == KFK4605_ITER_HTO_DRY_DEPOSITION_VELOCITY_M_S
    assert ht.dry_deposition_velocity_m_s == pytest.approx(5.0e-4)
    assert hto.dry_deposition_velocity_m_s == pytest.approx(1.8e-2)
    assert hto.dry_deposition_velocity_m_s / ht.dry_deposition_velocity_m_s == pytest.approx(36.0)


def test_ht_wet_deposition_is_fail_closed_but_explicit_hto_washout_is_allowed() -> None:
    with pytest.raises(UFOTRINativeAtmosphereError, match="HT wet deposition"):
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
            hto_washout_coefficient_s_1=1.0e-4,
        )

    hto = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=1.8e-2,
        hto_washout_coefficient_s_1=1.0e-4,
    )
    assert hto.wet_scavenging_rate_s_1 == 1.0e-4


def test_air_ht_to_hto_conversion_is_not_activated_in_kfk4605_path() -> None:
    evidence = atmospheric_oxidation_evidence()
    assert evidence.iter_benchmark_input_fraction_d_1 == KFK4605_ITER_AIR_OXIDATION_FRACTION_D_1
    assert evidence.iter_benchmark_input_fraction_d_1 == 0.005
    assert not evidence.section22_program_includes_air_conversion
    assert not evidence.active_in_kfk4605_fidelity_path
    assert evidence.source_conflict_preserved

    with pytest.raises(UFOTRINativeAtmosphereError, match="excludes atmospheric HT->HTO"):
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
            atmospheric_ht_to_hto_conversion_rate_s_1=0.005 / 86400.0,
        )


def test_source_depletion_activity_ledger_closes_for_ht() -> None:
    policy = kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT)
    dep = source_depletion_compatibility(1.0e8, 5000.0, 5.0, 560.0, policy)
    assert dep.source_after_bq_s < dep.source_before_bq_s
    assert dep.dry_loss_bq_s > 0.0
    assert dep.wet_loss_bq_s == 0.0
    assert dep.residual_bq_s == pytest.approx(0.0, abs=1.0e-8)


def test_hto_explicit_washout_is_accounted_without_creating_ht() -> None:
    policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=1.8e-2,
        hto_washout_coefficient_s_1=1.0e-4,
    )
    dep = source_depletion_compatibility(1.0e8, 5000.0, 5.0, 560.0, policy)
    assert dep.dry_loss_bq_s > 0.0
    assert dep.wet_loss_bq_s > 0.0
    assert dep.residual_bq_s == pytest.approx(0.0, abs=1.0e-8)


def test_straight_segment_returns_species_specific_air_and_surface_flux() -> None:
    ht = transport_straight_segment(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT),
    )
    assert ht.species is TritiumAtmosphericForm.HT
    assert ht.air_concentration_bq_m3 > 0.0
    assert ht.dry_surface_flux_bq_m2_s == pytest.approx(
        ht.air_concentration_bq_m3 * 5.0e-4
    )
    assert ht.atmospheric_ht_to_hto_generated_bq_s == 0.0
    assert ht.wet_source_loss_bq_s == 0.0
    assert ht.source_depletion_residual_bq_s == pytest.approx(0.0, abs=1e-8)


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(UFOTRINativeAtmosphereError):
        mol_sigma_m(0.0, "D")
    with pytest.raises(UFOTRINativeAtmosphereError):
        mol_sigma_m(1000.0, "G")
    with pytest.raises(UFOTRINativeAtmosphereError):
        wind_speed_power_law_m_s(-1.0, 10.0, 20.0, 0.2)
    with pytest.raises(UFOTRINativeAtmosphereError):
        split_release_into_hourly_slices(
            start_utc=T0,
            duration_s=0.0,
            total_activity_bq=1.0,
            species=TritiumAtmosphericForm.HT,
            source_id="bad",
        )
