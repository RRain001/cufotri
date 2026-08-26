from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
OLD_MAIN = "d24aa03b00dcb586a2d93e678f42cb7853b7c078"
IMPLEMENTATION = "95f78801d0fa3b507e6bd76249b192adf8b107cb"
MERGE_COMMIT = "43eabee5fc5029441c00cc0221d84bf887bc4660"
R2_HEAD = "7a06733f3201cc60c4c6599799892899cdb61d7f"
EXPECTED_TREE = "b2d06370e5c1ec2f7322aceabbbc2e909ae6f442"
REQUEST = ROOT / "docs/v3_1/reviews/v3_1_mass_basis_independent_rereview_r2_request.yaml"
CLOSURE = ROOT / "docs/v3_1/reports/v3_1_main_merge_closure.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def test_v3_1_merge_commit_preserves_exact_two_parent_history() -> None:
    parents = git("show", "-s", "--format=%P", MERGE_COMMIT).split()
    assert parents == [OLD_MAIN, IMPLEMENTATION]


def test_v3_1_merge_tree_matches_frozen_implementation_tree() -> None:
    assert git("show", "-s", "--format=%T", MERGE_COMMIT) == EXPECTED_TREE
    assert git("show", "-s", "--format=%T", IMPLEMENTATION) == EXPECTED_TREE


def test_v3_1_merge_commit_remains_in_current_history() -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", MERGE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=True,
    )


def test_r2_pass_is_bound_to_frozen_implementation() -> None:
    data = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    assert data["status"] == "PASS_INDEPENDENT_REREVIEW"
    verdict = data["reviewer_verdict"]
    assert verdict["status"] == "PASS_INDEPENDENT_REREVIEW"
    assert verdict["reviewed_sha"] == IMPLEMENTATION
    assert verdict["blocking_findings"] == []
    assert data["exit_policy"]["v4_implementation_authorized"] is False
    assert data["exit_policy"]["active_parameters"] == 0


def test_closure_records_merge_and_keeps_v4_closed() -> None:
    text = CLOSURE.read_text(encoding="utf-8")
    for token in (MERGE_COMMIT, IMPLEMENTATION, R2_HEAD, EXPECTED_TREE):
        assert token in text
    assert "V3_1_MASS_BASIS_CONTRACT = PASS_MAIN_MERGED" in text
    assert "V4_IMPLEMENTATION_AUTHORIZED = FALSE" in text
    assert "V3_PHYSICS_READY = FALSE" in text
    assert "ACTIVE_PARAMETERS = 0" in text
