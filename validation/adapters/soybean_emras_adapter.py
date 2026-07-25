#!/usr/bin/env python3
"""Fail-closed intake and synthetic-contract runner for soybean evidence."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import sys
import tempfile
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence_validation import (
    EvidenceValidationError,
    calculate_sha256,
    parse_finite_number,
    require_regular_file,
    validate_json_schema,
    verify_clean_numeric_series,
    verify_disjoint_ids,
    verify_manifest_file_entries,
)


SOURCE_MANIFEST = "source_manifest.yaml"
RAW_SCHEMA = ROOT / "schemas/v3/external_raw_data_manifest.schema.json"
INTAKE_SCHEMA = ROOT / "schemas/v3/external_intake_manifest.schema.json"
ADAPTER_VERSION = "2.0.0"

NUMERIC_RULES: dict[str, dict[str, dict[str, float]]] = {
    "meteorology": {
        "temperature_k": {"exclusive_minimum": 0.0, "maximum": 400.0},
        "relative_humidity_percent": {"minimum": 0.0, "maximum": 100.0},
    },
    "air_hto": {
        "air_hto_bq_m3": {"minimum": 0.0},
    },
    "plant_observations": {
        "observed_plant_water_hto_bq_l": {"minimum": 0.0},
        "model_plant_water_hto_bq_l": {"minimum": 0.0},
        "plant_obt_bq_l_combustion_water": {"minimum": 0.0},
    },
    "uncertainty": {
        "standard_uncertainty": {"minimum": 0.0},
    },
    "detection_limits": {
        "detection_limit": {"minimum": 0.0},
    },
}


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise EvidenceValidationError(f"cannot parse YAML {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"expected YAML mapping: {path}")
    return value


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceValidationError(f"{label} is not ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise EvidenceValidationError(f"{label} must be explicit UTC")
    return parsed.astimezone(timezone.utc)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise EvidenceValidationError(f"cannot parse CSV {path}: {exc}") from exc
    if not fields or not rows:
        raise EvidenceValidationError(
            f"CSV must contain a header and data rows: {path}"
        )
    return fields, rows


def _check_continuity(
    rows: list[dict[str, str]],
    *,
    time_column: str,
    expected_seconds: int,
    label: str,
) -> tuple[datetime, datetime]:
    times = [_parse_utc(row.get(time_column, ""), f"{label}.{time_column}") for row in rows]
    if times != sorted(times) or len(times) != len(set(times)):
        raise EvidenceValidationError(
            f"{label} timestamps must be strictly increasing and unique"
        )
    intervals = [
        int((right - left).total_seconds())
        for left, right in zip(times, times[1:])
    ]
    if any(interval != expected_seconds for interval in intervals):
        raise EvidenceValidationError(f"{label} time series is discontinuous")
    return times[0], times[-1]


def _normalized_rmse(
    rows: list[dict[str, str]],
    observed_column: str,
    model_column: str,
) -> float:
    observed = [
        parse_finite_number(row.get(observed_column), label=observed_column)
        for row in rows
    ]
    model = [
        parse_finite_number(row.get(model_column), label=model_column)
        for row in rows
    ]
    denominator = max(
        sum(abs(value) for value in observed) / len(observed),
        1.0e-300,
    )
    return math.sqrt(
        sum(
            (candidate - reference) ** 2
            for candidate, reference in zip(model, observed)
        )
        / len(observed)
    ) / denominator


def _empty_intake(
    *,
    source_path: Path,
    dataset_id: str = "NOT_AVAILABLE",
    evidence_type: str = "NONE",
) -> dict[str, Any]:
    return {
        "manifest_schema_version": "2.0.0",
        "dataset_id": dataset_id,
        "evidence_type": evidence_type,
        "raw_manifest_path": source_path.as_posix(),
        "raw_manifest_sha256": (
            calculate_sha256(source_path) if source_path.is_file() else "NOT_AVAILABLE"
        ),
        "adapter_version": ADAPTER_VERSION,
        "field_mapping": {},
        "unit_mapping": {},
        "time_coverage": {},
        "exposure_coverage": {
            "start_utc": "NOT_AVAILABLE",
            "end_utc": "NOT_AVAILABLE",
            "forcing_complete": False,
        },
        "calibration_ids": [],
        "holdout_ids": [],
        "validation_summary": {
            "schema_validated": False,
            "numeric_content_validated": False,
            "checksums_recomputed": False,
        },
        "generated_files": [],
        "calculated_checksums": {},
        "intake_status": "BLOCKED_EXTERNAL_DATA",
        "status": "BLOCKED_EXTERNAL_DATA",
        "checksums_sha256": {},
        "field_mappings": {},
        "calibration_sample_ids": [],
        "holdout_sample_ids": [],
        "empirical_validation": False,
        "calibration_permitted": False,
        "holdout_execution_permitted": False,
        "blocking_reasons": [],
        "metric_pipeline": {"status": "NOT_RUN_BLOCKED_EXTERNAL_DATA"},
    }


def _validate_intake_schema(result: dict[str, Any]) -> dict[str, Any]:
    validate_json_schema(result, INTAKE_SCHEMA)
    return result


def _blocked(
    reasons: list[str],
    *,
    source_path: Path,
    partial: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = _empty_intake(source_path=source_path)
    if partial:
        result.update(partial)
    result["intake_status"] = "BLOCKED_EXTERNAL_DATA"
    result["status"] = "BLOCKED_EXTERNAL_DATA"
    result["empirical_validation"] = False
    result["calibration_permitted"] = False
    result["holdout_execution_permitted"] = False
    result["blocking_reasons"] = sorted(set(reasons))
    if result["metric_pipeline"].get("status") == "PASS":
        result["metric_pipeline"] = {"status": "NOT_RUN_BLOCKED_EXTERNAL_DATA"}
    return _validate_intake_schema(result)


def _role_entries(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for item in source.get("files", []):
        if isinstance(item, dict) and isinstance(item.get("role"), str):
            entries[item["role"]] = item
    return entries


def _check_observable_metadata(
    rows: list[dict[str, str]],
    *,
    role: str,
    value_field: str,
    plant_units: dict[str, str],
) -> None:
    if not rows:
        raise EvidenceValidationError(f"{role} must contain at least one data row")
    for row_index, row in enumerate(rows, start=2):
        observable = row.get("observable", "").strip()
        unit = row.get("unit", "").strip()
        if not observable:
            raise EvidenceValidationError(
                f"{role}.observable row {row_index} must be non-empty"
            )
        if observable not in plant_units:
            raise EvidenceValidationError(
                f"{role}.observable row {row_index} is not a plant observable"
            )
        if unit != plant_units[observable]:
            raise EvidenceValidationError(
                f"{role}.unit row {row_index} does not match {observable}"
            )
        parse_finite_number(
            row.get(value_field),
            label=f"{role}.{value_field} row {row_index}",
            minimum=0.0,
        )


def validate_local_package(
    case_path: Path,
    package_directory: Path,
) -> dict[str, Any]:
    """Validate one local package and return a schema-validated intake record."""

    case = _load_mapping(case_path)
    source_path = package_directory / SOURCE_MANIFEST
    if not source_path.is_file():
        return _blocked(
            [f"missing {SOURCE_MANIFEST}"],
            source_path=source_path,
        )

    reasons: list[str] = []
    source = _load_mapping(source_path)
    partial = _empty_intake(
        source_path=source_path,
        dataset_id=str(source.get("dataset_id", "NOT_AVAILABLE")),
        evidence_type=str(source.get("evidence_type", "NONE")),
    )
    if source.get("holdout_inspected_before_preregistration") is not False:
        reasons.append("holdout inspected before preregistration")
    try:
        validate_json_schema(source, RAW_SCHEMA)
        partial["validation_summary"]["schema_validated"] = True
    except EvidenceValidationError as exc:
        reasons.append(str(exc))
        return _blocked(reasons, source_path=source_path, partial=partial)

    if source["dataset_id"] != case.get("dataset_id"):
        reasons.append("raw manifest dataset_id does not match case contract")
    if source["evidence_type"] != case.get("evidence_type"):
        reasons.append("raw manifest evidence_type does not match case contract")
    if not source["local_use_allowed"]:
        reasons.append("local_use_allowed must be true")
    if source["holdout_inspected_before_preregistration"] is not False:
        reasons.append("holdout inspected before preregistration")

    exposure_start = _parse_utc(
        source["exposure_start_utc"],
        "exposure_start_utc",
    )
    exposure_end = _parse_utc(
        source["exposure_end_utc"],
        "exposure_end_utc",
    )
    if exposure_end <= exposure_start:
        reasons.append("exposure_end_utc must be after exposure_start_utc")
    expected_seconds = int(source["expected_time_step_seconds"])

    required_roles = case.get("required_file_roles", [])
    expected_fields = case.get("expected_fields", {})
    if not isinstance(required_roles, list) or not isinstance(expected_fields, dict):
        reasons.append("case file-role contract is invalid")
        required_roles = []
        expected_fields = {}

    entries = _role_entries(source)
    missing_roles = sorted(set(required_roles) - set(entries))
    reasons.extend(f"missing required file role {role}" for role in missing_roles)
    calculated_checksums: dict[str, str] = {}
    try:
        calculated_checksums = verify_manifest_file_entries(
            source,
            manifest_path=source_path,
            allowed_raw_roots=[package_directory],
        )
        partial["validation_summary"]["checksums_recomputed"] = True
    except EvidenceValidationError as exc:
        reasons.append(str(exc))

    resolved_files: dict[str, Path] = {}
    field_mapping: dict[str, dict[str, str]] = {}
    unit_mapping: dict[str, dict[str, dict[str, str]]] = {}
    csv_rows: dict[str, list[dict[str, str]]] = {}
    for role in required_roles:
        entry = entries.get(role)
        if not entry:
            continue
        candidate = package_directory / str(entry["path"])
        try:
            path = require_regular_file(
                candidate,
                allowed_roots=[package_directory],
            )
        except EvidenceValidationError as exc:
            reasons.append(str(exc))
            continue
        resolved_files[role] = path
        role_contract = expected_fields.get(role, {})
        if not isinstance(role_contract, dict):
            reasons.append(f"{role} field contract must be a mapping")
            continue
        if path.suffix.lower() == ".csv":
            try:
                fields, rows = _read_csv(path)
                csv_rows[role] = rows
            except EvidenceValidationError as exc:
                reasons.append(str(exc))
                continue
            missing_fields = sorted(set(role_contract) - set(fields))
            reasons.extend(
                f"{role} missing field {field}" for field in missing_fields
            )
            field_mapping[role] = {
                field: field for field in role_contract if field in fields
            }
            applicable_rules = {
                field: rule
                for field, rule in NUMERIC_RULES.get(role, {}).items()
                if field in role_contract
            }
            try:
                verify_clean_numeric_series(
                    rows,
                    applicable_rules,
                    label=role,
                )
            except EvidenceValidationError as exc:
                reasons.append(str(exc))
        elif path.suffix.lower() in {".yaml", ".yml"}:
            try:
                payload = _load_mapping(path)
            except EvidenceValidationError as exc:
                reasons.append(str(exc))
                continue
            missing_fields = sorted(set(role_contract) - set(payload))
            reasons.extend(
                f"{role} missing field {field}" for field in missing_fields
            )
            field_mapping[role] = {
                field: field for field in role_contract if field in payload
            }
        else:
            reasons.append(f"{role} has unsupported file format")

        declared_units = source["units"].get(role, {})
        if not isinstance(declared_units, dict):
            reasons.append(f"{role} units must be a mapping")
            declared_units = {}
        unit_mapping[role] = {}
        for field, canonical_unit in role_contract.items():
            declared_unit = declared_units.get(field)
            if declared_unit != canonical_unit:
                reasons.append(
                    f"{role}.{field} unit must be explicit {canonical_unit}"
                )
                continue
            unit_mapping[role][field] = {
                "declared_unit": declared_unit,
                "canonical_unit": canonical_unit,
                "conversion": "identity",
            }

    time_coverage: dict[str, dict[str, Any]] = {}
    for role in case.get("continuous_series_roles", []):
        rows = csv_rows.get(role)
        if rows is None:
            continue
        time_column = case.get("time_columns", {}).get(role)
        if not time_column:
            reasons.append(f"missing time-column contract for {role}")
            continue
        try:
            first, last = _check_continuity(
                rows,
                time_column=time_column,
                expected_seconds=expected_seconds,
                label=role,
            )
            time_coverage[role] = {
                "start_utc": first.isoformat().replace("+00:00", "Z"),
                "end_utc": last.isoformat().replace("+00:00", "Z"),
                "continuous": True,
            }
            if first > exposure_start or last < exposure_end:
                reasons.append(f"{role} does not cover the exposure interval")
        except EvidenceValidationError as exc:
            reasons.append(str(exc))

    mixing_path = resolved_files.get("mixing_boundary")
    if mixing_path is not None:
        try:
            mixing = _load_mapping(mixing_path)
            parse_finite_number(
                mixing.get("chamber_volume_m3"),
                label="mixing_boundary.chamber_volume_m3",
                exclusive_minimum=0.0,
            )
            parse_finite_number(
                mixing.get("ventilation_or_mixing_rate_s"),
                label="mixing_boundary.ventilation_or_mixing_rate_s",
                exclusive_minimum=0.0,
            )
            if not str(mixing.get("air_replacement_boundary", "")).strip():
                raise EvidenceValidationError(
                    "mixing boundary lacks air replacement definition"
                )
        except EvidenceValidationError as exc:
            reasons.append(str(exc))

    plant_rows = csv_rows.get("plant_observations", [])
    if plant_rows:
        for row_index, row in enumerate(plant_rows, start=2):
            if not row.get("replicate_id", "").strip():
                reasons.append(
                    f"plant_observations.replicate_id row {row_index} is empty"
                )
            if not row.get("sample_id", "").strip():
                reasons.append(
                    f"plant_observations.sample_id row {row_index} is empty"
                )
            try:
                _parse_utc(
                    row.get("time_utc", ""),
                    f"plant_observations.time_utc row {row_index}",
                )
            except EvidenceValidationError as exc:
                reasons.append(str(exc))

    plant_units = source["units"].get("plant_observations", {})
    try:
        _check_observable_metadata(
            csv_rows.get("uncertainty", []),
            role="uncertainty",
            value_field="standard_uncertainty",
            plant_units=plant_units,
        )
    except EvidenceValidationError as exc:
        reasons.append(str(exc))
    try:
        _check_observable_metadata(
            csv_rows.get("detection_limits", []),
            role="detection_limits",
            value_field="detection_limit",
            plant_units=plant_units,
        )
    except EvidenceValidationError as exc:
        reasons.append(str(exc))

    calibration_ids = list(source["calibration_sample_ids"])
    holdout_ids = list(source["holdout_sample_ids"])
    try:
        verify_disjoint_ids(calibration_ids, holdout_ids)
    except EvidenceValidationError as exc:
        reasons.append(str(exc))
    available_ids = {row.get("sample_id") for row in plant_rows}
    if not set(calibration_ids + holdout_ids) <= available_ids:
        reasons.append(
            "calibration/holdout identifiers are absent from observations"
        )

    metric_result: dict[str, Any] = {"status": "NOT_RUN_NO_MODEL_OUTPUT"}
    synthetic = source["evidence_type"] == "SYNTHETIC_CONTRACT_TEST"
    metric = case.get("synthetic_metric_pipeline")
    if synthetic and isinstance(metric, dict) and plant_rows:
        try:
            value = _normalized_rmse(
                plant_rows,
                metric["observed_column"],
                metric["model_column"],
            )
            threshold = parse_finite_number(
                metric["threshold"],
                label="synthetic metric threshold",
                minimum=0.0,
            )
            metric_result = {
                "status": "PASS" if value <= threshold else "FAIL",
                "metric": "normalized_rmse",
                "value": value,
                "threshold": threshold,
            }
            if value > threshold:
                reasons.append("synthetic metric pipeline threshold failed")
        except (KeyError, EvidenceValidationError) as exc:
            reasons.append(f"synthetic metric pipeline invalid: {exc}")

    forcing_complete = (
        set(case.get("continuous_series_roles", [])) <= set(time_coverage)
        and not any(
            "does not cover the exposure interval" in reason for reason in reasons
        )
    )
    partial.update(
        {
            "field_mapping": field_mapping,
            "unit_mapping": unit_mapping,
            "time_coverage": time_coverage,
            "exposure_coverage": {
                "start_utc": source["exposure_start_utc"],
                "end_utc": source["exposure_end_utc"],
                "forcing_complete": forcing_complete,
            },
            "calibration_ids": calibration_ids,
            "holdout_ids": holdout_ids,
            "calculated_checksums": calculated_checksums,
            "checksums_sha256": calculated_checksums,
            "field_mappings": field_mapping,
            "calibration_sample_ids": calibration_ids,
            "holdout_sample_ids": holdout_ids,
            "metric_pipeline": metric_result,
        }
    )
    if reasons:
        return _blocked(reasons, source_path=source_path, partial=partial)

    status = (
        "PASS_SYNTHETIC_CONTRACT_ONLY"
        if synthetic
        else "READY_FOR_PREREGISTRATION"
    )
    partial.update(
        {
            "intake_status": status,
            "status": status,
            "validation_summary": {
                "schema_validated": True,
                "numeric_content_validated": True,
                "checksums_recomputed": True,
            },
            "empirical_validation": False,
            "calibration_permitted": False,
            "holdout_execution_permitted": False,
            "blocking_reasons": [],
        }
    )
    return _validate_intake_schema(partial)


def write_intake_manifest(result: dict[str, Any], path: Path) -> None:
    """Write validated metadata only; never copy raw values into the manifest."""

    _validate_intake_schema(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(result, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    written = _load_mapping(path)
    validate_json_schema(written, INTAKE_SCHEMA)


def write_intake_report(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Soybean external-evidence intake report",
        "",
        f"`SOYBEAN_ADAPTER_STATUS = {result['intake_status']}`",
        "",
        f"- Evidence type: `{result.get('evidence_type', 'NOT_AVAILABLE')}`",
        f"- Empirical validation: `{str(result['empirical_validation']).lower()}`",
        f"- Calibration permitted: `{str(result['calibration_permitted']).lower()}`",
        f"- Holdout execution permitted: "
        f"`{str(result['holdout_execution_permitted']).lower()}`",
        f"- Files checksummed: `{len(result.get('calculated_checksums', {}))}`",
        f"- Numeric content validated: "
        f"`{str(result['validation_summary']['numeric_content_validated']).lower()}`",
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


def _write_synthetic_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def create_synthetic_package(package_directory: Path) -> None:
    """Create a disposable, explicitly synthetic package for contract testing."""

    package_directory.mkdir(parents=True, exist_ok=True)
    contents = {
        "meteorology.csv": (
            "time_utc,temperature_k,relative_humidity_percent\n"
            "2025-01-01T00:00:00Z,293.15,60\n"
            "2025-01-01T01:00:00Z,294.15,61\n"
            "2025-01-01T02:00:00Z,295.15,62\n"
        ),
        "air_hto.csv": (
            "time_utc,air_hto_bq_m3\n"
            "2025-01-01T00:00:00Z,1000\n"
            "2025-01-01T01:00:00Z,1000\n"
            "2025-01-01T02:00:00Z,0\n"
        ),
        "plant_observations.csv": (
            "sample_id,time_utc,replicate_id,observed_plant_water_hto_bq_l,"
            "model_plant_water_hto_bq_l,plant_obt_bq_l_combustion_water\n"
            "CAL_001,2025-01-01T01:00:00Z,R1,100,102,5\n"
            "HOLD_001,2025-01-01T02:00:00Z,R2,60,59,7\n"
        ),
        "mixing_boundary.yaml": (
            "chamber_volume_m3: 10.0\n"
            "ventilation_or_mixing_rate_s: 0.01\n"
            "air_replacement_boundary: synthetic well-mixed replacement air\n"
        ),
        "uncertainty.csv": (
            "observable,standard_uncertainty,unit\n"
            "observed_plant_water_hto_bq_l,10,Bq L-1 plant water\n"
        ),
        "detection_limits.csv": (
            "observable,detection_limit,unit\n"
            "observed_plant_water_hto_bq_l,1,Bq L-1 plant water\n"
        ),
    }
    for filename, content in contents.items():
        _write_synthetic_file(package_directory / filename, content)

    roles = {
        "meteorology": "meteorology.csv",
        "air_hto": "air_hto.csv",
        "plant_observations": "plant_observations.csv",
        "mixing_boundary": "mixing_boundary.yaml",
        "uncertainty": "uncertainty.csv",
        "detection_limits": "detection_limits.csv",
    }
    files = []
    for role, filename in roles.items():
        path = package_directory / filename
        checksum = calculate_sha256(path)
        files.append(
            {
                "path": filename,
                "role": role,
                "expected_sha256": checksum,
                "calculated_sha256": checksum,
                "size_bytes": path.stat().st_size,
                "format": path.suffix.lstrip("."),
            }
        )
    source = {
        "manifest_schema_version": "1.0.0",
        "dataset_id": "SOYBEAN_SYNTHETIC_CONTRACT",
        "dataset_version": "1.0.0",
        "evidence_type": "SYNTHETIC_CONTRACT_TEST",
        "source": {
            "title": "Project-authored soybean contract fixture",
            "authority": "CTEAS_UFOTRI test suite",
            "reference": "tests only",
        },
        "licence_status": "SYNTHETIC_TEST",
        "local_use_allowed": True,
        "redistribution_allowed": True,
        "exposure_start_utc": "2025-01-01T00:00:00Z",
        "exposure_end_utc": "2025-01-01T02:00:00Z",
        "expected_time_step_seconds": 3600,
        "files": files,
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
    except (
        EvidenceValidationError,
        FileNotFoundError,
        RuntimeError,
        yaml.YAMLError,
    ) as exc:
        print(
            f"SOYBEAN_ADAPTER_STATUS = FAIL_CLOSED; reason={exc}",
            file=sys.stderr,
        )
        return 1

    print(f"SOYBEAN_ADAPTER_STATUS = {result['intake_status']}")
    print(f"EMPIRICAL_VALIDATION = {str(result['empirical_validation']).upper()}")
    print(f"CALIBRATION_PERMITTED = {str(result['calibration_permitted']).upper()}")
    if result.get("blocking_reasons"):
        print("BLOCKING_REASONS = " + ", ".join(result["blocking_reasons"]))
    return 1 if result["intake_status"] == "BLOCKED_EXTERNAL_DATA" else 0


if __name__ == "__main__":
    raise SystemExit(main())
