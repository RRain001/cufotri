#!/usr/bin/env python3
"""Machine-visible D5 qualification for UFOTRI Eq. (106)-(107) exposure."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.dose.public import calculate_public_dose_step
from cteas_ufotri.dose.ufotri_manual_v4 import (
    MANUAL_ADULT_REFERENCE_DF_SV_BQ,
    MANUAL_SKIN_TO_INHALATION_FRACTION,
    SECONDS_PER_DAY,
    UFOTRIFoodSpecificActivity,
    UFOTRIManualConsumptionRates,
    UFOTRIManualExposureState,
    UFOTRIManualFoodSnapshot,
    advance_ufotri_manual_exposure,
    calculate_ufotri_manual_dose,
    ufotri_exposure_policy_boundary,
    ufotri_manual_adult_reference_policy,
)

STAGE = "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1"


def _foods() -> UFOTRIManualFoodSnapshot:
    return UFOTRIManualFoodSnapshot(
        green_vegetable=UFOTRIFoodSpecificActivity(hto_bq_kg=30.0, obt_bq_kg=5.0),
        beef=UFOTRIFoodSpecificActivity(hto_bq_kg=20.0, obt_bq_kg=10.0),
        milk=UFOTRIFoodSpecificActivity(hto_bq_kg=15.0, obt_bq_kg=7.0),
    )


def _habits() -> UFOTRIManualConsumptionRates:
    return UFOTRIManualConsumptionRates(
        breathing_rate_m3_s=20.0 / SECONDS_PER_DAY,
        green_vegetable_kg_d=0.10,
        beef_kg_d=0.05,
        milk_kg_d=0.30,
        provenance_id="SYNTHETIC_D5_HABITS_R1",
    )


def _one_day_state() -> UFOTRIManualExposureState:
    return advance_ufotri_manual_exposure(
        UFOTRIManualExposureState.zero(
            exposure_provenance_id="SYNTHETIC_D5_EXPOSURE_R1"
        ),
        dt_s=SECONDS_PER_DAY,
        air_hto_bq_m3=100.0,
        foods=_foods(),
    )


def _partition_state(parts: int) -> UFOTRIManualExposureState:
    state = UFOTRIManualExposureState.zero(
        exposure_provenance_id="SYNTHETIC_D5_EXPOSURE_R1"
    )
    for _ in range(parts):
        state = advance_ufotri_manual_exposure(
            state,
            dt_s=SECONDS_PER_DAY / parts,
            air_hto_bq_m3=100.0,
            foods=_foods(),
        )
    return state


def build_result() -> dict[str, Any]:
    policy = ufotri_manual_adult_reference_policy()
    habits = _habits()
    state = _one_day_state()
    dose = calculate_ufotri_manual_dose(state, habits=habits, policy=policy)

    expected_inhalation = (
        habits.breathing_rate_m3_s
        * state.air_hto_bq_s_m3
        * policy.dose_coefficient_sv_bq
        * policy.quality_factor
    )
    expected_eq106 = expected_inhalation * 1.5
    expected_ingested_hto = (
        habits.green_vegetable_kg_d * state.green_vegetable_hto_bq_d_kg
        + habits.beef_kg_d * state.beef_hto_bq_d_kg
        + habits.milk_kg_d * state.milk_hto_bq_d_kg
    )
    expected_ingested_obt = (
        habits.green_vegetable_kg_d * state.green_vegetable_obt_bq_d_kg
        + habits.beef_kg_d * state.beef_obt_bq_d_kg
        + habits.milk_kg_d * state.milk_obt_bq_d_kg
    )
    expected_eq107 = (
        expected_ingested_hto + expected_ingested_obt
    ) * policy.dose_coefficient_sv_bq * policy.quality_factor

    repeat = calculate_ufotri_manual_dose(
        _one_day_state(), habits=_habits(), policy=ufotri_manual_adult_reference_policy()
    )
    hourly_state = _partition_state(24)
    quarter_hour_state = _partition_state(96)
    hourly_dose = calculate_ufotri_manual_dose(hourly_state, habits=habits, policy=policy)
    quarter_hour_dose = calculate_ufotri_manual_dose(
        quarter_hour_state, habits=habits, policy=policy
    )

    zero_food = UFOTRIManualFoodSnapshot(
        green_vegetable=UFOTRIFoodSpecificActivity(0.0, 0.0),
        beef=UFOTRIFoodSpecificActivity(0.0, 0.0),
        milk=UFOTRIFoodSpecificActivity(0.0, 0.0),
    )
    zero_state = advance_ufotri_manual_exposure(
        UFOTRIManualExposureState.zero(exposure_provenance_id="D5_ZERO"),
        dt_s=3600.0,
        air_hto_bq_m3=0.0,
        foods=zero_food,
    )
    zero_dose = calculate_ufotri_manual_dose(zero_state, habits=habits, policy=policy)

    modern_age = {
        "hto_dose_coefficient_sv_bq": 1.8e-11,
        "obt_ingestion_dose_coefficient_sv_bq": 4.2e-11,
        "breathing_rate_m3_day": 20.0,
        "drinking_water_l_day": 0.0,
        "leafy_kg_day": 0.0,
        "root_crop_kg_day": 0.0,
        "grain_kg_day": 0.0,
        "milk_l_day": 0.0,
        "beef_kg_day": 0.0,
    }
    modern_air_only = calculate_public_dose_step(
        SECONDS_PER_DAY, 100.0, {}, modern_age, skin_to_inhalation_factor=0.5
    )
    manual_air_only_state = advance_ufotri_manual_exposure(
        UFOTRIManualExposureState.zero(exposure_provenance_id="D5_AIR_ONLY"),
        dt_s=SECONDS_PER_DAY,
        air_hto_bq_m3=100.0,
        foods=zero_food,
    )
    manual_air_only = calculate_ufotri_manual_dose(
        manual_air_only_state,
        habits=UFOTRIManualConsumptionRates(
            breathing_rate_m3_s=20.0 / SECONDS_PER_DAY,
            green_vegetable_kg_d=0.0,
            beef_kg_d=0.0,
            milk_kg_d=0.0,
            provenance_id="D5_AIR_ONLY_HABITS",
        ),
        policy=policy,
    )

    boundary = ufotri_exposure_policy_boundary()
    invariants = {
        "manual_adult_reference_df_exact": policy.dose_coefficient_sv_bq
        == MANUAL_ADULT_REFERENCE_DF_SV_BQ,
        "eq106_inhalation_identity": math.isclose(
            dose.inhalation_dose_sv, expected_inhalation, rel_tol=0.0, abs_tol=1.0e-24
        ),
        "eq106_skin_is_50_percent": math.isclose(
            dose.skin_absorption_dose_sv,
            dose.inhalation_dose_sv * MANUAL_SKIN_TO_INHALATION_FRACTION,
            rel_tol=0.0,
            abs_tol=1.0e-24,
        ),
        "eq106_total_identity": math.isclose(
            dose.inhalation_dose_sv + dose.skin_absorption_dose_sv,
            expected_eq106,
            rel_tol=0.0,
            abs_tol=1.0e-24,
        ),
        "eq106_residual_closed": abs(dose.eq106_residual_sv) <= 1.0e-24,
        "eq107_three_food_identity": math.isclose(
            dose.ingestion_dose_sv, expected_eq107, rel_tol=0.0, abs_tol=1.0e-24
        ),
        "eq107_residual_closed": abs(dose.eq107_residual_sv) <= 1.0e-24,
        "hto_ingestion_tracked_separately": math.isclose(
            dose.ingested_hto_bq, expected_ingested_hto, rel_tol=0.0, abs_tol=1.0e-14
        ),
        "obt_ingestion_tracked_separately": math.isclose(
            dose.ingested_obt_bq, expected_ingested_obt, rel_tol=0.0, abs_tol=1.0e-14
        ),
        "obt_uses_same_manual_df": math.isclose(
            dose.ingestion_dose_sv,
            (dose.ingested_hto_bq + dose.ingested_obt_bq)
            * MANUAL_ADULT_REFERENCE_DF_SV_BQ,
            rel_tol=0.0,
            abs_tol=1.0e-24,
        ),
        "deterministic_repeat": dose == repeat,
        "hourly_partition_equivalence": math.isclose(
            dose.total_effective_dose_sv,
            hourly_dose.total_effective_dose_sv,
            rel_tol=1.0e-14,
            abs_tol=1.0e-24,
        ),
        "quarter_hour_partition_equivalence": math.isclose(
            dose.total_effective_dose_sv,
            quarter_hour_dose.total_effective_dose_sv,
            rel_tol=1.0e-14,
            abs_tol=1.0e-24,
        ),
        "zero_exposure_zero_dose": zero_dose.total_effective_dose_sv == 0.0,
        "manual_and_modern_coefficients_distinct": not math.isclose(
            manual_air_only.total_effective_dose_sv,
            modern_air_only.total_effective_dose_sv,
            rel_tol=0.0,
            abs_tol=0.0,
        ),
        "modern_air_only_uses_hpa_hto_coefficient": math.isclose(
            modern_air_only.total_effective_dose_sv,
            100.0 * 20.0 * 1.8e-11 * 1.5,
            rel_tol=0.0,
            abs_tol=1.0e-24,
        ),
    }
    if not all(invariants.values()):
        failed = sorted(key for key, value in invariants.items() if not value)
        raise RuntimeError(f"D5 exposure gate failed: {failed}")

    boundary_invariants = {
        "manual_food_classes_exact": boundary.manual_food_classes
        == ("green_vegetable", "beef", "milk"),
        "drinking_water_not_in_eq107": not boundary.manual_drinking_water_in_eq107,
        "root_crop_not_in_eq107": not boundary.manual_root_crop_in_eq107,
        "grain_not_in_eq107": not boundary.manual_grain_in_eq107,
        "no_separate_manual_obt_coefficient": not boundary.manual_separate_obt_coefficient,
        "modern_age_specific_policy_retained": boundary.modern_age_specific_coefficients_retained,
        "modern_separate_obt_coefficient_retained": boundary.modern_separate_obt_coefficient_retained,
        "modern_path_not_replaced": not boundary.existing_modern_path_replaced,
        "production_binding_not_authorized": not boundary.production_binding_authorized,
    }
    if not all(boundary_invariants.values()):
        failed = sorted(key for key, value in boundary_invariants.items() if not value)
        raise RuntimeError(f"D5 policy-boundary gate failed: {failed}")

    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": "PASS_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION",
        "manual_policy": {
            "coefficient_id": policy.coefficient_id,
            "dose_coefficient_sv_bq": policy.dose_coefficient_sv_bq,
            "quality_factor": policy.quality_factor,
            "skin_to_inhalation_fraction": policy.skin_to_inhalation_fraction,
            "ingested_obt_uses_hto_coefficient": policy.ingested_obt_uses_hto_coefficient,
        },
        "manual_equation_invariants": invariants,
        "policy_boundary_invariants": boundary_invariants,
        "controlled_result": {
            "inhalation_dose_sv": dose.inhalation_dose_sv,
            "skin_absorption_dose_sv": dose.skin_absorption_dose_sv,
            "ingestion_dose_sv": dose.ingestion_dose_sv,
            "total_effective_dose_sv": dose.total_effective_dose_sv,
            "ingested_hto_bq": dose.ingested_hto_bq,
            "ingested_obt_bq": dose.ingested_obt_bq,
        },
        "hard_boundaries": {
            "existing_modern_dose_path_changed": False,
            "frozen_rc1_changed": False,
            "historical_v2_changed": False,
            "project_breathing_rate_promoted_to_manual_default": False,
            "project_consumption_rates_promoted_to_manual_defaults": False,
            "modern_hpa_coefficients_relabelled_as_original_ufotri": False,
            "separate_obt_coefficient_relabelled_as_original_ufotri": False,
            "drinking_water_added_to_manual_eq107": False,
            "root_crop_added_to_manual_eq107": False,
            "grain_added_to_manual_eq107": False,
            "production_parameter_activation": False,
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "real_cteas_atmos_binding": False,
            "original_executable_equivalence": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(f"D5_EXPOSURE_STATUS={result['status']}")
    print(f"D5_EXPOSURE_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
