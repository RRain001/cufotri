from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import numpy as np
import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = (
    ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
)
PROTOCOL_PATH = (
    BENCHMARK
    / "preregistration"
    / "d3_true_reblinding_v3_protocol.yaml"
)
V3 = BENCHMARK / "reblinding_v3"
GENERATION_PATH = V3 / "generation_manifest_v3.yaml"
CLASSIFICATION_PATH = (
    V3 / "classification" / "blind_classification_manifest_v3.yaml"
)
CLASSIFICATION_RESULTS_PATH = (
    V3 / "classification" / "blind_classification_results_v3.csv"
)
UNBLINDING_PATH = V3 / "unblinding" / "unblinding_manifest_v3.yaml"
UNBLINDING_COMPARISON_PATH = (
    V3 / "unblinding" / "unblinding_comparison_v3.csv"
)
SECRET_COMMITMENT_PATH = V3 / "sealed_generation_secret_sha256"
PRIVATE_SECRET_PATH = (
    ROOT
    / "validation"
    / "external_local"
    / "d3_prospective_reblind_v3"
    / "sealed_generation_secret.json"
)
PROTOCOL = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
GENERATION = yaml.safe_load(GENERATION_PATH.read_text(encoding="utf-8"))
CLASSIFICATION = yaml.safe_load(
    CLASSIFICATION_PATH.read_text(encoding="utf-8")
)
UNBLINDING = yaml.safe_load(UNBLINDING_PATH.read_text(encoding="utf-8"))
PRECLASSIFICATION_COMMIT = str(CLASSIFICATION["preclassification_commit"])
CLASSIFICATION_COMMIT = str(UNBLINDING["classification_commit"])
OPAQUE_IDS = tuple(
    sorted(str(item["dataset_blind_id"]) for item in GENERATION["datasets"])
)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return [dict(row) for row in csv.DictReader(stream)]


def test_review_v1_v2_history_preserved() -> None:
    assert (
        BENCHMARK
        / "results"
        / "archive"
        / "v1_blinded_classification_results.csv"
    ).is_file()
    assert (BENCHMARK / "results" / "unblinding_comparison.csv").is_file()
    failure_doc = (
        ROOT
        / "docs"
        / "v3"
        / "experiments"
        / "d3_v2_blinding_failure_and_reblinding_protocol.md"
    ).read_text(encoding="utf-8")
    assert "INVALID_TRUTH_MAPPING_PREEXPOSED" in failure_doc
    assert "V2_EMPIRICAL_OR_BLIND_VALIDATION_CLAIM =\nFALSE" in failure_doc


def test_review_v1_archive_chronology_recorded_noncompliant() -> None:
    failure_doc = (
        ROOT
        / "docs"
        / "v3"
        / "experiments"
        / "d3_v2_blinding_failure_and_reblinding_protocol.md"
    ).read_text(encoding="utf-8")
    assert "V1_ARCHIVE_CONTENT_INTEGRITY =\nPASS" in failure_doc
    assert (
        "V1_ARCHIVE_COMMIT_CHRONOLOGY =\n"
        "NONCOMPLIANT_WITH_PLANNED_ORDER"
    ) in failure_doc


def test_review_new_ids_are_opaque_and_not_abc() -> None:
    assert len(OPAQUE_IDS) == 3
    assert not (set(OPAQUE_IDS) & {"A", "B", "C"})
    assert all(re.fullmatch(r"[A-Z2-9]{6}", item) for item in OPAQUE_IDS)


def test_review_new_ids_absent_before_preclassification() -> None:
    for blind_id in OPAQUE_IDS:
        result = git(
            "grep",
            "-n",
            blind_id,
            f"{PRECLASSIFICATION_COMMIT}^",
            "--",
            ".",
            check=False,
        )
        assert result.returncode == 1
        assert result.stdout == ""


