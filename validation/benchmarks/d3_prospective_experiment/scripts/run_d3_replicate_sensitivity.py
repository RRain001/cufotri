#!/usr/bin/env python3
"""Run preregistered replicate-count and noise sensitivity for D3."""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_prospective_core import (  # noqa: E402
    BENCHMARK,
    CLASSIFICATION_PROTOCOL_PATH,
    PRIMARY_TIMES,
    frozen_prediction_table,
    load_classification_protocol,
    prediction_vectors,
)
from generate_d3_prospective_forcing import (  # noqa: E402
    ASSUMPTIONS_PATH,
    assumption_value,
    load_assumptions,
)


ROOT = Path(__file__).resolve().parents[4]
RESULTS = BENCHMARK / "results"
REPORT = BENCHMARK / "reports" / "replicate_noise_tradeoff_report.md"
TRADEOFF_PATH = RESULTS / "replicate_noise_tradeoff.csv"
ACCURACY_PATH = RESULTS / "classification_accuracy_by_replicate_count.csv"
INCONCLUSIVE_PATH = RESULTS / "inconclusive_rate.csv"
TRADEOFF_COLUMNS = (
    "biological_replicates",
    "total_cv",
    "truth_kind",
    "monte_carlo_replicates",
    "correct_classification_rate",
    "inconclusive_rate",
    "both_inadequate_rate",
    "h2_selection_rate",
    "h3_selection_rate",
    "parameter_refit_count",
)
ACCURACY_COLUMNS = (
    "biological_replicates",
    "total_cv",
    "h2_truth_correct_rate",
    "h3_truth_correct_rate",
    "minimum_truth_correct_rate",
    "cv20_target_pass",
)
INCONCLUSIVE_COLUMNS = (
    "biological_replicates",
    "total_cv",
    "h2_truth_inconclusive_rate",
    "h3_truth_inconclusive_rate",
    "challenge_inconclusive_rate",
    "challenge_false_confident_rate",
    "challenge_target_pass",
)


def require_tracked_clean(path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if (
        subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=ROOT,
            check=False,
        ).returncode
        != 0
    ):
        raise ValueError(f"Frozen sensitivity input changed: {relative}")


def stable_seed(base: int, key: str) -> int:
    digest = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)
    return (base + digest) % (2**32 - 1)


def simulated_means(
    truth: np.ndarray,
    *,
    cv: float,
    replicates: int,
    experiments: int,
    seed: int,
) -> np.ndarray:
    sigma = math.sqrt(math.log1p(cv**2))
    mu = -0.5 * sigma**2
    rng = np.random.default_rng(seed)
    multiplier = rng.lognormal(
        mu, sigma, size=(experiments, len(truth), replicates)
    )
    return (truth[None, :, None] * multiplier).mean(axis=2)


def classify_matrix(
    observed: np.ndarray,
    h2: np.ndarray,
    h3: np.ndarray,
    protocol: dict[str, Any],
) -> np.ndarray:
    h2_rmse = np.sqrt(
        np.mean(
            (np.log10(observed) - np.log10(h2)[None, :]) ** 2, axis=1
        )
    )
    h3_rmse = np.sqrt(
        np.mean(
            (np.log10(observed) - np.log10(h3)[None, :]) ** 2, axis=1
        )
    )
    inconclusive = float(
        protocol["classifier"][
            "absolute_rmse_difference_inconclusive_dex"
        ]["value"]
    )
    inadequate = float(
        protocol["classifier"]["both_model_rmse_inadequate_dex"]["value"]
    )
    result = np.full(len(observed), "", dtype=object)
    close = np.abs(h2_rmse - h3_rmse) < inconclusive
    result[close] = "DATA_INCONCLUSIVE"
    both_bad = (
        ~close
        & (h2_rmse > inadequate)
        & (h3_rmse > inadequate)
    )
    result[both_bad] = "BOTH_INADEQUATE"
    undecided = result == ""
    result[undecided & (h2_rmse < h3_rmse)] = "H2_SUPPORTED_OVER_H3"
    result[undecided & (h3_rmse <= h2_rmse)] = "H3_SUPPORTED_OVER_H2"
    return result


