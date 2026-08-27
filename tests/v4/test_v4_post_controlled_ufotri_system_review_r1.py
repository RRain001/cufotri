from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_post_controlled_ufotri_system_review_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_post_controlled_ufotri_system_review_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-047-v4-post-controlled-ufotri-system-review-r1.md"


def load_governance() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_review_is_control_plane_only_and_anchored_to_clean_pr43_merge() -> None:
    data = load_governance()
    assert data["stage"] == "V4_POST_CONTROLLED_UFOTRI_SYSTEM_REVIEW_R1"
    assert data["status"] == "REVIEW_DECISION_COMPLETE_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "589d23a81fb27509fb8591dac8695971dc14905f"
    scope = data["review_scope"]
    assert scope["kind"] == "SYSTEM_LEVEL_CONTROL_PLANE_RERANK_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["workflow_changed"] is False
    assert scope["parameter_values_changed"] is False

    merge = data["controlled_end_to_end_merge"]
    assert merge["pr"] == 43
    assert merge["merge_sha"] == "589d23a81fb27509fb8591dac8695971dc14905f"
    assert merge["merge_tree"] == "b75843f57bb2fdb308083f76d6267f68933133a1"
    assert merge["parent1"] == "2814579b6bc345d31cabf36f7712ede78292ce46"
    assert merge["parent2"] == "64ea75593b34f864cc4c96f36bc8561ebaac5279"
    assert merge["no_drift_verified"] is True
    assert merge["head_to_merge_files_empty"] is True
    assert merge["certified_head"]["remediation_run"] == 33054272035
    assert merge["certified_head"]["protected_run"] == 33054272016
    assert merge["certified_head"]["protected_merge_ref"] == "e2d7f2e33e60d4376cd4fee393d0b38531ac57e6"
    assert merge["certified_head"]["portable_suite"] == {
        "passed": 1355,
        "skipped": 1,
        "deselected": 57,
        "warnings": 1,
    }
    assert merge["certified_head"]["frozen_boundary_suite"] == {"passed": 375}


