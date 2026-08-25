from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/governance/codex_branch_disposition.yaml"


def test_branch_disposition_is_complete_and_non_overlapping() -> None:
    payload = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "v1"
    assert payload["integration_policy"]["rewrite_existing_history"] is False
    assert payload["integration_policy"]["force_push_existing_stage_branches"] is False
    assert payload["integration_policy"]["merge_all_codex_branches"] is False
    assert payload["integration_policy"]["main_merge_authorized"] is False
    assert payload["integration_policy"]["active_parameters"] == 0
    assert payload["integration_policy"]["ufotri_active_database"] is False
    assert payload["integration_policy"]["v3_physics_ready"] is False

    classes = payload["classes"]
    assert set(classes) == {
        "CURRENT_CANDIDATE_LINE",
        "CURRENT_RUNTIME_SOURCE_CHECKPOINT",
        "SUPERSEDED_ARCHITECTURE_DO_NOT_MERGE",
        "HISTORICAL_MAIN_ANCESTOR_OR_EVIDENCE_LINE",
    }

    seen: set[str] = set()
    for disposition in classes.values():
        branches = disposition["branches"]
        assert branches
        assert len(branches) == len(set(branches))
        assert all(branch.startswith("codex/") for branch in branches)
        overlap = seen.intersection(branches)
        assert not overlap, f"branches assigned to multiple classes: {sorted(overlap)}"
        seen.update(branches)

    current = classes["CURRENT_CANDIDATE_LINE"]["branches"]
    superseded = classes["SUPERSEDED_ARCHITECTURE_DO_NOT_MERGE"]
    assert current[-1] == "codex/v3-repository-audit-remediation"
    assert superseded["merge_policy"] == "DO_NOT_MERGE"
    assert "codex/v3-parameter-database-layer" in superseded["branches"]
    assert "codex/v3-ufotri-physics-readiness-audit" in superseded["branches"]
