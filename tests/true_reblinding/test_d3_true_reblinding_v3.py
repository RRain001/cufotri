from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = (
    ROOT
    / "validation"
    / "benchmarks"
    / "d3_prospective_experiment"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

import classify_d3_true_reblinding_v3 as classifier  # noqa: E402
import d3_true_reblinding_v3_common as common  # noqa: E402
import generate_d3_true_reblinding_v3 as generator  # noqa: E402


PROTOCOL = common.load_protocol(require_clean=True)
GENERATION = common.load_generation_manifest(require_clean=True)
CLASSIFICATION = yaml.safe_load(
    common.CLASSIFICATION_MANIFEST_PATH.read_text(encoding="utf-8")
)
UNBLINDING = yaml.safe_load(
    common.UNBLINDING_MANIFEST_PATH.read_text(encoding="utf-8")
)
OPAQUE_IDS = tuple(
    sorted(str(item["dataset_blind_id"]) for item in GENERATION["datasets"])
)
PRECLASSIFICATION_COMMIT = str(CLASSIFICATION["preclassification_commit"])
CLASSIFICATION_COMMIT = str(UNBLINDING["classification_commit"])


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def git_show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}").stdout


def classification_rows() -> dict[str, dict[str, str]]:
    with common.CLASSIFICATION_RESULTS_PATH.open(
        encoding="utf-8", newline=""
    ) as stream:
        return {
            str(row["dataset_blind_id"]): dict(row)
            for row in csv.DictReader(stream)
        }


def test_old_abc_ids_not_reused() -> None:
    assert len(OPAQUE_IDS) == 3
    assert not (set(OPAQUE_IDS) & {"A", "B", "C"})
    assert all(common.OPAQUE_ID_PATTERN.fullmatch(item) for item in OPAQUE_IDS)


def test_new_dataset_hashes_differ_from_v1_v2() -> None:
    prior = {
        str(item)
        for group in PROTOCOL["prior_dataset_hashes"].values()
        for item in group
    }
    current = {str(item["sha256"]) for item in GENERATION["datasets"]}
    assert len(current) == 3
    assert current.isdisjoint(prior)


def test_generation_secret_not_tracked() -> None:
    for path in (common.SECRET_PATH, common.TRUTH_KEY_PATH):
        relative = path.relative_to(ROOT).as_posix()
        assert (
            git("ls-files", "--error-unmatch", relative, check=False).returncode
            != 0
        )
        assert git("check-ignore", "--quiet", relative, check=False).returncode == 0


@pytest.mark.private_reblinding_secret
def test_generation_secret_commitment_matches_when_available() -> None:
    if not common.SECRET_PATH.exists():
        pytest.skip("Private secret intentionally absent in this worktree")
    commitment = common.SECRET_COMMITMENT_PATH.read_text(
        encoding="utf-8"
    ).strip()
    assert common.sha256(common.SECRET_PATH) == commitment
    assert UNBLINDING["sealed_generation_secret_sha256_verified"] is True


def test_classifier_tree_contains_no_private_secret() -> None:
    tracked = git(
        "ls-tree",
        "-r",
        "--name-only",
        CLASSIFICATION_COMMIT,
        "validation/external_local/d3_prospective_reblind_v3",
    ).stdout
    assert tracked == ""


def test_preclassification_tree_contains_no_new_truth_mapping() -> None:
    association = re.compile(
        r"(truth_class|expected_result|truth_mapping|"
        r"SYNTHETIC_OUT_OF_MODEL_CHALLENGE)",
        re.IGNORECASE,
    )
    for blind_id in OPAQUE_IDS:
        matches = git(
            "grep",
            "-n",
            blind_id,
            PRECLASSIFICATION_COMMIT,
            "--",
            ".",
        ).stdout.splitlines()
        assert matches
        assert not any(association.search(line) for line in matches)


def test_classification_commit_contains_no_new_truth_mapping() -> None:
    paths = git(
        "ls-tree",
        "-r",
        "--name-only",
        CLASSIFICATION_COMMIT,
        "validation/benchmarks/d3_prospective_experiment/reblinding_v3",
    ).stdout.splitlines()
    assert not any("/unblinding/" in path for path in paths)
    for blind_id in OPAQUE_IDS:
        matches = git(
            "grep",
            "-n",
            blind_id,
            CLASSIFICATION_COMMIT,
            "--",
            "validation/benchmarks/d3_prospective_experiment/reblinding_v3",
        ).stdout
        assert "truth_class" not in matches
        assert "expected_result" not in matches
        assert "SYNTHETIC_OUT_OF_MODEL_CHALLENGE" not in matches


def test_classification_precedes_unblinding() -> None:
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
    assert len({PRECLASSIFICATION_COMMIT, CLASSIFICATION_COMMIT}) == 2


