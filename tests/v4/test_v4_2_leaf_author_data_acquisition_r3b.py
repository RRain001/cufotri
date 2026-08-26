"""V4-2 R3B author-held raw-data acquisition governance invariants."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/v4/leaf/v4_2_leaf_author_data_acquisition_r3b.yaml"
TEMPLATE = ROOT / "docs/v4/leaf/v4_2_leaf_author_data_request_template_r3b.md"
REVIEW = ROOT / "docs/v4/reports/v4_2_leaf_author_data_acquisition_r3b_review.md"


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def test_r3b_is_request_preparation_not_external_contact() -> None:
    data = _registry()
    assert data["base_main_sha"] == "224ee3bdda21a3f81676333cfbe841cb9e53c5a2"
    assert data["status"] == "READY_FOR_AUTHOR_CONTACT_NOT_SENT"
    scope = data["contact_scope"]
    assert scope["actual_contact_performed"] is False
    assert scope["email_or_message_sent"] is False
    assert scope["response_received"] is False
    assert scope["raw_author_file_received"] is False


def test_response_and_file_admission_states_are_fail_closed() -> None:
    data = _registry()
    response_states = set(data["allowed_response_states"])
    assert "REQUEST_PREPARED" in response_states
    assert "DATA_RECEIVED_COMPLETE_CANDIDATE" in response_states
    assert "IMPLEMENTATION_AUTHORIZED" not in response_states
    file_states = set(data["allowed_file_admission_states"])
    for state in (
        "HOLD_IDENTITY_AMBIGUOUS",
        "HOLD_VERSION_AMBIGUOUS",
        "HOLD_INTEGRITY_MISMATCH",
        "HOLD_REQUIRED_FIELDS_MISSING",
        "READY_FOR_FILE_LEVEL_AUDIT",
    ):
        assert state in file_states


def test_raw_record_request_contains_target_drivers_alignment_and_provenance() -> None:
    fields = _registry()["required_raw_record_fields"]
    assert "absolute_gsw_or_equivalent_rc" in fields["target"]
    assert {"PAR_or_Q", "VPDleaf_or_equivalent_direct_VPD", "Tleaf"}.issubset(fields["drivers"])
    assert {
        "timestamp_or_elapsed_time",
        "plant_or_biological_replicate_id",
        "developmental_stage_or_source_bound_stage_context",
    }.issubset(fields["alignment_and_identity"])
    assert {"instrument_model", "source_file_name", "variable_definitions_and_units"}.issubset(fields["provenance"])


def test_integrity_and_chain_of_custody_rules_preserve_received_bytes() -> None:
    data = _registry()
    integrity = set(data["file_integrity_requirements"])
    assert "preserve_received_bytes_without_editing" in integrity
    assert "compute_sha256" in integrity
    assert "keep_raw_author_files_out_of_git_repository" in integrity
    custody = set(data["chain_of_custody_rules"])
    assert "never_overwrite_received_raw_file" in custody
    assert "do_not_manually_transcribe_missing_columns_into_raw_data" in custody
    assert "do_not_join_different_experiments_to_close_missing_packet_fields" in custody


def test_two_requests_are_source_specific_and_not_cross_dataset_composition() -> None:
    requests = _registry()["request_targets"]
    assert [r["request_id"] for r in requests] == [
        "MOSTOFA_2025_RAW_LI680X_REQUEST",
        "ZANDALINAS_2020_RAW_LI6800_REQUEST",
    ]
    assert requests[0]["priority"] == 1
    assert requests[0]["public_dataset_doi"] == "10.5061/dryad.51c59zwkh"
    assert "Fig 3d" in requests[0]["experiment_anchor"]
    assert requests[1]["priority"] == 2
    assert requests[1]["article_doi"] == "10.1104/pp.20.00511"
    assert all(r["response_state"] == "REQUEST_PREPARED" for r in requests)
    assert all(r["file_admission_state"] == "NOT_RECEIVED" for r in requests)
    no_stitching = _registry()["admission_rules"]["no_stitching"]
    assert "separate evidence domains" in no_stitching


def test_vpd_and_declared_constant_rules_reject_range_substitution() -> None:
    rules = _registry()["admission_rules"]
    assert "Range midpoint substitution is prohibited" in rules["vpd_derivation"]
    assert "binds it to every admitted target row" in rules["declared_constants"]
    assert "explicit source-supported key/alignment contract" in rules["row_alignment"]


def test_request_template_asks_for_raw_export_without_fabricating_metadata() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    assert "original LI-6800/LI-680X export" in text
    assert "partial raw export is still useful" in text
    assert "missing fields do not need to be recreated" in text
    assert "invent or reconstruct missing timestamps" in text
    assert "alter original files to match the V4-2 schema" in text
    assert "has **not** been sent" in text


def test_review_keeps_solver_and_calibration_blocked() -> None:
    text = REVIEW.read_text(encoding="utf-8")
    for line in (
        "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE",
        "SOLVER_IMPLEMENTATION_STARTED = FALSE",
        "CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE",
        "CALIBRATION_STARTED = FALSE",
        "ACTIVE_PARAMETERS = 0",
        "V3_PHYSICS_READY = FALSE",
    ):
        assert line in text
    invariants = _registry()["hard_invariants"]
    assert invariants["leaf_implementation_authorized"] is False
    assert invariants["solver_implementation_started"] is False
    assert invariants["candidate_parameter_values_admitted"] is False
    assert invariants["calibration_started"] is False
    assert invariants["active_parameters"] == 0
    assert invariants["ufotri_active_database"] is False
    assert invariants["v3_physics_ready"] is False
    assert invariants["physical_validation_complete"] is False


def test_exit_policy_requires_separate_audit_before_any_implementation_decision() -> None:
    policy = _registry()["exit_policy"]
    assert "Remain HOLD" in policy["if_no_author_data_received"]
    assert "DATA_RECEIVED_INCOMPLETE" in policy["if_partial_data_received"]
    assert "separate immutable\nfile-level audit stage" in policy["if_complete_candidate_received"]
    assert "Neither is authorized" in policy["if_author_data_path_exhausted"]
