from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2.yaml"
HANDOFF = ROOT / "docs/v4/reports/v4_2_leaf_evidence_file_audit_r2_handoff.md"

BASE_MAIN = "e1bd2460fe242fe93f13b3d3a2f74607c9448544"
PACKET_DOCS_TIP = "442b553d6173d9fd62d33b0591613e4d7f03b593"
EXPECTED_PACKET_DOCS = {
    "docs/v4/leaf/v4_2_leaf_evidence_file_audit_r2.yaml",
    "docs/v4/reports/v4_2_leaf_evidence_file_audit_r2_handoff.md",
}


def _packet() -> dict:
    return yaml.safe_load(PACKET.read_text(encoding="utf-8"))


def test_r2_starts_pending_and_cannot_authorize_implementation() -> None:
    data = _packet()
    assert data["status"] == "PENDING_LOCAL_FILE_LEVEL_AUDIT"
    invariants = data["hard_invariants"]
    assert invariants["leaf_implementation_authorized"] is False
    assert invariants["solver_implementation_started"] is False
    assert invariants["candidate_parameter_values_admitted"] is False
    assert invariants["calibration_started"] is False
    assert invariants["active_parameters"] == 0
    assert invariants["ufotri_active_database"] is False
    assert invariants["v3_physics_ready"] is False
    assert invariants["physical_validation_complete"] is False


def test_r2_classification_and_verdict_enums_are_frozen() -> None:
    data = _packet()
    assert data["classification_enum"] == [
        "DIRECT_COLUMN",
        "DECLARED_CONSTANT_WITH_PROVENANCE",
        "EXPLICIT_DERIVATION_SUPPORTED",
        "MISSING",
        "AMBIGUOUS",
    ]
    assert set(data["allowed_final_verdicts"]) == {
        "PASS_ONE_COMPLETE_EMPIRICAL_PACKET_CANDIDATE",
        "HOLD_COMPONENT_EVIDENCE_ONLY",
        "HOLD_REQUIRED_FIELDS_MISSING",
        "HOLD_ALIGNMENT_OR_PROVENANCE_AMBIGUOUS",
    }


def test_r2_priority_files_are_frozen() -> None:
    audits = {item["candidate_id"]: item for item in _packet()["candidate_audits"]}
    monnens = audits["MONNENS_2023_SOYBEAN_VPD_DRYAD"]
    assert [f["file_name"] for f in monnens["files_required"]] == [
        "Monnens_et_al_All_data_Dryad.xlsx"
    ]
    tomeo = audits["TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"]
    expected = {
        "CE_GasExchangeParameters.csv": "30b955a1b12b22bf4e80353f8aaa7315",
        "Field_GasExchangeParameters.csv": "e9f7043885e7097448d37efaf92f9733",
        "README_for_CE_GasExchangeParameters.txt": "68cbfb56e9f656e5573713f9a1fdd761",
        "README_for_Field_GasExchangeParameters.txt": "07ce6434d693d28fc756ec6649e3ed01",
    }
    assert {f["file_name"]: f["source_md5"] for f in tomeo["files_required"]} == expected


def test_r2_packet_docs_interval_is_governance_only() -> None:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASE_MAIN}..{PACKET_DOCS_TIP}"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert set(changed) == EXPECTED_PACKET_DOCS
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("configs/") for path in changed)


def test_handoff_requires_actual_file_level_audit() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    assert "read-only audit of actual public source files" in text
    assert "Do not infer workbook contents from the article" in text
    assert "Two soybean datasets cannot be stitched into one packet" in text
    assert "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE" in text