def test_only_one_v3_realization_was_generated() -> None:
    commits = git(
        "log",
        "--format=%H",
        "--",
        "validation/benchmarks/d3_prospective_experiment/reblinding_v3/blinded",
    ).stdout.splitlines()
    assert commits == [PRECLASSIFICATION_COMMIT]
    assert GENERATION["generation_attempt"] == 1
    assert GENERATION["maximum_generation_attempts"] == 1


def test_no_regeneration_after_classification_result() -> None:
    with pytest.raises(FileExistsError, match="regeneration is prohibited"):
        generator.create_secret()


def test_no_retry_until_expected_result() -> None:
    assert CLASSIFICATION["classification_attempt"] == 1
    assert CLASSIFICATION["retry_permitted"] is False
    assert UNBLINDING["regeneration_or_retry_permitted"] is False
    with pytest.raises(FileExistsError, match="retry is prohibited"):
        classifier.run_classification()


def test_classifier_does_not_read_external_local_truth() -> None:
    source = Path(classifier.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "SECRET_PATH",
        "TRUTH_KEY_PATH",
        "mapping_from_secret",
        "truth_class",
    ):
        assert forbidden not in source


def test_classifier_uses_primary_times_only() -> None:
    assert PROTOCOL["sampling_contract"]["classification_times_h"] == [
        0.2,
        48,
        120,
    ]
    assert not PROTOCOL["sampling_contract"][
        "diagnostic_times_allowed_for_classification"
    ]
    for row in classification_rows().values():
        assert row["classification_times_h"] == "0.2;48;120"
        assert row["classifier_observable"] == "total plant-body TFWT"
        assert row["latent_state_used"] == "False"


def test_h2_h3_parameters_unchanged() -> None:
    assert PROTOCOL["model_contract"]["H2_SB1_FROZEN"] == {
        "slow_capture_fraction": 0.001,
        "slow_release_rate_s": 1.0e-6,
    }
    assert PROTOCOL["model_contract"]["H3_SB1_FROZEN"] == {
        "fast_to_slow_rate_s": 1.0e-7,
        "slow_to_fast_rate_s": 1.0e-6,
    }
    assert PROTOCOL["model_contract"]["parameter_refit"] is False


def test_thresholds_unchanged() -> None:
    assert (
        PROTOCOL["classifier"]["absolute_rmse_difference_inconclusive_dex"]
        == 0.15
    )
    assert PROTOCOL["classifier"]["both_model_rmse_inadequate_dex"] == 0.50


def test_forcing_contract_unchanged() -> None:
    forcing = PROTOCOL["forcing_contract"]
    assert forcing == {
        "exposure_duration_h": 24,
        "exposure_setpoint_bq_ml_water": 5270,
        "exposure_cv": 0.05,
        "post_exposure_background_positive": True,
        "post_exposure_background_mean_fraction": 0.0025,
        "post_exposure_background_maximum_fraction": 0.005,
    }
    assert (
        GENERATION["forcing_sha256"]
        == PROTOCOL["source_contract"]["measured_forcing_sha256"]
    )


def test_v1_v2_failure_history_preserved() -> None:
    required = (
        ROOT
        / "validation"
        / "benchmarks"
        / "d3_prospective_experiment"
        / "results"
        / "archive"
        / "v1_blinded_classification_results.csv",
        ROOT
        / "validation"
        / "benchmarks"
        / "d3_prospective_experiment"
        / "results"
        / "unblinding_comparison.csv",
        ROOT
        / "docs"
        / "v3"
        / "experiments"
        / "d3_v2_blinding_failure_and_reblinding_protocol.md",
    )
    assert all(path.is_file() for path in required)


def test_v3_unblinding_passes_three_of_three() -> None:
    assert UNBLINDING["status"] == "PASS_TRUE_REBLINDING"
    assert UNBLINDING["expectation_pass_count"] == 3
    assert UNBLINDING["expectation_total_count"] == 3


def test_attack_new_id_truth_association_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attacked = tmp_path / "contamination.csv"
    attacked.write_text(f"{OPAQUE_IDS[0]},H2\n", encoding="utf-8")
    monkeypatch.setattr(common, "repository_scan_paths", lambda: [attacked])
    hashes = {
        str(item["dataset_blind_id"]): str(item["sha256"])
        for item in GENERATION["datasets"]
    }
    assert (
        common.scan_for_new_truth_associations(list(OPAQUE_IDS), hashes)[
            "status"
        ]
        == "FAIL"
    )


