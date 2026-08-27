from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_system_food_intake_dose_adapter_decision_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_system_food_intake_dose_adapter_decision_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-036-v4-system-food-intake-dose-adapter-decision.md"


def load_governance() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_decision_is_control_plane_only_and_based_on_post_orchestration_main() -> None:
    data = load_governance()
    assert data["stage"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1"
    assert data["status"] == "PASS_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_AWAITING_CLOSURE_GATE"
    assert data["base_main_sha"] == "1884bb791873d47d08ceb6300d51b6974dddf37d"
    scope = data["scope"]
    assert scope["control_plane_and_interface_decision_only"] is True
    assert scope["production_src_changes"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["endpoint_adapter_implemented"] is False


def test_terminal_diagnostic_architecture_forbids_hidden_harvest_mutation() -> None:
    data = load_governance()
    architecture = data["architecture_decision"]
    assert architecture["selected_architecture"] == "OPT_IN_TERMINAL_DIAGNOSTIC_ENDPOINT_ADAPTER"
    assert architecture["one_way_readout_only"] is True
    assert architecture["may_change_replay_orchestration"] is False
    semantics = data["terminal_harvest_semantics"]
    assert semantics["explicit_terminal_event_only"] is True
    assert semantics["automatic_each_interval_harvest"] is False
    assert semantics["source_state_mutation"] is False
    assert semantics["same_trajectory_continuation_after_diagnostic_harvest"] == "FORBIDDEN"
    assert semantics["downstream_branch_is_environmental_mass_sink"] is False
    assert semantics["post_harvest_environmental_conservation_claim"] == "FORBIDDEN"


def test_harvest_modes_are_explicit_and_tfwt_fraction_is_never_inferred() -> None:
    modes = load_governance()["harvest_modes"]
    assert modes["request_mode_must_be_explicit"] is True
    assert modes["modes"]["OBT_ONLY"]["tfwt_harvest_fraction_must_be_none"] is True
    assert modes["modes"]["OBT_ONLY"]["expected_food_tfwt_bq"] == 0.0
    mixed = modes["modes"]["OBT_PLUS_TFWT"]
    assert mixed["tfwt_harvest_fraction_required"] is True
    assert mixed["infer_tfwt_fraction_from_obt_fraction"] is False
    assert mixed["preserve_component_inventories"] is True


def test_area_and_mass_basis_contracts_are_fail_closed() -> None:
    data = load_governance()
    area = data["area_geometry_contract"]
    assert area["replay_inventory_area_basis"] == "soil_surface_area"
    assert area["harvest_area_is_same_ground_support_extent"] is True
    assert area["leaf_area_conversion"] is False
    assert area["plant_area_conversion"] is False
    assert area["silent_area_conversion"] == "FORBIDDEN"
    assert area["downstream_mass_basis_area_kind"] == "NOT_APPLICABLE"

    basis = data["mass_basis_contract"]
    assert basis["food_product_contract_required"] is True
    assert basis["consumption_contract_required"] is True
    assert basis["tissue_scope_kind_required"] == "HARVEST_PRODUCT"
    assert basis["area_basis_kind_required"] == "NOT_APPLICABLE"
    assert basis["direct_comparison_required_before_intake"] is True
    assert basis["mass_basis_must_match"] is True
    assert basis["cross_basis_numerical_conversion"] == "FORBIDDEN"
    assert basis["evidence_declared_metadata_does_not_authorize_numeric_conversion"] is True


def test_system_identity_gates_cover_missing_cross_stage_checks() -> None:
    identity = load_governance()["identity_gates"]
    for field in (
        "endpoint_obt_tfwt_timestamp_exact",
        "endpoint_obt_tfwt_plant_identifier_exact",
        "endpoint_obt_tfwt_crop_identifier_exact",
        "endpoint_obt_tfwt_growth_stage_exact",
        "harvest_request_plant_identifier_matches_endpoint",
        "harvest_request_crop_identifier_matches_endpoint",
        "harvest_request_growth_stage_matches_endpoint",
        "food_product_identifier_chain_exact",
        "consumption_dose_age_group_exact",
    ):
        assert identity[field] is True
    assert identity["dose_radionuclide_identifier_required"] == "H-3"
    assert identity["dose_pathway_identifier_required"] == "food-ingestion"
    assert identity["fuzzy_or_alias_matching"] == "FORBIDDEN"


def test_provenance_and_annual_time_semantics_remain_domain_specific() -> None:
    data = load_governance()
    provenance = data["provenance_ownership"]
    assert provenance["replay_endpoint"] == "PRESERVE_UPSTREAM"
    assert provenance["harvest_event"] == "INDEPENDENT_EXPLICIT_PROVENANCE"
    assert provenance["consumption_parameters"] == "INDEPENDENT_EXPLICIT_PROVENANCE"
    assert provenance["dose_parameters"] == "INDEPENDENT_EXPLICIT_PROVENANCE"
    assert provenance["one_synthetic_provenance_for_all_domains"] == "FORBIDDEN"
    assert provenance["composite_audit_record_must_retain_all_domains"] is True

    time = data["time_semantics"]
    assert time["harvest_timestamp"] == "REPLAY_ENDPOINT_TIMESTAMP"
    assert time["intake_period"] == "annual"
    assert time["annual_means_environment_simulated_for_one_year"] is False
    assert time["annual_means_continuous_harvest_transfer_for_one_year"] is False


def test_first_exact_head_evidence_is_frozen_and_superseded_head_is_not_certified() -> None:
    evidence = load_governance()["first_exact_head_evidence"]
    assert evidence["certified_head_sha"] == "8b94002dbfbdd1a2278f95a345ba488d98e06474"
    assert evidence["certified_head_parent_sha"] == "1884bb791873d47d08ceb6300d51b6974dddf37d"
    assert evidence["protected_run_id"] == 33033725862
    assert evidence["protected_conclusion"] == "SUCCESS"
    assert evidence["remediation_run_id"] == 33033725958
    assert evidence["remediation_conclusion"] == "SUCCESS"
    assert evidence["portable"] == {"passed": 1259, "skipped": 1, "deselected": 57}
    assert evidence["explicit_frozen_current"]["passed"] == 327
    assert evidence["machine_gates"]["sensitivity"] == "PASS_SOFTWARE_SCREENING"
    assert evidence["machine_gates"]["root_operator_split"] == "PASS_SELECTION"
    assert evidence["machine_gates"]["soil_root_tfwt_obt"] == "PASS_INTEGRATION"
    assert evidence["machine_gates"]["replay_orchestration"] == "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"
    superseded = evidence["superseded_noncertified_head"]
    assert superseded["sha"] == "604b6a4ec2b3f025e2fa10ec024bb753f9a5f9e4"
    assert superseded["production_or_runtime_failure_observed"] is False


def test_future_implementation_is_gated_and_scope_creep_remains_forbidden() -> None:
    data = load_governance()
    gates = data["future_implementation_acceptance_gates"]
    assert gates["composition"]["direct_v3_solver_chain_equivalence"] is True
    assert gates["composition"]["endpoint_state_unchanged_before_after"] is True
    assert gates["fail_closed_basis"]["cross_basis_conversion_attempt"] == "REJECT"
    assert gates["reproducibility"]["deterministic_repeat"] is True
    assert gates["upstream_non_regression"]["replay_orchestration_unchanged"] is True

    next_stage = data["next_stage_recommendation"]
    assert next_stage["stage"] == "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_IMPLEMENTATION_R1"
    assert next_stage["implementation_authorized_now"] is False
    assert next_stage["authorization_effective_after_no_drift_merge"] is True
    assert "governance_closure_exact_head_protected_gate_success" in next_stage["authorization_requires"]
    assert "expected_head_merge_without_tree_drift" in next_stage["authorization_requires"]
    forbidden = next_stage["future_forbidden_scope"]
    assert "state_mutating_or_repeated_harvest" in forbidden
    assert "numerical_fresh_dry_water_hydrogen_conversion" in forbidden
    assert "real_cteas_atmos_binding" in forbidden


def test_hard_boundaries_and_documents_match_the_closure_state() -> None:
    data = load_governance()
    hard = data["hard_invariants"]
    assert hard["v3_default_profile_changed"] is False
    assert hard["replay_orchestration_changed"] is False
    assert hard["selected_operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["endpoint_adapter_implemented"] is False
    assert hard["state_mutating_harvest_authorized"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["real_cteas_atmos_coupling_active"] is False

    exit_state = data["exit_state"]
    assert exit_state["first_exact_head_gate_complete"] is True
    assert exit_state["governance_closure_complete"] is True
    assert exit_state["closure_exact_head_gate_complete"] is False
    assert exit_state["implementation_authorized"] is False
    assert exit_state["implementation_authorized_after_no_drift_merge"] is True

    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    assert "`PASS_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_AWAITING_CLOSURE_GATE`" in report
    assert "terminal diagnostic" in adr
    assert "cross-basis conversion is forbidden" in adr.lower()
    assert "`H-3`" in adr
    assert "8b94002dbfbdd1a2278f95a345ba488d98e06474" in adr
