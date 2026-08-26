from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
TARGET = "95f78801d0fa3b507e6bd76249b192adf8b107cb"
PACKET_DOCS_TIP = "fb29c97f6580e5b73a0641fe94414e0552b69bc6"
REQUEST = ROOT / "docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r2_request.yaml"
HANDOFF = ROOT / "docs/v3_1/reports/v3_1_mass_basis_independent_rereview_r2_handoff.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def test_r2_packet_is_bound_to_exact_frozen_target() -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    assert data["status"] == "PENDING_INDEPENDENT_REREVIEW"
    assert data["review_target"]["frozen_target_sha"] == TARGET
    assert data["review_target"]["prior_rereview_pr"] == 5
    assert data["prior_independent_rereview_r1"]["verdict"] == "HOLD_REMEDIATION_REQUIRED"
    assert data["prior_independent_rereview_r1"]["review_branch_head"] == (
        "d2014f584a3fa6fc373bf32a6477e950ace01b5a"
    )
    assert data["reviewer_verdict"]["status"] == "PENDING_INDEPENDENT_REREVIEW"
    assert data["reviewer_verdict"]["reviewed_sha"] is None
    assert data["reviewer_independence"]["reviewer_identity"] is None
    assert data["exit_policy"]["implementation_pr_merge_ready"] is False
    assert data["exit_policy"]["v4_implementation_authorized"] is False


def test_r2_packet_docs_are_the_only_changes_before_packet_docs_tip() -> None:
    changed = {
        line
        for line in git("diff", "--name-only", TARGET, PACKET_DOCS_TIP).splitlines()
        if line
    }
    assert changed == {
        "docs/v3_1/reports/v3_1_mass_basis_independent_rereview_r2_handoff.md",
        "docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r2_request.yaml",
    }


def test_frozen_target_remains_in_current_history() -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", TARGET, "HEAD"],
        cwd=ROOT,
        check=True,
    )


def test_r2_request_contains_all_blocking_checks() -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    ids = {item["id"] for item in data["required_checks"]}
    assert ids == {
        "PRIOR_BLOCKER_WHITESPACE_SCHEMA_PARITY",
        "NO_NUMERICAL_BASIS_CONVERSION",
        "EXPLICIT_SOURCE_TARGET_PAIRING",
        "PAIR_REUSE_FAIL_CLOSED",
        "EVIDENCE_TISSUE_SCOPE_BINDING",
        "EVIDENCE_AREA_BASIS_BINDING",
        "CROSS_BASIS_EVIDENCE_ID_BINDING",
        "SAME_BASIS_EVIDENCE_STATE_BYPASS",
        "PYTHON_SCHEMA_BOUNDARY",
        "FROZEN_RUNTIME_ISOLATION",
        "P7_8B2_SCOPE_COMPLIANCE",
    }
    assert all(item["blocking"] is True for item in data["required_checks"])


def test_handoff_names_r1_blocker_and_exact_remediation_evidence() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    assert TARGET in text
    assert "d2014f584a3fa6fc373bf32a6477e950ace01b5a" in text
    assert "same-basis" in text
    assert "32916837645" in text
    assert "32917177883" in text
    assert "1000 passed" in text
    assert "V4_IMPLEMENTATION_AUTHORIZED = FALSE" in text