def test_attack_old_dataset_replacement_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attacked = copy.deepcopy(GENERATION)
    old_hash = str(PROTOCOL["prior_dataset_hashes"]["v2"][0])
    attacked["datasets"][0]["sha256"] = old_hash
    attacked_path = ROOT / str(attacked["datasets"][0]["path"])
    original_sha256 = common.sha256

    def attacked_sha256(path: Path) -> str:
        if path == attacked_path:
            return old_hash
        return original_sha256(path)

    monkeypatch.setattr(common, "sha256", attacked_sha256)
    with pytest.raises(ValueError, match="reused a V1/V2 realization"):
        common.validate_dataset_hashes(
            PROTOCOL, attacked, require_clean=False
        )


def stable_seed(base: int, key: str) -> int:
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + digest) % (2**32 - 1)


def simulate_means(
    vector: np.ndarray,
    *,
    cv: float,
    replicates: int,
    experiments: int,
    seed: int,
) -> np.ndarray:
    sigma = math.sqrt(math.log1p(cv**2))
    mu = -0.5 * sigma**2
    rng = np.random.default_rng(seed)
    multipliers = rng.lognormal(
        mu, sigma, size=(experiments, len(vector), replicates)
    )
    return (vector[None, :, None] * multipliers).mean(axis=2)


def classify_matrix(
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
def independent_monte_carlo() -> dict[
    tuple[int, float, str], np.ndarray
]:
    predictions = PROTOCOL["classifier"][
        "frozen_primary_predictions_bq_l_water"
    ]
    h2 = np.asarray(predictions["H2_SB1_FROZEN"], dtype=float)
    h3 = np.asarray(predictions["H3_SB1_FROZEN"], dtype=float)
    challenge = np.sqrt(h2 * h3)
    challenge[1] *= 1.25
    base_seed = 2026072705
    output: dict[tuple[int, float, str], np.ndarray] = {}
    for replicates in (3, 4, 5, 6):
        for cv in (0.10, 0.15, 0.20, 0.25, 0.30):
            for label, vector in (
                ("H2_SB1_FROZEN", h2),
                ("H3_SB1_FROZEN", h3),
                ("SYNTHETIC_OUT_OF_MODEL_CHALLENGE", challenge),
            ):
                observed = simulate_means(
                    vector,
                    cv=cv,
                    replicates=replicates,
                    experiments=1000,
                    seed=stable_seed(
                        base_seed, f"{replicates}:{cv:.2f}:{label}"
                    ),
                )
                output[(replicates, cv, label)] = classify_matrix(
                    observed, h2, h3
                )
    return output


@pytest.fixture(scope="module")
def independent_cv20(
    independent_monte_carlo: dict[
        tuple[int, float, str], np.ndarray
    ],
) -> dict[int, tuple[float, float, float]]:
    output: dict[int, tuple[float, float, float]] = {}
    for replicates in (3, 4, 5, 6):
        h2_rate = float(
            np.mean(
                independent_monte_carlo[
                    (replicates, 0.20, "H2_SB1_FROZEN")
                ]
                == "H2_SUPPORTED_OVER_H3"
            )
        )
        h3_rate = float(
            np.mean(
                independent_monte_carlo[
                    (replicates, 0.20, "H3_SB1_FROZEN")
                ]
                == "H3_SUPPORTED_OVER_H2"
            )
        )
        challenge_false = float(
            np.mean(
                np.isin(
                    independent_monte_carlo[
                        (
                            replicates,
                            0.20,
                            "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
                        )
                    ],
                    [
                        "H2_SUPPORTED_OVER_H3",
                        "H3_SUPPORTED_OVER_H2",
                    ],
                )
            )
        )
        output[replicates] = (h2_rate, h3_rate, challenge_false)
    return output


def test_independent_mc_recomputes_all_sixty_cells(
    independent_monte_carlo: dict[
        tuple[int, float, str], np.ndarray
    ],
) -> None:
    assert len(independent_monte_carlo) == 60
    assert all(len(result) == 1000 for result in independent_monte_carlo.values())


@pytest.mark.parametrize(
    ("replicates", "expected"),
    [
        (3, (0.869, 0.846, 0.067)),
        (4, (0.914, 0.877, 0.047)),
        (5, (0.937, 0.927, 0.035)),
        (6, (0.955, 0.955, 0.027)),
    ],
)
def test_independent_mc_cv20_reproduces_frozen_values(
    independent_cv20: dict[int, tuple[float, float, float]],
    replicates: int,
    expected: tuple[float, float, float],
) -> None:
    assert independent_cv20[replicates] == pytest.approx(expected, abs=0)


def test_independent_mc_confirms_default_five(
    independent_cv20: dict[int, tuple[float, float, float]],
) -> None:
    passing = [
        replicates
        for replicates, (h2, h3, challenge) in independent_cv20.items()
        if h2 >= 0.90 and h3 >= 0.90 and challenge <= 0.10
    ]
    assert passing == [5, 6]
    assert PROTOCOL["sensitivity_contract"]["default_replicates"] == 5
