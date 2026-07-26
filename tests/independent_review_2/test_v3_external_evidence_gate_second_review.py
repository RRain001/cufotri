from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import yaml

import scripts.verify_v3_physics_start_gate as gate
from validation.evidence_validation import calculate_sha256


EXPECTED_BLOCKED = "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _entry_projection(entry: dict) -> dict:
    projected = {
        key: value for key, value in entry.items() if key != "approval"
    }
    licence = dict(projected["licence_review"])
    licence.pop("review_record_sha256", None)
    projected["licence_review"] = licence
    return projected


def _build_independent_parameter_chain(
    repository: Path,
) -> tuple[Path, dict[str, Path]]:
    """Build a new chain without importing remediation fixture builders."""

    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "config", "user.email", "review2@example.invalid")
    _git(repository, "config", "user.name", "Second Independent Reviewer")

    dataset_id = "REVIEW2_PARAMETER_FREEZE"
    raw_directory = repository / "validation/external_local/review2_parameter"
    raw_directory.mkdir(parents=True)
    observations = raw_directory / "review2_observations.csv"
    observations.write_text(
        "case_id,observed_bq\nCAL_R2,10\nHOLD_R2,20\n",
        encoding="utf-8",
    )
    observations_hash = calculate_sha256(observations)
    source = {
        "title": "Second-review isolated parameter-freeze chain",
        "authority": "Independent reviewer fixture authority",
        "reference": "test://independent-review-2/parameter-freeze",
    }
    raw_manifest = raw_directory / "review2_raw_manifest.yaml"
    _write_yaml(
        raw_manifest,
        {
            "manifest_schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "dataset_version": "review2-1",
            "artifact_purpose": "SECOND_INDEPENDENT_REVIEW_ONLY",
            "test_only": True,
            "origin_class": "INDEPENDENT_REVIEW_2",
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "source": source,
            "licence_status": "VERIFIED",
            "local_use_allowed": True,
            "redistribution_allowed": False,
            "exposure_start_utc": "2026-02-01T00:00:00Z",
            "exposure_end_utc": "2026-02-01T01:00:00Z",
            "expected_time_step_seconds": 3600,
            "files": [
                {
                    "path": observations.name,
                    "role": "review2_observations",
                    "expected_sha256": observations_hash,
                    "calculated_sha256": observations_hash,
                    "size_bytes": observations.stat().st_size,
                    "format": "csv",
                }
            ],
            "units": {
                "review2_observations": {"observed_bq": "Bq"}
            },
            "calibration_sample_ids": ["CAL_R2"],
            "holdout_sample_ids": ["HOLD_R2"],
            "holdout_inspected_before_preregistration": False,
        },
    )
    raw_manifest_hash = calculate_sha256(raw_manifest)

    approval_record = (
        repository
        / "validation/v3/policy/approvals/review2_parameter_approval.yaml"
    )
    entry_core = {
        "dataset_id": dataset_id,
        "raw_manifest_sha256": raw_manifest_hash,
        "evidence_type": "CONTROLLED_EXPERIMENT",
        "empirical_eligibility": "APPROVED",
        "test_only": True,
        "source_authority": {
            "organization": source["authority"],
            "dataset_title": source["title"],
            "reference": source["reference"],
        },
        "licence_review": {
            "status": "APPROVED_LOCAL_USE",
            "review_record_path": approval_record.relative_to(
                repository
            ).as_posix(),
            "review_record_sha256": "0" * 64,
        },
    }
    entry_hash = _canonical_hash(_entry_projection(entry_core))
    registry_hash = _canonical_hash(
        {
            "schema_version": "1.0",
            "entries": [_entry_projection(entry_core)],
        }
    )
    _write_yaml(
        approval_record,
        {
            "schema_version": "1.0",
            "dataset_id": dataset_id,
            "decision": "APPROVED",
            "test_only": True,
            "approved_entry_sha256": entry_hash,
            "approved_registry_sha256": registry_hash,
        },
    )
    _git(
        repository,
        "add",
        approval_record.relative_to(repository).as_posix(),
    )
    _git(repository, "commit", "-q", "-m", "Approve review2 chain")
    approval_commit = _git(repository, "rev-parse", "HEAD")
    entry = {
        **entry_core,
        "licence_review": {
            **entry_core["licence_review"],
            "review_record_sha256": calculate_sha256(approval_record),
        },
        "approval": {
            "approval_commit": approval_commit,
            "approved_registry_sha256": registry_hash,
            "approved_entry_sha256": entry_hash,
        },
    }
    registry = repository / gate.TRUSTED_POLICY_PATH
    _write_yaml(registry, {"schema_version": "1.0", "entries": [entry]})
    _git(repository, "add", registry.relative_to(repository).as_posix())
    _git(repository, "commit", "-q", "-m", "Publish review2 policy")
    main_sha = _git(repository, "rev-parse", "HEAD")
    _git(
        repository,
        "update-ref",
        gate.TRUSTED_REMOTE_REF,
        main_sha,
    )
    _git(repository, "switch", "-q", "-c", "review2-evidence")

    intake = repository / "validation/review2/intake.yaml"
    _write_yaml(
        intake,
        {
            "manifest_schema_version": "2.0.0",
            "dataset_id": dataset_id,
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "raw_manifest_path": raw_manifest.relative_to(repository).as_posix(),
            "raw_manifest_sha256": raw_manifest_hash,
            "adapter_version": "2.0.0",
            "field_mapping": {
                "review2_observations": {"observed_bq": "observed_bq"}
            },
            "unit_mapping": {
                "review2_observations": {
                    "observed_bq": {
                        "declared_unit": "Bq",
                        "canonical_unit": "Bq",
                        "conversion": "identity",
                    }
                }
            },
            "time_coverage": {},
            "exposure_coverage": {
                "start_utc": "2026-02-01T00:00:00Z",
                "end_utc": "2026-02-01T01:00:00Z",
                "forcing_complete": True,
            },
            "calibration_ids": ["CAL_R2"],
            "holdout_ids": ["HOLD_R2"],
            "validation_summary": {
                "schema_validated": True,
                "numeric_content_validated": True,
                "checksums_recomputed": True,
            },
            "generated_files": [],
            "calculated_checksums": {
                "review2_observations": observations_hash
            },
            "intake_status": "READY_FOR_PREREGISTRATION",
            "status": "READY_FOR_PREREGISTRATION",
            "checksums_sha256": {
                "review2_observations": observations_hash
            },
            "field_mappings": {
                "review2_observations": {"observed_bq": "observed_bq"}
            },
            "calibration_sample_ids": ["CAL_R2"],
            "holdout_sample_ids": ["HOLD_R2"],
            "empirical_validation": False,
            "calibration_permitted": False,
            "holdout_execution_permitted": False,
            "blocking_reasons": [],
            "metric_pipeline": {"status": "NOT_RUN_NO_MODEL_OUTPUT"},
        },
    )
    intake_hash = calculate_sha256(intake)
    prediction_reference = "validation/review2/predictions.csv"
    metric_rule = {
        "metric_id": "review2_nrmse",
        "required": True,
        "comparator": "LE",
        "threshold": 0.3,
        "value_unit": "1",
        "missing_policy": "FAIL",
        "calculation": {
            "method": "NORMALIZED_RMSE",
            "observation_role": "review2_observations",
            "observation_id_column": "case_id",
            "observation_value_column": "observed_bq",
            "result_file": prediction_reference,
            "prediction_id_column": "case_id",
            "prediction_value_column": "predicted_bq",
        },
    }
    frozen = repository / "validation/review2/frozen_preregistration.yaml"
    _write_yaml(
        frozen,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "calibration_ids": ["CAL_R2"],
            "holdout_ids": ["HOLD_R2"],
            "primary_metrics": [metric_rule],
            "parameter_set": ["approved_decay_rate"],
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )
    _git(repository, "add", frozen.relative_to(repository).as_posix())
    _git(repository, "commit", "-q", "-m", "Freeze review2 contract")
    preregistration_commit = _git(repository, "rev-parse", "HEAD")
    frozen_hash = calculate_sha256(frozen)
    preregistration = repository / "validation/review2/preregistration.yaml"
    _write_yaml(
        preregistration,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_file": frozen.relative_to(repository).as_posix(),
            "preregistration_sha256": frozen_hash,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_R2"],
            "holdout_ids": ["HOLD_R2"],
            "primary_metrics": [metric_rule],
            "parameter_set": ["approved_decay_rate"],
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )

    parameters = {"approved_decay_rate": 0.2}
    parameter_hash = _canonical_hash(parameters)
    config_hash = "3" * 64
    calibration = repository / "validation/review2/calibration.yaml"
    _write_yaml(
        calibration,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_sha256": frozen_hash,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_R2"],
            "parameter_result_hash": parameter_hash,
            "config_hash": config_hash,
            "model_commit": preregistration_commit,
            "parameters": parameters,
            "metrics": {"review2_nrmse": 0.1},
            "status": "CALIBRATION_COMPLETE",
            "generated_at": "2026-02-02T00:00:00Z",
        },
    )
    identifiability = repository / "validation/review2/identifiability.yaml"
    _write_yaml(
        identifiability,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "preregistration_sha256": frozen_hash,
            "parameter_result_hash": parameter_hash,
            "methods": ["profile_likelihood"],
            "condition_number": 1.2,
            "max_parameter_correlation": 0.1,
            "boundary_hits": [],
            "status": "IDENTIFIABLE",
            "generated_at": "2026-02-02T00:00:00Z",
        },
    )
    predictions = repository / prediction_reference
    predictions.write_text(
        "case_id,predicted_bq\nHOLD_R2,24\n",
        encoding="utf-8",
    )
    holdout = repository / "validation/review2/holdout.yaml"
    _write_yaml(
        holdout,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_sha256": frozen_hash,
            "preregistration_commit": preregistration_commit,
            "model_commit": preregistration_commit,
            "config_hash": config_hash,
            "parameter_result_hash": parameter_hash,
            "holdout_ids": ["HOLD_R2"],
            "result_file_checksums": {
                prediction_reference: calculate_sha256(predictions)
            },
            "metrics": [
                {
                    "metric_id": "review2_nrmse",
                    "value": 0.2,
                    "value_unit": "1",
                }
            ],
            "declared_verdict": "PASS",
            "generated_at": "2026-02-03T00:00:00Z",
        },
    )
    reports: dict[str, Path] = {}
    for name, check in (
        ("v1", "V1_RECOMPUTE"),
        ("v2", "V2_ACCEPTANCE"),
        ("validation_readiness", "VALIDATION_READINESS"),
    ):
        report = repository / f"validation/review2/{name}.yaml"
        _write_yaml(
            report,
            {
                "schema_version": "1.0.0",
                "check": check,
                "status": "PASS",
                "model_commit": preregistration_commit,
                "generated_at": "2026-02-03T00:00:00Z",
            },
        )
        reports[name] = report
    bundle = repository / "validation/review2/bundle.yaml"
    _write_yaml(
        bundle,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_hash,
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "artifact_purpose": "SECOND_INDEPENDENT_REVIEW_ONLY",
            "test_only": True,
            "origin_class": "INDEPENDENT_REVIEW_2",
            "raw_manifest_path": raw_manifest.relative_to(repository).as_posix(),
            "intake_manifest_path": intake.relative_to(repository).as_posix(),
            "preregistration_record_path": preregistration.relative_to(
                repository
            ).as_posix(),
            "calibration_result_path": calibration.relative_to(
                repository
            ).as_posix(),
            "identifiability_result_path": identifiability.relative_to(
                repository
            ).as_posix(),
            "holdout_result_path": holdout.relative_to(repository).as_posix(),
        },
    )
    config = repository / "validation/review2/gate.yaml"
    (repository / "docs/v3/gates").mkdir(parents=True)
    _write_yaml(
        config,
        {
            "schema_version": "3.0.0",
            "evidence_bundle_path": bundle.relative_to(repository).as_posix(),
            "allowed_raw_data_roots": ["validation/external_local"],
            "required_regression_reports": {
                key: value.relative_to(repository).as_posix()
                for key, value in reports.items()
            },
        },
    )
    _git(repository, "add", ".")
    _git(repository, "commit", "-q", "-m", "Commit review2 holdout chain")
    return config, {
        "calibration": calibration,
        "identifiability": identifiability,
        "holdout": holdout,
    }


