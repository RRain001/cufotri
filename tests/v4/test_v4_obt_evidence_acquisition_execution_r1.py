"""V4 OBT evidence acquisition execution R1 governance invariants."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_obt_evidence_acquisition_execution_r1.yaml"
MESSAGES = ROOT / "docs/v4/gates/obt_evidence_request_messages_r1.md"
REPORT = ROOT / "docs/v4/reports/v4_obt_evidence_acquisition_execution_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-040-v4-obt-evidence-acquisition-execution-r1.md"


def _data() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_execution_is_anchored_to_pr36_no_drift_merge() -> None:
    data = _data()
    assert data["stage"] == "V4_OBT_EVIDENCE_ACQUISITION_EXECUTION_R1"
    assert data["status"] == "PASS_EXECUTION_CONTROL_EXACT_HEAD_AWAITING_CLOSURE_GATE"
    source = data["source_authorization"]
    assert source["source_pr"] == 36
    assert source["merge_sha"] == "ca77d8abf4d7babe2669aa829f028e4ac45f653d"
    assert source["parent1"] == "d28695a13eae1fe4a7afb55a7a8a179d366de44c"
    assert source["parent2"] == "acfd0f087b3a05d414a55a1d3a480eee8223a83b"
    assert source["merge_tree"] == source["pr_head_tree"] == "2be97abe215c365bd496123719ac99863bccb210"
    assert source["head_to_merge_files_empty"] is True
    assert source["main_equals_merge_sha"] is True
    assert source["merge_tree_drift"] is False


def test_preregistration_science_is_not_modified() -> None:
    frozen = _data()["frozen_sources"]
    assert frozen["request_package_modified_in_this_stage"] is False
    assert frozen["observation_operator_modified_in_this_stage"] is False
    assert frozen["holdout_policy_modified_in_this_stage"] is False
    assert frozen["identifiability_policy_modified_in_this_stage"] is False
    scope = _data()["scope"]
    assert scope["kind"] == "EXTERNAL_DATA_REQUEST_AND_METADATA_INTAKE_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["runtime_candidate_state_activated"] is False
    assert scope["parameter_values_admitted"] is False
    assert scope["calibration_started"] is False


def test_contact_routes_distinguish_current_from_historical() -> None:
    targets = {row["target_id"]: row for row in _data()["contact_targets"]}
    assert targets["VATO_IRSN_EDF"]["send_eligible_now"] is False
    assert targets["VATO_IRSN_EDF"]["contact_route_state"] == "CURRENT_INSTITUTION_ROUTE_FOUND_DIRECT_ADDRESS_NOT_REVERIFIED"
    assert all(route["current_delivery_asserted"] is False for route in targets["VATO_IRSN_EDF"]["historical_routes"])
    micro = targets["MICRO_TOM_2024"]
    assert micro["send_eligible_now"] is True
    assert micro["verified_route"]["address"] == "katayama.kazunari.947@m.kyushu-u.ac.jp"
    assert micro["request_sent"] is False
    renard = targets["RENARD_RYEGRASS_2017"]
    assert renard["send_eligible_now"] is False
    assert renard["historical_route"]["address"] == "hugo.renard@irsn.fr"
    assert renard["historical_route"]["current_delivery_asserted"] is False


def test_send_event_cannot_be_inferred_from_prepared_message() -> None:
    contract = _data()["send_event_contract"]
    assert contract["address_or_template_presence_implies_sent"] is False
    assert contract["historical_address_may_be_claimed_current_without_verification"] is False
    assert contract["first_send_requires_certified_execution_control_head"] is True
    required = set(contract["required_fields"])
    assert {"target_id", "exact_recipient_route", "message_artifact_and_revision", "sent_timestamp_utc"}.issubset(required)
    text = MESSAGES.read_text(encoding="utf-8")
    assert "Status: `PREPARED_NOT_SENT`" in text
    assert "Presence in this repository is not evidence that a request was sent" in text


def test_raw_data_custody_and_metadata_only_intake_are_fail_closed() -> None:
    data = _data()
    custody = data["raw_file_custody"]
    assert custody["repository_storage_allowed"] is False
    assert custody["git_ignored_external_storage_required"] is True
    assert custody["hash_before_content_inspection"] is True
    assert custody["hash_algorithm"] == "SHA256"
    assert custody["original_bytes_immutable"] is True
    allowed = set(data["metadata_only_intake_allowed"])
    assert {"original_filename", "sha256", "schema_and_field_names", "units", "experiment_run_and_replicate_identifiers"}.issubset(allowed)
    forbidden = set(data["metadata_only_intake_forbidden"])
    assert "quantitative_holdout_plant_tritium_values" in forbidden
    assert "candidate_parameter_fit" in forbidden
    assert "current_kf_kr_recalibration" in forbidden


def test_hard_invariants_keep_physics_and_calibration_frozen() -> None:
    inv = _data()["hard_invariants"]
    assert inv["requests_sent"] is False
    assert inv["raw_packet_received"] is False
    assert inv["quantitative_model_fit_inspection"] is False
    assert inv["holdout_values_inspected"] is False
    assert inv["active_parameters"] == 0
    assert inv["calibration_started"] is False
    assert inv["obt_multi_pool_implementation_authorized"] is False
    assert inv["obt_parameter_activation_authorized"] is False
    assert inv["current_kf_kr_calibration_authorized"] is False
    assert inv["leaf_r5_authorized"] is False
    assert inv["root_q_w_production_input_resolved"] is False
    assert inv["full_hydrology_authorized"] is False
    assert inv["real_cteas_atmos_binding"] is False
    assert inv["empirical_validation"] is False
    assert inv["physical_accuracy_claim"] is False


def test_first_execution_head_is_certified_and_failed_attempt_is_non_certifying() -> None:
    data = _data()
    gate = data["first_execution_head_gate"]
    assert gate["complete"] is True
    assert gate["certified_head"] == "15f3e4be9e03cf9ff49fe1a1fe1b0a516de628a5"
    assert gate["protected_gate"] == "SUCCESS"
    assert gate["protected_run_id"] == 33045107295
    assert gate["protected_checkout_merge_ref"] == "d20da58ac9721d5703ade8bcc5807453596466c7"
    assert gate["portable_suite"] == "PASS_1311_WITH_1_SKIP_57_DESELECTED"
    assert gate["frozen_boundary_suite"] == "PASS_373"
    assert gate["remediation"] == "SUCCESS"
    assert gate["remediation_run_id"] == 33045107285
    assert gate["external_send_before_gate_allowed"] is False
    assert gate["verified_route_send_gate_satisfied"] is True

    machine = gate["machine_gates"]
    assert machine["sensitivity_screening"] == "PASS_SOFTWARE_SCREENING"
    assert machine["root_operator_split"] == "PASS_SELECTION"
    assert machine["soil_root_tfwt_obt_integration"] == "PASS_INTEGRATION"
    assert machine["replay_orchestration"] == "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"
    assert machine["food_intake_dose_endpoint"] == "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION"

    superseded = data["superseded_non_certifying_head"]
    assert superseded["head"] == "f92b2e962acbc4c6cedfe4a1bd872b53cd084f9c"
    assert superseded["protected_result"] == "FAILURE"
    assert superseded["failure_class"] == "GOVERNANCE_TEST_WORDING_ASSERTION_ONLY"
    assert superseded["production_or_scientific_failure"] is False
    assert superseded["certification_evidence"] is False


def test_report_and_adr_record_certification_without_claiming_send() -> None:
    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    assert "MERGE_TREE_DRIFT = FALSE" in report
    assert "FIRST_EXACT_HEAD = 15f3e4be9e03cf9ff49fe1a1fe1b0a516de628a5" in report
    assert "FIRST_PROTECTED_RUN = 33045107295_SUCCESS" in report
    assert "FIRST_REMEDIATION_RUN = 33045107285_SUCCESS" in report
    assert "REQUESTS_SENT = FALSE" in report
    assert "PASS_EXECUTION_CONTROL_EXACT_HEAD_AWAITING_CLOSURE_GATE" in adr
    assert "requires a certified execution head before an external send is recorded" in adr


def test_closure_is_minimal_and_send_remains_unperformed() -> None:
    closure = _data()["closure"]
    assert closure["status"] == "AWAITING_CLOSURE_EXACT_HEAD_DUAL_CI"
    assert closure["request_message_artifact_changed_in_closure"] is False
    assert closure["workflow_changed_in_closure"] is False
    assert closure["preregistration_contract_changed_in_closure"] is False
    assert closure["production_source_changed_in_closure"] is False
    assert closure["numerical_coupling_changed_in_closure"] is False
    assert closure["requests_sent_in_closure"] is False


def test_next_transition_allows_send_not_model_implementation() -> None:
    transition = _data()["next_transition"]
    assert transition["after_closure_dual_ci_and_no_drift_merge"] == "SEND_ONLY_ON_CURRENTLY_VERIFIED_ROUTE"
    assert transition["eligible_first_target"] == "MICRO_TOM_2024"
    assert transition["vato_requires_contact_reverification"] is True
    assert transition["renard_requires_contact_reverification"] is True
    assert transition["option_b_implementation_authorized_after_send"] is False
    assert transition["parameter_fit_authorized_after_send"] is False