def test_review_new_hashes_differ_from_v1_v2() -> None:
    old = {
        str(item)
        for values in PROTOCOL["prior_dataset_hashes"].values()
        for item in values
    }
    new = {str(item["sha256"]) for item in GENERATION["datasets"]}
    assert len(new) == 3
    assert new.isdisjoint(old)
    for item in GENERATION["datasets"]:
        path = ROOT / str(item["path"])
        assert file_sha256(path) == item["sha256"]


def test_review_public_secret_integrity_is_portable() -> None:
    relative = PRIVATE_SECRET_PATH.relative_to(ROOT).as_posix()
    assert (
        git("ls-files", "--error-unmatch", relative, check=False).returncode
        != 0
    )
    assert git("check-ignore", "--quiet", relative, check=False).returncode == 0
    committed_paths = git(
        "ls-tree",
        "-r",
        "--name-only",
        "HEAD",
        "--",
        "validation/external_local",
    ).stdout.splitlines()
    assert relative not in committed_paths
    commitment = SECRET_COMMITMENT_PATH.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{64}", commitment)
    assert GENERATION["sealed_generation_secret_sha256"] == commitment
    assert CLASSIFICATION["sealed_generation_secret_sha256"] == commitment
    assert UNBLINDING["sealed_generation_secret_sha256_verified"] is True
    assert UNBLINDING["truth_key_matches_sealed_secret"] is True
    assert CLASSIFICATION["truth_key_accessed"] is False
    assert CLASSIFICATION["secret_accessed"] is False
    assert GENERATION["generation_attempt"] == 1
    assert GENERATION["regeneration_permitted"] is False
    assert CLASSIFICATION["classification_attempt"] == 1
    assert CLASSIFICATION["retry_permitted"] is False
    assert UNBLINDING["generation_attempt"] == GENERATION["generation_attempt"]
    assert UNBLINDING["classification_attempt"] == CLASSIFICATION[
        "classification_attempt"
    ]


def test_review_private_secret_matches_commitment_when_available() -> None:
    if not PRIVATE_SECRET_PATH.is_file():
        pytest.skip("SKIP_PRIVATE_SECRET_NOT_AVAILABLE")
    relative = PRIVATE_SECRET_PATH.relative_to(ROOT).as_posix()
    assert (
        git("ls-files", "--error-unmatch", relative, check=False).returncode
        != 0
    )
    assert git("check-ignore", "--quiet", relative, check=False).returncode == 0
    assert file_sha256(PRIVATE_SECRET_PATH) == (
        SECRET_COMMITMENT_PATH.read_text(encoding="utf-8").strip()
    )


def test_review_classifier_worktree_never_contains_secret() -> None:
    classifier_worktree = (
        ROOT.parent / "CETAS_ufotri_d3_v3_blind_classifier"
    )
    assert classifier_worktree.is_dir()
    private = (
        classifier_worktree
        / "validation"
        / "external_local"
        / "d3_prospective_reblind_v3"
    )
    assert not private.exists() or not any(
        item.is_file() for item in private.rglob("*")
    )


def test_review_preclassification_tree_has_no_new_mapping() -> None:
    forbidden = re.compile(
        r"truth_class|expected_result|truth_mapping|"
        r"SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
        re.IGNORECASE,
    )
    for blind_id in OPAQUE_IDS:
        lines = git(
            "grep",
            "-n",
            blind_id,
            PRECLASSIFICATION_COMMIT,
            "--",
            ".",
        ).stdout.splitlines()
        assert lines
        assert not any(forbidden.search(line) for line in lines)


def test_review_classification_tree_has_no_new_mapping() -> None:
    paths = git(
        "ls-tree",
        "-r",
        "--name-only",
        CLASSIFICATION_COMMIT,
        str(V3.relative_to(ROOT)),
    ).stdout.splitlines()
    assert not any("/unblinding/" in path for path in paths)
    for blind_id in OPAQUE_IDS:
        lines = git(
            "grep",
            "-n",
            blind_id,
            CLASSIFICATION_COMMIT,
            "--",
            str(V3.relative_to(ROOT)),
        ).stdout
        assert "truth_class" not in lines
        assert "expected_result" not in lines
        assert "SYNTHETIC_OUT_OF_MODEL_CHALLENGE" not in lines


