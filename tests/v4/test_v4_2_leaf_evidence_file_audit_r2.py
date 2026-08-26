"""V4-2 leaf evidence file audit R2 result invariants.

Validates the machine-readable audit result against the governance packet:
verdict legality, per-candidate field coverage, hash verification, and the
frozen non-implementation boundary.
"""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2_result.yaml"
PACKET = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2.yaml"

REQUIRED_FIELD_IDS = [
    "observed_stomatal_conductance_or_leaf_surface_resistance",
    "target_measurement_basis",
    "light_or_PAR",
    "VPD_or_explicit_humidity_to_VPD_basis",
    "leaf_temperature",
    "dataset_bound_growth_stage_ontology",
    "crop_identity",
    "timestamp_and_interval_semantics",
    "replicate_or_independent_group_identity",
    "quantitative_units",
    "variable_level_provenance",
    "matched_records_or_explicit_alignment_contract",
]

CLASSIFICATION_ENUM = {
    "DIRECT_COLUMN",
    "DECLARED_CONSTANT_WITH_PROVENANCE",
    "EXPLICIT_DERIVATION_SUPPORTED",
    "MISSING",
    "AMBIGUOUS",
}


def _result() -> dict:
    return yaml.safe_load(RESULT.read_text(encoding="utf-8"))


def _packet() -> dict:
    return yaml.safe_load(PACKET.read_text(encoding="utf-8"))


def test_verdict_is_a_legal_hold_and_consistent_with_packet() -> None:
    data = _result()
    assert (
        data["final_verdict"] == "HOLD_REQUIRED_FIELDS_MISSING"
    ), data["final_verdict"]
    assert data["final_verdict"] in set(_packet()["allowed_final_verdicts"])
    packet_status = _packet()["status"]
    assert packet_status == "COMPLETE_HOLD_REQUIRED_FIELDS_MISSING", packet_status
    for candidate in _packet()["candidate_audits"]:
        assert candidate["result"] == "HOLD_REQUIRED_FIELDS_MISSING"
        assert candidate["full_packet_candidate"] is False


def test_both_candidates_have_full_twelve_field_matrices() -> None:
    matrix = _result()["per_candidate_field_matrix"]
    assert set(matrix) == {
        "MONNENS_2023_SOYBEAN_VPD_DRYAD",
        "TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD",
    }
    for candidate_id, rows in matrix.items():
        ids = [row["field_id"] for row in rows]
        assert ids == REQUIRED_FIELD_IDS, f"{candidate_id} field coverage mismatch"
        for row in rows:
            assert row["classification"] in CLASSIFICATION_ENUM, row
            assert (
                row.get("source_file")
                or row.get("exact_column_or_constant")
                or row.get("notes")
                or row.get("provenance")
            ), row


def test_tomeo_published_md5_values_all_match_locally() -> None:
    tomeo = next(
        entry
        for entry in _result()["source_file_hashes"]
        if entry["candidate_id"] == "TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"
    )
    required = {
        "CE_GasExchangeParameters.csv": "30b955a1b12b22bf4e80353f8aaa7315",
        "Field_GasExchangeParameters.csv": "e9f7043885e7097448d37efaf92f9733",
        "README_for_CE_GasExchangeParameters.txt": "68cbfb56e9f656e5573713f9a1fdd761",
        "README_for_Field_GasExchangeParameters.txt": "07ce6434d693d28fc756ec6649e3ed01",
    }
    local = {f["file_name"]: f for f in tomeo["files"]}
    assert set(local) == set(required)
    for name, published_md5 in required.items():
        assert local[name]["md5_local"] == published_md5, name
        assert local[name]["md5_published"] == published_md5, name
        assert local[name]["md5_match"] is True, name
        assert len(local[name]["sha256"]) == 64, name
        assert local[name]["byte_size"] > 0, name


def test_monnens_xlsx_bytes_were_retrieved_and_hashed() -> None:
    monnens = next(
        entry
        for entry in _result()["source_file_hashes"]
        if entry["candidate_id"] == "MONNENS_2023_SOYBEAN_VPD_DRYAD"
    )
    xlsx = next(
        f
        for f in monnens["files"]
        if f["file_name"] == "Monnens_et_al_All_data_Dryad.xlsx"
    )
    assert xlsx["byte_size"] == 38689
    assert xlsx["md5"] == "a4f69d2088981df440372a058fc1dfe6"
    assert len(xlsx["sha256"]) == 64


def test_driver_columns_are_absent_and_alignment_failed_for_both() -> None:
    data = _result()
    inventory = data["source_file_inventory"]
    tomeo_files = inventory["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]
    for table in (
        tomeo_files["CE_GasExchangeParameters.csv"],
        tomeo_files["Field_GasExchangeParameters.csv"],
    ):
        assert table["driver_columns_present"] == []
    monnens = inventory["MONNENS_2023_SOYBEAN_VPD_DRYAD"]
    xlsx = monnens["Monnens_et_al_All_data_Dryad.xlsx"]
    assert "no absolute stomatal" in xlsx["key_observation"]
    alignment = data["missingness_and_alignment"]
    assert alignment["MONNENS_2023_SOYBEAN_VPD_DRYAD"]["row_alignment"] == "FAIL"
    assert (
        alignment["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]["row_alignment"]
        == "FAIL_AS_DRIVER_RESPONSE_PACKET"
    )


def test_response_domain_stage_and_group_assessments_are_recorded() -> None:
    data = _result()
    assert (
        data["response_domain_assessment"]["MONNENS_2023_SOYBEAN_VPD_DRYAD"]
        == "TWO_CONDITION_CONTRAST"
    )
    assert (
        data["response_domain_assessment"]["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]
        == "INSUFFICIENT_SUPPORT"
    )
    stage = data["stage_ontology_assessment"]
    assert stage["MONNENS_2023_SOYBEAN_VPD_DRYAD"] == "MISSING"
    assert stage["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD_FIELD"] == "SUPPORTED_CAMP_MAPPING"
    assert stage["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD_CE"] == "MISSING"
    groups = data["independent_group_assessment"]
    assert groups["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]["ce_independent_plants"] == 71
    assert groups["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]["field_plots"] == 31


def test_cross_dataset_stitching_was_not_attempted() -> None:
    stitch = _result()["cross_dataset_stitching_check"]
    assert stitch["performed"] is True
    assert stitch["result"] == "NOT_ATTEMPTED_AND_FORBIDDEN"


def test_audit_preserves_non_implementation_boundary() -> None:
    invariants = _result()["hard_invariants"]
    assert invariants["leaf_implementation_authorized"] is False
    assert invariants["solver_implementation_started"] is False
    assert invariants["candidate_parameter_values_admitted"] is False
    assert invariants["calibration_started"] is False
    assert invariants["active_parameters"] == 0
    assert invariants["ufotri_active_database"] is False
    assert invariants["v3_physics_ready"] is False
    assert invariants["physical_validation_complete"] is False


def test_no_repository_copy_of_third_party_files_is_declared() -> None:
    """Raw third-party bytes must stay in the external workspace only."""
    hashes = _result()["source_file_hashes"]
    for entry in hashes:
        for f in entry["files"]:
            assert not f["file_name"].startswith("/"), f
            assert "repo_path" not in f and "committed_as" not in f
    text = RESULT.read_text(encoding="utf-8")
    assert "repo_copy" not in text and "committed_path" not in text
