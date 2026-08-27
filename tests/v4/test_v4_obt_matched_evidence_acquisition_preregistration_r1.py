from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_obt_matched_evidence_acquisition_preregistration_r1.yaml"
CONTRACT = ROOT / "docs/v4/contracts/obt_matched_evidence_acquisition_preregistration_r1.yaml"
REQUEST = ROOT / "docs/v4/gates/obt_matched_evidence_request_package_r1.md"
REPORT = ROOT / "docs/v4/reports/v4_obt_matched_evidence_acquisition_preregistration_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-039-v4-obt-matched-evidence-acquisition-preregistration-r1.md"
IMPLEMENTATION_STATUS = ROOT / "docs/implementation_status.md"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def test_preregistration_is_control_plane_only_and_anchored_to_no_drift_merge() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1"
    assert data["status"] == "PASS_PREREGISTRATION_EXACT_HEAD_AWAITING_CLOSURE_GATE"
    assert data["base_main_sha"] == "d28695a13eae1fe4a7afb55a7a8a179d366de44c"
    scope = data["stage_scope"]
    assert scope["kind"] == "CONTROL_PLANE_AND_DATA_ACQUISITION_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["parameter_activation"] is False
    assert scope["calibration"] is False
    assert scope["request_execution"] is False
    source = data["source_authorization"]
    assert source["pr"] == 35
    assert source["merge_sha"] == "d28695a13eae1fe4a7afb55a7a8a179d366de44c"
    assert source["merge_tree"] == "b9ed9d9fe6c92e196b48c3059e71d70bb21b4c14"
    assert source["no_drift_verified"] is True
    assert source["head_to_merge_files_empty"] is True
    assert source["evidence_disposition"] == "ACQUIRABLE_WITH_PREREGISTRATION"


def test_two_layer_preregistration_prevents_post_fit_rule_selection() -> None:
    data = load_yaml(CONTRACT)
    layers = data["preregistration_layers"]
    layer_a = layers["layer_a_acquisition_preregistration"]
    assert layer_a["frozen_now"] is True
    assert layer_a["may_be_changed_after_quantitative_fit_inspection"] is False
    layer_b = layers["layer_b_dataset_shape_amendment"]
    assert layer_b["future_stage_required"] is True
    assert layer_b["must_precede_quantitative_model_fit"] is True
    assert layer_b["must_precede_holdout_value_inspection"] is True
    assert "quantitative_holdout_plant_tritium_values" in layer_b["may_not_inspect"]
    assert "holdout_performance_metrics" in layer_b["may_not_inspect"]

    gov = load_yaml(GOVERNANCE)
    prereg = gov["preregistration"]
    assert prereg["exact_sample_size_invented_now"] is False
    assert prereg["exact_identifiability_thresholds_invented_now"] is False
    assert prereg["exact_holdout_group_count_invented_now"] is False


def test_observation_operator_forbids_silent_partition_and_proxy_relabeling() -> None:
    data = load_yaml(CONTRACT)
    obs = data["observation_operator"]
    assert obs["T"]["silent_water_mass_inference"] == "forbidden"
    assert obs["T"]["silent_fresh_dry_water_hydrogen_conversion"] == "forbidden"
    assert obs["B_n"]["biological_equivalence_to_all_slow_organic_matter_asserted"] is False
    assert "directly_reported_E_OBT" in obs["B_x"]["source_options"]
    assert obs["B_x"]["total_minus_ne_requires_matched_tissue_time_and_basis"] is True
    assert obs["B_x"]["literature_fraction_partition"] == "forbidden"
    assert obs["B_x"]["cross_crop_fraction_partition"] == "forbidden"
    assert obs["B_total"]["split_into_components_without_measurement"] == "forbidden"
    assert obs["P"]["classification"] == "LATENT_LUMPED_PRECURSOR_ACTIVITY_STATE"
    assert obs["P"]["asserted_chemical_identity"] is False
    assert obs["P"]["existing_photosynthesis_starch_PAR_or_carbohydrate_relabelled_as_P"] == "forbidden"


