from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_acquisition_r3.yaml"


def _data() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def _candidates() -> dict[str, dict]:
    return {item["candidate_id"]: item for item in _data()["r3_candidates"]}


def test_r3_is_broadened_search_not_implementation() -> None:
    data = _data()
    assert data["status"] == "IN_PROGRESS_BROADENED_EMPIRICAL_SEARCH"
    inv = data["hard_invariants"]
    assert inv["leaf_implementation_authorized"] is False
    assert inv["solver_implementation_started"] is False
    assert inv["candidate_parameter_values_admitted"] is False
    assert inv["calibration_started"] is False
    assert inv["active_parameters"] == 0
    assert inv["ufotri_active_database"] is False
    assert inv["v3_physics_ready"] is False
    assert inv["physical_validation_complete"] is False


def test_r3_preserves_r2_holds_and_no_stitching() -> None:
    data = _data()
    assert data["r2_findings_preserved"]["monnens_2023"] == "HOLD_REQUIRED_FIELDS_MISSING"
    assert data["r2_findings_preserved"]["tomeo_rosenthal_2018"] == "HOLD_REQUIRED_FIELDS_MISSING"
    assert data["r2_findings_preserved"]["cross_dataset_stitching"] == "FORBIDDEN_WITHOUT_SEPARATE_REVIEW"


def test_r3_prefers_single_soybean_experiment() -> None:
    data = _data()
    assert data["search_order"][0] == "public_single_experiment_soybean_raw_records"
    minimum = set(data["admission_minimum"])
    assert {
        "absolute_observed_gsw_or_rc",
        "VPD_or_full_humidity_derivation_inputs",
        "PAR_or_light",
        "Tleaf",
        "dataset_bound_stage_or_explicit_developmental_context",
        "independent_group_identity",
        "matched_row_or_explicit_alignment_contract",
    } <= minimum


def test_mostofa_is_priority_file_audit_but_not_admitted() -> None:
    candidate = _candidates()["MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD"]
    assert candidate["species"] == "Glycine max"
    assert candidate["priority"] == 1
    assert candidate["disposition"] == "PRIORITY_FILE_LEVEL_AUDIT_REQUIRED"
    assert candidate["full_packet_admitted"] is False
    evidence = set(candidate["public_evidence_summary"])
    assert "gsw_recorded_every_5_seconds" in evidence
    assert "reproductive_stage_R1_declared" in evidence
    unresolved = set(candidate["unresolved"])
    assert "per_record_Tleaf_not_yet_verified" in unresolved
    assert "per_record_VPD_or_full_humidity_inputs_not_yet_verified" in unresolved


def test_tejera_is_driver_rich_but_target_incomplete() -> None:
    candidate = _candidates()["TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD"]
    assert candidate["species"] == "Glycine max"
    assert candidate["disposition"] == "DRIVER_RICH_COMPONENT_EVIDENCE_FILE_AUDIT_REQUIRED"
    assert candidate["full_packet_admitted"] is False
    evidence = set(candidate["public_evidence_summary"])
    assert {"row_level_Tleaf", "row_level_PAR", "row_level_VPDleaf", "RunID_independent_record_identity"} <= evidence
    assert "public_README_column_list_does_not_include_gsw_or_rc" in set(candidate["unresolved"])


def test_non_soybean_methods_benchmark_cannot_be_parameter_source() -> None:
    method = _candidates()["RIZZO_BAILEY_2026_METHODS_BENCHMARK"]
    assert method["species"] == "mixed_non_soybean"
    assert method["disposition"] == "COMPLETE_VARIABLE_METHODS_BENCHMARK_NOT_SOYBEAN_PARAMETER_SOURCE"
    assert method["full_packet_admitted"] is False


def test_zandalinas_still_requires_raw_data_discovery() -> None:
    candidate = _candidates()["ZANDALINAS_2020_SOYBEAN_SYSTEMIC_STOMATAL_RESPONSE"]
    assert candidate["species"] == "Glycine max"
    assert candidate["disposition"] == "PRIORITY_AUTHOR_OR_RAW_DATA_DISCOVERY"
    assert candidate["full_packet_admitted"] is False
    unresolved = set(candidate["unresolved"])
    assert "raw_LI_6800_log_availability_not_established" in unresolved
    assert "VPD_or_humidity_record_availability_not_established" in unresolved
