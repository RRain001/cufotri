from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "docs/v4/governance/v4_current_system_state.yaml"
STAGE = ROOT / "docs/v4/governance/v4_state_normalization_r1.yaml"
ADR45 = ROOT / "docs/v4/adr/ADR-045-v4-root-total-uptake-ufotri-eq39-implementation-r1.md"
R5 = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r5.yaml"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_current_state_authority_splits_ambiguous_root_q_w_flag():
    current = _load(CURRENT)
    baseline = current["controlled_baseline_state"]
    legacy = current["legacy_flag_normalization"]

    assert baseline["root_q_w_controlled_construction_path_resolved"] is True
    assert baseline["root_q_w_production_case_input_ready"] is False
    assert legacy["deprecated_current_state_flag"] == "ROOT_Q_W_PRODUCTION_INPUT_RESOLVED"
    assert legacy["current_authority_must_use_split_flags"] is True
    assert "root_q_w_production_input_resolved" not in baseline


def test_normalization_is_grounded_in_historical_semantics_without_rewriting_history():
    adr45 = ADR45.read_text(encoding="utf-8")
    r5 = _load(R5)
    current = _load(CURRENT)

    assert "ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE" in adr45
    assert r5["hard_boundaries"]["root_q_w_production_input_resolved"] is False
    assert current["legacy_flag_normalization"]["historical_stage_files_are_immutable"] is True


def test_internal_development_route_defers_production_and_real_atmos():
    current = _load(CURRENT)
    stage = _load(STAGE)
    policy = current["scope_policy"]

    assert stage["normalization_decisions"]["project_phase"] == "INTERNAL_V4_DEVELOPMENT_COMPLETION"
    assert current["project_phase"].startswith("INTERNAL_V4_")
    assert policy["real_production_inputs_currently_required"] is False
    assert policy["real_production_inputs_deferred"] is True
    assert policy["real_cteas_atmos_binding_currently_required"] is False
    assert policy["real_cteas_atmos_binding_deferred"] is True
    assert policy["production_case_declaration_track_active"] is False
    assert policy["production_case_declaration_issue"] == 52


def test_normalization_snapshot_selected_the_two_stage_internal_route():
    stage = _load(STAGE)

    assert stage["route_reset"]["mandatory_internal_sequence"] == [
        "V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1",
        "V4_DEVELOPMENT_BASELINE_RC1",
    ]
    assert stage["route_reset"]["next_stage"] == "V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1"
    assert stage["route_reset"]["new_physics_pre_authorized"] is False


def test_optional_extensions_are_not_internal_completion_blockers():
    current = _load(CURRENT)
    optional = current["optional_or_held_extensions"]

    expected = {
        "leaf_r5_dynamic_stomatal",
        "full_richards_darcy_hydrology",
        "obt_multi_pool",
        "ufotri_short_term_3h_delay",
        "penman_eq38_aerodynamic_term",
    }
    assert set(optional) == expected
    assert all(item["mandatory_for_v4_internal_completion"] is False for item in optional.values())


def test_readiness_claims_remain_fail_closed():
    current = _load(CURRENT)
    boundaries = current["readiness_boundaries"]

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


def test_stage_scope_is_governance_only():
    stage = _load(STAGE)
    scope = stage["scope"]

    assert stage["stage"] == "V4_STATE_NORMALIZATION_R1"
    assert scope["kind"] == "GOVERNANCE_STATE_NORMALIZATION_ONLY"
    for key, value in scope.items():
        if key != "kind":
            assert value is False

    authorization = stage["next_stage_authorization"]
    assert authorization["selected"] == "V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1"
    assert authorization["solver_change_authorized"] is False
    assert authorization["numerical_coupling_change_authorized"] is False
    assert authorization["production_manifest_projection_authorized"] is False
    assert authorization["production_parameter_activation_authorized"] is False
    assert authorization["real_atmos_binding_authorized"] is False