def rate(result: np.ndarray, label: str) -> float:
    return float(np.mean(result == label))


def write_csv(
    path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def render_report(
    accuracy_rows: list[dict[str, Any]],
    inconclusive_rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    cv20 = [
        row for row in accuracy_rows if math.isclose(row["total_cv"], 0.20)
    ]
    challenge_cv20 = {
        row["biological_replicates"]: row
        for row in inconclusive_rows
        if math.isclose(row["total_cv"], 0.20)
    }
    passing = [
        row["biological_replicates"]
        for row in cv20
        if row["cv20_target_pass"]
        and challenge_cv20[row["biological_replicates"]][
            "challenge_target_pass"
        ]
    ]
    lines = [
        "# D3 replicate and uncertainty sensitivity report",
        "",
        "Each cell contains 1,000 synthetic experiments. Replicate means are",
        "classified against the two frozen predictions with the preregistered",
        "0.15/0.50 dex fail-closed thresholds. No parameter is fitted.",
        "",
        "```text",
        "EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN",
        "PARAMETER_REFIT_COUNT = 0",
        f"CV20_PASSING_REPLICATE_COUNTS = {passing or 'NONE'}",
        "DEFAULT_PLANNING_REPLICATES = 5",
        "DEFAULT_IS_STATISTICAL_POWER_PROOF = FALSE",
        "V3_PHYSICS_START_GATE =",
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "```",
        "",
        "## CV20 decision table",
        "",
        "| replicates | H2 correct | H3 correct | challenge false confident | combined target |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in cv20:
        challenge = challenge_cv20[row["biological_replicates"]]
        combined = bool(
            row["cv20_target_pass"] and challenge["challenge_target_pass"]
        )
        lines.append(
            f'| {row["biological_replicates"]} | '
            f'{row["h2_truth_correct_rate"]:.3f} | '
            f'{row["h3_truth_correct_rate"]:.3f} | '
            f'{challenge["challenge_false_confident_rate"]:.3f} | '
            f'{"PASS" if combined else "FAIL"} |'
        )
    lines.extend(
        [
            "",
            "Five replicates remain the operational planning default for sample-loss",
            "and anomaly resistance, but the dry-run Monte Carlo result determines",
            "whether that default satisfies the frozen classification target.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    require_tracked_clean(CLASSIFICATION_PROTOCOL_PATH)
    require_tracked_clean(ASSUMPTIONS_PATH)
    protocol = load_classification_protocol()
    assumptions = load_assumptions(require_committed=True)
    sensitivity = protocol["sensitivity_contract"]
    replicate_counts = [int(value) for value in sensitivity["replicate_counts"]]
    cvs = [float(value) for value in sensitivity["total_cv"]]
    experiments = int(sensitivity["monte_carlo_replicates_per_cell"])
    base_seed = int(
        assumption_value(
            assumptions["random_seeds"], "replicate_sensitivity_seed"
        )
    )
    prediction_table, _ = frozen_prediction_table()
    _, h2, h3 = prediction_vectors(prediction_table, PRIMARY_TIMES)
    challenge = np.sqrt(h2 * h3)
    challenge_time = float(
        protocol["challenge_contract"]["systematic_deviation_time_h"]["value"]
    )
    challenge_factor = float(
        protocol["challenge_contract"]["systematic_deviation_factor"]["value"]
    )
    challenge[int(np.where(np.isclose(PRIMARY_TIMES, challenge_time))[0][0])] *= (
        challenge_factor
    )
    truths = {
        "H2_SB1_FROZEN": (h2, "H2_SUPPORTED_OVER_H3"),
        "H3_SB1_FROZEN": (h3, "H3_SUPPORTED_OVER_H2"),
        "SYNTHETIC_OUT_OF_MODEL_CHALLENGE": (
            challenge,
            "DATA_INCONCLUSIVE",
        ),
    }
    tradeoff_rows: list[dict[str, Any]] = []
    result_cache: dict[tuple[int, float, str], np.ndarray] = {}
    for replicates in replicate_counts:
        for cv in cvs:
            for truth_kind, (truth, expected) in truths.items():
                observations = simulated_means(
                    truth,
                    cv=cv,
                    replicates=replicates,
                    experiments=experiments,
                    seed=stable_seed(
                        base_seed, f"{replicates}:{cv:.2f}:{truth_kind}"
                    ),
                )
                result = classify_matrix(observations, h2, h3, protocol)
                result_cache[(replicates, cv, truth_kind)] = result
                tradeoff_rows.append(
                    {
                        "biological_replicates": replicates,
                        "total_cv": cv,
                        "truth_kind": truth_kind,
                        "monte_carlo_replicates": experiments,
                        "correct_classification_rate": rate(result, expected),
                        "inconclusive_rate": rate(
                            result, "DATA_INCONCLUSIVE"
                        ),
                        "both_inadequate_rate": rate(
                            result, "BOTH_INADEQUATE"
                        ),
                        "h2_selection_rate": rate(
                            result, "H2_SUPPORTED_OVER_H3"
                        ),
                        "h3_selection_rate": rate(
                            result, "H3_SUPPORTED_OVER_H2"
                        ),
                        "parameter_refit_count": 0,
                    }
                )
    accuracy_rows: list[dict[str, Any]] = []
    inconclusive_rows: list[dict[str, Any]] = []
    h2_target = float(sensitivity["h2_truth_correct_minimum_at_cv20"])
    h3_target = float(sensitivity["h3_truth_correct_minimum_at_cv20"])
    challenge_target = float(
        sensitivity["challenge_false_confident_maximum"]
    )
    for replicates in replicate_counts:
        for cv in cvs:
            h2_result = result_cache[(replicates, cv, "H2_SB1_FROZEN")]
            h3_result = result_cache[(replicates, cv, "H3_SB1_FROZEN")]
            challenge_result = result_cache[
                (
                    replicates,
                    cv,
                    "SYNTHETIC_OUT_OF_MODEL_CHALLENGE",
                )
            ]
            h2_correct = rate(h2_result, "H2_SUPPORTED_OVER_H3")
            h3_correct = rate(h3_result, "H3_SUPPORTED_OVER_H2")
            challenge_false = float(
                np.mean(
                    np.isin(
                        challenge_result,
                        [
                            "H2_SUPPORTED_OVER_H3",
                            "H3_SUPPORTED_OVER_H2",
                        ],
                    )
                )
            )
            accuracy_rows.append(
                {
                    "biological_replicates": replicates,
                    "total_cv": cv,
                    "h2_truth_correct_rate": h2_correct,
                    "h3_truth_correct_rate": h3_correct,
                    "minimum_truth_correct_rate": min(
                        h2_correct, h3_correct
                    ),
                    "cv20_target_pass": bool(
                        not math.isclose(cv, 0.20)
                        or (
                            h2_correct >= h2_target
                            and h3_correct >= h3_target
                        )
                    ),
                }
            )
            inconclusive_rows.append(
                {
                    "biological_replicates": replicates,
                    "total_cv": cv,
                    "h2_truth_inconclusive_rate": rate(
                        h2_result, "DATA_INCONCLUSIVE"
                    ),
                    "h3_truth_inconclusive_rate": rate(
                        h3_result, "DATA_INCONCLUSIVE"
                    ),
                    "challenge_inconclusive_rate": rate(
                        challenge_result, "DATA_INCONCLUSIVE"
                    ),
                    "challenge_false_confident_rate": challenge_false,
                    "challenge_target_pass": bool(
                        challenge_false <= challenge_target
                    ),
                }
            )
    write_csv(TRADEOFF_PATH, TRADEOFF_COLUMNS, tradeoff_rows)
    write_csv(ACCURACY_PATH, ACCURACY_COLUMNS, accuracy_rows)
    write_csv(INCONCLUSIVE_PATH, INCONCLUSIVE_COLUMNS, inconclusive_rows)
    render_report(accuracy_rows, inconclusive_rows, REPORT)
    print(
        "REPLICATE_SENSITIVITY_STATUS = COMPLETED; "
        f"CELLS = {len(tradeoff_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
