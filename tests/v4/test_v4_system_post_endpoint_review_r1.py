from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_post_endpoint_review_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_post_endpoint_review_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-037-v4-system-post-endpoint-review.md"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def load_governance() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_post_endpoint_review_is_control_plane_only_and_anchored_to_no_drift_merge() -> None:
    data = load_governance()
    assert data["stage"] == "V4_SYSTEM_POST_ENDPOINT_REVIEW_R1"
    assert data["status"] == "PASS_REVIEW_EXACT_HEAD_AWAITING_CLOSURE_GATE"
    assert data["base_main_sha"] == "48bb658c986d4ca1f355991e4e298a16863fec3b"
    scope = data["review_scope"]
    assert scope["kind"] == "SYSTEM_LEVEL_CONTROL_PLANE_REVIEW_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["parameter_activation"] is False
    assert scope["calibration"] is False

    merge = data["endpoint_merge"]
    assert merge["pr"] == 33
    assert merge["merge_sha"] == "48bb658c986d4ca1f355991e4e298a16863fec3b"
    assert merge["merge_tree"] == "bb7fe7a751cc23d3147a4c9b52bc510cd66f5915"
    assert merge["parent1"] == "f13a36d2bd5b92a86bf6405388c8e5eb5d3a5472"
    assert merge["parent2"] == "269dd5f2a96d7270ee7a342cdd18f33bd877d1eb"
    assert merge["no_drift_verified"] is True
    assert merge["head_to_merge_files_empty"] is True
    assert merge["closure_portable_suite"] == {"passed": 1275, "skipped": 1, "deselected": 57}
    assert merge["closure_frozen_suite"] == {"passed": 337}


def test_north_star_is_software_connected_but_not_declared_physics_ready() -> None:
    data = load_governance()
    chain = data["north_star_software_connectivity"]
    assert chain["cteas_atmos_live_binding"] is False
    assert chain["normalized_replay_forcing"] is True
    assert chain["baseline_leaf_exchange"] is True
    assert chain["three_layer_soil_root"] is True
    assert chain["tfwt"] is True
    assert chain["reduced_obt"] is True
    assert chain["terminal_food_transfer"] is True
    assert chain["intake"] is True
    assert chain["dose"] is True
    assert chain["interpretation"] == "SOFTWARE_CHAIN_CONNECTED_WITH_SYNTHETIC_OR_REPLAY_INPUTS_NOT_PHYSICS_READY"


