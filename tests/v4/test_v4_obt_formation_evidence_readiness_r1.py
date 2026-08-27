from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_obt_formation_evidence_readiness_r1.yaml"
PACKET = ROOT / "docs/v4/contracts/obt_formation_evidence_packet_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_obt_formation_evidence_readiness_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-038-v4-obt-formation-evidence-readiness-r1.md"
WORKFLOW = ROOT / ".github/workflows/v3-integration-gate.yml"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_obt_evidence_readiness_is_control_plane_only_and_anchored_to_post_endpoint_merge() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "V4_OBT_FORMATION_EVIDENCE_READINESS_R1"
    assert data["status"] == "EVIDENCE_READINESS_ASSESSED_AWAITING_FIRST_EXACT_HEAD_CI"
    assert data["base_main_sha"] == "d8c3336c14db1d695e70dc62755b00ce5235d04d"

    scope = data["stage_scope"]
    assert scope["kind"] == "CONTROL_PLANE_AND_EVIDENCE_READINESS_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["parameter_values_admitted"] is False
    assert scope["calibration"] is False

    entry = data["entry_authorization"]
    assert entry["source_pr"] == 34
    assert entry["source_merge_sha"] == "d8c3336c14db1d695e70dc62755b00ce5235d04d"
    assert entry["source_merge_tree"] == "e00d73be6c26f127e2274f59b1139c99eed5a168"
    assert entry["source_parent1"] == "48bb658c986d4ca1f355991e4e298a16863fec3b"
    assert entry["source_parent2"] == "667d5e2bdcf9cae326f37980b6033a219ab8540a"
    assert entry["no_drift_verified"] is True
    assert entry["head_to_merge_files_empty"] is True


def test_candidate_architecture_remains_symbolic_and_runtime_inactive() -> None:
    data = load_yaml(GOVERNANCE)
    candidate = data["frozen_candidate_architecture"]
    assert candidate["current_runnable_baseline"]["equation"] == "dB/dt = k_f T - k_r B"
    assert candidate["current_runnable_baseline"]["remains_default"] is True
    selected = candidate["selected_future_candidate"]
    assert selected["model_id"] == "option_b_two_pool_biological_extension"
    assert selected["selected_for_v4"] is True
    assert selected["implemented"] is False
    assert selected["runtime_admissible"] is False
    assert selected["numerical_parameter_values_selected"] is False


def test_state_observability_does_not_invent_precursor_or_component_mapping() -> None:
    data = load_yaml(GOVERNANCE)
    states = data["state_classification"]
    assert states["T"]["classification"] == "DIRECT_OBSERVABLE_IF_EXTRACTION_AND_BASIS_EXPLICIT"
    assert states["P"]["classification"] == "LATENT_LUMPED_PRECURSOR_ACTIVITY_STATE"
    assert states["P"]["direct_chemical_identity_asserted"] is False
    assert states["B_x"]["classification"] == "OPERATIONAL_ANALYTICAL_OBSERVABLE_IF_PROTOCOL_EXPLICIT"
    assert states["B_x"]["automatic_equivalence_to_tfwt"] is False
    assert states["B_x"]["automatic_equivalence_to_generic_fast_pool"] is False
    assert states["B_n"]["classification"] == "OPERATIONAL_ANALYTICAL_OBSERVABLE_IF_PROTOCOL_EXPLICIT"
    assert states["B_n"]["automatic_equivalence_to_all_slow_organic_matter"] is False
    assert states["B_total"]["silent_partition_to_components"] == "forbidden"
    assert states["u_P"]["functional_form_selected"] is False


def test_repository_has_no_available_option_b_packet() -> None:
    data = load_yaml(GOVERNANCE)
    audit = data["repository_evidence_audit"]
    assert audit["matched_option_b_raw_packet_present"] is False
    assert audit["soybean_request_package_status"] == "READY_TO_SEND_MANUALLY_NOT_SENT"
    assert audit["soybean_data_status"] == "BLOCKED_EXTERNAL_DATA"
    assert audit["preregistration_status"] == "DRAFT_NOT_PREREGISTERED"
    assert audit["calibration_status"] == "NOT_RUN_BLOCKED_EXTERNAL_DATA"
    assert audit["identifiability_status"] == "NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE"


