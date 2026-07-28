#!/usr/bin/env python3
"""Classify committed D3 blinded datasets without reading the local truth key."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from d3_prospective_core import (  # noqa: E402
    BENCHMARK,
    CLASSIFICATION_PROTOCOL_PATH,
    LOCAL_ROOT,
    PRIMARY_TIMES,
    SYNTHETIC_STATUS,
    TRACKED_DATA_ROOT,
    classify_means,
    frozen_prediction_table,
    load_classification_protocol,
    prediction_vectors,
    sha256,
)
from generate_d3_blinded_datasets import DATASET_COLUMNS  # noqa: E402


ROOT = Path(__file__).resolve().parents[4]
RESULTS = BENCHMARK / "results"
REPORTS = BENCHMARK / "reports"
CLASSIFICATION_RESULTS_PATH = (
    RESULTS / "d3_blinded_classification_results.csv"
)
TIME_SUMMARY_PATH = RESULTS / "d3_blinded_time_summary.csv"
CLASSIFICATION_MANIFEST_PATH = RESULTS / "classification_manifest.yaml"
PREUNBLINDING_REPORT_PATH = (
    REPORTS / "blinded_classification_preunblinding.md"
)
GENERATION_MANIFEST_PATH = TRACKED_DATA_ROOT / "generation_manifest.yaml"
TRUTH_KEY_HASH_PATH = TRACKED_DATA_ROOT / "truth_key_sha256"
TRUTH_KEY_PATH = LOCAL_ROOT / "truth" / "truth_key.yaml"
RESULT_COLUMNS = (
    "dataset_blind_id",
    "classification_result",
    "h2_log10_rmse",
    "h3_log10_rmse",
    "absolute_rmse_difference_dex",
    "classifier_observable",
    "classification_times_h",
    "parameter_refit_count",
    "latent_state_used",
    "dataset_sha256",
    "protocol_sha256",
)
TIME_COLUMNS = (
    "dataset_blind_id",
    "hours_after_exposure",
    "uncensored_replicate_count",
    "mean_tfwt_bq_l_water",
    "sample_standard_deviation_bq_l_water",
    "standard_error_bq_l_water",
    "replicate_cv",
    "below_detection_limit_excluded_count",
    "non_ok_quality_excluded_count",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root", type=Path, default=TRACKED_DATA_ROOT
    )
    parser.add_argument("--results-root", type=Path, default=RESULTS)
    parser.add_argument("--reports-root", type=Path, default=REPORTS)
    return parser.parse_args()


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
        raise ValueError(f"Tracked input differs from committed HEAD: {relative}")


def assert_truth_key_not_tracked() -> None:
    relative = TRUTH_KEY_PATH.relative_to(ROOT).as_posix()
    if (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    ):
        raise ValueError("Truth key is tracked by Git")
    require_tracked_clean(TRUTH_KEY_HASH_PATH)


def validate_committed_inputs(dataset_root: Path) -> dict[str, Any]:
    require_tracked_clean(CLASSIFICATION_PROTOCOL_PATH)
    require_tracked_clean(GENERATION_MANIFEST_PATH)
    assert_truth_key_not_tracked()
    manifest = yaml.safe_load(
        GENERATION_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    if (
        manifest["truth_mapping_disclosed"]
        or manifest["real_external_evidence"]
        or manifest["trusted_registry_eligible"]
        or manifest["production_eligible"]
        or manifest["v3_physics_start_gate"]
        != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    ):
        raise ValueError("Generation manifest evidence boundary changed")
    expected = {
        str(item["dataset_blind_id"]): str(item["sha256"])
        for item in manifest["datasets"]
    }
    if set(expected) != {"A", "B", "C"}:
        raise ValueError("Generation manifest blind IDs changed")
    for blind_id, expected_hash in expected.items():
        path = dataset_root / f"dataset_{blind_id}.csv"
        require_tracked_clean(path)
        if sha256(path) != expected_hash:
            raise ValueError(f"Dataset {blind_id} checksum mismatch")
    return manifest


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"Invalid boolean value: {value}")
    return normalized == "true"


def load_blinded_dataset(path: Path, blind_id: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if tuple(frame.columns) != DATASET_COLUMNS:
        raise ValueError(f"Dataset {blind_id} columns changed")
    if set(frame["dataset_blind_id"].astype(str)) != {blind_id}:
        raise ValueError(f"Dataset {blind_id} contains a different blind ID")
    if set(frame["synthetic_status"]) != {SYNTHETIC_STATUS}:
        raise ValueError(f"Dataset {blind_id} synthetic status changed")
    if set(frame["organ"]) != {"combined_stem_and_leaf"}:
        raise ValueError(f"Dataset {blind_id} organ contract changed")
    frame["below_detection_limit"] = frame[
        "below_detection_limit"
    ].map(parse_bool)
    return frame


def aggregate_primary_times(
    frame: pd.DataFrame,
    blind_id: str,
    protocol: dict[str, Any],
) -> tuple[np.ndarray | None, list[dict[str, Any]]]:
    minimum = int(
        protocol["sampling_contract"][
            "minimum_uncensored_replicates_per_time"
        ]
    )
    accepted_flag = protocol["quality_control_contract"][
        "accepted_quality_flag"
    ]
    means: list[float] = []
    rows: list[dict[str, Any]] = []
    for hour in PRIMARY_TIMES:
        selected = frame[np.isclose(frame["hours_after_exposure"], hour)]
        non_ok = int((selected["quality_flag"] != accepted_flag).sum())
        accepted = selected[selected["quality_flag"] == accepted_flag]
        below = int(accepted["below_detection_limit"].sum())
        accepted = accepted[~accepted["below_detection_limit"]]
        values = accepted["tfwt_bq_l_water"].to_numpy(float)
        if len(values) < minimum:
            rows.append(
                {
                    "dataset_blind_id": blind_id,
                    "hours_after_exposure": hour,
                    "uncensored_replicate_count": len(values),
                    "mean_tfwt_bq_l_water": "",
                    "sample_standard_deviation_bq_l_water": "",
                    "standard_error_bq_l_water": "",
                    "replicate_cv": "",
                    "below_detection_limit_excluded_count": below,
                    "non_ok_quality_excluded_count": non_ok,
                }
            )
            return None, rows
        mean = float(values.mean())
        standard_deviation = float(values.std(ddof=1))
        means.append(mean)
        rows.append(
            {
                "dataset_blind_id": blind_id,
                "hours_after_exposure": hour,
                "uncensored_replicate_count": len(values),
                "mean_tfwt_bq_l_water": mean,
                "sample_standard_deviation_bq_l_water": standard_deviation,
                "standard_error_bq_l_water": (
                    standard_deviation / np.sqrt(len(values))
                ),
                "replicate_cv": standard_deviation / mean,
                "below_detection_limit_excluded_count": below,
                "non_ok_quality_excluded_count": non_ok,
            }
        )
    return np.asarray(means, dtype=float), rows


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


def render_preunblinding_report(
    results: list[dict[str, Any]],
    output_path: Path,
    result_hash: str,
) -> None:
    lines = [
        "# D3 blinded classification pre-unblinding result",
        "",
        "```text",
        "EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN",
        "REAL_EXTERNAL_EVIDENCE = FALSE",
        "PARAMETER_REFIT_COUNT = 0",
        "LATENT_STATE_USED = FALSE",
        "TRUTH_KEY_ACCESSED = FALSE",
        "V3_PHYSICS_START_GATE =",
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "```",
        "",
        "| blind dataset | result | H2 RMSE | H3 RMSE | absolute difference |",
        "|---|---|---:|---:|---:|",
    ]
    for row in results:
        lines.append(
            f'| {row["dataset_blind_id"]} | '
            f'{row["classification_result"]} | '
            f'{float(row["h2_log10_rmse"]):.6f} | '
            f'{float(row["h3_log10_rmse"]):.6f} | '
            f'{float(row["absolute_rmse_difference_dex"]):.6f} |'
        )
    lines.extend(
        [
            "",
            f"`classification_result_sha256 = {result_hash}`",
            "",
            "This report was generated without opening or parsing the local truth key.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_classification(
    dataset_root: Path,
    results_root: Path,
    reports_root: Path,
) -> dict[str, Any]:
    manifest = validate_committed_inputs(dataset_root)
    protocol = load_classification_protocol()
    prediction_table, _ = frozen_prediction_table()
    _, h2, h3 = prediction_vectors(prediction_table, PRIMARY_TIMES)
    result_rows: list[dict[str, Any]] = []
    time_rows: list[dict[str, Any]] = []
    for blind_id in ("A", "B", "C"):
        path = dataset_root / f"dataset_{blind_id}.csv"
        frame = load_blinded_dataset(path, blind_id)
        means, current_time_rows = aggregate_primary_times(
            frame, blind_id, protocol
        )
        time_rows.extend(current_time_rows)
        if means is None:
            result = "DATA_INCONCLUSIVE"
            h2_rmse = float("nan")
            h3_rmse = float("nan")
        else:
            result, h2_rmse, h3_rmse = classify_means(
                means, h2, h3, protocol
            )
        result_rows.append(
            {
                "dataset_blind_id": blind_id,
                "classification_result": result,
                "h2_log10_rmse": h2_rmse,
                "h3_log10_rmse": h3_rmse,
                "absolute_rmse_difference_dex": abs(h2_rmse - h3_rmse),
                "classifier_observable": "total plant-body TFWT",
                "classification_times_h": "0.2;48;120",
                "parameter_refit_count": 0,
                "latent_state_used": False,
                "dataset_sha256": sha256(path),
                "protocol_sha256": sha256(CLASSIFICATION_PROTOCOL_PATH),
            }
        )

    result_path = results_root / CLASSIFICATION_RESULTS_PATH.name
    time_path = results_root / TIME_SUMMARY_PATH.name
    report_path = reports_root / PREUNBLINDING_REPORT_PATH.name
    manifest_path = results_root / CLASSIFICATION_MANIFEST_PATH.name
    write_csv(result_path, RESULT_COLUMNS, result_rows)
    write_csv(time_path, TIME_COLUMNS, time_rows)
    result_hash = sha256(result_path)
    render_preunblinding_report(result_rows, report_path, result_hash)
    classification_manifest = {
        "manifest_id": "D3_BLINDED_CLASSIFICATION_EXECUTION_V2",
        "status": "COMPLETED_PREUNBLINDING",
        "truth_key_accessed": False,
        "truth_mapping_disclosed": False,
        "parameter_refit_count": 0,
        "latent_state_used": False,
        "classifier_observable": "total plant-body TFWT",
        "classification_times_h": [0.2, 48, 120],
        "classification_result_sha256": result_hash,
        "time_summary_sha256": sha256(time_path),
        "preunblinding_report_sha256": sha256(report_path),
        "generation_manifest_sha256": sha256(GENERATION_MANIFEST_PATH),
        "truth_key_sha256_record_sha256": sha256(TRUTH_KEY_HASH_PATH),
        "protocol_sha256": sha256(CLASSIFICATION_PROTOCOL_PATH),
        "allowed_results": protocol["classifier"]["allowed_results"],
        "real_external_evidence": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(classification_manifest, sort_keys=False),
        encoding="utf-8",
    )
    return classification_manifest


def main() -> int:
    args = parse_args()
    manifest = run_classification(
        args.dataset_root, args.results_root, args.reports_root
    )
    print(
        "BLINDED_CLASSIFICATION_STATUS = "
        f'{manifest["status"]}; '
        f'TRUTH_KEY_ACCESSED = {manifest["truth_key_accessed"]}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
