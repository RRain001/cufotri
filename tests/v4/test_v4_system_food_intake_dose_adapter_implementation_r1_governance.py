from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "docs/v4/results/v4_system_food_intake_dose_adapter_implementation_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_food_intake_dose_adapter_implementation_r1.md"
REVIEW = ROOT / "docs/v4/reviews/v4_system_food_intake_dose_adapter_implementation_r1.md"
SOURCE = ROOT / "src/cteas_ufotri/v4_integration/food_intake_dose_endpoint.py"
MACHINE = ROOT / "scripts/v4/run_food_intake_dose_endpoint_adapter_r1.py"
V3_PIPELINE = ROOT / "src/cteas_ufotri/v3_pipeline/pipeline_runner.py"


def load_result() -> dict:
    return yaml.safe_load(RESULT.read_text(encoding="utf-8"))


def test_first_exact_head_certification_and_counts_are_frozen() -> None:
    data = load_result()
    assert data["stage"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_IMPLEMENTATION_R1"
    assert (
        data["status"]
        == "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION_AWAITING_CLOSURE_GATE"
    )
    assert data["base_main_sha"] == "f13a36d2bd5b92a86bf6405388c8e5eb5d3a5472"
    assert data["certified_implementation_head"] == "7118fb227045500b58391b0144f2cb639579dce3"
    assert data["certified_implementation_tree"] == "e7a84bbb67d9932f518e3ccf51ccdb7db0ce1975"

    gate = data["first_exact_head_certification"]
    assert gate["protected"]["run_id"] == 33035667912
    assert gate["protected"]["conclusion"] == "SUCCESS"
    assert gate["remediation"]["run_id"] == 33035667915
    assert gate["remediation"]["conclusion"] == "SUCCESS"
    assert gate["portable_suite"] == {
        "passed": 1269,
        "skipped": 1,
        "deselected": 57,
        "warnings": 1,
    }
    assert gate["frozen_current_suite"] == {"passed": 337}
    assert gate["machine_gates"]["food_intake_dose_endpoint"] == (
        "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION"
    )


def test_machine_result_closes_all_terminal_software_invariants() -> None:
    data = load_result()
    machine = data["endpoint_machine_result"]
    assert machine["source_kind"] == "SYNTHETIC_TEST_ONLY"
    assert all(machine["invariants"].values())
    assert machine["mixed_output"] == {
        "food_total_bq": 25.0,
        "food_obt_bq": 10.0,
        "food_tfwt_bq": 15.0,
        "annual_intake_bq": 100.0,
        "committed_dose_sv": 1.9999999999999997e-09,
    }
    assert machine["obt_only_output"]["food_tfwt_bq"] == 0.0
    assert machine["obt_only_output"]["food_total_bq"] == 10.0
    assert machine["obt_only_output"]["annual_intake_bq"] == 40.0


def test_superseded_exact_float_failure_is_recorded_as_non_certified() -> None:
    data = load_result()
    failed = data["superseded_non_certified_attempt"]
    assert failed["head"] == "7df074c25f2ef7aaf7553aa57bf384e86851d5ac"
    assert failed["protected_run"] == 33035343479
    assert failed["remediation_run"] == 33035343332
    assert failed["failure_scope"] == "SYNTHETIC_MACHINE_ASSERTION_ONLY"
    assert failed["failure_cause"] == "EXACT_BINARY_FLOAT_EQUALITY_FOR_MIXED_DOSE"
    assert failed["production_runtime_physics_failure"] is False
    assert failed["correction"] == "math.isclose_rel_tol_1e-12"

    machine_source = MACHINE.read_text(encoding="utf-8")
    assert "import math" in machine_source
    assert "math.isclose(" in machine_source
    assert "rel_tol=1.0e-12" in machine_source
    assert "mixed.dose_state.dose() == 2.0e-9" not in machine_source


def test_adapter_is_opt_in_reuses_existing_solvers_and_does_not_enter_v3_default() -> None:
    data = load_result()
    scope = data["scope"]
    assert scope["endpoint_adapter_implemented"] is True
    assert scope["opt_in_v4_only"] is True
    assert scope["v3_default_changed"] is False
    assert scope["replay_orchestration_changed"] is False
    assert scope["upstream_solver_equations_changed"] is False

    source = SOURCE.read_text(encoding="utf-8")
    v3_pipeline = V3_PIPELINE.read_text(encoding="utf-8")
    assert "class V4FoodIntakeDoseEndpointAdapter" in source
    assert "class V4TerminalHarvestRequest" in source
    assert "FoodTransferSolver" in source
    assert "FoodIntakeSolver" in source
    assert "DoseSolver" in source
    assert "require_direct_comparison" in source
    assert "radionuclide_identifier != \"H-3\"" in source
    assert "pathway_identifier != \"food-ingestion\"" in source
    assert "food_intake_dose_endpoint" not in v3_pipeline
    assert "V4FoodIntakeDoseEndpointAdapter" not in v3_pipeline


def test_no_conversion_no_environmental_sink_and_provenance_boundaries_remain_frozen() -> None:
    data = load_result()
    scope = data["scope"]
    assert scope["state_mutating_harvest"] is False
    assert scope["repeated_harvest"] is False
    assert scope["continuous_food_chain_kinetics"] is False
    assert scope["numerical_mass_basis_conversion"] is False
    assert scope["numerical_area_conversion"] is False

    interpretation = data["interpretation_boundaries"]
    assert interpretation["food_readout_is_terminal_diagnostic_not_environmental_sink"] is True
    assert interpretation["physical_parameter_validation"] is False
    assert interpretation["physical_uncertainty_ranking"] == "NOT_AVAILABLE"
    assert interpretation["real_atmos_coupling_readiness"] is False

    assert data["provenance_domains_retained_independently"] == [
        "replay_tfwt",
        "replay_obt",
        "harvest",
        "food_product_basis",
        "consumption_basis",
        "consumption",
        "dose",
    ]


def test_closure_preserves_holds_and_only_authorizes_post_endpoint_review_after_merge() -> None:
    data = load_result()
    scope = data["scope"]
    assert scope["parameter_activation"] is False
    assert scope["calibration"] is False
    assert scope["leaf_r5"] is False
    assert scope["obt_redesign"] is False
    assert scope["full_hydrology"] is False
    assert scope["real_cteas_atmos_binding"] is False
    assert scope["empirical_validation"] is False
    assert scope["physical_accuracy_claim"] is False

    roadmap = data["roadmap"]
    assert roadmap["merge_authorized_before_closure_exact_head_ci"] is False
    assert roadmap["next_stage_if_closure_and_no_drift_merge_pass"] == (
        "V4_SYSTEM_POST_ENDPOINT_REVIEW_R1"
    )
    assert roadmap["next_stage_scope"] == "CONTROL_PLANE_ONLY"
    assert roadmap["automatic_leaf_r5_authorization"] is False
    assert roadmap["automatic_obt_redesign_authorization"] is False
    assert roadmap["automatic_full_hydrology_authorization"] is False
    assert roadmap["automatic_parameter_activation_authorization"] is False
    assert roadmap["automatic_real_cteas_atmos_binding_authorization"] is False

    report = REPORT.read_text(encoding="utf-8")
    review = REVIEW.read_text(encoding="utf-8")
    assert "`V4_SYSTEM_POST_ENDPOINT_REVIEW_R1`" in report
    assert "`PASS_INDEPENDENT_REVIEW_WITH_INTERPRETATION_BOUNDARIES`" in review
    assert "Leaf R5 = HOLD" in review
