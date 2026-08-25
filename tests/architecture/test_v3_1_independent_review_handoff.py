from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
REQUEST = ROOT / "docs/v3_1/reviews/v3_1_mass_basis_independent_review_request.yaml"
TARGET_SHA = "4664e4c09f20bbfd48c5d1c750efafeb6d6e9643"
REVIEW_PACKET_HEAD_SHA = "8e4c1184394ca35e78cbad50a0c4e1cca777cdf9"
EXPECTED_PACKET_FILES = {
    "docs/v3_1/reports/v3_1_mass_basis_independent_review_handoff.md",
    "docs/v3_1/reviews/v3_1_mass_basis_independent_review_request.yaml",
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


def test_independent_review_packet_is_bound_to_exact_frozen_target() -> None:
    payload = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    target = payload["review_target"]
    independence = payload["reviewer_independence"]

    assert payload["stage"] == "V3.1"
    assert payload["review_type"] == "REVIEWER_INDEPENDENT"
    assert payload["status"] == "PENDING_INDEPENDENT_REVIEW"
    assert target["frozen_target_sha"] == TARGET_SHA
    assert target["independent_review_branch"] == (
        "codex/v3-1-mass-basis-independent-review"
    )
    assert independence["must_not_be_implementation_author"] is True
    assert independence["must_not_claim_same_author_rereview_as_independent"] is True
    assert independence["implementation_author_technical_rereview_satisfies_gate"] is False
    assert independence["reviewer_identity"] is None


def test_review_packet_historical_interval_contains_docs_only() -> None:
    git("merge-base", "--is-ancestor", TARGET_SHA, REVIEW_PACKET_HEAD_SHA)
    git("merge-base", "--is-ancestor", REVIEW_PACKET_HEAD_SHA, "HEAD")

    changed = set(
        git("diff", "--name-only", f"{TARGET_SHA}..{REVIEW_PACKET_HEAD_SHA}").splitlines()
    )
    assert changed == EXPECTED_PACKET_FILES


def test_pending_verdict_cannot_authorize_merge_or_v4() -> None:
    payload = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    verdict = payload["reviewer_verdict"]
    policy = payload["exit_policy"]

    assert verdict["status"] == "PENDING_INDEPENDENT_REVIEW"
    assert verdict["reviewed_sha"] is None
    assert verdict["reviewer_identity"] is None
    assert verdict["blocking_findings"] == []

    assert policy["implementation_pr_merge_ready"] is False
    assert policy["main_merge_authorized_by_this_request"] is False
    assert policy["active_parameters"] == 0
    assert policy["calibration_started"] is False
    assert policy["ufotri_active_database"] is False
    assert policy["v3_physics_ready"] is False
    assert policy["v4_implementation_authorized"] is False
