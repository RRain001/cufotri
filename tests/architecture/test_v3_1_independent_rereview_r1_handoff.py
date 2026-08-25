from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
TARGET = "e28fd18033984e9fda252aa87b81b399b60ece1e"
PACKET_DOCS_TIP = "5c5bb1148d83fb6cc34e7e21ef1f298439b7240a"
REQUEST = ROOT / "docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r1_request.yaml"
HANDOFF = ROOT / "docs/v3_1/reports/v3_1_mass_basis_independent_rereview_r1_handoff.md"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
    ).strip()


def test_rereview_packet_is_bound_to_exact_frozen_target() -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    assert data["status"] == "PENDING_INDEPENDENT_REREVIEW"
    assert data["review_target"]["frozen_target_sha"] == TARGET
    assert data["review_target"]["prior_review_pr"] == 4
    assert data["prior_independent_review"]["verdict"] == "HOLD_REMEDIATION_REQUIRED"
    assert data["prior_independent_review"]["review_id"] == "PRR_kwDOTiMPdM8AAAABKupe9g"
    assert data["reviewer_verdict"]["status"] == "PENDING_INDEPENDENT_REREVIEW"
    assert data["exit_policy"]["implementation_pr_merge_ready"] is False
    assert data["exit_policy"]["v4_implementation_authorized"] is False


def test_rereview_packet_docs_are_the_only_changes_before_packet_docs_tip() -> None:
    changed = {
        line
        for line in git("diff", "--name-only", TARGET, PACKET_DOCS_TIP).splitlines()
        if line
    }
    assert changed == {
        "docs/v3_1/reports/v3_1_mass_basis_independent_rereview_r1_handoff.md",
        "docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r1_request.yaml",
    }


def test_frozen_target_remains_in_current_history() -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", TARGET, "HEAD"],
        cwd=ROOT,
        check=True,
    )


def test_handoff_names_prior_blocker_and_new_exact_head_evidence() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    assert TARGET in text
    assert "PRR_kwDOTiMPdM8AAAABKupe9g" in text
    assert "whitespace-only" in text
    assert "32809809310" in text
    assert "32810070923" in text
    assert "V4_IMPLEMENTATION_AUTHORIZED = FALSE" in text
