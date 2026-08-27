from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_replay_input_adapter_decision_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_replay_input_adapter_decision_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-033-v4-system-replay-input-adapter-decision.md"


def test_decision_is_control_plane_only_and_formally_selected() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1"
    assert data["status"] == "PASS_SYSTEM_REPLAY_ORCHESTRATION_DECISION"
    assert data["base_main_sha"] == "c5d58271c68cc79a9e0492ab934025d752f02e30"
    scope = data["scope"]
    assert scope["control_plane_and_interface_decision_only"] is True
    assert scope["production_src_changes"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["adapter_or_orchestrator_implemented"] is False


def test_field_only_adapter_is_rejected_and_system_orchestrator_selected() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    decision = data["architecture_decision"]
    assert decision["field_only_adapter"]["selected"] is False
    assert decision["field_only_adapter"]["disposition"] == "REJECT_INSUFFICIENT_FOR_COMPLETE_V4_CHAIN"
    assert decision["selected_architecture"] == "OPT_IN_REPLAY_INPUT_SYSTEM_ORCHESTRATOR"
    assert decision["current_v4_four_module_integrator"]["disposition"] == "FREEZE_AS_REFERENCE_BASELINE"
    assert decision["selected_future_layer"]["may_change_component_solver_equations"] is False
    assert decision["selected_future_layer"]["may_change_v3_default_pipeline"] is False


def test_forcing_ownership_remains_separated_and_fail_closed() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    ownership = data["future_input_ownership"]
    atmos = ownership["atmos_or_replay_record"]
    assert "air_hto_concentration_bq_m3" in atmos["owns"]
    assert "surface_deposition_flux_total_bq_m2_s" in atmos["owns"]
    assert "root_q_w_i" in atmos["does_not_own"]
    soil = ownership["three_layer_soil_external_forcing"]
    assert soil["atmospheric_deposition_mapping"] == "ONLY_SURFACE_DEPOSITION_FLUX_TOTAL_TO_L1"
    assert soil["precipitation_to_soil_water_inference"] == "FORBIDDEN"
    root = ownership["root_water_flux_forcing"]
    assert root["provenance_must_be_independent_from_atmos_record"] is True
    assert root["infer_from_temperature_humidity_wind_precipitation"] == "FORBIDDEN"
    assert ownership["leaf_exchange_inputs"]["dynamic_stomatal_model_authorized"] is False


def test_selected_interval_order_preserves_leaf_before_obt_and_root_post_obt() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    order = data["selected_interval_order"]
    operations = [entry["operation"] for entry in order["steps"]]
    assert operations.index("COMPUTE_BASELINE_SIGNED_LEAF_EXCHANGE_FROM_ATMOS_RECORD") < operations.index(
        "ADVANCE_OBT_USING_LEAF_UPDATED_TFWT_INVENTORY"
    )
    assert operations.index("ADVANCE_OBT_USING_LEAF_UPDATED_TFWT_INVENTORY") < operations.index(
        "RECONCILE_ENDPOINT_TFWT_AS_LEAF_INTERMEDIATE_MINUS_OBT_LOSS_PLUS_ROOT_GAIN"
    )
    preserved = order["preserved_semantics"]
    assert preserved["obt_sees_same_interval_leaf_exchange"] is True
    assert preserved["obt_sees_same_interval_root_gain"] is False
    assert preserved["root_reads_interval_start_soil"] is True
    assert preserved["root_gain_is_post_obt"] is True
    assert preserved["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert order["timestamp_rule"]["do_not_reset_or_forge_component_timestamps"] is True


def test_first_exact_head_gate_is_recorded_and_closure_gate_remains_required() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    gate = data["decision_gate"]
    assert gate["decision_head_sha"] == "45298061c58cbf8f558f4b25de02ca6288dcb104"
    assert gate["protected_gate_run_id"] == 33030199770
    assert gate["remediation_run_id"] == 33030199769
    assert gate["protected_gate_status"] == "SUCCESS"
    assert gate["remediation_status"] == "SUCCESS"
    assert gate["portable_suite"] == "1226 passed, 1 skipped, 57 deselected"
    assert gate["frozen_boundary_suite"] == "295 passed"
    assert gate["sensitivity_status"] == "PASS_SOFTWARE_SCREENING"
    assert gate["operator_split_status"] == "PASS_SELECTION"
    assert gate["soil_root_tfwt_obt_status"] == "PASS_INTEGRATION"
    assert gate["closure_exact_head_gate_required"] is True


def test_future_implementation_requires_zero_leaf_equivalence_and_no_drift_merge() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    gates = data["future_implementation_acceptance_gates"]
    assert gates["zero_leaf_exchange_equivalence"]["required"] is True
    assert gates["zero_leaf_exchange_equivalence"]["reference"] == "V4SoilRootTFWTOBTIntegrator"
    assert gates["conservation"]["root_plan_applied_once"] is True
    assert gates["temporal"]["restart_equivalence"] is True
    assert gates["mapping"]["no_puff_ledger_amount_as_surface_flux"] is True
    next_stage = data["next_stage_recommendation"]
    assert next_stage["stage"] == "V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1"
    assert next_stage["selected_for_post_merge_authorization"] is True
    assert next_stage["implementation_authorized_now"] is False
    assert next_stage["authorization_effective_after_no_drift_merge"] is True
    assert "closure_exact_head_protected_gate_success" in next_stage["authorization_requires"]
    assert "expected_head_merge_without_tree_drift" in next_stage["authorization_requires"]


def test_hard_boundaries_and_documents_do_not_authorize_scope_creep() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["existing_v4_four_module_integrator_changed"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["food_intake_dose_v4_integration_authorized"] is False
    assert hard["full_soil_hydrology_authorized"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False
    assert hard["empirical_validation"] is False
    exit_state = data["exit_state"]
    assert exit_state["governance_closure_complete"] is True
    assert exit_state["closure_exact_head_gate_complete"] is False
    assert exit_state["implementation_authorized"] is False
    assert exit_state["implementation_authorized_after_no_drift_merge"] is True
    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    assert "`PASS_SYSTEM_REPLAY_ORCHESTRATION_DECISION`" in report
    assert "field-only adapter" in adr
    assert "zero-leaf equivalence" in adr
    assert "Real CTEAS-Atmos binding remains blocked" in adr
