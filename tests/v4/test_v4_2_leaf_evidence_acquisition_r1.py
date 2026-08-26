from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/v4/leaf/v4_2_leaf_evidence_acquisition_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_2_leaf_evidence_acquisition_r1.md"

BASE_MAIN = "702ce51fccc167127b7a318f3d8652c064e73aef"
CONTENT_TIP = "e2f76d58343c61e679d6b74da6e01f49a9783474"
EXPECTED_CONTENT_FILES = {
    "docs/v4/leaf/v4_2_leaf_evidence_acquisition_r1.yaml",
    "docs/v4/reports/v4_2_leaf_evidence_acquisition_r1.md",
}


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def _candidates_by_id() -> dict[str, dict]:
    return {item["candidate_id"]: item for item in _registry()["candidates"]}


def test_r1_is_a_hold_not_an_implementation_authorization() -> None:
    data = _registry()
    assert data["status"] == "HOLD_FILE_LEVEL_EVIDENCE_AUDIT_REQUIRED"
    decision = data["round_r1_decision"]
    assert decision["full_empirical_packet_found"] is False
    assert decision["matched_validation_dataset_admitted"] is False
    assert decision["dataset_specific_stage_ontology_admitted"] is False
    assert decision["empirical_response_domains_admitted"] is False
    assert decision["calibration_started"] is False
    assert decision["leaf_implementation_authorized"] is False
    assert decision["candidate_parameter_values_admitted"] is False
    assert decision["active_parameters"] == 0
    assert decision["ufotri_active_database"] is False
    assert decision["v3_physics_ready"] is False
    assert decision["physical_validation_complete"] is False


def test_no_r1_candidate_is_admitted_as_a_full_packet() -> None:
    candidates = _registry()["candidates"]
    assert candidates
    assert all(item["full_packet_admitted"] is False for item in candidates)


def test_priority_order_preserves_soybean_file_audits_first() -> None:
    candidates = sorted(_registry()["candidates"], key=lambda item: item["priority"])
    assert candidates[0]["candidate_id"] == "MONNENS_2023_SOYBEAN_VPD_DRYAD"
    assert candidates[1]["candidate_id"] == "TOMEO_ROSENTHAL_2018_SOYBEAN_DRYAD"
    assert candidates[0]["disposition"] == "PRIORITY_FILE_LEVEL_AUDIT_REQUIRED"
    assert candidates[1]["disposition"] == "COMPONENT_EVIDENCE_STAGE_STRONG_FILE_AUDIT_REQUIRED"


def test_cross_species_method_benchmark_cannot_authorize_parameters() -> None:
    candidate = _candidates_by_id()["RIZZO_2026_STOMATAL_CALIBRATION_DRYAD"]
    assert candidate["full_packet_admitted"] is False
    assert candidate["implementation_authorization_contribution"] == "METHODS_ONLY"
    assert "not_soybean" in candidate["limitations_for_current_target"]
    assert "cannot_substitute_cross_species_parameter_values" in candidate["limitations_for_current_target"]


def test_r1_content_scope_is_governance_only() -> None:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASE_MAIN}..{CONTENT_TIP}"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    assert set(changed) == EXPECTED_CONTENT_FILES
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("configs/") for path in changed)


def test_report_preserves_file_level_audit_boundary() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "HOLD_FILE_LEVEL_EVIDENCE_AUDIT_REQUIRED" in text
    assert "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE" in text
    assert "priority candidate" in text
    assert "not an admitted" in text
    assert "DIRECT_COLUMN" in text
    assert "MISSING" in text
