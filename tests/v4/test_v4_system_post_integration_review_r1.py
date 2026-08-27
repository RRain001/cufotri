from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_post_integration_review_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_post_integration_review_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-032-v4-system-post-integration-priority.md"


def test_post_integration_review_updates_system_state_without_reopening_v3() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_SYSTEM_POST_INTEGRATION_REVIEW_R1"
    assert data["status"] == "PASS_SYSTEM_POST_INTEGRATION_REVIEW"
    assert data["review_scope"]["solver_source_changed"] is False
    assert data["review_scope"]["numerical_coupling_changed"] is False
    assert data["post_integration_system_state"]["soil"]["status"] == "IMPLEMENTED_AND_INTEGRATED"
    assert data["post_integration_system_state"]["soil"]["full_hydrology"] is False
    assert data["post_integration_system_state"]["root"]["status"] == "IMPLEMENTED_AND_INTEGRATED"
    assert data["post_integration_system_state"]["root"]["q_w_source"] == "EXTERNAL_EXPLICIT_FORCING"
    assert data["stale_prior_assumptions_resolved"]["roadmap_three_layer_soil_candidate_not_implemented"] == "NOW_FALSE"
    assert data["stale_prior_assumptions_resolved"]["v3_default_baseline_replaced"] is False


def test_review_selects_control_plane_input_decision_without_implementation_authorization() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    ranking = data["candidate_ranking"]
    assert ranking[0]["candidate"] == "V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1"
    assert ranking[0]["disposition"] == "SELECT_NEXT_CONTROL_PLANE_STAGE"
    assert ranking[0]["implementation_authorized_now"] is False
    assert ranking[1]["candidate"] == "FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION"
    assert ranking[2]["candidate"] == "LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION"
    assert ranking[2]["disposition"] == "HOLD"
    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1"
    assert next_stage["authorization_effective_after_review_merge"] is True
    assert next_stage["scope"] == "CONTROL_PLANE_AND_INTERFACE_DECISION_ONLY"
    assert next_stage["adapter_implementation_authorized"] is False
    assert next_stage["solver_changes_authorized"] is False


def test_review_gate_evidence_and_hard_boundaries_are_frozen() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    gate = data["review_gate"]
    assert gate["review_head_sha"] == "cbd2dafc374e22da17c197b7255444836fdc8393"
    assert gate["protected_gate_run_id"] == 33029158798
    assert gate["remediation_run_id"] == 33029158729
    assert gate["protected_gate_status"] == "SUCCESS"
    assert gate["remediation_status"] == "SUCCESS"
    assert gate["sensitivity_status"] == "PASS_SOFTWARE_SCREENING"
    assert gate["operator_split_status"] == "PASS_SELECTION"
    assert gate["soil_root_tfwt_obt_status"] == "PASS_INTEGRATION"
    assert gate["closure_exact_head_gate_required"] is True
    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["full_soil_hydrology_authorized"] is False
    assert hard["plant_water_dynamics_authorized"] is False
    assert hard["food_intake_dose_v4_integration_authorized"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False


def test_report_and_adr_keep_next_stage_as_decision_not_implementation() -> None:
    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    assert "`PASS_SYSTEM_POST_INTEGRATION_REVIEW`" in report
    assert "is selected as the next control-plane/interface decision stage" in report
    assert "does not authorize adapter implementation" in adr
    assert "root `q_w,i`" in adr
    assert "Real CTEAS-Atmos binding remains blocked" in adr