def test_atmos_is_rechecked_but_remains_external_and_fail_closed() -> None:
    data = load_governance()
    atmos = data["atmos_recheck"]
    assert atmos["repository"] == "RRain001/CTEAS-Atmos"
    assert atmos["current_main_sha"] == "341d9d6b3b45b6e2416e09aec0b381adf137fd3e"
    assert atmos["same_as_exchange_contract_audit_reference"] is True
    assert atmos["true_surface_deposition_flux_product_confirmed"] is False
    assert atmos["real_binding_status"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert atmos["disposition"] == "EXTERNAL_PREREQUISITE_SKIP_UNTIL_ATMOS_READY"
    assert atmos["modifies_atmos_repository"] is False


def test_root_structure_is_advanced_without_claiming_production_qw_is_resolved() -> None:
    data = load_governance()
    resolved = data["resolved_or_advanced_blockers"]
    assert resolved["layered_root_architecture_selected"] is True
    assert resolved["three_layer_root_flux_core_implemented"] is True
    assert resolved["v4_root_operator_split_selected"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert resolved["v4_root_integrated_with_soil_tfwt_obt"] is True
    assert resolved["root_q_w_production_input_resolved"] is False
    assert resolved["ufotri_20_40_40_active"] is False
    assert resolved["ufotri_reference_layer_rates_active"] is False
    assert resolved["short_term_3h_delay_active"] is False


def test_obt_evidence_readiness_is_selected_without_authorizing_obt_implementation() -> None:
    data = load_governance()
    basis = data["obt_evidence_basis"]
    assert basis["prior_priority_records"] == [
        "R1_OBT_DAYLIGHT_FORMATION_STATE",
        "R2_OBT_NIGHTTIME_FORMATION_STATE",
        "R3_OBT_PHOTOSYNTHETIC_FORCING_STATE",
    ]
    assert basis["prior_priority"] == "CRITICAL"
    assert basis["prior_ranks"] == [1, 2, 3]
    assert basis["selected_v4_architecture"] == "PRECURSOR_PLUS_EXCHANGEABLE_NONEXCHANGEABLE_OBT_POOLS"
    assert basis["current_runnable_baseline"] == "REDUCED_FIRST_ORDER_KF_KR"
    assert basis["matched_empirical_evidence_complete"] is False
    assert basis["multi_pool_implementation_authorized"] is False
    assert basis["parameter_values_authorized"] is False

    ranking = data["candidate_ranking"]
    assert ranking[0]["candidate"] == "V4_OBT_FORMATION_EVIDENCE_READINESS_R1"
    assert ranking[0]["disposition"] == "SELECT_NEXT_CONTROL_PLANE_STAGE"
    assert ranking[0]["implementation_authorized_now"] is False
    assert ranking[1]["candidate"] == "V4_ROOT_QW_PRODUCTION_INPUT_EVIDENCE_R1"
    assert ranking[1]["disposition"] == "DEFER_ONE_STAGE_STRUCTURE_READY_INPUT_UNRESOLVED"
    assert ranking[2]["candidate"] == "POST_END_TO_END_PARAMETER_EVIDENCE_PRIORITY_REVIEW"
    assert ranking[2]["disposition"] == "DEFER_UNTIL_CRITICAL_OBT_EVIDENCE_DECISION"

    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_OBT_FORMATION_EVIDENCE_READINESS_R1"
    assert next_stage["scope"] == "CONTROL_PLANE_AND_EVIDENCE_READINESS_ONLY"
    assert next_stage["new_obt_solver_authorized"] is False
    assert next_stage["precursor_pool_runtime_authorized"] is False
    assert next_stage["exchangeable_nonexchangeable_runtime_authorized"] is False
    assert next_stage["obt_parameter_activation_authorized"] is False
    assert next_stage["current_kf_kr_calibration_authorized"] is False
    assert next_stage["global_parameter_activation_authorized"] is False


def test_leaf_and_stale_obt_branch_remain_fail_closed() -> None:
    data = load_governance()
    leaf = data["leaf_status"]
    assert leaf["r4_status"] == "READY_FOR_FEASIBILITY_REVIEW_NOT_EXECUTED"
    assert leaf["experiment_executed"] is False
    assert leaf["empirical_packet_collected"] is False
    assert leaf["leaf_r5_authorized"] is False
    assert leaf["disposition"] == "HOLD_R4_EVIDENCE_CHECKPOINT"

    stale = data["stale_branch_disposition"]
    assert stale["branch"] == "codex/v4-3-obt-formation-readiness"
    assert stale["head_sha"] == "d4bb2def0e81fe5a26b772a239e8c6de8f0d0dcc"
    assert stale["contains_obt_readiness_work"] is False
    assert stale["authority"] == "NONE_STALE_EMPTY_ANCHOR"
    assert stale["reuse_for_next_stage"] is False


def test_next_stage_requires_matched_evidence_and_forbids_shortcuts() -> None:
    data = load_governance()
    questions = data["next_stage_required_questions"]
    assert questions["biological_pool_definitions_frozen"] == "required"
    assert questions["direct_vs_derived_vs_latent_state_classification"] == "required"
    assert questions["matched_dataset_or_acquisition_plan"] == "required"
    assert questions["identifiability_gate"] == "required"
    assert questions["independent_holdout_gate"] == "required"
    assert questions["fail_closed_if_evidence_insufficient"] == "required"
    assert questions["literature_ranges_as_substitute_for_matched_data"] == "forbidden"
    assert questions["synthetic_fixtures_as_empirical_evidence"] == "forbidden"

    required = set(data["required_matched_evidence_fields"])
    assert {
        "time_resolved_tfwt",
        "time_resolved_obt",
        "daylight_or_light_state",
        "photosynthetic_activity_or_PAR",
        "temperature",
        "crop_identity",
        "developmental_stage",
        "plant_mass_basis",
        "tissue_scope",
        "area_basis",
        "timestamp_and_time_support",
        "independent_biological_replicates",
        "provenance",
    } <= required


def test_first_exact_head_and_governance_closure_are_frozen_before_second_gate() -> None:
    data = load_governance()
    failed = data["superseded_first_attempt"]
    assert failed["head_sha"] == "3e788e8f0919e7dc42ed068269c6bcc750575c87"
    assert failed["certified"] is False
    assert failed["remediation"] == {"run_id": 33037233021, "status": "SUCCESS"}
    assert failed["protected_gate"] == {"run_id": 33037232966, "status": "FAILURE"}
    assert failed["portable_suite"] == {"passed": 1283, "failed": 1, "skipped": 1, "deselected": 57}
    assert failed["failure_classification"] == "GOVERNANCE_DOCUMENT_STRING_CONSISTENCY_ONLY"
    assert failed["runtime_failure"] is False
    assert failed["model_failure"] is False
    assert failed["roadmap_decision_changed_by_fix"] is False

    gate = data["first_exact_head_gate"]
    assert gate["complete"] is True
    assert gate["head_sha"] == "c571a1e6bdf856f76a326f68cb10c304973128c0"
    assert gate["protected_gate"] == {"run_id": 33037462292, "status": "SUCCESS"}
    assert gate["remediation"] == {"run_id": 33037462279, "status": "SUCCESS"}
    assert gate["portable_suite"] == {"passed": 1284, "skipped": 1, "deselected": 57}
    assert gate["frozen_boundary_suite"] == {"passed": 346}
    assert gate["checkout_merge_sha"] == "eac67ac3ec27d64b32e0a4af54f4fa9533ed88b9"
    assert gate["machine_gates"] == {
        "sensitivity": "PASS_SOFTWARE_SCREENING",
        "root_operator_split": "PASS_SELECTION",
        "soil_root_tfwt_obt": "PASS_INTEGRATION",
        "replay_orchestration": "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION",
        "food_intake_dose_endpoint": "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION",
    }

    closure = data["governance_closure"]
    assert closure["written"] is True
    assert closure["source_review_head"] == "c571a1e6bdf856f76a326f68cb10c304973128c0"
    assert closure["production_source_changed_by_closure"] is False
    assert closure["workflow_changed_by_closure"] is False
    assert closure["scripts_changed_by_closure"] is False
    assert closure["solver_or_runtime_semantics_changed_by_closure"] is False
    assert closure["review_decision_changed_by_closure"] is False
    assert closure["closure_exact_head_gate_complete"] is False
    assert closure["status"] == "AWAITING_CLOSURE_EXACT_HEAD_GATE"


def test_hard_invariants_and_review_artifacts_remain_fail_closed() -> None:
    data = load_governance()
    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["v4_runtime_changed"] is False
    assert hard["component_solver_equations_changed"] is False
    assert hard["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["obt_multi_pool_implementation_authorized"] is False
    assert hard["obt_parameter_activation_authorized"] is False
    assert hard["root_q_w_production_input_resolved"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False

    exit_state = data["exit_state"]
    assert exit_state["review_decision_complete"] is True
    assert exit_state["first_exact_head_gate_complete"] is True
    assert exit_state["governance_closure_written"] is True
    assert exit_state["governance_closure_exact_head_gate_complete"] is False
    assert exit_state["merge_authorized"] is False
    assert exit_state["next_stage_after_successful_merge"] == "V4_OBT_FORMATION_EVIDENCE_READINESS_R1"

    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for text in (report, adr):
        assert "V4_OBT_FORMATION_EVIDENCE_READINESS_R1" in text
        assert "ACTIVE_PARAMETERS = 0" in text
        assert "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in text
        assert "c571a1e6bdf856f76a326f68cb10c304973128c0" in text
        assert "33037462292" in text
        assert "33037462279" in text
    assert "tests/v4/test_v4_system_post_endpoint_review_r1.py" in workflow
