from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
TRUSTED_REGISTRY = "validation/v3/policy/trusted_external_evidence_registry.yaml"
CONFTEXT = ROOT / "tests/conftest.py"
HISTORICAL_NODEIDS = {
    "tests/external_evidence_acquisition/test_d3_ufotri_manual_data_mapping_independent_rereview_r1.py::test_external_gate_scripts_remain_fail_closed",
    "tests/external_evidence_acquisition/test_external_input_test_portability_r1.py::test_external_gate_and_physics_gate_remain_fail_closed",
    "tests/independent_review_d3_true_reblinding/test_d3_true_reblinding_independent_review.py::test_review_classifier_worktree_never_contains_secret",
    "tests/independent_review_sb1_mechanisms/test_sb1_mechanism_independent_review.py::test_review_no_formal_src_changes",
    "tests/independent_review_sb1_mechanisms/test_sb1_mechanism_independent_review.py::test_review_no_formal_config_changes",
    "tests/independent_review_sb1_mechanisms/test_sb1_mechanism_independent_review.py::test_review_trusted_registry_unchanged",
    "tests/independent_review_sb4/test_emras_soybean_sb4_independent_review.py::test_review_sb4_formal_boundaries_unchanged",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def assert_unchanged(base: str, tip: str, *paths: str) -> None:
    git("cat-file", "-e", f"{base}^{{commit}}")
    git("cat-file", "-e", f"{tip}^{{commit}}")
    git("merge-base", "--is-ancestor", base, tip)
    changed = git("diff", "--name-only", f"{base}...{tip}", "--", *paths)
    assert changed == ""


def test_historical_context_classification_is_exact_and_auditable() -> None:
    text = CONFTEXT.read_text(encoding="utf-8")
    assert "HISTORICAL_REVIEW_CONTEXT_NODEIDS" in text
    for nodeid in HISTORICAL_NODEIDS:
        assert nodeid in text
    assert text.count("::test_") == len(HISTORICAL_NODEIDS)


def test_d3_manual_mapping_review_preserved_protected_paths() -> None:
    assert_unchanged(
        "f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a",
        "0164a99cae30ab44411fe98be9ea9cc512c51966",
        "src",
        "configs",
        TRUSTED_REGISTRY,
    )


def test_external_evidence_unblocking_stage_preserved_model_and_config() -> None:
    assert_unchanged(
        "f618515caef22a19867d75d59b1d4c78f1cb212f",
        "2a3bbd1f43fa92db4c54b9604b186af0bbba4c5c",
        "src",
        "configs",
    )


def test_sb1_independent_review_finalization_preserved_formal_boundaries() -> None:
    assert_unchanged(
        "744db57e87f8f7e3c202cda070c4ce95fd5c109b",
        "5c1d4bf39415be9b6e7960efeda23af50570f518",
        "src",
        "configs",
        TRUSTED_REGISTRY,
    )


def test_sb4_independent_review_preserved_formal_boundaries() -> None:
    assert_unchanged(
        "d08d9d81f3ef10b11c2431e7bebe2f802c56cd18",
        "b540387087cecedee2a3d2a078657e0b313a2c8e",
        "src",
        "configs",
        TRUSTED_REGISTRY,
    )
