"""Freeze the reviewed V4 sensitivity screening R1 result and boundaries."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "docs/v4/results/v4_system_sensitivity_screening_execution_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_sensitivity_screening_execution_r1.md"
REVIEW = ROOT / "docs/v4/reviews/v4_system_sensitivity_screening_execution_r1.md"


def _result() -> dict:
    return yaml.safe_load(RESULT.read_text(encoding="utf-8"))


def test_result_is_bound_to_actual_successful_ci_identity() -> None:
    result = _result()
    assert result["status"] == "PASS_SOFTWARE_SCREENING"
    identity = result["execution_identity"]
    assert identity["pull_request"] == 21
    assert identity["exact_pr_head_sha"] == "6a4c87b4daeef672451e14d42a7935401e58c476"
    assert identity["protected_integration_run_id"] == 32947990894
    assert identity["protected_integration_job_id"] == 98112824987
    assert identity["actions_checkout_merge_sha"] == "8ee97771618bc3952fd9d8fb947a252aecad0267"


def test_failed_first_attempt_is_retained_without_solver_repair() -> None:
    first = _result()["first_attempt_record"]
    assert first["head_sha"] == "9bbed395dd972908969abfdc1a4f4da9bdf39680"
    assert first["result"] == "FAIL_SYNTHETIC_FIXTURE_NUMERICAL_CONDITIONING"
    assert first["production_solver_modified"] is False
    corrected = _result()["corrected_execution"]
    assert corrected["synthetic_soil_half_life_s"] == 1000.0
    assert corrected["half_life_is_physical_parameter_selection"] is False
    assert corrected["half_life_is_calibration"] is False


def test_actual_profile_endpoints_are_frozen() -> None:
    profiles = _result()["profile_outputs"]
    assert profiles["OBT_ONLY_ENDPOINT"]["final_committed_dose_sv"] == pytest.approx(1.4377914010978703)
    assert profiles["MIXED_OBT_TFWT_ENDPOINT"]["final_committed_dose_sv"] == pytest.approx(6.003182404167035)
    day_night = profiles["DAY_NIGHT_SEQUENCE"]
    assert day_night["final_committed_dose_sv"] == pytest.approx(5.735860613837632)
    assert day_night["final_soil_inventory_bq_m2"] == pytest.approx(66.21213925251114)
    assert day_night["final_tfwt_inventory_bq_m2"] == pytest.approx(80.71202416443077)
    assert day_night["final_obt_inventory_bq_m2"] == pytest.approx(7.442826366431547)
    assert len(day_night["per_step_root_transfer_bq_m2"]) == 6
    assert len(day_night["per_step_obt_formation_bq_m2"]) == 6


def test_local_response_values_are_computational_not_physical_ranking() -> None:
    result = _result()
    response = result["fine_step_local_dose_elasticity"]
    assert response["relative_step"] == 0.005
    assert response["interpretation"] == "LOCAL_COMPUTATIONAL_INFLUENCE_NOT_PHYSICAL_UNCERTAINTY"
    values = response["values"]
    assert values["atmos.air_hto_concentration"] == pytest.approx(0.6708504225382111)
    assert values["leaf.total_resistance"] == pytest.approx(-0.5590559951818248)
    assert values["soil.water_content"] == pytest.approx(-0.27619228454260397)
    assert values["root.k_root"] == pytest.approx(0.27618828866895934)
    assert values["food.tfwt_harvest_fraction"] == pytest.approx(0.8442885516051023)
    assert result["physical_uncertainty_ranking"] == "NOT_AVAILABLE"
    boundaries = result["interpretation_boundaries"]
    assert boundaries["local_elasticity_is_global_sensitivity"] is False
    assert boundaries["local_elasticity_is_physical_uncertainty"] is False
    assert boundaries["endpoint_fraction_magnitude_proves_food_physics"] is False
    assert boundaries["numerical_influence_validates_parameter_semantics"] is False


def test_structural_zero_and_execution_invariants_are_frozen() -> None:
    result = _result()
    assert all(value == 0.0 for value in result["structural_zero_verification"].values() if isinstance(value, float))
    invariants = result["invariants"]
    assert invariants["deterministic_repeat_equal"] is True
    assert invariants["restart_equivalence"] is True
    assert invariants["max_abs_balance_residual"] == 0.0
    assert invariants["all_structural_zero_checks_pass"] is True
    assert invariants["all_local_response_steps_converged"] is True


def test_next_stage_is_design_only_and_does_not_assume_three_layers() -> None:
    decision = _result()["roadmap_decision"]
    assert decision["leaf_r5_authorized"] is False
    assert decision["global_uncertainty_analysis_authorized"] is False
    assert decision["production_parameter_ranking_authorized"] is False
    assert decision["soil_root_layered_implementation_authorized"] is False
    assert decision["next_stage"] == "V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1"
    assert decision["next_stage_scope"] == "CONTROL_PLANE_ONLY"

    report = REPORT.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    assert "must not assume three layers" in report
    assert "PASS_INDEPENDENT_REVIEW_WITH_INTERPRETATION_BOUNDARIES" in review
    assert "No layered implementation, fixed" in review