def test_external_evidence_supports_acquisition_not_a_composite_validation_case() -> None:
    data = load_yaml(GOVERNANCE)
    disposition = data["evidence_disposition"]
    assert disposition["selected"] == "ACQUIRABLE_WITH_PREREGISTRATION"
    assert disposition["repository_packet_available"] is False

    sources = {item["evidence_id"]: item for item in data["external_evidence_audit"]["sources"]}
    assert sources["VATO_MARO_2017"]["role"] == "PRIORITY_A_ACQUISITION_TARGET"
    assert sources["VATO_MARO_2017"]["direct_component_raw_table_obtained_by_repository"] is False
    assert sources["VATO_MARO_2017"]["owner_clarification_required"] is True
    assert sources["RENARD_RYEGRASS_2017"]["role"] == "PRIORITY_B_CONTROLLED_COMPONENT_ACQUISITION_TARGET"
    assert sources["MICRO_TOM_2024"]["role"] == "PRIORITY_B_CONTROLLED_COMPONENT_ACQUISITION_TARGET"
    assert sources["SOYBEAN_DAY_NIGHT_SUPPORT"]["admissible_as_option_b_component_validation_case"] is False

    policy = data["cross_study_policy"]
    assert "one_calibration_case" in policy["independent_studies_may_not_be_spliced_for"]
    assert policy["fixed_literature_fraction_partition_of_total_obt"] == "forbidden"
    assert policy["plot_digitization_to_replace_unavailable_raw_table"] == "forbidden"
    assert policy["synthetic_fixture_as_empirical_evidence"] == "forbidden"


def test_packet_contract_requires_matched_components_basis_quality_and_holdout() -> None:
    packet = load_yaml(PACKET)
    assert packet["contract_id"] == "V4_OBT_MATCHED_EVIDENCE_PACKET_R1"
    assert packet["packet_identity"]["single_experiment_or_internally_aligned_program_required"] is True
    assert packet["packet_identity"]["cross_study_splicing_for_parameter_fit"] == "FORBIDDEN"
    assert packet["packet_identity"]["literature_fraction_used_to_partition_total_obt"] == "FORBIDDEN"

    required = packet["required_quantitative_fields"]
    assert required["plant"] == ["tfwt", "exchangeable_obt", "nonexchangeable_obt"]
    assert "photosynthetic_activity_or_PAR" in required["biological_forcing"]
    assert "biological_replicate_id" in required["sample_identity"]
    assert "mass_basis" in required["basis"]
    assert "uncertainty" in required["analytical_quality"]
    assert "file_sha256_after_receipt" in required["provenance"]

    holdout = packet["replicate_and_holdout_contract"]
    assert holdout["independent_biological_replicates_required"] is True
    assert holdout["calibration_holdout_partition_must_precede_holdout_inspection"] is True
    assert holdout["holdout_must_be_independent_of_parameter_fit"] is True
    assert holdout["exact_minimum_sample_count_selected_here"] is False


def test_identifiability_gate_fail_closes_and_next_stage_is_acquisition_only() -> None:
    data = load_yaml(GOVERNANCE)
    gate = data["identifiability_gate"]
    assert gate["bx_bn_direct_or_protocol_defined_component_observations_required"] is True
    assert gate["aggregate_obt_partition_by_literature_fraction_allowed"] is False
    assert gate["option_a_option_b_same_case_comparison_required"] is True
    assert gate["forcing_excitation_required_for_claimed_response_terms"] is True
    assert gate["structural_identifiability_assessment_required"] is True
    assert gate["practical_identifiability_assessment_required"] is True
    assert gate["calibration_holdout_partition_preregistered_before_holdout_inspection"] is True
    assert gate["failure_disposition"] == "HOLD_SELECTED_CANDIDATE_KEEP_REDUCED_BASELINE"

    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1"
    assert next_stage["scope"] == "CONTROL_PLANE_AND_DATA_ACQUISITION_ONLY"
    assert "implement_option_b_solver" in next_stage["may_not"]
    assert "activate_any_parameter" in next_stage["may_not"]
    assert "calibrate_current_kf_kr" in next_stage["may_not"]


def test_hard_invariants_and_first_gate_state_remain_closed() -> None:
    data = load_yaml(GOVERNANCE)
    hard = data["hard_invariants"]
    assert hard["v3_default_changed"] is False
    assert hard["v4_runtime_changed"] is False
    assert hard["production_source_changed"] is False
    assert hard["solver_equations_changed"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["obt_multi_pool_implementation_authorized"] is False
    assert hard["obt_parameter_activation_authorized"] is False
    assert hard["current_kf_kr_calibration_authorized"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["root_q_w_production_input_resolved"] is False
    assert hard["full_hydrology_authorized"] is False
    assert hard["real_cteas_atmos_binding"] is False

    first = data["first_exact_head_gate"]
    assert first["complete"] is False
    assert first["head_sha"] is None
    assert data["governance_closure"]["written"] is False
    assert data["exit_state"]["merge_authorized"] is False


def test_readiness_artifacts_and_protected_gate_name_the_frozen_disposition() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for text in (adr, report):
        assert "ACQUIRABLE_WITH_PREREGISTRATION" in text
        assert "V4_OBT_MATCHED_EVIDENCE_ACQUISITION_PREREGISTRATION_R1" in text
        assert "ACTIVE_PARAMETERS = 0" in text
        assert "CROSS_STUDY_CASE_FUSION = FORBIDDEN" in text
    assert "tests/v4/test_v4_obt_formation_evidence_readiness_r1.py" in workflow
