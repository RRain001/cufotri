"""1993 manual authority ADR guard; original executable parity remains separate."""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "v4" / "adr" / "ADR-085-ufotri-1993-manual-first-reconstruction-authority.md"


def test_manual_first_1993_is_normative_without_original_fortran() -> None:
    matrix = yaml.safe_load(
        (ROOT / "docs" / "v4" / "1993_upgrade" / "physics_delta_matrix.yaml").read_text(encoding="utf-8")
    )
    assert matrix["target_source"]["report"] == "KfK 5194"
    assert matrix["baseline_source"]["report"] == "KfK 4605"
    assert matrix["manual_based_1993_reconstruction_source"] == "KFK5194_1993_PRIMARY_NORMATIVE"
    assert matrix["original_fortran_source_available"] is False
    assert matrix["original_executable_required_for_manual_based_implementation"] is False
    assert matrix["independent_feature_scientific_review_required"] is True
    assert matrix["legacy_exact_reader_parity_requires_external_evidence"] is True
    assert matrix["manual_first_authority_decision"].endswith(ADR.name)


def test_adr_and_project_status_keep_external_claims_unestablished() -> None:
    adr = ADR.read_text(encoding="utf-8")
    for token in (
        "KfK 5194", "KfK 4853", "KfK 4605", "manual-first",
        "SOURCE_LIMITED", "original executable", "per-feature",
        "independent", "opt-in", "NOT_ESTABLISHED", "IWASH=0"
    ):
        assert token in adr
    assert "original FORTRAN source/executable is NOT a prerequisite" in adr or (
        "Original FORTRAN source/executable is NOT a prerequisite" in adr
    )
    matrix = yaml.safe_load(
        (ROOT / "docs" / "v4" / "1993_upgrade" / "physics_delta_matrix.yaml").read_text(encoding="utf-8")
    )
    assert matrix["runtime_1993_profile_activated"] is False
    assert matrix["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert matrix["external_empirical_validation"] == "NOT_ESTABLISHED"
    assert matrix["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    status = (ROOT / "STATUS.md").read_text(encoding="utf-8")
    assert "ADR-085-ufotri-1993-manual-first-reconstruction-authority.md" in status
    assert "has not been obtained" in status
    assert "not" in status.lower()
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "KfK 5194 (1993)" in agents
    assert "KfK 4605 (1990)" in agents
