from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "docs/v3/governance/v3_protected_integration_review.yaml"
ALLOWED_TEST_GOVERNANCE_FILES = {
    "tests/conftest.py",
    "tests/external_evidence_acquisition/test_d3_ufotri_manual_data_mapping.py",
}


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_review_contract_preserves_verified_runtime_candidate() -> None:
    payload = yaml.safe_load(REVIEW.read_text(encoding="utf-8"))
    lineage = payload["lineage"]
    frozen = payload["frozen_runtime_state"]

    assert payload["stage"] == "protected_integration_review"
    assert payload["review_branch"] == "codex/v3-protected-integration-review"
    assert lineage["main_base_sha"] == "6671f5793d04842bf2ceae4904f3c0cf30a0d7e0"
    assert lineage["verified_runtime_candidate_sha"] == (
        "8d5bff32a6fd43b3109f59f086170d89a0e9a8cd"
    )
    assert lineage["merge_base_equals_main_base"] is True
    assert lineage["candidate_ahead_of_main_at_review_entry"] == 44
    assert lineage["candidate_behind_main_at_review_entry"] == 0
    assert lineage["linear_fast_forward_possible_at_review_entry"] is True

    assert frozen["runtime_source_changes_after_verified_candidate"] is False
    assert frozen["physics_equations_changed_after_verified_candidate"] is False
    assert frozen["numerical_coupling_changed_after_verified_candidate"] is False
    assert frozen["active_parameters"] == 0
    assert frozen["calibration_started"] is False
    assert frozen["ufotri_active_database"] is False
    assert frozen["v3_physics_ready"] is False


def test_main_base_and_verified_candidate_are_ancestors_of_review_head() -> None:
    payload = yaml.safe_load(REVIEW.read_text(encoding="utf-8"))
    lineage = payload["lineage"]
    git("merge-base", "--is-ancestor", lineage["main_base_sha"], "HEAD")
    git("merge-base", "--is-ancestor", lineage["verified_runtime_candidate_sha"], "HEAD")
    assert git("merge-base", lineage["main_base_sha"], "HEAD") == lineage["main_base_sha"]


def test_review_only_changes_governance_ci_tests_and_docs_after_verified_candidate() -> None:
    payload = yaml.safe_load(REVIEW.read_text(encoding="utf-8"))
    entry = payload["lineage"]["verified_runtime_candidate_sha"]
    changed = set(git("diff", "--name-only", f"{entry}..HEAD").splitlines())

    assert changed
    forbidden_prefixes = (
        "src/",
        "configs/",
        "parameters/",
        "validation/results/",
        "schemas/",
    )
    offenders = sorted(
        path for path in changed if path.startswith(forbidden_prefixes)
    )
    assert offenders == []
    unexpected = sorted(
        path
        for path in changed
        if not path.startswith((".github/", "docs/", "tests/architecture/"))
        and path not in ALLOWED_TEST_GOVERNANCE_FILES
    )
    assert unexpected == []


def test_main_policy_records_completed_explicit_merge_step() -> None:
    payload = yaml.safe_load(REVIEW.read_text(encoding="utf-8"))
    policy = payload["main_policy"]
    gates = payload["review_gates"]
    integration = payload["main_integration"]
    lineage = payload["lineage"]

    assert policy["main_merge_authorized"] is True
    assert policy["main_merge_performed"] is True
    assert policy["main_merge_recommended"] is True
    assert policy["branch_protection_currently_enabled"] is False
    assert policy["required_status_checks_currently_enabled"] is False
    assert policy["recommended_required_check"] == (
        "V3 Protected Integration Gate / integration-gate"
    )

    assert integration["authorized"] is True
    assert integration["performed"] is True
    assert integration["pull_request"] == 1
    assert integration["merge_method"] == "MERGE_COMMIT_PRESERVE_EXISTING_STAGE_SHAS"
    assert integration["merge_commit_sha"] == (
        "c2e106dee185a4cd850c203b5e284f1db337ea0e"
    )
    assert integration["merge_parent_old_main"] == lineage["main_base_sha"]
    assert integration["merge_parent_review_head"] == lineage["final_review_head_sha"]
    assert integration["merge_tree_equals_review_head_tree"] is True
    assert integration["stage_commit_identities_preserved"] is True

    parents = git("show", "-s", "--format=%P", integration["merge_commit_sha"]).split()
    assert parents == [
        integration["merge_parent_old_main"],
        integration["merge_parent_review_head"],
    ]
    assert git("show", "-s", "--format=%T", integration["merge_commit_sha"]) == (
        integration["merge_tree_sha"]
    )
    assert integration["merge_tree_sha"] == integration["review_head_tree_sha"]

    assert gates["linear_ancestry"] == "PASS"
    assert gates["remediation_ci_at_verified_candidate"] == "PASS"
    assert gates["final_review_head_gate"] == "PASS"
