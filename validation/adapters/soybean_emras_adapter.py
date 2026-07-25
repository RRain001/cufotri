#!/usr/bin/env python3
"""Fail-closed intake and synthetic-contract runner for soybean evidence."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import math
from pathlib import Path
import sys
import tempfile
from typing import Any

import yaml


SOURCE_MANIFEST = "source_manifest.yaml"
REQUIRED_SOURCE_FIELDS = {
    "dataset_id",
    "evidence_type",
    "empirical_validation",
    "licence_use_permitted",
    "redistribution_permitted",
    "licence_source",
    "exposure_start_utc",
    "exposure_end_utc",
    "expected_time_step_seconds",
    "files",
    "units",
    "calibration_sample_ids",
    "holdout_sample_ids",
    "holdout_inspected_before_preregistration",
}


def _load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be explicit UTC")
    return parsed.astimezone(timezone.utc)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        rows = list(reader)
    if not fields or not rows:
        raise ValueError(f"CSV must contain a header and data rows: {path}")
    return fields, rows


def _check_continuity(
    rows: list[dict[str, str]],
    *,
    time_column: str,
    expected_seconds: int,
    label: str,
) -> tuple[datetime, datetime]:
    times = [_parse_utc(row[time_column], f"{label}.{time_column}") for row in rows]
    if times != sorted(times) or len(times) != len(set(times)):
        raise ValueError(f"{label} time must be strictly increasing and unique")
    intervals = [
        int((right - left).total_seconds())
        for left, right in zip(times, times[1:])
    ]
    if any(interval != expected_seconds for interval in intervals):
        raise ValueError(f"{label} time series is discontinuous")
    return times[0], times[-1]


def _normalized_rmse(
    rows: list[dict[str, str]],
    observed_column: str,
    model_column: str,
) -> float:
    observed = [float(row[observed_column]) for row in rows]
    model = [float(row[model_column]) for row in rows]
    denominator = max(sum(abs(value) for value in observed) / len(observed), 1.0e-300)
    return math.sqrt(
        sum((candidate - reference) ** 2 for candidate, reference in zip(model, observed))
        / len(observed)
    ) / denominator


def _blocked(reasons: list[str]) -> dict[str, Any]:
    return {
        "status": "BLOCKED_EXTERNAL_DATA",
        "blocking_reasons": sorted(set(reasons)),
        "calibration_permitted": False,
        "holdout_execution_permitted": False,
        "empirical_validation": False,
        "checksums_sha256": {},
        "field_mappings": {},
        "metric_pipeline": {"status": "NOT_RUN_BLOCKED_EXTERNAL_DATA"},
    }


def validate_local_package(case_path: Path, package_directory: Path) -> dict[str, Any]:
    """Validate one local package and return a metadata-only intake result."""

    case = _load_mapping(case_path)
    source_path = package_directory / SOURCE_MANIFEST
    if not source_path.is_file():
        return _blocked([f"missing {SOURCE_MANIFEST}"])

    source = _load_mapping(source_path)
    reasons = [
        f"missing source field {name}"
        for name in sorted(REQUIRED_SOURCE_FIELDS - set(source))
    ]
    evidence_type = str(source.get("evidence_type", "MISSING"))
    synthetic = evidence_type == "SYNTHETIC_CONTRACT_TEST"
    if evidence_type != case.get("evidence_type"):
        reasons.append("source evidence_type does not match case contract")
    if source.get("dataset_id") != case.get("dataset_id"):
        reasons.append("source dataset_id does not match case contract")
    if source.get("licence_use_permitted") is not True:
        reasons.append("licence_use_permitted must be true")
    if source.get("empirical_validation") is not False:
        reasons.append("intake source cannot predeclare empirical validation")
    if source.get("holdout_inspected_before_preregistration") is not False:
        reasons.append("holdout inspected before preregistration")

    try:
        exposure_start = _parse_utc(
            source.get("exposure_start_utc", ""),
            "exposure_start_utc",
        )
        exposure_end = _parse_utc(
            source.get("exposure_end_utc", ""),
            "exposure_end_utc",
        )
        if exposure_end <= exposure_start:
            reasons.append("exposure_end_utc must be after exposure_start_utc")
    except ValueError as exc:
        reasons.append(str(exc))
        exposure_start = exposure_end = datetime(1970, 1, 1, tzinfo=timezone.utc)

    try:
        expected_seconds = int(source.get("expected_time_step_seconds", 0))
        if expected_seconds <= 0:
            raise ValueError
    except (TypeError, ValueError):
        reasons.append("expected_time_step_seconds must be a positive integer")
        expected_seconds = 0

    files = source.get("files", {})
    units = source.get("units", {})
    if not isinstance(files, dict):
        reasons.append("files must be a mapping")
        files = {}
    if not isinstance(units, dict):
        reasons.append("units must be a mapping")
        units = {}

    required_roles = case.get("required_file_roles", [])
    expected_fields = case.get("expected_fields", {})
    if not isinstance(required_roles, list) or not isinstance(expected_fields, dict):
        reasons.append("case file-role contract is invalid")
        required_roles = []
        expected_fields = {}

    resolved_files: dict[str, Path] = {}
    checksums: dict[str, str] = {}
    field_mappings: dict[str, dict[str, str]] = {}
    csv_rows: dict[str, list[dict[str, str]]] = {}
    for role in required_roles:
        relative = files.get(role)
        if not isinstance(relative, str) or not relative.strip():
            reasons.append(f"missing required file role {role}")
            continue
        path = package_directory / relative
        if not path.is_file():
            reasons.append(f"missing file for role {role}")
            continue
        resolved_files[role] = path
        checksums[role] = _sha256(path)
        role_contract = expected_fields.get(role, {})
        if path.suffix.lower() == ".csv":
            try:
                fields, rows = _read_csv(path)
                csv_rows[role] = rows
            except ValueError as exc:
                reasons.append(str(exc))
                continue
            missing_fields = sorted(set(role_contract) - set(fields))
            reasons.extend(
                f"{role} missing field {field}" for field in missing_fields
            )
            field_mappings[role] = {
                field: field for field in role_contract if field in fields
            }
        elif path.suffix.lower() in {".yaml", ".yml"}:
            try:
                payload = _load_mapping(path)
            except (ValueError, yaml.YAMLError) as exc:
                reasons.append(str(exc))
                continue
            missing_fields = sorted(set(role_contract) - set(payload))
            reasons.extend(
                f"{role} missing field {field}" for field in missing_fields
            )
            field_mappings[role] = {
                field: field for field in role_contract if field in payload
            }
        else:
            reasons.append(f"{role} has unsupported file format")

        declared_units = units.get(role, {})
        if not isinstance(declared_units, dict):
            reasons.append(f"{role} units must be a mapping")
            declared_units = {}
        for field, expected_unit in role_contract.items():
            if declared_units.get(field) != expected_unit:
                reasons.append(
                    f"{role}.{field} unit must be explicit {expected_unit}"
                )

    if expected_seconds > 0:
        for role in case.get("continuous_series_roles", []):
            if role not in csv_rows:
                continue
            time_column = case["time_columns"].get(role)
            if not time_column:
                reasons.append(f"missing time-column contract for {role}")
                continue
            try:
                first, last = _check_continuity(
                    csv_rows[role],
                    time_column=time_column,
                    expected_seconds=expected_seconds,
                    label=role,
                )
                if role == "air_hto" and (
                    first > exposure_start or last < exposure_end
                ):
                    reasons.append("air HTO does not cover the exposure interval")
            except (KeyError, ValueError) as exc:
                reasons.append(str(exc))

    mixing_path = resolved_files.get("mixing_boundary")
    if mixing_path is not None:
        try:
            mixing = _load_mapping(mixing_path)
            for field in (
                "chamber_volume_m3",
                "ventilation_or_mixing_rate_s",
            ):
                if float(mixing[field]) <= 0.0:
                    reasons.append(f"mixing_boundary.{field} must be positive")
            if not str(mixing.get("air_replacement_boundary", "")).strip():
                reasons.append("mixing boundary lacks air replacement definition")
        except (KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            reasons.append(f"invalid mixing boundary: {exc}")

    plant_rows = csv_rows.get("plant_observations", [])
    if plant_rows:
        if any(not row.get("replicate_id", "").strip() for row in plant_rows):
            reasons.append("plant observations require replicate identifiers")
        if any(not row.get("sample_id", "").strip() for row in plant_rows):
            reasons.append("plant observations require sample identifiers")

    calibration_ids = source.get("calibration_sample_ids", [])
    holdout_ids = source.get("holdout_sample_ids", [])
    if not isinstance(calibration_ids, list) or not calibration_ids:
        reasons.append("calibration_sample_ids must be non-empty")
        calibration_ids = []
    if not isinstance(holdout_ids, list) or not holdout_ids:
        reasons.append("holdout_sample_ids must be non-empty")
        holdout_ids = []
    if set(calibration_ids) & set(holdout_ids):
        reasons.append("calibration and holdout sample identifiers overlap")
    available_ids = {row.get("sample_id") for row in plant_rows}
    if not set(calibration_ids + holdout_ids) <= available_ids:
        reasons.append("calibration/holdout identifiers are absent from observations")

    metric_result: dict[str, Any] = {"status": "NOT_RUN_NO_MODEL_OUTPUT"}
    metric = case.get("synthetic_metric_pipeline")
    if synthetic and isinstance(metric, dict) and plant_rows:
        try:
            value = _normalized_rmse(
                plant_rows,
                metric["observed_column"],
                metric["model_column"],
            )
            threshold = float(metric["threshold"])
            metric_result = {
                "status": "PASS" if value <= threshold else "FAIL",
                "metric": "normalized_rmse",
                "value": value,
                "threshold": threshold,
            }
            if value > threshold:
                reasons.append("synthetic metric pipeline threshold failed")
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            reasons.append(f"synthetic metric pipeline invalid: {exc}")

    if reasons:
        result = _blocked(reasons)
        result["checksums_sha256"] = checksums
        result["field_mappings"] = field_mappings
        result["metric_pipeline"] = metric_result
        return result

    status = (
        "PASS_SYNTHETIC_CONTRACT_ONLY"
        if synthetic
        else "READY_FOR_PREREGISTRATION"
    )
    return {
        "status": status,
        "dataset_id": source["dataset_id"],
        "evidence_type": evidence_type,
        "empirical_validation": False,
        "licence_use_permitted": True,
        "redistribution_permitted": bool(source["redistribution_permitted"]),
        "checksums_sha256": checksums,
        "field_mappings": field_mappings,
        "calibration_sample_ids": calibration_ids,
        "holdout_sample_ids": holdout_ids,
        "metric_pipeline": metric_result,
        "calibration_permitted": False,
        "holdout_execution_permitted": False,
        "blocking_reasons": [],
    }


def write_intake_manifest(result: dict[str, Any], path: Path) -> None:
    """Write metadata only; never copy raw values into the manifest."""

    payload = {
        "manifest_version": "1.0.0",
        **result,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def write_intake_report(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Soybean external-evidence intake report",
        "",
        f"`SOYBEAN_ADAPTER_STATUS = {result['status']}`",
        "",
        f"- Evidence type: `{result.get('evidence_type', 'NOT_AVAILABLE')}`",
        f"- Empirical validation: `{str(result['empirical_validation']).lower()}`",
        f"- Calibration permitted: `{str(result['calibration_permitted']).lower()}`",
        f"- Holdout execution permitted: "
        f"`{str(result['holdout_execution_permitted']).lower()}`",
        f"- Files checksummed: `{len(result.get('checksums_sha256', {}))}`",
        f"- Metric pipeline: "
        f"`{result.get('metric_pipeline', {}).get('status', 'NOT_RUN')}`",
        "",
        "## Blocking reasons",
        "",
    ]
    reasons = result.get("blocking_reasons", [])
    lines.extend(f"- {reason}" for reason in reasons)
    if not reasons:
        lines.append("- none at intake-contract level")
    lines.extend(
        [
            "",
            "This report is intake metadata only. It cannot establish empirical",
            "validation or authorize calibration/holdout execution.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def create_synthetic_package(package_directory: Path) -> None:
    """Create a disposable, explicitly synthetic package for contract testing."""

    package_directory.mkdir(parents=True, exist_ok=True)
    (package_directory / "meteorology.csv").write_text(
        "time_utc,temperature_k,relative_humidity_percent\n"
        "2025-01-01T00:00:00Z,293.15,60\n"
        "2025-01-01T01:00:00Z,294.15,61\n"
        "2025-01-01T02:00:00Z,295.15,62\n",
        encoding="utf-8",
    )
    (package_directory / "air_hto.csv").write_text(
        "time_utc,air_hto_bq_m3\n"
        "2025-01-01T00:00:00Z,1000\n"
        "2025-01-01T01:00:00Z,1000\n"
        "2025-01-01T02:00:00Z,0\n",
        encoding="utf-8",
    )
    (package_directory / "plant_observations.csv").write_text(
        "sample_id,time_utc,replicate_id,observed_plant_water_hto_bq_l,"
        "model_plant_water_hto_bq_l,plant_obt_bq_l_combustion_water\n"
        "CAL_001,2025-01-01T01:00:00Z,R1,100,102,5\n"
        "HOLD_001,2025-01-01T02:00:00Z,R2,60,59,7\n",
        encoding="utf-8",
    )
    (package_directory / "mixing_boundary.yaml").write_text(
        "chamber_volume_m3: 10.0\n"
        "ventilation_or_mixing_rate_s: 0.01\n"
        "air_replacement_boundary: synthetic well-mixed replacement air\n",
        encoding="utf-8",
    )
    (package_directory / "uncertainty.csv").write_text(
        "observable,standard_uncertainty,unit\n"
        "observed_plant_water_hto_bq_l,10,Bq L-1 plant water\n",
        encoding="utf-8",
    )
    (package_directory / "detection_limits.csv").write_text(
        "observable,detection_limit,unit\n"
        "observed_plant_water_hto_bq_l,1,Bq L-1 plant water\n",
        encoding="utf-8",
    )
    source = {
        "dataset_id": "SOYBEAN_SYNTHETIC_CONTRACT",
        "evidence_type": "SYNTHETIC_CONTRACT_TEST",
        "empirical_validation": False,
        "licence_use_permitted": True,
        "redistribution_permitted": True,
        "licence_source": "project-authored synthetic values",
        "exposure_start_utc": "2025-01-01T00:00:00Z",
        "exposure_end_utc": "2025-01-01T02:00:00Z",
        "expected_time_step_seconds": 3600,
        "files": {
            "meteorology": "meteorology.csv",
            "air_hto": "air_hto.csv",
            "plant_observations": "plant_observations.csv",
            "mixing_boundary": "mixing_boundary.yaml",
            "uncertainty": "uncertainty.csv",
            "detection_limits": "detection_limits.csv",
        },
        "units": {
            "meteorology": {
                "time_utc": "UTC ISO-8601",
                "temperature_k": "K",
                "relative_humidity_percent": "percent",
            },
            "air_hto": {
                "time_utc": "UTC ISO-8601",
                "air_hto_bq_m3": "Bq m-3 air",
            },
            "plant_observations": {
                "sample_id": "identifier",
                "time_utc": "UTC ISO-8601",
                "replicate_id": "identifier",
                "observed_plant_water_hto_bq_l": "Bq L-1 plant water",
                "model_plant_water_hto_bq_l": "Bq L-1 plant water",
                "plant_obt_bq_l_combustion_water": "Bq L-1 combustion water",
            },
            "mixing_boundary": {
                "chamber_volume_m3": "m3",
                "ventilation_or_mixing_rate_s": "s-1",
                "air_replacement_boundary": "text",
            },
            "uncertainty": {
                "observable": "identifier",
                "standard_uncertainty": "declared observable unit",
                "unit": "unit string",
            },
            "detection_limits": {
                "observable": "identifier",
                "detection_limit": "declared observable unit",
                "unit": "unit string",
            },
        },
        "calibration_sample_ids": ["CAL_001"],
        "holdout_sample_ids": ["HOLD_001"],
        "holdout_inspected_before_preregistration": False,
    }
    (package_directory / SOURCE_MANIFEST).write_text(
        yaml.safe_dump(source, sort_keys=False),
        encoding="utf-8",
    )


def inspect_local_package(case_path: Path, local_root: Path) -> dict[str, Any]:
    """Backward-compatible check used by the architecture gate."""

    return validate_local_package(case_path, local_root / "soybean_emras")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        type=Path,
        default=Path("validation/cases/soybean_emras_template.yaml"),
    )
    parser.add_argument(
        "--local-root",
        type=Path,
        default=Path("validation/external_local"),
    )
    parser.add_argument("--output-manifest", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--synthetic-contract", action="store_true")
    arguments = parser.parse_args()

    try:
        if arguments.synthetic_contract:
            with tempfile.TemporaryDirectory(
                prefix="cteas_soybean_synthetic_"
            ) as temporary:
                package = Path(temporary) / "soybean_emras"
                create_synthetic_package(package)
                result = validate_local_package(arguments.case.resolve(), package)
        else:
            result = inspect_local_package(
                arguments.case.resolve(),
                arguments.local_root.resolve(),
            )
        if arguments.output_manifest:
            write_intake_manifest(result, arguments.output_manifest.resolve())
        if arguments.report:
            write_intake_report(result, arguments.report.resolve())
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"SOYBEAN_ADAPTER_STATUS = FAIL_CLOSED; reason={exc}", file=sys.stderr)
        return 1

    print(f"SOYBEAN_ADAPTER_STATUS = {result['status']}")
    print(f"EMPIRICAL_VALIDATION = {str(result['empirical_validation']).upper()}")
    print(f"CALIBRATION_PERMITTED = {str(result['calibration_permitted']).upper()}")
    if result.get("blocking_reasons"):
        print("BLOCKING_REASONS = " + ", ".join(result["blocking_reasons"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