def test_review_commit_ancestry_is_strict() -> None:
    assert (
        git(
            "merge-base",
            "--is-ancestor",
            PRECLASSIFICATION_COMMIT,
            CLASSIFICATION_COMMIT,
            check=False,
        ).returncode
        == 0
    )
    assert (
        git(
            "merge-base",
            "--is-ancestor",
            CLASSIFICATION_COMMIT,
            "HEAD",
            check=False,
        ).returncode
        == 0
    )
    assert PRECLASSIFICATION_COMMIT != CLASSIFICATION_COMMIT


def test_review_only_one_generation_and_classification() -> None:
    generation_commits = git(
        "log",
        "--format=%H",
        "--",
        str((V3 / "blinded").relative_to(ROOT)),
    ).stdout.splitlines()
    classification_commits = git(
        "log",
        "--format=%H",
        "--",
        str((V3 / "classification").relative_to(ROOT)),
    ).stdout.splitlines()
    assert generation_commits == [PRECLASSIFICATION_COMMIT]
    assert classification_commits == [CLASSIFICATION_COMMIT]
    assert GENERATION["generation_attempt"] == 1
    assert CLASSIFICATION["classification_attempt"] == 1
    assert CLASSIFICATION["retry_permitted"] is False


def test_review_classifier_source_has_no_private_mapping_access() -> None:
    source = (
        BENCHMARK
        / "scripts"
        / "classify_d3_true_reblinding_v3.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "SECRET_PATH",
        "TRUTH_KEY_PATH",
        "mapping_from_secret",
        "truth_class",
    ):
        assert forbidden not in source


def independent_classify(
    observed: np.ndarray,
) -> tuple[str, float, float]:
    predictions = PROTOCOL["classifier"][
        "frozen_primary_predictions_bq_l_water"
    ]
    h2 = np.asarray(predictions["H2_SB1_FROZEN"], dtype=float)
    h3 = np.asarray(predictions["H3_SB1_FROZEN"], dtype=float)
    h2_rmse = float(
        np.sqrt(np.mean((np.log10(observed) - np.log10(h2)) ** 2))
    )
    h3_rmse = float(
        np.sqrt(np.mean((np.log10(observed) - np.log10(h3)) ** 2))
    )
    if abs(h2_rmse - h3_rmse) < 0.15:
        result = "DATA_INCONCLUSIVE"
    elif h2_rmse > 0.50 and h3_rmse > 0.50:
        result = "BOTH_INADEQUATE"
    elif h2_rmse < h3_rmse:
        result = "H2_SUPPORTED_OVER_H3"
    else:
        result = "H3_SUPPORTED_OVER_H2"
    return result, h2_rmse, h3_rmse


@pytest.fixture(scope="module")
def independent_results() -> dict[str, tuple[str, float, float]]:
    output: dict[str, tuple[str, float, float]] = {}
    for item in GENERATION["datasets"]:
        blind_id = str(item["dataset_blind_id"])
        frame = pd.read_csv(ROOT / str(item["path"]))
        means = []
        for hour in (0.2, 48.0, 120.0):
            selected = frame[
                np.isclose(frame["hours_after_exposure"], hour)
                & (frame["quality_flag"] == "OK")
                & (~frame["below_detection_limit"])
            ]
            assert len(selected) == 5
            means.append(float(selected["tfwt_bq_l_water"].mean()))
        output[blind_id] = independent_classify(
            np.asarray(means, dtype=float)
        )
    return output


@pytest.mark.parametrize("blind_id", OPAQUE_IDS)
def test_review_independent_classification_matches_committed(
    blind_id: str,
    independent_results: dict[str, tuple[str, float, float]],
) -> None:
    committed = {
        row["dataset_blind_id"]: row
        for row in read_csv(CLASSIFICATION_RESULTS_PATH)
    }[blind_id]
    result, h2_rmse, h3_rmse = independent_results[blind_id]
    assert result == committed["classification_result"]
    assert h2_rmse == pytest.approx(float(committed["h2_log10_rmse"]))
    assert h3_rmse == pytest.approx(float(committed["h3_log10_rmse"]))


