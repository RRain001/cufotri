"""V4 system physics-gap and sensitivity-audit R1 governance invariants."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/v4/governance/v4_system_physics_gap_sensitivity_audit_r1.yaml"
PLAN = ROOT / "docs/v4/governance/v4_system_sensitivity_screening_execution_r1_plan.yaml"
ADR = ROOT / "docs/v4/adr/ADR-028-v4-system-physics-gap-sensitivity-audit-r1.md"
REVIEW = ROOT / "docs/v4/reports/v4_system_physics_gap_sensitivity_audit_r1_review.md"


def _audit() -> dict:
    return yaml.safe_load(AUDIT.read_text(encoding="utf-8"))


def _plan() -> dict:
    return yaml.safe_load(PLAN.read_text(encoding="utf-8"))


def _inputs() -> dict[str, dict]:
    return {item["input_id"]: item for item in _audit()["system_inputs"]}


def test_audit_is_structural_only_and_preserves_nonactivation_boundary() -> None:
    a = _audit()
    assert a["status"] == "PASS_STRUCTURAL_AUDIT"
    assert a["base_main_sha"] == "ae315f9e3f1108c9e527508728e28a6fbbce75e7"
    inv = a["hard_invariants"]
    assert inv["numerical_sensitivity_results_available"] is False
    assert inv["physical_uncertainty_ranking_available"] is False
    assert inv["three_layer_soil_implemented"] is False
    assert inv["leaf_r5_authorized"] is False
    assert inv["real_cteas_atmos_coupling_active"] is False
    assert inv["solver_changes_authorized"] is False
    assert inv["numerical_coupling_changes_authorized"] is False
    assert inv["active_parameters"] == 0
    assert inv["calibration_started"] is False
    assert inv["v3_physics_ready"] is False


def test_prior_scientific_priority_is_not_relabelled_as_numeric_sensitivity() -> None:
    rules = _audit()["interpretation_rules"]
    assert rules["prior_scientific_priority_is_numeric_sensitivity_result"] is False
    assert rules["structural_reach_is_empirical_uncertainty"] is False
    assert rules["synthetic_screening_is_physical_validation"] is False
    assert rules["large_external_endpoint_scaling_is_environmental_physics_priority"] is False
    assert rules["missing_equation_may_receive_guessed_sensitivity_score"] is False
    assert rules["combined_scalar_priority_score_created"] is False


def test_actual_pipeline_ordering_creates_delayed_soil_root_reach() -> None:
    inv = _audit()["call_graph_invariants"]
    assert inv["root_reads_soil_snapshot"] == "STEP_START"
    assert inv["obt_reads_tfwt_snapshot"] == "POST_LEAF_PRE_ROOT"
    inputs = _inputs()
    dep = inputs["atmos.surface_deposition_flux"]
    assert "DELAYED_MULTI_STEP_TO_ROOT_PLANT_DOSE" in dep["structural_reach"]
    assert dep["same_step_root_effect"] is False
    root = inputs["root.k_root"]
    assert "DELAYED_MULTI_STEP_TO_OBT_DOSE" in root["structural_reach"]
    assert root["same_step_obt_effect"] is False


def test_current_meteorology_is_not_falsely_ranked_under_precomputed_resistance() -> None:
    inputs = _inputs()
    for input_id in (
        "atmos.temperature",
        "atmos.relative_humidity",
        "atmos.wind_speed",
        "atmos.precipitation_rate",
    ):
        item = inputs[input_id]
        assert item["perturbation_eligibility"] == "NO_EFFECT_CURRENT_EQUATION"
        assert item["disposition"] == "DEFER_CURRENT_STRUCTURAL_ZERO"


def test_nonintegrated_subsystem_fluxes_do_not_receive_end_to_end_scores() -> None:
    inputs = _inputs()
    for input_id in (
        "soil.transport_flux",
        "tfwt.water_loss_flux",
        "tfwt.transformation_flux",
    ):
        item = inputs[input_id]
        assert item["pipeline_exposed"] is False
        assert item["perturbation_eligibility"] == "NOT_INTEGRATED_CURRENT_PIPELINE"
        assert item["disposition"] == "HOLD_NOT_INTEGRATED"


def test_inventory_basis_denominators_are_structural_zero_at_fixed_inventory() -> None:
    inputs = _inputs()
    assert inputs["tfwt.water_content"]["perturbation_eligibility"] == "NO_EFFECT_CURRENT_EQUATION"
    assert inputs["obt.plant_mass"]["perturbation_eligibility"] == "NO_EFFECT_CURRENT_EQUATION"
    assert "DIAGNOSTIC_ONLY_FIXED_INVENTORY" in inputs["tfwt.water_content"]["structural_reach"]
    assert "DIAGNOSTIC_ONLY_FIXED_INVENTORY" in inputs["obt.plant_mass"]["structural_reach"]


def test_runnable_environmental_and_provisional_inputs_are_separated() -> None:
    inputs = _inputs()
    assert inputs["leaf.total_resistance"]["perturbation_eligibility"] == "RUNNABLE_CURRENT_PIPELINE"
    assert inputs["obt.kf"]["perturbation_eligibility"] == "RUNNABLE_CURRENT_PIPELINE"
    assert inputs["obt.kr"]["perturbation_eligibility"] == "RUNNABLE_CURRENT_PIPELINE"
    assert inputs["root.k_root"]["perturbation_eligibility"] == "RUNNABLE_PROVISIONAL_ABSTRACTION_ONLY"
    assert inputs["food.harvest_fraction"]["perturbation_eligibility"] == "RUNNABLE_PROVISIONAL_ABSTRACTION_ONLY"
    assert inputs["obt.daylight_multiplier"]["perturbation_eligibility"] == "RUNNABLE_PROVISIONAL_ABSTRACTION_ONLY"


def test_missing_obt_mechanisms_are_not_given_placeholder_sensitivity() -> None:
    inputs = _inputs()
    for input_id in (
        "obt.photosynthetic_activity",
        "obt.temperature_response",
        "obt.growth_stage_response",
    ):
        item = inputs[input_id]
        assert item["perturbation_eligibility"] == "NO_EFFECT_CURRENT_EQUATION"
        assert item["disposition"] == "HOLD_REDESIGN_REQUIRED"


def test_external_exposure_arithmetic_stays_outside_environmental_physics_rank() -> None:
    inputs = _inputs()
    assert inputs["intake.annual_consumption_amount"]["exact_scaling"] == "DIRECT_LINEAR"
    assert inputs["intake.food_product_mass"]["exact_scaling"] == "INVERSE_LINEAR_AT_FIXED_FOOD_ACTIVITY"
    assert inputs["dose.dose_coefficient"]["exact_scaling"] == "DIRECT_LINEAR"
    for input_id in (
        "food.harvest_area",
        "intake.annual_consumption_amount",
        "intake.food_product_mass",
        "dose.dose_coefficient",
    ):
        assert inputs[input_id]["disposition"] == "KEEP_EXTERNAL_GOVERNANCE"


def test_screening_plan_requires_multistep_profiles_and_no_invented_ranges() -> None:
    p = _plan()
    assert p["status"] == "PREREGISTERED_NOT_EXECUTED"
    assert p["reference_case"]["minimum_intervals"] >= 2
    profile_ids = {profile["profile_id"] for profile in p["reference_case"]["required_profiles"]}
    assert {"OBT_ONLY_ENDPOINT", "MIXED_OBT_TFWT_ENDPOINT", "DAY_NIGHT_SEQUENCE"}.issubset(profile_ids)
    methods = p["screening_methods"]
    assert methods["local_numeric_response"]["relative_step"] == "TBD_EXECUTION_PREFLIGHT"
    assert methods["local_numeric_response"]["relative_step_is_physical_uncertainty"] is False
    assert methods["local_numeric_response"]["convergence_check_required"] is True
    ranges = p["range_policy"]
    assert ranges["empirical_uncertainty_ranges_available"] is False
    assert ranges["global_sobol_or_monte_carlo_authorized"] is False
    assert ranges["arbitrary_literature_range_import"] == "forbidden"


def test_screening_plan_preserves_conservation_restart_and_interpretation_boundaries() -> None:
    p = _plan()
    invariants = set(p["outputs"]["invariants"])
    assert {"soil_balance_residual", "root_balance_residual", "tfwt_balance_residual", "obt_balance_residual", "food_balance_residual", "restart_equivalence"}.issubset(invariants)
    policy = p["ranking_policy"]
    assert policy["produce_numeric_influence_table"] is True
    assert policy["produce_physical_uncertainty_ranking"] is False
    assert policy["combine_external_scenario_with_environmental_physics_rank"] is False
    assert policy["high_baseline_influence_can_validate_parameter"] is False
    assert policy["zero_current_influence_can_reject_future_mechanism"] is False


def test_review_and_adr_point_to_separate_execution_stage() -> None:
    adr = ADR.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    for text in (adr, review):
        assert "NUMERICAL_SENSITIVITY_RESULTS = NOT_YET_EXECUTED" in text
        assert "PHYSICAL_UNCERTAINTY_RANKING = NOT_AVAILABLE" in text
        assert "NEXT_STAGE = V4_SYSTEM_SENSITIVITY_SCREENING_EXECUTION_R1" in text
