from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_post_orchestration_review_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_post_orchestration_review_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-035-v4-system-post-orchestration-review.md"
REPLAY = ROOT / "src/cteas_ufotri/v4_integration/replay_input_orchestration.py"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def _data() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_review_first_exact_head_gate_is_closed_and_closure_is_pending() -> None:
    data = _data()
    assert data["stage"] == "V4_SYSTEM_POST_ORCHESTRATION_REVIEW_R1"
    assert data["status"] == "PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_CLOSURE_GATE"
    assert data["base_main_sha"] == "a03da884eb60b82658c07e0ca57db7058480260f"

    gate = data["first_exact_head_gate"]
    assert gate["complete"] is True
    assert gate["head_sha"] == "baf27ed33348e44ecb9ff04b8b633deecfbfa3c2"
    assert gate["protected_gate"] == {"run_id": 33032403498, "status": "SUCCESS"}
    assert gate["remediation"] == {"run_id": 33032403623, "status": "SUCCESS"}
    assert gate["portable_suite"] == {"passed": 1253, "skipped": 1, "deselected": 57}
    assert gate["frozen_boundary_suite"] == {"passed": 321}
    assert gate["machine_gates"]["sensitivity"] == "PASS_SOFTWARE_SCREENING"
    assert gate["machine_gates"]["root_operator_split"] == "PASS_SELECTION"
    assert gate["machine_gates"]["soil_root_tfwt_obt"] == "PASS_INTEGRATION"
    assert gate["machine_gates"]["replay_orchestration"] == "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"
    assert gate["empirical_validation"] is False
    assert gate["physical_accuracy_claim"] is False


def test_next_stage_remains_endpoint_decision_not_implementation() -> None:
    data = _data()
    ranking = data["candidate_ranking"]
    assert ranking[0]["candidate"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1"
    assert ranking[0]["disposition"] == "SELECT_NEXT_CONTROL_PLANE_STAGE"
    assert ranking[0]["implementation_authorized_now"] is False

    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1"
    assert next_stage["scope"] == "CONTROL_PLANE_AND_INTERFACE_DECISION_ONLY"
    assert next_stage["adapter_implementation_authorized"] is False
    assert next_stage["continuous_harvest_authorized"] is False
    assert next_stage["state_mutating_harvest_authorized"] is False
    assert next_stage["numerical_mass_basis_conversion_authorized"] is False
    assert next_stage["parameter_activation_authorized"] is False
    assert next_stage["solver_changes_authorized"] is False
    assert next_stage["real_cteas_atmos_binding_authorized"] is False


def test_future_endpoint_boundary_is_terminal_fail_closed_and_non_mutating() -> None:
    boundary = _data()["future_adapter_boundary_requirements"]
    assert boundary["harvest_semantics"] == "TERMINAL_DIAGNOSTIC_READOUT_ONLY"
    assert boundary["harvest_trigger"] == "EXPLICIT_CALLER_REQUEST"
    assert boundary["source_state"] == "REPLAY_ENDPOINT_TFWT_AND_OBT"
    assert boundary["source_state_mutation"] == "FORBIDDEN_R1"
    assert boundary["continue_same_trajectory_after_harvest"] == "FORBIDDEN_R1"
    assert boundary["harvest_timestamp"] == "MUST_EQUAL_REPLAY_ENDPOINT"
    assert boundary["source_area_basis"] == "soil_surface_area"
    assert boundary["hidden_area_conversion"] == "FORBIDDEN"
    assert boundary["harvest_area_m2"] == "EXPLICIT_REQUIRED"
    assert boundary["mass_basis_contract_required"] is True
    assert boundary["direct_basis_rule"] == "IDENTICAL_MASS_TISSUE_AREA_ONLY"
    assert boundary["numerical_cross_basis_conversion"] == "FORBIDDEN"
    assert boundary["endpoint_modes"] == ["OBT_ONLY", "OBT_PLUS_TFWT"]
    assert boundary["mixed_tfwt_fraction"] == "EXPLICIT_REQUIRED"
    assert boundary["independent_parameter_provenance"] is True
    assert boundary["endpoint_identity_fail_closed"] is True
    assert boundary["upstream_side_effects"] == "FORBIDDEN"
    assert boundary["compose_existing_endpoint_solvers"] is True


def test_governance_closure_changes_no_runtime_or_workflow_semantics() -> None:
    data = _data()
    closure = data["governance_closure"]
    assert closure["written"] is True
    assert closure["source_review_head"] == "baf27ed33348e44ecb9ff04b8b633deecfbfa3c2"
    assert closure["production_source_changed_by_closure"] is False
    assert closure["workflow_semantics_changed_by_closure"] is False
    assert closure["scripts_changed_by_closure"] is False
    assert closure["functional_tests_changed_by_closure"] is False
    assert closure["endpoint_apis_changed_by_closure"] is False
    assert closure["solver_or_runtime_semantics_changed_by_closure"] is False
    assert closure["closure_exact_head_gate_complete"] is False
    assert closure["status"] == "AWAITING_CLOSURE_EXACT_HEAD_GATE"
    assert closure["changed_files_only"] == [
        "docs/v4/adr/ADR-035-v4-system-post-orchestration-review.md",
        "docs/v4/governance/v4_system_post_orchestration_review_r1.yaml",
        "docs/v4/reports/v4_system_post_orchestration_review_r1.md",
        "tests/v4/test_v4_system_post_orchestration_review_r1.py",
    ]

    # The frozen workflow still only contains the review test as the stage-specific addition;
    # the closure itself must not need a new execution step.
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/v4/test_v4_system_post_orchestration_review_r1.py" in workflow
    assert "Execute V4 replay-input orchestration R1" in workflow
    assert "V4 food intake dose" not in workflow


def test_hard_boundaries_remain_frozen_through_closure() -> None:
    hard = _data()["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["replay_orchestration_changed"] is False
    assert hard["existing_v4_four_module_integrator_changed"] is False
    assert hard["component_solver_equations_changed"] is False
    assert hard["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["physical_validation_complete"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["obt_redesign_authorized"] is False
    assert hard["full_soil_hydrology_authorized"] is False
    assert hard["plant_water_dynamics_authorized"] is False
    assert hard["root_q_w_inferred_from_atmos"] is False
    assert hard["food_intake_dose_v4_adapter_implementation_authorized"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False


def test_exit_requires_second_gate_expected_head_merge_and_no_drift() -> None:
    data = _data()
    exit_state = data["exit_state"]
    assert exit_state["review_decision_complete"] is True
    assert exit_state["first_exact_head_gate_complete"] is True
    assert exit_state["governance_closure_written"] is True
    assert exit_state["governance_closure_exact_head_gate_complete"] is False
    assert exit_state["merge_authorized"] is False
    assert exit_state["next_stage_after_successful_merge"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1"
    assert all(data["closure_rule"].values())

    replay = REPLAY.read_text(encoding="utf-8")
    assert "class V4ReplayInputSystemOrchestrator" in replay
    text = ADR.read_text(encoding="utf-8") + REPORT.read_text(encoding="utf-8")
    assert "`PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_CLOSURE_GATE`" in text
    assert "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1" in text
    assert "terminal diagnostic harvest" in text.lower()
