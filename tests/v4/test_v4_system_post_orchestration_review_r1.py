from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_post_orchestration_review_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_post_orchestration_review_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-035-v4-system-post-orchestration-review.md"
REPLAY = ROOT / "src/cteas_ufotri/v4_integration/replay_input_orchestration.py"
FOOD = ROOT / "src/cteas_ufotri/plant/food_v3/food_transfer_solver.py"
INTAKE = ROOT / "src/cteas_ufotri/exposure/intake_v3/intake_solver.py"
DOSE = ROOT / "src/cteas_ufotri/exposure/dose_v3/dose_solver.py"
MASS_BASIS = ROOT / "src/cteas_ufotri/plant/mass_basis_v3_1/contract.py"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def _data() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_review_is_control_plane_only_and_uses_post_orchestration_main() -> None:
    data = _data()
    assert data["stage"] == "V4_SYSTEM_POST_ORCHESTRATION_REVIEW_R1"
    assert data["status"] == "PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "a03da884eb60b82658c07e0ca57db7058480260f"
    scope = data["review_scope"]
    assert scope["kind"] == "SYSTEM_LEVEL_CONTROL_PLANE_REVIEW_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["parameter_activation"] is False
    assert scope["calibration"] is False
    assert scope["empirical_validation"] is False
    assert scope["real_cteas_atmos_binding"] is False


def test_pr30_merge_and_prior_food_deferral_blocker_are_resolved() -> None:
    data = _data()
    merge = data["orchestration_merge"]
    assert merge["pr"] == 30
    assert merge["merge_sha"] == "a03da884eb60b82658c07e0ca57db7058480260f"
    assert merge["merge_tree"] == "0f424c3f5892e25113bfe4b134677c02b4590e46"
    assert merge["parent1"] == "8588d9e59916c89c2dfa4007dbedfea39b2d2e9f"
    assert merge["parent2"] == "ddbe21e4b8121983bc7fe1b94c1507caddf209ca"
    assert merge["no_drift_verified"] is True
    assert merge["replay_machine_status"] == "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"

    resolved = data["resolved_prior_blockers"]
    assert resolved["old_food_intake_dose_disposition"] == "DEFER_UNTIL_UPSTREAM_INPUT_BOUNDARY_DECIDED"
    assert resolved["upstream_input_boundary_now_decided"] is True
    assert resolved["replay_orchestration_now_merged"] is True
    assert resolved["food_intake_dose_v4_endpoint_wiring_still_missing"] is True


def test_next_stage_is_food_intake_dose_adapter_decision_not_implementation() -> None:
    data = _data()
    ranking = data["candidate_ranking"]
    assert ranking[0]["rank"] == 1
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
    data = _data()
    boundary = data["future_adapter_boundary_requirements"]
    assert boundary["harvest_semantics"] == "TERMINAL_DIAGNOSTIC_READOUT_ONLY"
    assert boundary["harvest_trigger"] == "EXPLICIT_CALLER_REQUEST"
    assert boundary["source_state"] == "REPLAY_ENDPOINT_TFWT_AND_OBT"
    assert boundary["source_state_mutation"] == "FORBIDDEN_R1"
    assert boundary["continue_same_trajectory_after_harvest"] == "FORBIDDEN_R1"
    assert boundary["source_area_basis"] == "soil_surface_area"
    assert boundary["hidden_area_conversion"] == "FORBIDDEN"
    assert boundary["mass_basis_contract_required"] is True
    assert boundary["direct_basis_rule"] == "IDENTICAL_MASS_TISSUE_AREA_ONLY"
    assert boundary["numerical_cross_basis_conversion"] == "FORBIDDEN"
    assert boundary["endpoint_modes"] == ["OBT_ONLY", "OBT_PLUS_TFWT"]
    assert boundary["mixed_tfwt_fraction"] == "EXPLICIT_REQUIRED"
    assert boundary["independent_parameter_provenance"] is True
    assert boundary["endpoint_identity_fail_closed"] is True
    assert boundary["upstream_side_effects"] == "FORBIDDEN"


def test_current_public_apis_support_readout_boundary_without_claiming_state_depletion() -> None:
    replay = REPLAY.read_text(encoding="utf-8")
    food = FOOD.read_text(encoding="utf-8")
    intake = INTAKE.read_text(encoding="utf-8")
    dose = DOSE.read_text(encoding="utf-8")
    basis = MASS_BASIS.read_text(encoding="utf-8")

    assert "state: V4SoilRootTFWTOBTState" in replay
    assert "class FoodTransferSolver" in food
    assert "obt_state: OBTState" in food
    assert "tfwt_state: TFWTState" in food
    assert "remaining_plant_inventory_bq" in food
    assert "return FoodTransferResult" in food
    assert "class FoodIntakeSolver" in intake
    assert "food_product_mass_kg" in intake
    assert "annual_consumption_amount" in intake
    assert "class DoseSolver" in dose
    assert "committed_dose_sv" in dose
    assert "direct comparison only for identical mass/tissue/area bases" in basis
    assert "no numerical" in basis.lower()


def test_sensitivity_is_used_only_to_prioritize_endpoint_definition_not_values() -> None:
    data = _data()
    sensitivity = data["sensitivity_interpretation"]
    assert sensitivity["result_kind"] == "SYNTHETIC_LOCAL_COMPUTATIONAL_SCREENING"
    assert sensitivity["physical_uncertainty_ranking_available"] is False
    assert sensitivity["food_tfwt_harvest_fraction_local_dose_elasticity"] > 0.8
    assert sensitivity["interpretation"] == "ENDPOINT_DEFINITION_MATTERS_NOT_PARAMETER_VALIDATION"
    assert sensitivity["endpoint_scaling_is_environmental_physics_priority"] is False


def test_leaf_obt_hydrology_and_real_atmos_remain_held() -> None:
    data = _data()
    ranking = {item["candidate"]: item["disposition"] for item in data["candidate_ranking"]}
    assert ranking["REAL_CTEAS_ATMOS_BINDING"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert ranking["LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION"] == "HOLD_R4_EVIDENCE_CHECKPOINT"
    assert ranking["OBT_PHYSICS_REDESIGN"] == "HOLD_MATCHED_EVIDENCE_REQUIRED"
    assert ranking["FULL_SOIL_HYDROLOGY_OR_PLANT_WATER_DYNAMICS"] == "HOLD"

    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["replay_orchestration_changed"] is False
    assert hard["existing_v4_four_module_integrator_changed"] is False
    assert hard["component_solver_equations_changed"] is False
    assert hard["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["obt_redesign_authorized"] is False
    assert hard["full_soil_hydrology_authorized"] is False
    assert hard["plant_water_dynamics_authorized"] is False
    assert hard["root_q_w_inferred_from_atmos"] is False
    assert hard["food_intake_dose_v4_adapter_implementation_authorized"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False


def test_review_requires_two_exact_head_gates_and_is_in_protected_suite() -> None:
    data = _data()
    gate = data["review_exact_head_gate"]
    assert gate["complete"] is False
    assert gate["status"] == "AWAITING_EXACT_HEAD_GATE"
    closure = data["closure_rule"]
    assert all(closure.values())

    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/v4/test_v4_system_post_orchestration_review_r1.py" in workflow
    text = REPORT.read_text(encoding="utf-8") + ADR.read_text(encoding="utf-8")
    assert "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1" in text
    assert "terminal diagnostic harvest" in text.lower()