def test_review_unblinding_is_three_of_three() -> None:
    comparisons = read_csv(UNBLINDING_COMPARISON_PATH)
    assert len(comparisons) == 3
    assert {row["expectation_pass"] for row in comparisons} == {"True"}
    assert UNBLINDING["status"] == "PASS_TRUE_REBLINDING"
    assert UNBLINDING["expectation_pass_count"] == 3


def test_review_frozen_scientific_contract() -> None:
    assert PROTOCOL["model_contract"]["H2_SB1_FROZEN"] == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }
    assert PROTOCOL["model_contract"]["H3_SB1_FROZEN"] == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }
    assert PROTOCOL["sampling_contract"]["classification_times_h"] == [
        0.2,
        48,
        120,
    ]
    assert (
        PROTOCOL["classifier"]["absolute_rmse_difference_inconclusive_dex"]
        == 0.15
    )
    assert PROTOCOL["classifier"]["both_model_rmse_inadequate_dex"] == 0.50


def contamination_scan(lines: list[str], opaque_ids: tuple[str, ...]) -> str:
    association = re.compile(
        r"(?:^|[^A-Z0-9_])(?:H2|H3|CHALLENGE|TRUTH_KIND|"
        r"EXPECTED_RESULT|TRUTH_MAPPING)(?:$|[^A-Z0-9_])",
        re.IGNORECASE,
    )
    for line in lines:
        if any(item in line.upper() for item in opaque_ids):
            if association.search(line):
                return "FAIL"
    return "PASS"


def test_review_attack_mapping_injection_fails() -> None:
    assert contamination_scan(
        [f"{OPAQUE_IDS[0]},H2"], OPAQUE_IDS
    ) == "FAIL"


def test_review_attack_old_dataset_hash_fails() -> None:
    old_hash = str(PROTOCOL["prior_dataset_hashes"]["v2"][0])
    allowed = {
        str(item["sha256"]) for item in GENERATION["datasets"]
    }
    assert old_hash not in allowed


def stable_seed(base: int, key: str) -> int:
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + digest) % (2**32 - 1)


def simulate(
    truth: np.ndarray, cv: float, replicates: int, label: str
) -> np.ndarray:
    sigma = math.sqrt(math.log1p(cv**2))
    mu = -0.5 * sigma**2
    rng = np.random.default_rng(
        stable_seed(2026072705, f"{replicates}:{cv:.2f}:{label}")
    )
    multiplier = rng.lognormal(
        mu, sigma, size=(1000, len(truth), replicates)
    )
    return (truth[None, :, None] * multiplier).mean(axis=2)


def classify_many(
    observed: np.ndarray, h2: np.ndarray, h3: np.ndarray
) -> np.ndarray:
    h2_rmse = np.sqrt(
        np.mean(
            (np.log10(observed) - np.log10(h2)[None, :]) ** 2,
            axis=1,
        )
    )
    h3_rmse = np.sqrt(
        np.mean(
            (np.log10(observed) - np.log10(h3)[None, :]) ** 2,
            axis=1,
        )
    )
    result = np.full(len(observed), "", dtype=object)
    close = np.abs(h2_rmse - h3_rmse) < 0.15
    result[close] = "DATA_INCONCLUSIVE"
    both_bad = ~close & (h2_rmse > 0.50) & (h3_rmse > 0.50)
    result[both_bad] = "BOTH_INADEQUATE"
    undecided = result == ""
    result[undecided & (h2_rmse < h3_rmse)] = "H2_SUPPORTED_OVER_H3"
    result[undecided & (h3_rmse <= h2_rmse)] = "H3_SUPPORTED_OVER_H2"
    return result


