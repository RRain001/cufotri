#!/usr/bin/env python3
"""Exercise a fail-closed intake review for the synthetic D3 blinded files."""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path
import shutil
import stat
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "d3_prospective_experiment"
LOCAL_ROOT = (
    ROOT / "validation" / "external_local" / "d3_prospective_experiment"
)
RAW_SNAPSHOT = LOCAL_ROOT / "intake" / "raw_read_only"
MANIFEST_PATH = BENCHMARK / "results" / "data_intake_manifest.yaml"
SCHEMA_REVIEW_PATH = BENCHMARK / "results" / "data_intake_schema_review.csv"
REPORT_PATH = BENCHMARK / "reports" / "data_intake_dry_run_report.md"
FORCING_REPORT_PATH = BENCHMARK / "reports" / "forcing_quality_report.md"
FORCING_SUMMARY_PATH = BENCHMARK / "results" / "forcing_quality_summary.yaml"
EXPECTED_COLUMNS = (
    "experiment_id",
    "dataset_blind_id",
    "chamber_id",
    "replicate_id",
    "sample_datetime_utc",
    "hours_after_exposure",
    "organ",
    "fresh_mass_g",
    "dry_mass_g",
    "tissue_water_ml",
    "tfwt_bq_l_water",
    "analytical_uncertainty",
    "detection_limit_bq_l",
    "below_detection_limit",
    "quality_flag",
    "assumption_set",
    "synthetic_status",
)
NUMERIC_FIELDS = (
    "hours_after_exposure",
    "fresh_mass_g",
    "dry_mass_g",
    "tissue_water_ml",
    "tfwt_bq_l_water",
    "analytical_uncertainty",
    "detection_limit_bq_l",
)
SCHEMA_COLUMNS = (
    "dataset_blind_id",
    "row_count",
    "schema_pass",
    "unit_contract_pass",
    "missing_value_count",
    "nonfinite_numeric_count",
    "invalid_mass_count",
    "detection_flag_mismatch_count",
    "synthetic_status_pass",
    "registry_eligible",
    "production_eligible",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"Invalid boolean: {value}")
    return normalized == "true"