def test_acquisition_hierarchy_and_request_package_are_frozen_but_not_sent() -> None:
    data = load_yaml(CONTRACT)
    targets = data["acquisition_hierarchy"]
    assert [(x["priority"], x["target_id"]) for x in targets[:3]] == [
        ("A", "VATO_IRSN_EDF"),
        ("B1", "MICRO_TOM_2024"),
        ("B2", "RENARD_RYEGRASS_2017"),
    ]
    execution = data["request_execution"]
    assert execution["performed_in_this_stage"] is False
    assert execution["repository_may_claim_request_sent"] is False

    request = REQUEST.read_text()
    assert "Status: `PREREGISTERED_NOT_SENT`" in request
    assert "Priority A — VATO / IRSN-EDF" in request
    assert "Priority B1 — controlled MicroTom experiment" in request
    assert "Priority B2 — Renard ryegrass experiment" in request
    assert "REQUEST_DATE =" in request
    assert "RESPONSE_DISPOSITION = NOT_SENT" in request


def test_packet_acceptance_is_raw_provenance_first_and_never_figure_digitization() -> None:
    data = load_yaml(CONTRACT)
    acceptance = data["raw_packet_acceptance"]
    required = set(acceptance["required"])
    assert {
        "source_owner_identifier",
        "original_filenames",
        "sha256_for_every_original_file",
        "licence_or_explicit_local_research_use_status",
        "machine_readable_table_or_owner_supplied_documented_export",
        "biological_replicate_identifier",
        "analytical_component_definition",
        "uncertainty",
        "detection_or_quantification_limit",
    } <= required
    assert acceptance["original_bytes_immutable"] is True
    assert acceptance["raw_values_committed_to_repository"] is False
    assert acceptance["publication_summary_alone_sufficient"] is False
    assert acceptance["plot_digitization_allowed"] is False
    assert acceptance["ocr_as_raw_data_substitute_allowed"] is False
    assert acceptance["model_generated_pseudo_observation_allowed"] is False


def test_missing_censoring_and_holdout_rules_are_fail_closed() -> None:
    data = load_yaml(CONTRACT)
    missing = data["missing_censoring_and_exclusion"]
    assert missing["missing_quantitative_value_action"] == "KEEP_MISSING"
    assert missing["below_detection_action"] == "KEEP_CENSORED_WITH_REPORTED_LIMIT"
    assert missing["automatic_zero_substitution"] == "forbidden"
    assert missing["automatic_half_limit_substitution"] == "forbidden"
    assert missing["automatic_limit_substitution"] == "forbidden"
    assert missing["fit_based_exclusion"] == "forbidden"

    split = data["calibration_holdout"]
    assert split["split_unit"] == "WHOLE_INDEPENDENT_BIOLOGICAL_REPLICATE_OR_COMPLETE_EXPERIMENTAL_RUN"
    assert split["random_time_row_split"] == "forbidden"
    assert split["split_must_precede_quantitative_holdout_inspection"] is True
    assert split["exact_holdout_group_count_selected_now"] is False
    assert split["insufficient_groups_may_be_repaired_by_time_row_split"] is False


