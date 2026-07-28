#!/usr/bin/env python3
"""Compare committed blinded results with the local synthetic truth key."""

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
LOCAL_ROOT = (
    ROOT / "validation" / "external_local" / "d3_prospective_experiment"
)
RESULT_PATH = BENCHMARK / "results" / "d3_blinded_classification_results.csv"
TRUTH_KEY_PATH = LOCAL_ROOT / "truth" / "truth_key.yaml"
TRUTH_HASH_PATH = LOCAL_ROOT / "truth_key_sha256"
COMPARISON_PATH = BENCHMARK / "results" / "unblinding_comparison.csv"
MANIFEST_PATH = BENCHMARK / "results" / "unblinding_manifest.yaml"
REPORT_PATH = BENCHMARK / "reports" / "blinded_classification_report.md"
COMPARISON_COLUMNS = (
    "dataset_blind_id",
    "truth_kind",
    "expected_result",
    "actual_result",
    "expectation_pass",
    "h2_log10_rmse",
    "h3_log10_rmse",
    "absolute_rmse_difference_dex",
)


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        raise ValueError(f"Tracked classification input changed: {relative}")


def load_verified_truth() -> dict[str, Any]:
    if (
        subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                TRUTH_KEY_PATH.relative_to(ROOT).as_posix(),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        ).returncode
        == 0
    ):
        raise ValueError("Truth key must not be tracked")
    require_tracked_clean(TRUTH_HASH_PATH)
    recorded = TRUTH_HASH_PATH.read_text(encoding="utf-8").strip()
    if sha256(TRUTH_KEY_PATH) != recorded:
        raise ValueError("Truth-key SHA-256 mismatch")
    truth = yaml.safe_load(TRUTH_KEY_PATH.read_text(encoding="utf-8"))
    if truth["tracked"] is not False:
        raise ValueError("Truth key tracking boundary changed")
    return truth


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=COMPARISON_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def render_report(rows: list[dict[str, Any]], output_path: Path) -> None:
    passed = sum(bool(row["expectation_pass"]) for row in rows)
    lines = [
        "# D3 blinded synthetic classification and unblinding report",
        "",
        "```text",
        "EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN",
        "REAL_EXTERNAL_EVIDENCE = FALSE",
        "EMPIRICAL_VALIDATION_CLAIM = FALSE",
        "PARAMETER_REFIT_COUNT = 0",
        "TRUTH_KEY_HASH_VERIFIED = TRUE",
        f"EXPECTED_CLASSIFICATION_PASS_COUNT = {passed}_OF_{len(rows)}",
        "V3_PHYSICS_START_GATE =",
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "```",
        "",
        "| blind ID | truth | expected | actual | check | H2 RMSE | H3 RMSE | difference |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f'| {row["dataset_blind_id"]} | {row["truth_kind"]} | '
            f'{row["expected_result"]} | {row["actual_result"]} | '
            f'{"PASS" if row["expectation_pass"] else "FAIL"} | '
            f'{float(row["h2_log10_rmse"]):.6f} | '
            f'{float(row["h3_log10_rmse"]):.6f} | '
            f'{float(row["absolute_rmse_difference_dex"]):.6f} |'
        )
    lines.extend(
        [
            "",
            "Dataset C confirms that the classifier does not force a binary model",
            "choice. Datasets A and B do not meet their expected selections because",
            "their realized absolute RMSE differences are below the preregistered",
            "0.15 dex threshold. The frozen threshold, aggregation, seeds, and data",
            "were not changed after unblinding.",
            "",
            "The dry run therefore fails its H2/H3 positive-control classification",
            "objective while passing its out-of-model fail-closed objective. It cannot",
            "authorize formal H2/H3 selection, trusted-registry promotion, empirical",
            "validation, or V3 physics.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    require_tracked_clean(RESULT_PATH)
    truth = load_verified_truth()
    with RESULT_PATH.open(encoding="utf-8", newline="") as stream:
        results = {
            row["dataset_blind_id"]: row for row in csv.DictReader(stream)
        }
    rows: list[dict[str, Any]] = []
    for item in truth["datasets"]:
        blind_id = str(item["dataset_blind_id"])
        result = results[blind_id]
        actual = result["classification_result"]
        expected = str(item["expected_result"])
        rows.append(
            {
                "dataset_blind_id": blind_id,
                "truth_kind": item["truth_kind"],
                "expected_result": expected,
                "actual_result": actual,
                "expectation_pass": actual == expected,
                "h2_log10_rmse": result["h2_log10_rmse"],
                "h3_log10_rmse": result["h3_log10_rmse"],
                "absolute_rmse_difference_dex": result[
                    "absolute_rmse_difference_dex"
                ],
            }
        )
    write_csv(COMPARISON_PATH, rows)
    render_report(rows, REPORT_PATH)
    passed = sum(bool(row["expectation_pass"]) for row in rows)
    manifest = {
        "manifest_id": "D3_SYNTHETIC_UNBLINDING_V1",
        "status": (
            "PASS_ALL_EXPECTATIONS"
            if passed == len(rows)
            else "FAIL_POSITIVE_CONTROL_CLASSIFICATION"
        ),
        "truth_key_hash_verified": True,
        "truth_key_git_tracked": False,
        "classification_result_commit": subprocess.run(
            [
                "git",
                "log",
                "-1",
                "--format=%H",
                "--",
                RESULT_PATH.relative_to(ROOT).as_posix(),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "expectation_pass_count": passed,
        "expectation_total_count": len(rows),
        "comparison_sha256": sha256(COMPARISON_PATH),
        "report_sha256": sha256(REPORT_PATH),
        "parameter_refit_count": 0,
        "real_external_evidence": False,
        "trusted_registry_eligible": False,
        "production_eligible": False,
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
    }
    MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    print(
        f'UNBLINDING_STATUS = {manifest["status"]}; '
        f"EXPECTATIONS = {passed}/{len(rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