def write_schema_review(rows: list[dict[str, Any]]) -> None:
    SCHEMA_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCHEMA_REVIEW_PATH.open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=SCHEMA_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def render_forcing_report() -> None:
    summary = yaml.safe_load(
        FORCING_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    lines = [
        "# D3 synthetic forcing quality report",
        "",
        "```text",
        "FORCING_SOURCE = SYNTHETIC_CONTROLLED_EXPERIMENT",
        "REAL_EXTERNAL_EVIDENCE = FALSE",
        "FORCING_INTERVAL = 5_MINUTES_COMPLETE",
        "```",
        "",
        "| scenario | rows | exposure mean | exposure CV | background mean fraction | background max fraction |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary["scenarios"]:
        lines.append(
            f'| {item["scenario_id"]} | {item["row_count"]} | '
            f'{item["actual_exposure_mean"]:.6f} | '
            f'{item["actual_exposure_cv"]:.6f} | '
            f'{item["post_exposure_background_mean_fraction"]:.6f} | '
            f'{item["post_exposure_background_maximum_fraction"]:.6f} |'
        )
    lines.extend(
        [
            "",
            "The measured-background scenario is the primary synthetic forcing.",
            "The zero-background scenario is sensitivity-only and is not evidence",
            "that a real chamber background will be zero.",
        ]
    )
    FORCING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FORCING_REPORT_PATH.write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def render_intake_report(
    manifest: dict[str, Any], rows: list[dict[str, Any]]
) -> None:
    lines = [
        "# D3 synthetic data intake dry-run report",
        "",
        "```text",
        "INTAKE_CLASS = SYNTHETIC_INTERNAL_TEST_DATA",
        "RAW_SNAPSHOT_READ_ONLY = TRUE",
        "SHA256_MANIFEST = PASS",
        "LICENCE_REVIEW = SYNTHETIC_INTERNAL_TEST_DATA",
        "REGISTRY_ELIGIBILITY = FALSE",
        "PRODUCTION_ELIGIBILITY = FALSE",
        "REAL_EXTERNAL_VALIDATION = NOT_STARTED",
        "V3_PHYSICS_START_GATE =",
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "```",
        "",
        "| blind ID | rows | schema | units | missing | nonfinite | mass errors | detection mismatches |",
        "|---|---:|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f'| {row["dataset_blind_id"]} | {row["row_count"]} | '
            f'{"PASS" if row["schema_pass"] else "FAIL"} | '
            f'{"PASS" if row["unit_contract_pass"] else "FAIL"} | '
            f'{row["missing_value_count"]} | '
            f'{row["nonfinite_numeric_count"]} | '
            f'{row["invalid_mass_count"]} | '
            f'{row["detection_flag_mismatch_count"]} |'
        )
    lines.extend(
        [
            "",
            "The read-only snapshot is a local ignored copy of the synthetic",
            "blinded files, not an external raw-data package. The review proves",
            "only that the intake workflow detects schema, unit, missing-value,",
            "mass, detection-limit, licence, and eligibility boundaries.",
            "",
            f'`manifest_sha256 = {sha256(MANIFEST_PATH)}`',
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RAW_SNAPSHOT.mkdir(parents=True, exist_ok=True)
    file_entries: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    for blind_id in ("A", "B", "C"):
        source = LOCAL_ROOT / f"dataset_{blind_id}.csv"
        snapshot = RAW_SNAPSHOT / source.name
        temporary = snapshot.with_suffix(".csv.tmp")
        shutil.copyfile(source, temporary)
        temporary.chmod(0o444)
        temporary.replace(snapshot)
        mode = snapshot.stat().st_mode
        if mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            raise ValueError(f"Intake snapshot is writable: {snapshot}")
        with snapshot.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            columns = tuple(reader.fieldnames or ())
        missing = sum(
            value is None or str(value).strip() == ""
            for row in rows
            for value in row.values()
        )
        nonfinite = 0
        invalid_mass = 0
        detection_mismatch = 0
        for row in rows:
            for field in NUMERIC_FIELDS:
                try:
                    value = float(row[field])
                except (TypeError, ValueError):
                    nonfinite += 1
                    continue
                if not math.isfinite(value) or value < 0:
                    nonfinite += 1
            if not (
                float(row["fresh_mass_g"]) > float(row["dry_mass_g"]) >= 0
                and math.isclose(
                    float(row["tissue_water_ml"]),
                    float(row["fresh_mass_g"]) - float(row["dry_mass_g"]),
                    abs_tol=0.011,
                )
            ):
                invalid_mass += 1
            expected_flag = float(row["tfwt_bq_l_water"]) < float(
                row["detection_limit_bq_l"]
            )
            if parse_bool(row["below_detection_limit"]) != expected_flag:
                detection_mismatch += 1
        unit_pass = {
            "hours_after_exposure",
            "fresh_mass_g",
            "dry_mass_g",
            "tissue_water_ml",
            "tfwt_bq_l_water",
            "detection_limit_bq_l",
        } <= set(columns)
        synthetic_pass = {
            row["synthetic_status"] for row in rows
        } == {"SYNTHETIC_NOT_EXTERNAL_EVIDENCE"}
        review_rows.append(
            {
                "dataset_blind_id": blind_id,
                "row_count": len(rows),
                "schema_pass": columns == EXPECTED_COLUMNS,
                "unit_contract_pass": unit_pass,
                "missing_value_count": missing,
                "nonfinite_numeric_count": nonfinite,
                "invalid_mass_count": invalid_mass,
                "detection_flag_mismatch_count": detection_mismatch,
                "synthetic_status_pass": synthetic_pass,
                "registry_eligible": False,
                "production_eligible": False,
            }
        )
        file_entries.append(
            {
                "dataset_blind_id": blind_id,
                "source_path": source.relative_to(ROOT).as_posix(),
                "snapshot_path": snapshot.relative_to(ROOT).as_posix(),
                "sha256": sha256(snapshot),
                "byte_size": snapshot.stat().st_size,
                "read_only": True,
                "licence": "SYNTHETIC_INTERNAL_TEST_DATA",
            }
        )
    if not all(
        row["schema_pass"]
        and row["unit_contract_pass"]
        and row["missing_value_count"] == 0
        and row["nonfinite_numeric_count"] == 0
        and row["invalid_mass_count"] == 0
        and row["detection_flag_mismatch_count"] == 0
        and row["synthetic_status_pass"]
        and not row["registry_eligible"]
        and not row["production_eligible"]
        for row in review_rows
    ):
        raise ValueError("Synthetic data intake review failed")
    write_schema_review(review_rows)
    manifest = {
        "manifest_id": "D3_SYNTHETIC_DATA_INTAKE_DRY_RUN_V1",
        "status": "PASS_SYNTHETIC_INTAKE_WORKFLOW",
        "licence": "SYNTHETIC_INTERNAL_TEST_DATA",
        "raw_snapshot_read_only": True,
        "schema_validation": "PASS",
        "unit_review": "PASS",
        "missing_value_review": "PASS",
        "detection_limit_review": "PASS",
        "independent_intake_logic": (
            "SEPARATE_FROM_DATASET_GENERATOR_NO_TRUTH_KEY_ACCESS"
        ),
        "truth_key_accessed": False,
        "registry_eligible": False,
        "production_eligible": False,
        "real_external_validation": "NOT_STARTED",
        "formal_v3_physics": "NOT_STARTED",
        "v3_physics_start_gate": (
            "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
        "files": file_entries,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    render_intake_report(manifest, review_rows)
    render_forcing_report()
    print("DATA_INTAKE_DRY_RUN_STATUS = PASS_SYNTHETIC_INTAKE_WORKFLOW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
