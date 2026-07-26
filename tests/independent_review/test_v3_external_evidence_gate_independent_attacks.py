from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import scripts.verify_v3_physics_start_gate as gate
from tests.helpers.v3_gate_fixture import (
    build_gate_repository as build_protected_gate_repository,
)


EXPECTED_BLOCKED = "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _build_independent_chain(
    repository: Path,
    *,
    holdout_verdict: str = "PASS",
) -> tuple[Path, dict[str, Path]]:
    """Build a review-only chain without using the remediation test fixture."""

    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "reviewer@example.invalid")
    _git(repository, "config", "user.name", "Independent Gate Reviewer")

    raw_directory = repository / "validation/external_local/review_only"
    raw_directory.mkdir(parents=True)
    measurement_path = raw_directory / "measurements.csv"
    measurement_path.write_text(
        "sample_id,activity_bq\n"
        "CAL_REVIEW,11\n"
        "HOLD_REVIEW,17\n",
        encoding="utf-8",
    )
    measurement_hash = _sha256(measurement_path)

    raw_manifest_path = raw_directory / "raw_manifest.yaml"
    _write_yaml(
        raw_manifest_path,
        {
            "manifest_schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "dataset_version": "review-fixture-1",
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "source": {
                "title": "TEST-ONLY independent adversarial fixture",
                "authority": "pytest independent review",
                "reference": "NOT EMPIRICAL; MUST NOT UNBLOCK PRODUCTION",
            },
            "licence_status": "VERIFIED",
            "local_use_allowed": True,
            "redistribution_allowed": False,
            "exposure_start_utc": "2026-01-01T00:00:00Z",
            "exposure_end_utc": "2026-01-01T01:00:00Z",
            "expected_time_step_seconds": 3600,
            "files": [
                {
                    "path": "measurements.csv",
                    "role": "observations",
                    "expected_sha256": measurement_hash,
                    "calculated_sha256": measurement_hash,
                    "size_bytes": measurement_path.stat().st_size,
                    "format": "csv",
                }
            ],
            "units": {"observations": {"activity_bq": "Bq"}},
            "calibration_sample_ids": ["CAL_REVIEW"],
            "holdout_sample_ids": ["HOLD_REVIEW"],
            "holdout_inspected_before_preregistration": False,
        },
    )
    raw_manifest_hash = _sha256(raw_manifest_path)

    intake_path = repository / "validation/review_artifacts/intake.yaml"
    intake = {
        "manifest_schema_version": "2.0.0",
        "dataset_id": "INDEPENDENT_REVIEW_ONLY",
        "evidence_type": "CONTROLLED_EXPERIMENT",
        "raw_manifest_path": raw_manifest_path.relative_to(repository).as_posix(),
        "raw_manifest_sha256": raw_manifest_hash,
        "adapter_version": "2.0.0",
        "field_mapping": {"observations": {"activity_bq": "activity_bq"}},
        "unit_mapping": {
            "observations": {
                "activity_bq": {
                    "declared_unit": "Bq",
                    "canonical_unit": "Bq",
                    "conversion": "identity",
                }
            }
        },
        "time_coverage": {},
        "exposure_coverage": {
            "start_utc": "2026-01-01T00:00:00Z",
            "end_utc": "2026-01-01T01:00:00Z",
            "forcing_complete": True,
        },
        "calibration_ids": ["CAL_REVIEW"],
        "holdout_ids": ["HOLD_REVIEW"],
        "validation_summary": {
            "schema_validated": True,
            "numeric_content_validated": True,
            "checksums_recomputed": True,
        },
        "generated_files": [],
        "calculated_checksums": {"observations": measurement_hash},
        "intake_status": "READY_FOR_PREREGISTRATION",
        "status": "READY_FOR_PREREGISTRATION",
        "checksums_sha256": {"observations": measurement_hash},
        "field_mappings": {"observations": {"activity_bq": "activity_bq"}},
        "calibration_sample_ids": ["CAL_REVIEW"],
        "holdout_sample_ids": ["HOLD_REVIEW"],
        "empirical_validation": False,
        "calibration_permitted": False,
        "holdout_execution_permitted": False,
        "blocking_reasons": [],
        "metric_pipeline": {"status": "NOT_RUN_NO_MODEL_OUTPUT"},
    }
    _write_yaml(intake_path, intake)
    intake_hash = _sha256(intake_path)

    preregistration_path = (
        repository / "validation/preregistration/independent_review.yaml"
    )
    _write_yaml(
        preregistration_path,
        {
            "fixture_notice": "TEST ONLY",
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
            "calibration_ids": ["CAL_REVIEW"],
            "holdout_ids": ["HOLD_REVIEW"],
            "threshold": 0.5,
        },
    )
    _git(
        repository,
        "add",
        preregistration_path.relative_to(repository).as_posix(),
    )
    _git(repository, "commit", "-q", "-m", "Freeze independent preregistration")
    preregistration_commit = _git(repository, "rev-parse", "HEAD")
    preregistration_hash = _sha256(preregistration_path)

    preregistration_record_path = (
        repository / "validation/review_artifacts/preregistration_record.yaml"
    )
    _write_yaml(
        preregistration_record_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_file": preregistration_path.relative_to(
                repository
            ).as_posix(),
            "preregistration_sha256": preregistration_hash,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_REVIEW"],
            "holdout_ids": ["HOLD_REVIEW"],
            "primary_metric": "normalized_rmse",
            "thresholds": {"normalized_rmse": 0.5},
            "parameter_set": ["review_rate"],
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )

    parameters = {"review_rate": 0.25}
    parameter_hash = _canonical_hash(parameters)
    configuration_hash = "2" * 64
    calibration_path = repository / "validation/review_artifacts/calibration.yaml"
    _write_yaml(
        calibration_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_sha256": preregistration_hash,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_REVIEW"],
            "parameter_result_hash": parameter_hash,
            "config_hash": configuration_hash,
            "model_commit": preregistration_commit,
            "parameters": parameters,
            "metrics": {"normalized_rmse": 0.1},
            "status": "CALIBRATION_COMPLETE",
            "generated_at": "2026-01-02T00:00:00Z",
        },
    )

    identifiability_path = (
        repository / "validation/review_artifacts/identifiability.yaml"
    )
    _write_yaml(
        identifiability_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "preregistration_sha256": preregistration_hash,
            "parameter_result_hash": parameter_hash,
            "methods": ["profile_likelihood"],
            "condition_number": 1.5,
            "max_parameter_correlation": 0.1,
            "boundary_hits": [],
            "status": "IDENTIFIABLE",
            "generated_at": "2026-01-02T00:00:00Z",
        },
    )

    prediction_path = repository / "validation/review_artifacts/predictions.csv"
    prediction_path.write_text(
        "sample_id,predicted_bq\nHOLD_REVIEW,16\n",
        encoding="utf-8",
    )
    holdout_path = repository / "validation/review_artifacts/holdout.yaml"
    _write_yaml(
        holdout_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_sha256": preregistration_hash,
            "preregistration_commit": preregistration_commit,
            "model_commit": preregistration_commit,
            "config_hash": configuration_hash,
            "parameter_result_hash": parameter_hash,
            "holdout_ids": ["HOLD_REVIEW"],
            "result_file_checksums": {
                prediction_path.relative_to(repository).as_posix(): _sha256(
                    prediction_path
                )
            },
            "metrics": {"normalized_rmse": 0.2},
            "verdict": holdout_verdict,
            "generated_at": "2026-01-03T00:00:00Z",
        },
    )

    report_paths: dict[str, Path] = {}
    for key, check in (
        ("v1", "V1_RECOMPUTE"),
        ("v2", "V2_ACCEPTANCE"),
        ("validation_readiness", "VALIDATION_READINESS"),
    ):
        report_path = (
            repository / f"validation/review_artifacts/{key}_report.yaml"
        )
        _write_yaml(
            report_path,
            {
                "schema_version": "1.0.0",
                "check": check,
                "status": "PASS",
                "model_commit": preregistration_commit,
                "generated_at": "2026-01-03T00:00:00Z",
            },
        )
        report_paths[key] = report_path

    bundle_path = repository / "validation/review_artifacts/bundle.yaml"
    _write_yaml(
        bundle_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "INDEPENDENT_REVIEW_ONLY",
            "raw_manifest_path": raw_manifest_path.relative_to(
                repository
            ).as_posix(),
            "intake_manifest_path": intake_path.relative_to(repository).as_posix(),
            "preregistration_record_path": preregistration_record_path.relative_to(
                repository
            ).as_posix(),
            "calibration_result_path": calibration_path.relative_to(
                repository
            ).as_posix(),
            "identifiability_result_path": identifiability_path.relative_to(
                repository
            ).as_posix(),
            "holdout_result_path": holdout_path.relative_to(repository).as_posix(),
        },
    )

    config_path = repository / "validation/review_artifacts/gate_config.yaml"
    (repository / "docs/v3/gates").mkdir(parents=True)
    _write_yaml(
        config_path,
        {
            "schema_version": "2.0.0",
            "evidence_bundle_path": bundle_path.relative_to(repository).as_posix(),
            "allowed_artifact_roots": ["validation", "docs/v3/gates"],
            "allowed_raw_data_roots": ["validation/external_local"],
            "required_regression_reports": {
                key: report.relative_to(repository).as_posix()
                for key, report in report_paths.items()
            },
        },
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-q", "-m", "Add independent holdout fixture")

    return config_path, {
        "raw_file": measurement_path,
        "holdout": holdout_path,
    }


def _build_independent_chain(
    repository: Path,
    *,
    holdout_verdict: str = "PASS",
) -> tuple[Path, dict[str, Path]]:
    """Use a separately named protected-ref chain for the imported attacks."""

    return build_protected_gate_repository(
        repository,
        dataset_id="INDEPENDENT_REVIEW_ONLY",
        declared_verdict=holdout_verdict,
    )


def test_rejects_production_reference_to_test_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, _ = _build_independent_chain(tmp_path)
    monkeypatch.setattr(gate, "ROOT", tmp_path)

    result = gate.evaluate_gate(config_path)

    assert result["status"] == EXPECTED_BLOCKED


def test_rejects_raw_file_replaced_after_initial_checksum(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_independent_chain(tmp_path)
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    original_verify = gate.verify_manifest_file_entries

    def verify_then_replace(*args, **kwargs):
        checksums = original_verify(*args, **kwargs)
        original = paths["raw_file"].read_text(encoding="utf-8")
        replacement = original.replace("CAL_001,1", "CAL_001,9")
        assert len(replacement.encode("utf-8")) == len(original.encode("utf-8"))
        paths["raw_file"].write_text(replacement, encoding="utf-8")
        return checksums

    monkeypatch.setattr(
        gate,
        "verify_manifest_file_entries",
        verify_then_replace,
    )

    result = gate.evaluate_gate_for_test(
        config_path,
        repository_root=tmp_path,
    )

    assert result["status"] == EXPECTED_BLOCKED


def test_rejects_failed_holdout_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, _ = _build_independent_chain(
        tmp_path,
        holdout_verdict="FAIL",
    )
    monkeypatch.setattr(gate, "ROOT", tmp_path)

    result = gate.evaluate_gate_for_test(
        config_path,
        repository_root=tmp_path,
    )

    assert result["status"] == EXPECTED_BLOCKED
