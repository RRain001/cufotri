#!/usr/bin/env python3
"""Machine gate for UFOTRI native primary-atmosphere core R1."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path

from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    MOL_SMOOTH_TERRAIN_COEFFICIENTS,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    UFOTRINativeAtmosphereError,
    atmospheric_oxidation_evidence,
    kfk4605_iter_benchmark_policy,
    mol_sigma_m,
    source_depletion_compatibility,
    split_release_into_hourly_slices,
    transport_straight_segment,
    wind_speed_power_law_m_s,
)

ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1"


def _manual_text() -> str:
    return (ROOT / "ufotri_manual.md").read_text(encoding="utf-8")


def build_result() -> dict:
    manual = _manual_text()
    oxidation = atmospheric_oxidation_evidence()

    manual_semantics = {
        "musemet_primary_model_present": "# 2.1 Primary Dispersion Model MUSEMET" in manual,
        "hourly_trajectory_records_present": "hourly records of wind velocities and wind directions" in manual,
        "segmented_gaussian_present": "two-dimensional Gaussian model (segmented plume model)" in manual,
        "source_over_one_hour_split_present": "Source terms of more than one hour are divided into one-hour intervals" in manual,
        "mol_table9_present": "Table 9. Diffusion coefficients of the S.C.N./C.E.N Mol" in manual,
        "mixing_lid_sigma_cap_present": "\\sigma_{z}$ is limited to 0.8 h" in manual,
        "dry_source_depletion_present": "Dry deposition of radioactivity from the plume is described by the source depletion model" in manual,
        "ht_wet_negligible_present": "They are very small for HT, i.e. wet deposition is negligible" in manual,
        "hto_washout_present": "wet deposition of tritium is in the model considered as washout from the whole plume" in manual,
        "air_conversion_excluded_present": "Conversion of tritium gas into tritiated water within the atmosphere is not included in the program" in manual,
        "iter_oxidation_input_present": "Oxidation rate in air</td><td>0.5 %/d" in manual,
    }

    expected_coefficients = {
        "A": (0.946, 0.796, 1.321, 0.711),
        "B": (0.826, 0.796, 0.950, 0.711),
        "C": (0.586, 0.796, 0.700, 0.711),
        "D": (0.418, 0.796, 0.520, 0.711),
        "E": (0.297, 0.796, 0.382, 0.711),
        "F": (0.235, 0.796, 0.311, 0.711),
    }
    coefficient_check = all(
        (
            MOL_SMOOTH_TERRAIN_COEFFICIENTS[key].p_y,
            MOL_SMOOTH_TERRAIN_COEFFICIENTS[key].q_y,
            MOL_SMOOTH_TERRAIN_COEFFICIENTS[key].p_z,
            MOL_SMOOTH_TERRAIN_COEFFICIENTS[key].q_z,
        )
        == values
        for key, values in expected_coefficients.items()
    )

    _, sigma_z_uncapped = mol_sigma_m(1000.0, "D")
    _, sigma_z_capped = mol_sigma_m(1.0e6, "A", mixing_lid_m=100.0)
    wind_check = math.isclose(
        wind_speed_power_law_m_s(5.0, 60.0, 10.0, 0.34),
        5.0 * (10.0 / 60.0) ** 0.34,
        rel_tol=1.0e-15,
    )

    slices = split_release_into_hourly_slices(
        start_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        duration_s=9000.0,
        total_activity_bq=9.0e9,
        species=TritiumAtmosphericForm.HT,
        source_id="MACHINE_LONG_HT",
    )
    release_split_check = (
        [item.duration_s for item in slices] == [3600.0, 3600.0, 1800.0]
        and math.isclose(
            sum(item.released_activity_bq for item in slices),
            9.0e9,
            rel_tol=0.0,
            abs_tol=1.0e-6,
        )
    )

    ht_policy = kfk4605_iter_benchmark_policy(TritiumAtmosphericForm.HT)
    hto_policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=1.8e-2,
        hto_washout_coefficient_s_1=1.0e-4,
    )
    ht_dep = source_depletion_compatibility(1.0e8, 5000.0, 5.0, 560.0, ht_policy)
    hto_dep = source_depletion_compatibility(1.0e8, 5000.0, 5.0, 560.0, hto_policy)
    ht_result = transport_straight_segment(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=ht_policy,
    )

    oxidation_rejected = False
    try:
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
            atmospheric_ht_to_hto_conversion_rate_s_1=0.005 / 86400.0,
        )
    except UFOTRINativeAtmosphereError:
        oxidation_rejected = True

    ht_wet_rejected = False
    try:
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
            hto_washout_coefficient_s_1=1.0e-4,
        )
    except UFOTRINativeAtmosphereError:
        ht_wet_rejected = True

    numerical_checks = {
        "table9_coefficients_exact": coefficient_check,
        "sigma_d_positive": sigma_z_uncapped > 0.0,
        "sigma_z_08_lid_cap": math.isclose(sigma_z_capped, 80.0, rel_tol=0.0, abs_tol=1e-12),
        "wind_power_law_literal": wind_check,
        "release_hourly_split_activity_closed": release_split_check,
        "ht_source_depletion_closed": math.isclose(ht_dep.residual_bq_s, 0.0, abs_tol=1.0e-8),
        "ht_wet_loss_zero": ht_dep.wet_loss_bq_s == 0.0,
        "hto_explicit_washout_positive": hto_dep.wet_loss_bq_s > 0.0,
        "hto_source_depletion_closed": math.isclose(hto_dep.residual_bq_s, 0.0, abs_tol=1.0e-8),
        "ht_air_concentration_positive": ht_result.air_concentration_bq_m3 > 0.0,
        "ht_dry_flux_identity": math.isclose(
            ht_result.dry_surface_flux_bq_m2_s,
            5.0e-4 * ht_result.air_concentration_bq_m3,
            rel_tol=1.0e-15,
        ),
        "air_oxidation_generates_zero_hto": ht_result.atmospheric_ht_to_hto_generated_bq_s == 0.0,
        "air_oxidation_nonzero_policy_rejected": oxidation_rejected,
        "ht_wet_policy_rejected": ht_wet_rejected,
        "oxidation_source_conflict_preserved": (
            not oxidation.section22_program_includes_air_conversion
            and not oxidation.active_in_kfk4605_fidelity_path
            and oxidation.iter_benchmark_input_fraction_d_1 == 0.005
            and oxidation.source_conflict_preserved
        ),
    }

    forbidden_claims = {
        "original_musemet_numerical_equivalence": False,
        "complete_hourly_bent_trajectory_recovered": False,
        "building_wake_numerics_recovered": False,
        "thermal_lift_original_numerics_recovered": False,
        "atmospheric_ht_to_hto_conversion_activated": False,
        "real_cteas_atmos_binding": False,
        "production_parameter_activation": False,
        "rc1_default_changed": False,
    }

    passed = all(manual_semantics.values()) and all(numerical_checks.values())
    return {
        "stage": STAGE,
        "status": "PASS_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE" if passed else "FAIL_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE",
        "manual_semantics": manual_semantics,
        "numerical_checks": numerical_checks,
        "forbidden_claims": forbidden_claims,
        "remaining_native_atmosphere_work": [
            "HOURLY_BENT_SEGMENT_TRAJECTORY",
            "PRIMARY_HT_HTO_FORCING_ADAPTERS",
            "HTO_TWO_REGIME_WASHOUT_PARAMETER_RECOVERY",
            "BUILDING_WAKE_FIDELITY",
            "THERMAL_LIFT_FIDELITY",
            "NATIVE_END_TO_END_ATMOS_TO_DOSE_QUALIFICATION",
        ],
        "source_limited_boundaries": [
            "ORIGINAL_MUSEMET_SOURCE_DEPLETION_DISCRETISATION",
            "ORIGINAL_BUILDING_WAKE_NUMERICS",
            "ORIGINAL_THERMAL_LIFT_NUMERICS",
        ],
    }


def main() -> None:
    result = build_result()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["status"].startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