def test_rejects_calibration_parameter_set_not_frozen_by_preregistration(
    tmp_path: Path,
) -> None:
    config, paths = _build_independent_parameter_chain(tmp_path)
    baseline = gate.evaluate_gate_for_test(
        config,
        repository_root=tmp_path,
    )
    assert baseline["status"] == "READY_FOR_BOUNDED_V3_PHYSICS"

    replacement_parameters = {"unregistered_rate": 0.2}
    replacement_hash = _canonical_hash(replacement_parameters)
    calibration = yaml.safe_load(
        paths["calibration"].read_text(encoding="utf-8")
    )
    calibration["parameters"] = replacement_parameters
    calibration["parameter_result_hash"] = replacement_hash
    _write_yaml(paths["calibration"], calibration)
    identifiability = yaml.safe_load(
        paths["identifiability"].read_text(encoding="utf-8")
    )
    identifiability["parameter_result_hash"] = replacement_hash
    _write_yaml(paths["identifiability"], identifiability)
    holdout = yaml.safe_load(paths["holdout"].read_text(encoding="utf-8"))
    holdout["parameter_result_hash"] = replacement_hash
    _write_yaml(paths["holdout"], holdout)
    _git(
        tmp_path,
        "add",
        *(path.relative_to(tmp_path).as_posix() for path in paths.values()),
    )
    _git(
        tmp_path,
        "commit",
        "-q",
        "-m",
        "Replace frozen parameter set after preregistration",
    )

    attacked = gate.evaluate_gate_for_test(
        config,
        repository_root=tmp_path,
    )
    assert attacked["status"] == EXPECTED_BLOCKED
