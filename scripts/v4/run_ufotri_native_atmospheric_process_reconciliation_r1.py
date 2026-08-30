#!/usr/bin/env python3
"""Machine-readable qualification for UFOTRI native atmosphere H4."""

from __future__ import annotations

import json
import math

from cteas_ufotri.atmosphere.ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode,
    kfk4332_liftoff_evidence,
    kfk4332_source_depletion_integral_m,
    kfk5194_washout,
    source_depletion_kfk4332,
    transport_straight_segment_reconciled,
)
from cteas_ufotri.atmosphere.ufotri_native_v4 import (
    MOL_SMOOTH_TERRAIN_COEFFICIENTS,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    source_depletion_compatibility,
)

STAGE = "UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1"


def build_result() -> dict[str, object]:
    class_mode = KFK5194HTOWashoutMode.PRECALCULATED_CLASSES
    power_mode = KFK5194HTOWashoutMode.POWER_LAW
    class_values = [
        kfk5194_washout(
            species=TritiumAtmosphericForm.HTO,
            precipitation_mm_h=intensity,
            mode=class_mode,
        )
        for intensity in (0.5, 1.0, 3.0)
    ]
    power = kfk5194_washout(
        species=TritiumAtmosphericForm.HTO,
        precipitation_mm_h=4.0,
        mode=power_mode,
    )
    ht_wet = kfk5194_washout(
        species=TritiumAtmosphericForm.HT,
        precipitation_mm_h=10.0,
        mode=power_mode,
    )

    c = MOL_SMOOTH_TERRAIN_COEFFICIENTS["D"]
    x = 1000.0
    ground_integral = kfk4332_source_depletion_integral_m(
        downwind_m=x,
        effective_release_height_m=0.0,
        stability_class="D",
        mixing_lid_m=10000.0,
    )
    ground_expected = x ** (1.0 - c.q_z) / (c.p_z * (1.0 - c.q_z))

    hto_policy = NativeSpeciesPolicy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=1.8e-2,
        hto_washout_coefficient_s_1=power.coefficient_s_1,
    )
    reconciled = source_depletion_kfk4332(
        source_bq_s=1.0e8,
        downwind_m=5000.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=hto_policy,
    )
    transport = transport_straight_segment_reconciled(
        source_bq_s=1.0e8,
        downwind_m=1000.0,
        crosswind_m=0.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        receptor_height_m=1.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
        ),
    )
    h1_compat = source_depletion_compatibility(
        1.0e8,
        5000.0,
        5.0,
        560.0,
        NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
        ),
    )
    h4_ht = source_depletion_kfk4332(
        source_bq_s=1.0e8,
        downwind_m=5000.0,
        wind_speed_m_s=5.0,
        effective_release_height_m=20.0,
        stability_class="D",
        mixing_lid_m=560.0,
        policy=NativeSpeciesPolicy(
            species=TritiumAtmosphericForm.HT,
            dry_deposition_velocity_m_s=5.0e-4,
        ),
    )
    liftoff = kfk4332_liftoff_evidence()

    recovered_checks = {
        "kfk5194_iwash0_three_classes_exact": (
            [item.coefficient_s_1 for item in class_values]
            == [6.0e-5, 1.0e-4, 4.0e-4]
            and [item.mean_relative_precipitation_duration for item in class_values]
            == [0.5, 0.75, 0.72]
        ),
        "kfk5194_iwash1_power_law_exact": math.isclose(
            power.coefficient_s_1,
            9.0e-5 * 4.0**0.6,
            rel_tol=1.0e-15,
        ),
        "ht_washout_remains_zero": ht_wet.coefficient_s_1 == 0.0,
        "eq220_ground_release_identity": math.isclose(
            ground_integral,
            ground_expected,
            rel_tol=2.0e-13,
        ),
        "eq220_eq227_activity_ledger_closes": math.isclose(
            reconciled.residual_bq_s,
            0.0,
            abs_tol=1.0e-8,
        ),
        "h4_reconciled_transport_positive": transport.air_concentration_bq_m3 > 0.0,
        "h4_reconciled_transport_ledger_closes": math.isclose(
            transport.source_depletion_residual_bq_s,
            0.0,
            abs_tol=1.0e-8,
        ),
        "h4_supersedes_h1_compatibility_numerically": not math.isclose(
            h4_ht.source_after_bq_s,
            h1_compat.source_after_bq_s,
            rel_tol=1.0e-10,
        ),
        "atmospheric_ht_to_hto_still_zero": (
            transport.atmospheric_ht_to_hto_generated_bq_s == 0.0
        ),
    }

    boundary_checks = {
        "iwash1_regtim_not_invented": power.mean_relative_precipitation_duration is None,
        "liftoff_threshold_semantics_recovered": (
            liftoff.threshold_lp == 30.0
            and liftoff.thermal_buoyancy_dominates_above_threshold
        ),
        "liftoff_eq322_numeric_kept_source_limited": not liftoff.numeric_equation_322_recovered,
        "building_wake_kept_source_limited": not liftoff.building_wake_complete_numerics_recovered,
        "plume_rise_kept_source_limited": not liftoff.plume_rise_complete_numerics_recovered,
    }

    forbidden_claims = {
        "original_musemet_closed_form_three_case_equivalence": False,
        "liftoff_eq322_numeric_equivalence": False,
        "building_wake_complete_equivalence": False,
        "plrise_risefx_complete_equivalence": False,
        "atmospheric_ht_to_hto_conversion_activated": False,
        "cteas_atmos_binding": False,
        "production_parameter_activation": False,
        "calibration": False,
        "empirical_validation": False,
        "original_ufotri_executable_equivalence": False,
    }

    passed = (
        all(recovered_checks.values())
        and all(boundary_checks.values())
        and not any(forbidden_claims.values())
    )
    return {
        "stage": STAGE,
        "status": (
            "PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION"
            if passed
            else "FAIL_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION"
        ),
        "recovered_checks": recovered_checks,
        "boundary_checks": boundary_checks,
        "source_status": {
            "kfk4332_eq220_dry_source_depletion": "RECOVERED_DIRECT_EQUATION_DETERMINISTIC_QUADRATURE",
            "kfk4332_eq227_wet_source_depletion": "RECOVERED",
            "original_musemet_three_case_closed_form": "SOURCE_LIMITED_NO_NUMERICAL_EQUIVALENCE_CLAIM",
            "kfk5194_iwash0": "RECOVERED",
            "kfk5194_iwash1_awash_bwash": "RECOVERED",
            "kfk5194_iwash1_regtim": "SOURCE_LIMITED_DO_NOT_INVENT",
            "kfk4332_liftoff_threshold": "RECOVERED_SEMANTICS_ONLY",
            "kfk4332_liftoff_eq322_numeric": "SOURCE_LIMITED_OCR_AMBIGUOUS",
            "building_wake": "SOURCE_LIMITED",
            "plume_rise_rising_phase": "SOURCE_LIMITED",
        },
        "h1_compatibility_function_retained_for_history": True,
        "h4_plus_authoritative_transport": "transport_straight_segment_reconciled",
        "forbidden_claims": forbidden_claims,
        "next_stage_after_clean_closure": "UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1",
    }


def main() -> None:
    result = build_result()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["status"].startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