def test_controlled_ufotri_chain_is_connected_without_full_production_claim() -> None:
    state = load_governance()["current_system_state"]
    assert state["software_chain_connected_with_controlled_ufotri_profiles"] is True
    assert state["normalized_replay_or_synthetic_atmosphere"] is True
    assert state["baseline_leaf_exchange"] is True
    assert state["three_layer_soil_root"] is True
    assert state["root_total_uptake_boundary"] == "EQUILIBRIUM_RADIATION_EQ39"
    assert state["root_distribution"] == [0.2, 0.4, 0.4]
    assert state["root_q_w_production_input_resolved"] is True
    assert state["obt_runtime"] == "REDUCED_UFOTRI_KF_KR_BASELINE"
    assert state["terminal_harvest"] == "KEEP_HARVEST_EVENT"
    assert state["food_intake_dose_endpoint"] is True
    assert state["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert state["full_model_production_ready"] is False


def test_obt_evidence_and_root_qw_are_removed_from_leading_unresolved_blockers() -> None:
    data = load_governance()
    resolved = data["resolved_or_superseded_previous_blockers"]
    assert resolved["obt_external_evidence_acquisition_selected"] is False
    assert resolved["obt_external_email_acquisition_required"] is False
    assert resolved["obt_controlled_ufotri_baseline_active"] is True
    assert resolved["obt_multi_pool_implementation_authorized"] is False
    assert resolved["root_q_w_production_input_resolved"] is True
    assert resolved["ufotri_20_40_40_controlled_profile_active"] is True
    assert resolved["ufotri_reference_layer_rates_active"] is False
    assert resolved["short_term_3h_delay_active"] is False


def test_production_input_readiness_is_selected_before_new_physics() -> None:
    data = load_governance()
    ranking = data["candidate_ranking"]
    assert ranking[0]["candidate"] == "V4_PRODUCTION_INPUT_READINESS_AUDIT_R1"
    assert ranking[0]["disposition"] == "SELECT_NEXT_CONTROL_PLANE_STAGE"
    assert ranking[1]["candidate"] == "REAL_CTEAS_ATMOS_BINDING"
    assert ranking[1]["disposition"] == "HOLD_EXTERNAL_PREREQUISITE_SURFACE_FLUX_UNCONFIRMED"
    assert ranking[2]["candidate"] == "LEAF_R5_DYNAMIC_STOMATAL_IMPLEMENTATION"
    assert ranking[2]["disposition"] == "HOLD_R4_EVIDENCE_CHECKPOINT_NOT_EXECUTED"
    assert ranking[3]["candidate"] == "FULL_SOIL_HYDROLOGY_OR_PLANT_WATER_DYNAMICS"
    assert ranking[3]["disposition"] == "HOLD_NOT_REQUIRED_FOR_SELECTED_CONTROLLED_PATH"
    assert ranking[4]["candidate"] == "OBT_MULTI_POOL_OR_EXTERNAL_MATCHED_EVIDENCE_TRACK"
    assert ranking[4]["disposition"] == "HOLD_SUPERSEDED_FOR_CONTROLLED_UFOTRI_BASELINE"

    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_PRODUCTION_INPUT_READINESS_AUDIT_R1"
    assert next_stage["scope"] == "CONTROL_PLANE_AND_INPUT_INVENTORY_ONLY"
    assert next_stage["new_physics_implementation_authorized"] is False
    assert next_stage["solver_changes_authorized"] is False
    assert next_stage["numerical_coupling_changes_authorized"] is False
    assert next_stage["parameter_fitting_authorized"] is False
    assert next_stage["real_cteas_atmos_binding_authorized"] is False
    assert next_stage["leaf_r5_authorized"] is False
    assert next_stage["full_hydrology_authorized"] is False
    assert next_stage["multi_pool_obt_authorized"] is False


def test_remaining_physics_tracks_remain_fail_closed() -> None:
    blockers = load_governance()["remaining_blockers"]
    assert blockers["real_cteas_atmos_binding"]["status"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert blockers["real_cteas_atmos_binding"]["true_surface_deposition_flux_product_confirmed"] is False
    assert blockers["real_cteas_atmos_binding"]["implementation_authorized_now"] is False
    assert blockers["leaf_r5"]["status"] == "R4_EVIDENCE_CHECKPOINT_NOT_EXECUTED"
    assert blockers["leaf_r5"]["implementation_authorized_now"] is False
    assert blockers["full_hydrology_or_plant_water_dynamics"]["status"] == "NOT_REQUIRED_FOR_SELECTED_CONTROLLED_EQ39_PATH"
    assert blockers["full_hydrology_or_plant_water_dynamics"]["implementation_authorized_now"] is False
    assert blockers["obt_multi_pool_or_external_matched_evidence"]["status"] == "NOT_SELECTED_FOR_CONTROLLED_BASELINE_ROUTE"
    assert blockers["obt_multi_pool_or_external_matched_evidence"]["implementation_authorized_now"] is False


def test_next_audit_covers_all_production_input_domains_and_classifications() -> None:
    data = load_governance()
    domains = data["production_input_readiness_audit_required_domains"]
    assert {
        "air_hto_concentration",
        "surface_deposition_flux",
        "temperature",
        "humidity",
        "wind_speed",
        "precipitation",
        "timestamp_interval_and_location_identity",
    } <= set(domains["atmosphere"])
    assert {
        "net_radiation",
        "lai",
        "soil_water_state",
        "maximum_water",
        "wilting_water",
        "latent_heat",
        "water_density",
        "psychrometric_constant",
    } <= set(domains["root_eq39"])
    assert "resistance_chain_or_controlled_baseline_source" in domains["leaf_exchange"]
    assert "dose_coefficient" in domains["endpoint"]
    assert {"units", "missing_data_policy", "timestamps_and_time_support", "provenance", "scenario_identity"} <= set(domains["cross_cutting"])
    assert data["required_input_classification"] == [
        "CONTROLLED_UFOTRI_BASELINE_OR_PROFILE",
        "PHYSICAL_CONSTANT",
        "EXPLICIT_EXTERNAL_SCENARIO_INPUT",
        "REAL_UPSTREAM_DATA_PREREQUISITE",
        "UNRESOLVED_OR_SYNTHETIC_ONLY",
    ]


def test_hard_boundaries_and_review_artifacts_are_consistent() -> None:
    data = load_governance()
    hard = data["hard_boundaries"]
    assert hard["v3_default_path_changed"] is False
    assert hard["calibration_started"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False
    assert hard["full_model_production_ready"] is False
    assert hard["real_cteas_atmos_binding"] is False
    assert hard["leaf_r5"] is False
    assert hard["full_hydrology"] is False
    assert hard["full_penman_eq38_production_active"] is False
    assert hard["ufotri_reference_layer_rates_active"] is False
    assert hard["short_term_3h_delay_active"] is False
    assert hard["multi_pool_obt"] is False

    exit_state = data["exit_state_if_exact_head_and_merge_clean"]
    assert exit_state["review_decision_complete"] is True
    assert exit_state["software_chain_connected_with_controlled_ufotri_profiles"] is True
    assert exit_state["root_q_w_production_input_resolved"] is True
    assert exit_state["full_model_production_ready"] is False
    assert exit_state["next_stage"] == "V4_PRODUCTION_INPUT_READINESS_AUDIT_R1"

    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    for text in (report, adr):
        assert "V4_PRODUCTION_INPUT_READINESS_AUDIT_R1" in text
        assert "SOFTWARE_CHAIN_CONNECTED_WITH_CONTROLLED_UFOTRI_PROFILES=TRUE" in text
        assert "ROOT_Q_W_PRODUCTION_INPUT_RESOLVED=TRUE" in text
        assert "FULL_MODEL_PRODUCTION_READY=FALSE" in text
        assert "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in text
