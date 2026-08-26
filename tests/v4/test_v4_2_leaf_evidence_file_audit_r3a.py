"""V4-2 leaf evidence file audit R3A result invariants.

Validates the machine-readable R3A audit result: verdict legality, per-candidate
12-field coverage, hash records, driver/target asymmetry findings, and the
frozen non-implementation boundary.
"""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r3a_result.yaml"
PACKET = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r3a.yaml"

REQUIRED_FIELD_IDS = [
    "observed_stomatal_conductance_or_leaf_surface_resistance",
    "target_measurement_basis",
    "light_or_PAR",
    "VPD_or_explicit_humidity_to_VPD_basis",
    "leaf_temperature",
    "dataset_bound_growth_stage_or_explicit_developmental_context",
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

CANDIDATE_IDS = {
    "MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD",
    "TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD",
    "HELICOVERPA_ZEA_SALIVA_SOYBEAN_STOMATAL_DRYAD",
}


def _result() -> dict:
    return yaml.safe_load(RESULT.read_text(encoding="utf-8"))


def _packet() -> dict:
    return yaml.safe_load(PACKET.read_text(encoding="utf-8"))


def test_verdict_is_legal_hold_and_packet_status_matches() -> None:
    data = _result()
    assert data["final_verdict"] == "HOLD_REQUIRED_FIELDS_MISSING"
    assert data["final_verdict"] in set(_packet()["allowed_final_verdicts"])
    assert _packet()["status"] == "COMPLETE_HOLD_REQUIRED_FIELDS_MISSING"
    per_candidate_results = {
        "MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD": "HOLD_REQUIRED_FIELDS_MISSING",
        "TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD": "HOLD_COMPONENT_EVIDENCE_ONLY",
        "HELICOVERPA_ZEA_SALIVA_SOYBEAN_STOMATAL_DRYAD": "HOLD_REQUIRED_FIELDS_MISSING",
    }
    for candidate in _packet()["candidate_audits"]:
        assert candidate["result"] == per_candidate_results[candidate["candidate_id"]]
        assert candidate["full_packet_candidate"] is False


def test_all_three_candidates_have_full_twelve_field_matrices() -> None:
    results = {c["candidate_id"]: c for c in _result()["candidate_results"]}
    assert set(results) == CANDIDATE_IDS
    for cid, cand in results.items():
        ids = [row["field_id"] for row in cand["field_matrix"]]
        assert ids == REQUIRED_FIELD_IDS, f"{cid} field coverage mismatch"
        for row in cand["field_matrix"]:
            assert row["classification"] in CLASSIFICATION_ENUM, (cid, row)


def test_mostofa_target_is_direct_but_drivers_missing() -> None:
    mostofa = next(
        c
        for c in _result()["candidate_results"]
        if c["candidate_id"].startswith("MOSTOFA")
    )
    by_id = {row["field_id"]: row for row in mostofa["field_matrix"]}
    target = by_id["observed_stomatal_conductance_or_leaf_surface_resistance"]
    assert target["classification"] == "DIRECT_COLUMN"
    assert target["unit"] == "mol m-2 s-1"
    assert target["missing_count"] == "0_of_150"
    timing = by_id["timestamp_and_interval_semantics"]
    assert timing["classification"] == "DIRECT_COLUMN"
    assert "5 s" in timing["row_alignment"]
    for field in ("light_or_PAR", "VPD_or_explicit_humidity_to_VPD_basis", "leaf_temperature"):
        assert by_id[field]["classification"] == "MISSING", field
    groups = by_id["replicate_or_independent_group_identity"]
    assert groups["classification"] == "MISSING"
    inventory = _result()["source_file_inventory"]["MOSTOFA_2025_CRYPTIC_ISOPRENE_SOYBEAN_DRYAD"]
    fig3d = inventory["target_sheet_Fig3d"]
    assert fig3d["data_rows"] == 150
    assert abs(fig3d["time_step_minutes"] - 0.083333) < 1e-6
    assert fig3d["series_count"] == 1
    assert fig3d["gsw_missing"] == 0


def test_tejera_drivers_complete_but_target_absent() -> None:
    tejera = next(
        c
        for c in _result()["candidate_results"]
        if c["candidate_id"].startswith("TEJERA")
    )
    by_id = {row["field_id"]: row for row in tejera["field_matrix"]}
    assert by_id["observed_stomatal_conductance_or_leaf_surface_resistance"]["classification"] == "MISSING"
    for field in ("light_or_PAR", "VPD_or_explicit_humidity_to_VPD_basis", "leaf_temperature"):
        assert by_id[field]["classification"] == "DIRECT_COLUMN", field
    inv = _result()["source_file_inventory"]["TEJERA_NIEVES_WALKER_2024_ACI_SOYBEAN_DRYAD"]
    csv_inv = inv["ACiMethod_4.0_RepositoryData.csv"]
    assert csv_inv["conductance_or_resistance_columns"] in ([], "NONE")
    assert csv_inv["soybean_rows"] == 3282
    assert csv_inv["shape"] == "19601 rows x 10 cols"


def test_helicoverpa_target_ambiguous_and_script_gap_recorded() -> None:
    helio = next(
        c
        for c in _result()["candidate_results"]
        if c["candidate_id"].startswith("HELICOVERPA")
    )
    by_id = {row["field_id"]: row for row in helio["field_matrix"]}
    assert by_id["observed_stomatal_conductance_or_leaf_surface_resistance"]["classification"] == "AMBIGUOUS"
    assert by_id["quantitative_units"]["classification"] == "MISSING"
    script = _result()["source_file_inventory"]["HELICOVERPA_ZEA_SALIVA_SOYBEAN_STOMATAL_DRYAD"]["script_audit"]
    assert script["Stomatal_conductance_R_listed_in_README"] is True
    assert script["Stomatal_conductance_R_present_in_repository"] is False
    assert script["any_available_script_reads_fig1e"] is False


def test_source_hashes_recorded_for_every_downloaded_file() -> None:
    data = _result()
    assert {e["candidate_id"] for e in data["source_file_hashes"]} == CANDIDATE_IDS
    for entry in data["source_file_hashes"]:
        assert str(entry["download_date"]) == "2026-08-26"
        assert entry["dataset_doi"].startswith("10.5061/dryad.")
        for f in entry["files"]:
            assert len(f["sha256"]) == 64 and f["byte_size"] > 0, f["file_name"]
            assert not f["file_name"].startswith("/")
    mostofa_xlsx = next(
        f
        for e in data["source_file_hashes"]
        if e["candidate_id"].startswith("MOSTOFA")
        for f in e["files"]
        if f["file_name"].endswith(".xlsx")
    )
    assert mostofa_xlsx["byte_size"] == 87814
    assert mostofa_xlsx["md5"] == "b5debc8f97717e4212a076ada0a379a8"


def test_no_stitching_and_constant_rules_enforced() -> None:
    data = _result()
    assert data["cross_dataset_rule"]["stitching_attempts"] == 0
    consts = data["declared_constant_applicability"]
    assert consts["mostofa_article_conditions"] == "NOT_ADMISSIBLE_THIS_ROUND"
    vpd = data["vpd_derivation_assessment"]
    assert vpd["mostofa"] == "IMPOSSIBLE_MISSING_PER_ROW_INPUTS"
    assert vpd["tejera"] == "NOT_REQUIRED_DIRECT_COLUMN_PRESENT"


def test_non_implementation_boundary_preserved() -> None:
    invariants = _result()["hard_invariants"]
    assert invariants["leaf_implementation_authorized"] is False
    assert invariants["solver_implementation_started"] is False
    assert invariants["candidate_parameter_values_admitted"] is False
    assert invariants["calibration_started"] is False
    assert invariants["active_parameters"] == 0
    assert invariants["ufotri_active_database"] is False
    assert invariants["v3_physics_ready"] is False
    assert invariants["physical_validation_complete"] is False
