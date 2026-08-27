from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "docs/v4/governance/v4_current_system_state.yaml"
REVIEW = ROOT / "docs/v4/governance/v4_development_completeness_review_r1.yaml"
SOIL = ROOT / "docs/v4/reports/v4_three_layer_soil_core_implementation_r1.md"
ROOT_REPORT = ROOT / "docs/v4/reports/v4_three_layer_root_flux_core_implementation_r1.md"
EQ39 = ROOT / "docs/v4/adr/ADR-045-v4-root-total-uptake-ufotri-eq39-implementation-r1.md"
INTEGRATION = ROOT / "docs/v4/reports/v4_soil_root_tfwt_obt_integration_r1.md"
REPLAY = ROOT / "docs/v4/reports/v4_system_replay_input_orchestration_implementation_r1.md"
ENDPOINT = ROOT / "docs/v4/reports/v4_system_food_intake_dose_adapter_implementation_r1.md"
E2E = ROOT / "docs/v4/adr/ADR-046-v4-controlled-ufotri-end-to-end-numerical-integration-r1.md"
LEAF = ROOT / "docs/v4/leaf/v4_2_leaf_dynamic_stomatal_readiness.yaml"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_completeness_review_has_zero_mandatory_internal_blockers():
    review = _load(REVIEW)
    verdict = review["verdict"]
    assert verdict["token"] == "PASS_NO_MANDATORY_INTERNAL_BLOCKERS"
    assert verdict["mandatory_internal_blocker_count"] == 0
    assert verdict["selected_v4_baseline_internal_development_complete_for_rc_entry"] is True

    matrix = review["review_matrix"]
    assert matrix
    assert all(item["mandatory_blocker"] is False for item in matrix.values())


def test_completeness_review_snapshot_authorizes_rc1_without_pinning_living_state():
    current = _load(CURRENT)
    review = _load(REVIEW)
    current_review = current["development_completeness_review"]
    auth = review["next_stage_authorization"]

    assert auth["selected"] == "V4_DEVELOPMENT_BASELINE_RC1"
    assert auth["new_physics_subsystem_authorized"] is False
    assert current["project_phase"].startswith("INTERNAL_V4_")
    assert current_review["verdict"] == "PASS_NO_MANDATORY_INTERNAL_BLOCKERS"
    assert current_review["mandatory_internal_blocker_count"] == 0
    assert current["current_next_stage"]["new_physics_implementation_pre_authorized"] is False


def test_soil_root_and_eq39_selected_baseline_evidence_exists():
    soil = SOIL.read_text(encoding="utf-8")
    root = ROOT_REPORT.read_text(encoding="utf-8")
    eq39 = EQ39.read_text(encoding="utf-8")

    assert "L1↔L2" in soil and "L2↔L3" in soil
    assert "Restart" in soil
    assert "J_root,i = q_w,i * C_w,i" in root
    assert "E_p = [Delta / (Delta + gamma)] R_n / (lambda rho_w)" in eq39
    assert "ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE" in eq39


def test_coupled_and_endpoint_software_gates_are_present():
    integration = INTEGRATION.read_text(encoding="utf-8")
    replay = REPLAY.read_text(encoding="utf-8")
    endpoint = ENDPOINT.read_text(encoding="utf-8")
    e2e = E2E.read_text(encoding="utf-8")

    assert "PASS_SOIL_ROOT_TFWT_OBT_INTEGRATION" in integration
    assert "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION" in replay
    assert "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION" in endpoint
    assert "SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES=TRUE" in e2e
    assert "restart equivalence" in e2e.lower()
    assert "deterministic repeat" in e2e.lower()


def test_leaf_r5_is_evidence_hold_not_mandatory_gap():
    leaf = _load(LEAF)
    current = _load(CURRENT)

    assert leaf["status"] == "HOLD_EMPIRICAL_EVIDENCE_REQUIRED"
    assert leaf["hard_invariants"]["leaf_implementation_authorized"] is False
    extension = current["optional_or_held_extensions"]["leaf_r5_dynamic_stomatal"]
    assert extension["mandatory_for_v4_internal_completion"] is False


def test_optional_extensions_are_not_promoted_into_blockers():
    review = _load(REVIEW)
    current = _load(CURRENT)

    assert set(review["non_blocking_extensions"]) == {
        "leaf_r5_dynamic_stomatal",
        "full_richards_darcy_hydrology",
        "obt_multi_pool",
        "ufotri_short_term_3h_delay",
        "penman_eq38_aerodynamic_term",
    }
    assert all(
        item["mandatory_for_v4_internal_completion"] is False
        for item in current["optional_or_held_extensions"].values()
    )


def test_production_atmos_and_validation_claims_remain_deferred_fail_closed():
    current = _load(CURRENT)
    scope = current["scope_policy"]
    boundaries = current["readiness_boundaries"]

    assert scope["real_production_inputs_currently_required"] is False
    assert scope["real_production_inputs_deferred"] is True
    assert scope["real_cteas_atmos_binding_currently_required"] is False
    assert scope["real_cteas_atmos_binding_deferred"] is True

    assert boundaries == {
        "full_model_production_ready": False,
        "production_input_packet_ready": False,
        "real_cteas_atmos_binding": False,
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "calibration_started": False,
        "active_parameters": 0,
        "v3_default_path_changed": False,
    }


def test_review_authorizes_rc_only_not_new_physics():
    review = _load(REVIEW)
    auth = review["next_stage_authorization"]

    assert auth["selected"] == "V4_DEVELOPMENT_BASELINE_RC1"
    assert auth["new_physics_subsystem_authorized"] is False
    assert auth["solver_equation_change_authorized"] is False
    assert auth["production_input_binding_authorized"] is False
    assert auth["real_atmos_binding_authorized"] is False
    assert auth["calibration_authorized"] is False
    assert auth["empirical_validation_claim_authorized"] is False
    assert auth["physical_accuracy_claim_authorized"] is False
