"""Build isolated protected-ref V3 evidence-gate repositories for tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml

from scripts.verify_v3_physics_start_gate import (
    TRUSTED_POLICY_PATH,
    trusted_registry_entry_hash,
    trusted_registry_projection_hash,
)
from validation.evidence_validation import calculate_sha256


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def build_gate_repository(
    root: Path,
    *,
    dataset_id: str = "GATE_FIXTURE",
    evidence_type: str = "CONTROLLED_EXPERIMENT",
    declared_verdict: str = "PASS",
    metric_value: Any = 0.2,
    metric_unit: str = "1",
    test_only: bool = True,
) -> tuple[Path, dict[str, Path]]:
    """Build a chain where policy approval predates preregistration and holdout."""

    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Evidence Gate Test")

    raw_directory = root / "validation/external_local/gate_fixture"
    raw_directory.mkdir(parents=True)
    raw_file = raw_directory / "observations.csv"
    raw_file.write_text(
        "sample_id,value\nCAL_001,1\nHOLD_001,2\n",
        encoding="utf-8",
    )
    raw_checksum = calculate_sha256(raw_file)
    source = {
        "title": "Test-only complete artifact chain",
        "authority": "pytest fixture authority",
        "reference": "test://gate-fixture",
    }
    raw_manifest_path = raw_directory / "source_manifest.yaml"
    raw_manifest = {
        "manifest_schema_version": "1.0.0",
        "dataset_id": dataset_id,
        "dataset_version": "1.0.0",
        "artifact_purpose": "TEST_ONLY_POSITIVE_PATH",
        "test_only": test_only,
        "origin_class": "PYTEST_FIXTURE",
        "evidence_type": evidence_type,
        "source": source,
        "licence_status": (
            "VERIFIED"
            if evidence_type in {
                "CONTROLLED_EXPERIMENT",
                "MATCHED_FIELD_OBSERVATION",
                "LICENSED_EXTERNAL_HOLDOUT",
            }
            else "SYNTHETIC_TEST"
        ),
        "local_use_allowed": True,
        "redistribution_allowed": False,
        "exposure_start_utc": "2025-01-01T00:00:00Z",
        "exposure_end_utc": "2025-01-01T01:00:00Z",
        "expected_time_step_seconds": 3600,
        "files": [
            {
                "path": "observations.csv",
                "role": "observations",
                "expected_sha256": raw_checksum,
                "calculated_sha256": raw_checksum,
                "size_bytes": raw_file.stat().st_size,
                "format": "csv",
            }
        ],
        "units": {"observations": {"value": "Bq"}},
        "calibration_sample_ids": ["CAL_001"],
        "holdout_sample_ids": ["HOLD_001"],
        "holdout_inspected_before_preregistration": False,
    }
    write_yaml(raw_manifest_path, raw_manifest)
    raw_manifest_sha256 = calculate_sha256(raw_manifest_path)

    approval_record_path = (
        root / "validation/v3/policy/approvals/gate_fixture_approval.yaml"
    )
    entry_core = {
        "dataset_id": dataset_id,
        "raw_manifest_sha256": raw_manifest_sha256,
        "evidence_type": evidence_type,
        "empirical_eligibility": "APPROVED",
        "test_only": test_only,
        "source_authority": {
            "organization": source["authority"],
            "dataset_title": source["title"],
            "reference": source["reference"],
        },
        "licence_review": {
            "status": "APPROVED_LOCAL_USE",
            "review_record_path": approval_record_path.relative_to(root).as_posix(),
            "review_record_sha256": "0" * 64,
        },
    }
    entry_hash = trusted_registry_entry_hash(entry_core)
    registry_projection_hash = trusted_registry_projection_hash(
        {"schema_version": "1.0", "entries": [entry_core]}
    )
    write_yaml(
        approval_record_path,
        {
            "schema_version": "1.0",
            "dataset_id": dataset_id,
            "decision": "APPROVED",
            "test_only": test_only,
            "approved_entry_sha256": entry_hash,
            "approved_registry_sha256": registry_projection_hash,
        },
    )
    git(root, "add", approval_record_path.relative_to(root).as_posix())
    git(root, "commit", "-q", "-m", "Approve isolated evidence eligibility")
    approval_commit = git(root, "rev-parse", "HEAD")
    approval_record_sha256 = calculate_sha256(approval_record_path)

    registry_entry = {
        **entry_core,
        "licence_review": {
            **entry_core["licence_review"],
            "review_record_sha256": approval_record_sha256,
        },
        "approval": {
            "approval_commit": approval_commit,
            "approved_registry_sha256": registry_projection_hash,
            "approved_entry_sha256": entry_hash,
        },
    }
    registry_path = root / TRUSTED_POLICY_PATH
    write_yaml(
        registry_path,
        {"schema_version": "1.0", "entries": [registry_entry]},
    )
    git(root, "add", registry_path.relative_to(root).as_posix())
    git(root, "commit", "-q", "-m", "Register isolated evidence policy")
    registry_commit = git(root, "rev-parse", "HEAD")
    git(
        root,
        "update-ref",
        "refs/remotes/origin/main",
        registry_commit,
    )
    git(root, "switch", "-q", "-c", "evidence-chain")

    intake_path = root / "validation/intake/gate_fixture.yaml"
    intake = {
        "manifest_schema_version": "2.0.0",
        "dataset_id": dataset_id,
        "evidence_type": evidence_type,
        "raw_manifest_path": raw_manifest_path.relative_to(root).as_posix(),
        "raw_manifest_sha256": raw_manifest_sha256,
        "adapter_version": "2.0.0",
        "field_mapping": {"observations": {"value": "value"}},
        "unit_mapping": {
            "observations": {
                "value": {
                    "declared_unit": "Bq",
                    "canonical_unit": "Bq",
                    "conversion": "identity",
                }
            }
        },
        "time_coverage": {},
        "exposure_coverage": {
            "start_utc": "2025-01-01T00:00:00Z",
            "end_utc": "2025-01-01T01:00:00Z",
            "forcing_complete": True,
        },
        "calibration_ids": ["CAL_001"],
        "holdout_ids": ["HOLD_001"],
        "validation_summary": {
            "schema_validated": True,
            "numeric_content_validated": True,
            "checksums_recomputed": True,
        },
        "generated_files": [],
        "calculated_checksums": {"observations": raw_checksum},
        "intake_status": "READY_FOR_PREREGISTRATION",
        "status": "READY_FOR_PREREGISTRATION",
        "checksums_sha256": {"observations": raw_checksum},
        "field_mappings": {"observations": {"value": "value"}},
        "calibration_sample_ids": ["CAL_001"],
        "holdout_sample_ids": ["HOLD_001"],
        "empirical_validation": False,
        "calibration_permitted": False,
        "holdout_execution_permitted": False,
        "blocking_reasons": [],
        "metric_pipeline": {"status": "NOT_RUN_NO_MODEL_OUTPUT"},
    }
    write_yaml(intake_path, intake)
    intake_sha256 = calculate_sha256(intake_path)

    preregistration_file = root / "validation/preregistration/gate_fixture.yaml"
    metric_calculation = {
        "method": "NORMALIZED_RMSE",
        "observation_role": "observations",
        "observation_id_column": "sample_id",
        "observation_value_column": "value",
        "result_file": "validation/results/model_output.csv",
        "prediction_id_column": "sample_id",
        "prediction_value_column": "prediction",
    }
    write_yaml(
        preregistration_file,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
            "calibration_ids": ["CAL_001"],
            "holdout_ids": ["HOLD_001"],
            "primary_metrics": [
                {
                    "metric_id": "normalized_rmse",
                    "required": True,
                    "comparator": "LE",
                    "threshold": 0.25,
                    "value_unit": "1",
                    "missing_policy": "FAIL",
                    "calculation": metric_calculation,
                }
            ],
            "parameter_set": ["turnover_rate"],
        },
    )
    git(root, "add", preregistration_file.relative_to(root).as_posix())
    git(root, "commit", "-q", "-m", "Freeze preregistration")
    preregistration_commit = git(root, "rev-parse", "HEAD")
    preregistration_sha256 = calculate_sha256(preregistration_file)

    preregistration_record_path = (
        root / "validation/preregistration/gate_fixture_record.yaml"
    )
    write_yaml(
        preregistration_record_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_sha256,
            "intake_manifest_sha256": intake_sha256,
            "preregistration_file": preregistration_file.relative_to(root).as_posix(),
            "preregistration_sha256": preregistration_sha256,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_001"],
            "holdout_ids": ["HOLD_001"],
            "primary_metrics": [
                {
                    "metric_id": "normalized_rmse",
                    "required": True,
                    "comparator": "LE",
                    "threshold": 0.25,
                    "value_unit": "1",
                    "missing_policy": "FAIL",
                    "calculation": metric_calculation,
                }
            ],
            "parameter_set": ["turnover_rate"],
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )

    parameters = {"turnover_rate": 0.1}
    parameter_hash = canonical_hash(parameters)
    config_hash = "1" * 64
    calibration_path = root / "validation/results/calibration.yaml"
    write_yaml(
        calibration_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_sha256,
            "intake_manifest_sha256": intake_sha256,
            "preregistration_sha256": preregistration_sha256,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_001"],
            "parameter_result_hash": parameter_hash,
            "config_hash": config_hash,
            "model_commit": preregistration_commit,
            "parameters": parameters,
            "metrics": {"normalized_rmse": 0.1},
            "status": "CALIBRATION_COMPLETE",
            "generated_at": "2025-01-02T00:00:00Z",
        },
    )
    identifiability_path = root / "validation/results/identifiability.yaml"
    write_yaml(
        identifiability_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "preregistration_sha256": preregistration_sha256,
            "parameter_result_hash": parameter_hash,
            "methods": ["jacobian", "profile_likelihood"],
            "condition_number": 2.0,
            "max_parameter_correlation": 0.2,
            "boundary_hits": [],
            "status": "IDENTIFIABLE",
            "generated_at": "2025-01-02T00:00:00Z",
        },
    )
    model_output_path = root / "validation/results/model_output.csv"
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction = (
        2.0 * (1.0 + float(metric_value))
        if isinstance(metric_value, (int, float)) and not isinstance(metric_value, bool)
        else 2.4
    )
    model_output_path.write_text(
        f"sample_id,prediction\nHOLD_001,{prediction:.15g}\n",
        encoding="utf-8",
    )
    holdout_path = root / "validation/results/holdout.yaml"
    write_yaml(
        holdout_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "evidence_type": evidence_type,
            "raw_manifest_sha256": raw_manifest_sha256,
            "intake_manifest_sha256": intake_sha256,
            "preregistration_sha256": preregistration_sha256,
            "preregistration_commit": preregistration_commit,
            "model_commit": preregistration_commit,
            "config_hash": config_hash,
            "parameter_result_hash": parameter_hash,
            "holdout_ids": ["HOLD_001"],
            "result_file_checksums": {
                model_output_path.relative_to(root).as_posix(): calculate_sha256(
                    model_output_path
                )
            },
            "metrics": [
                {
                    "metric_id": "normalized_rmse",
                    "value": metric_value,
                    "value_unit": metric_unit,
                }
            ],
            "declared_verdict": declared_verdict,
            "generated_at": "2025-01-03T00:00:00Z",
        },
    )

    report_paths: dict[str, Path] = {}
    for key, check in (
        ("v1", "V1_RECOMPUTE"),
        ("v2", "V2_ACCEPTANCE"),
        ("validation_readiness", "VALIDATION_READINESS"),
    ):
        report_path = root / f"validation/results/{key}_regression.yaml"
        write_yaml(
            report_path,
            {
                "schema_version": "1.0.0",
                "check": check,
                "status": "PASS",
                "model_commit": preregistration_commit,
                "generated_at": "2025-01-03T00:00:00Z",
            },
        )
        report_paths[key] = report_path

    bundle_path = root / "validation/v3/evidence_bundle.yaml"
    write_yaml(
        bundle_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_sha256,
            "evidence_type": evidence_type,
            "artifact_purpose": "TEST_ONLY_POSITIVE_PATH",
            "test_only": test_only,
            "origin_class": "PYTEST_FIXTURE",
            "raw_manifest_path": raw_manifest_path.relative_to(root).as_posix(),
            "intake_manifest_path": intake_path.relative_to(root).as_posix(),
            "preregistration_record_path": preregistration_record_path.relative_to(
                root
            ).as_posix(),
            "calibration_result_path": calibration_path.relative_to(root).as_posix(),
            "identifiability_result_path": identifiability_path.relative_to(
                root
            ).as_posix(),
            "holdout_result_path": holdout_path.relative_to(root).as_posix(),
        },
    )
    config_path = root / "validation/v3/gate.yaml"
    (root / "docs/v3/gates").mkdir(parents=True)
    write_yaml(
        config_path,
        {
            "schema_version": "3.0.0",
            "evidence_bundle_path": bundle_path.relative_to(root).as_posix(),
            "allowed_raw_data_roots": ["validation/external_local"],
            "required_regression_reports": {
                key: path.relative_to(root).as_posix()
                for key, path in report_paths.items()
            },
        },
    )
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "Add holdout evidence")
    return config_path, {
        "approval_record": approval_record_path,
        "registry": registry_path,
        "bundle": bundle_path,
        "raw_manifest": raw_manifest_path,
        "raw_file": raw_file,
        "intake": intake_path,
        "preregistration_file": preregistration_file,
        "preregistration_record": preregistration_record_path,
        "calibration": calibration_path,
        "identifiability": identifiability_path,
        "holdout": holdout_path,
        "model_output": model_output_path,
        **{f"report_{key}": value for key, value in report_paths.items()},
    }
