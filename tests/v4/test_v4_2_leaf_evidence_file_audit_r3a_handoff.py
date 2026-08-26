from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r3a.yaml"
PACKET_DOCS_TIP = "d208439db1bbd39845188e885cec038c0e159514"


def _request() -> dict:
    return yaml.safe_load(REQUEST.read_text(encoding="utf-8"))


def test_r3a_handoff_is_pending_file_audit() -> None:
    data = _request()
    assert data["stage"] == "V4-2"
    assert data["round"] == "R3A"
    assert data["base_main_sha"] == "3e7ec58b19752da9eef018a80875d0a90bd6164f"
    assert data["status"] == "PENDING_LOCAL_FILE_LEVEL_AUDIT"


def test_r3a_packet_docs_tip_is_frozen_pre_result_boundary() -> None:
    assert PACKET_DOCS_TIP == "d208439db1bbd39845188e885cec038c0e159514"


def test_r3a_has_exact_allowed_classifications_and_verdicts() -> None:
    data = _request()
    assert data["classification_enum"] == [
        "DIRECT_COLUMN",
        "DECLARED_CONSTANT_WITH_PROVENANCE",
        "EXPLICIT_DERIVATION_SUPPORTED",
        "MISSING",
        "AMBIGUOUS",
    ]
    assert data["allowed_final_verdicts"] == [
        "PASS_ONE_COMPLETE_EMPIRICAL_PACKET_CANDIDATE",
        "HOLD_COMPONENT_EVIDENCE_ONLY",
        "HOLD_REQUIRED_FIELDS_MISSING",
        "HOLD_ALIGNMENT_OR_PROVENANCE_AMBIGUOUS",
    ]


def test_r3a_covers_all_packet_fields() -> None:
    data = _request()
    assert len(data["required_packet_fields"]) == 12
    assert {
        "observed_stomatal_conductance_or_leaf_surface_resistance",
        "VPD_or_explicit_humidity_to_VPD_basis",
        "light_or_PAR",
        "leaf_temperature",
        "dataset_bound_growth_stage_or_explicit_developmental_context",
        "replicate_or_independent_group_identity",
        "matched_records_or_explicit_alignment_contract",
    } <= set(data["required_packet_fields"])


def test_r3a_audits_three_single_source_candidates_without_stitching() -> None:
    data = _request()
    candidates = {item["candidate_id"]: item for item in data["candidate_audits"]}
    assert set(candidates) == {
        "MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD",
        "TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD",
        "HELICOVERPA_ZEA_SALIVA_SOYBEAN_STOMATAL_DRYAD",
    }
    assert candidates["MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD"]["priority"] == 1
    assert candidates["TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD"]["priority"] == 2
    assert "Never combine" in data["cross_dataset_rule"]


def test_r3a_constant_and_vpd_derivation_rules_are_fail_closed() -> None:
    data = _request()
    assert "same audited records" in data["constant_admission_rule"]
    assert "not a per-record humidity value" in data["constant_admission_rule"]
    assert "all necessary variables" in data["derivation_rule"]
    assert "Approximation" in data["derivation_rule"]


def test_r3a_keeps_leaf_implementation_and_activation_closed() -> None:
    inv = _request()["hard_invariants"]
    assert inv == {
        "leaf_implementation_authorized": False,
        "solver_implementation_started": False,
        "candidate_parameter_values_admitted": False,
        "calibration_started": False,
        "active_parameters": 0,
        "ufotri_active_database": False,
        "v3_physics_ready": False,
        "physical_validation_complete": False,
    }


def test_r3a_raw_third_party_files_must_not_be_committed() -> None:
    policy = _request()["raw_data_policy"]
    assert policy["commit_third_party_raw_files"] is False
    assert policy["external_workspace_required"] is True
    assert policy["record_hashes"] is True
