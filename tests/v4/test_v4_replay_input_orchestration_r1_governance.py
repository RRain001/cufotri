from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_replay_input_orchestration_implementation_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_replay_input_orchestration_implementation_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-034-v4-system-replay-input-orchestration-implementation.md"
SOURCE = ROOT / "src/cteas_ufotri/v4_integration/replay_input_orchestration.py"
FROZEN_CORE = ROOT / "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def test_implementation_is_authorized_opt_in_and_awaits_exact_head_gate() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1"
    assert data["status"] == "IMPLEMENTED_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "8588d9e59916c89c2dfa4007dbedfea39b2d2e9f"
    assert data["authorization"]["source_decision"] == "V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1"
    assert data["authorization"]["decision_no_drift_verified"] is True
    assert data["implementation"]["opt_in_only"] is True
    assert data["implementation"]["existing_four_module_integrator_modified"] is False
    assert data["implementation"]["v3_default_pipeline_modified"] is False
    assert data["implementation"]["component_solver_equations_modified"] is False


def test_selected_operator_order_and_input_ownership_are_preserved() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["implementation"]["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    order = data["interval_order"]
    assert order.index("COMPUTE_BASELINE_SIGNED_LEAF_EXCHANGE") < order.index("ADVANCE_OBT_FROM_LEAF_UPDATED_TFWT")
    assert order.index("ADVANCE_OBT_FROM_LEAF_UPDATED_TFWT") < order.index("RECONCILE_ENDPOINT_TFWT_WITH_POST_OBT_ROOT_GAIN")
    ownership = data["input_ownership"]
    assert ownership["atmosphere_replay"]["deposition_mapping"] == "SURFACE_DEPOSITION_FLUX_TO_L1_ONLY"
    assert ownership["atmosphere_replay"]["precipitation_to_infiltration"] == "FORBIDDEN"
    assert ownership["soil_external"]["base_surface_deposition_must_be_zero"] is True
    assert ownership["soil_external"]["base_root_slots_must_be_zero"] is True
    assert ownership["root_q_w"]["independent_from_atmos_provenance"] is True
    assert ownership["root_q_w"]["inferred_from_atmos_meteorology"] is False
    assert ownership["leaf"]["dynamic_leaf_r5"] is False


def test_acceptance_gates_include_zero_leaf_equivalence_and_conservation() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    gates = data["acceptance_gates"]
    zero = gates["zero_leaf_exchange_equivalence"]
    assert zero["required"] is True
    assert zero["reference"] == "V4SoilRootTFWTOBTIntegrator"
    assert "endpoint_state" in zero["comparison"]
    assert "core_balance_residuals" in zero["comparison"]
    assert gates["nonzero_leaf_before_obt"] == "required"
    assert gates["signed_leaf_reemission_conservation"] == "required"
    assert gates["precipitation_not_infiltration"] == "required"
    assert gates["provenance_independence"] == "required"
    assert gates["restart_equivalence"] == "required"
    assert gates["machine_harness"] == "scripts/v4/run_replay_input_orchestration_r1.py"
    conservation = data["conservation"]
    assert conservation["leaf_exchange_is_signed_external_transfer"] is True
    assert conservation["root_is_internal_to_coupled_system"] is True
    assert conservation["root_plan_applied_once"] is True


def test_source_is_new_high_level_layer_and_frozen_core_does_not_reverse_import_it() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    frozen = FROZEN_CORE.read_text(encoding="utf-8")
    assert "class V4ReplayInputSystemOrchestrator" in source
    assert "class V4ReplayIntervalInput" in source
    assert "class ReplayDomainProvenance" in source
    assert "signed_leaf_exchange_flux" in source
    assert "V4SoilRootTFWTOBTIntegrator" not in source
    assert "replay_input_orchestration" not in frozen
    assert "v3_pipeline" not in source


def test_protected_gate_explicitly_runs_replay_orchestration_machine_harness() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/v4/test_v4_replay_input_orchestration_r1.py" in workflow
    assert "Execute V4 replay-input orchestration R1" in workflow
    assert "python scripts/v4/run_replay_input_orchestration_r1.py" in workflow


def test_hard_boundaries_and_closure_rule_prevent_scope_creep() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["existing_v4_four_module_integrator_changed"] is False
    assert hard["existing_component_solver_equations_changed"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["food_intake_dose_v4_integration_authorized"] is False
    assert hard["full_soil_hydrology_authorized"] is False
    assert hard["plant_water_dynamics_authorized"] is False
    assert hard["root_q_w_inferred_from_atmos"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False
    assert data["exact_head_gate"]["complete"] is False
    assert data["closure_rule"]["governance_closure_required_after_first_exact_head_pass"] is True
    assert data["exit_state"]["merge_authorized"] is False
    assert data["exit_state"]["next_stage_after_successful_merge"] == "SYSTEM_LEVEL_POST_ORCHESTRATION_REVIEW"
    assert "`IMPLEMENTED_AWAITING_EXACT_HEAD_GATE`" in REPORT.read_text(encoding="utf-8")
    assert "`IMPLEMENTED_AWAITING_EXACT_HEAD_GATE`" in ADR.read_text(encoding="utf-8")