def test_identifiability_and_hard_holds_remain_closed() -> None:
    contract = load_yaml(CONTRACT)
    ident = contract["identifiability_preregistration"]
    assert "structural_identifiability_with_selected_observation_operator_and_latent_P" in ident["required_before_candidate_implementation_or_fit"]
    assert "profile_likelihood_or_equivalent_profiles_for_free_parameters" in ident["required_before_candidate_implementation_or_fit"]
    assert "scaled_jacobian_or_fisher_singular_values_and_conditioning" in ident["required_before_candidate_implementation_or_fit"]
    assert ident["exact_numerical_thresholds_selected_now"] is False
    assert ident["optimizer_convergence_proves_identifiability"] is False
    assert ident["parameter_activation_on_non_identifiable_fit"] == "forbidden"

    hard = load_yaml(GOVERNANCE)["hard_invariants"]
    assert hard["requests_sent"] is False
    assert hard["raw_packet_received"] is False
    assert hard["quantitative_model_fit_inspection"] is False
    assert hard["holdout_values_inspected"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["obt_multi_pool_implementation_authorized"] is False
    assert hard["obt_parameter_activation_authorized"] is False
    assert hard["current_kf_kr_calibration_authorized"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["root_q_w_production_input_resolved"] is False
    assert hard["full_hydrology_authorized"] is False
    assert hard["real_cteas_atmos_binding"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False


def test_first_exact_head_and_governance_closure_are_frozen() -> None:
    data = load_yaml(GOVERNANCE)
    gate = data["first_exact_head_gate"]
    assert gate["complete"] is True
    assert gate["head_sha"] == "8d1c866b6750e68cbae2313c110fe3c94dc19a59"
    assert gate["protected_gate"] == {"run_id": 33042549240, "status": "SUCCESS"}
    assert gate["remediation"] == {"run_id": 33042549262, "status": "SUCCESS"}
    assert gate["checkout_merge_sha"] == "f11203f0f464b27618e814a10c5c50b43241b4e0"
    assert gate["portable_suite"] == {"passed": 1302, "skipped": 1, "deselected": 57}
    assert gate["frozen_boundary_suite"] == {"passed": 364}
    assert gate["machine_gates"] == {
        "sensitivity": "PASS_SOFTWARE_SCREENING",
        "root_operator_split": "PASS_SELECTION",
        "soil_root_tfwt_obt": "PASS_INTEGRATION",
        "replay_orchestration": "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION",
        "food_intake_dose_endpoint": "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION",
    }
    assert gate["request_execution"] is False
    assert gate["raw_packet_received"] is False
    assert gate["quantitative_fit_inspection"] is False
    assert gate["empirical_validation"] is False
    assert gate["physical_accuracy_claim"] is False

    closure = data["governance_closure"]
    assert closure["written"] is True
    assert closure["source_preregistration_head"] == "8d1c866b6750e68cbae2313c110fe3c94dc19a59"
    assert closure["implementation_status_updated"] is True
    assert closure["changed_files_only"] == [
        "docs/v4/adr/ADR-039-v4-obt-matched-evidence-acquisition-preregistration-r1.md",
        "docs/v4/governance/v4_obt_matched_evidence_acquisition_preregistration_r1.yaml",
        "docs/v4/reports/v4_obt_matched_evidence_acquisition_preregistration_r1.md",
        "tests/v4/test_v4_obt_matched_evidence_acquisition_preregistration_r1.py",
        "docs/implementation_status.md",
    ]
    assert closure["acquisition_contract_changed_by_closure"] is False
    assert closure["request_package_changed_by_closure"] is False
    assert closure["workflow_changed_by_closure"] is False
    assert closure["production_source_changed_by_closure"] is False
    assert closure["scientific_preregistration_changed_by_closure"] is False
    assert closure["closure_exact_head_gate_complete"] is False
    assert closure["merge_authorized"] is False


def test_adr_report_status_and_workflow_freeze_same_next_stage() -> None:
    adr = ADR.read_text()
    report = REPORT.read_text()
    status = IMPLEMENTATION_STATUS.read_text()
    workflow = WORKFLOW.read_text()

    assert "Status: `PASS_PREREGISTRATION_EXACT_HEAD_AWAITING_CLOSURE_GATE`" in adr
    assert "two-layer blind workflow" in adr
    assert "Random row-wise or time-point splitting is forbidden" in adr
    assert "Protected 33042549240 = SUCCESS" in adr
    assert "`V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1`" in adr

    assert "REQUESTS_SENT = FALSE" in report
    assert "RAW_PACKET_RECEIVED = FALSE" in report
    assert "QUANTITATIVE_MODEL_FIT_INSPECTION = FALSE" in report
    assert "Random timestamp/row splitting is prohibited" in report
    assert "NEXT_STAGE_AUTHORIZED_NOW = FALSE" in report
    assert "V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1" in report

    assert "V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1 = PASS_PREREGISTRATION_EXACT_HEAD_AWAITING_CLOSURE_GATE" in status
    assert "NEXT_STAGE_AUTHORIZED_NOW = FALSE" in status
    assert "tests/v4/test_v4_obt_matched_evidence_acquisition_preregistration_r1.py" in workflow