@pytest.fixture(scope="module")
def independent_mc() -> dict[tuple[int, float, str], np.ndarray]:
    predictions = PROTOCOL["classifier"][
        "frozen_primary_predictions_bq_l_water"
    ]
    h2 = np.asarray(predictions["H2_SB1_FROZEN"], dtype=float)
    h3 = np.asarray(predictions["H3_SB1_FROZEN"], dtype=float)
    challenge = np.sqrt(h2 * h3)
    challenge[1] *= 1.25
    result: dict[tuple[int, float, str], np.ndarray] = {}
    for replicates in (3, 4, 5, 6):
        for cv in (0.10, 0.15, 0.20, 0.25, 0.30):
            for label, vector in (
                ("H2_SB1_FROZEN", h2),
                ("H3_SB1_FROZEN", h3),
                ("SYNTHETIC_OUT_OF_MODEL_CHALLENGE", challenge),
            ):
                observed = simulate(vector, cv, replicates, label)
                result[(replicates, cv, label)] = classify_many(
                    observed, h2, h3
                )
    return result


def test_review_independent_mc_recomputes_sixty_cells(
    independent_mc: dict[tuple[int, float, str], np.ndarray],
) -> None:
    assert len(independent_mc) == 60
    assert all(len(item) == 1000 for item in independent_mc.values())


@pytest.mark.parametrize(
    ("replicates", "expected"),
    [
        (3, (0.869, 0.846, 0.067)),
        (4, (0.914, 0.877, 0.047)),
        (5, (0.937, 0.927, 0.035)),
        (6, (0.955, 0.955, 0.027)),
    ],
)
def test_review_independent_mc_cv20(
    independent_mc: dict[tuple[int, float, str], np.ndarray],
    replicates: int,
    expected: tuple[float, float, float],
) -> None:
    h2 = float(
        np.mean(
            independent_mc[(replicates, 0.20, "H2_SB1_FROZEN")]
            == "H2_SUPPORTED_OVER_H3"
        )
    )
    h3 = float(
        np.mean(
            independent_mc[(replicates, 0.20, "H3_SB1_FROZEN")]
            == "H3_SUPPORTED_OVER_H2"
        )
    )
    challenge = float(
        np.mean(
            np.isin(
                independent_mc[
                    (
                        replicates,
                        0.20,
                        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
                    )
                ],
                ["H2_SUPPORTED_OVER_H3", "H3_SUPPORTED_OVER_H2"],
            )
        )
    )
    assert (h2, h3, challenge) == pytest.approx(expected, abs=0)


def test_review_mc_confirms_default_five(
    independent_mc: dict[tuple[int, float, str], np.ndarray],
) -> None:
    passing = []
    for replicates in (3, 4, 5, 6):
        h2 = np.mean(
            independent_mc[(replicates, 0.20, "H2_SB1_FROZEN")]
            == "H2_SUPPORTED_OVER_H3"
        )
        h3 = np.mean(
            independent_mc[(replicates, 0.20, "H3_SB1_FROZEN")]
            == "H3_SUPPORTED_OVER_H2"
        )
        challenge = np.mean(
            np.isin(
                independent_mc[
                    (
                        replicates,
                        0.20,
                        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
                    )
                ],
                ["H2_SUPPORTED_OVER_H3", "H3_SUPPORTED_OVER_H2"],
            )
        )
        if h2 >= 0.90 and h3 >= 0.90 and challenge <= 0.10:
            passing.append(replicates)
    assert passing == [5, 6]
    assert PROTOCOL["sensitivity_contract"]["default_replicates"] == 5


def test_review_evidence_boundary_remains_fail_closed() -> None:
    boundary = PROTOCOL["evidence_boundary"]
    assert boundary["real_external_evidence"] is False
    assert boundary["trusted_registry_eligible"] is False
    assert boundary["production_eligible"] is False
    assert boundary["formal_v3_physics"] == "NOT_STARTED"
    assert (
        boundary["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
