from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import scripts.verify_v3_physics_start_gate as physics_gate
from validation.evidence_validation import (
    EvidenceValidationError,
    calculate_sha256,
    require_regular_file,
)
from validation.adapters.soybean_emras_adapter import (
    create_synthetic_package,
    validate_local_package,
)


ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_CASE = (
    ROOT / "validation/cases/soybean_external_contract_synthetic.yaml"
)


def _load_source(package: Path) -> dict:
    return yaml.safe_load(
        (package / "source_manifest.yaml").read_text(encoding="utf-8")
    )


def _write_source(package: Path, source: dict) -> None:
    (package / "source_manifest.yaml").write_text(
        yaml.safe_dump(source, sort_keys=False),
        encoding="utf-8",
    )


def test_jsonschema_dependency_is_available() -> None:
    version = importlib.metadata.version("jsonschema")
    assert tuple(int(item) for item in version.split(".")[:2]) >= (4, 23)


def test_require_regular_file_rejects_broken_symlink(tmp_path: Path) -> None:
    broken = tmp_path / "broken.yaml"
    broken.symlink_to(tmp_path / "missing-target.yaml")

    with pytest.raises(EvidenceValidationError, match="does not exist"):
        require_regular_file(broken, allowed_roots=[tmp_path])


def _refresh_file_checksum(package: Path, role: str) -> None:
    source = _load_source(package)
    entry = next(item for item in source["files"] if item["role"] == role)
    path = package / entry["path"]
    checksum = calculate_sha256(path)
    entry["expected_sha256"] = checksum
    entry["calculated_sha256"] = checksum
    entry["size_bytes"] = path.stat().st_size
    _write_source(package, source)


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
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def _build_gate_repository(
    root: Path,
    *,
    evidence_type: str = "CONTROLLED_EXPERIMENT",
) -> tuple[Path, dict[str, Path]]:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Evidence Gate Test")

    raw_directory = root / "validation/external_local/gate_fixture"
    raw_directory.mkdir(parents=True)
    raw_file = raw_directory / "observations.csv"
    raw_file.write_text("sample_id,value\nCAL_001,1\nHOLD_001,2\n", encoding="utf-8")
    raw_checksum = calculate_sha256(raw_file)
    raw_manifest_path = raw_directory / "source_manifest.yaml"
    raw_manifest = {
        "manifest_schema_version": "1.0.0",
        "dataset_id": "GATE_FIXTURE",
        "dataset_version": "1.0.0",
        "evidence_type": evidence_type,
        "source": {
            "title": "Test-only complete artifact chain",
            "authority": "pytest fixture",
            "reference": "not empirical evidence",
        },
        "licence_status": (
            "VERIFIED"
            if evidence_type in physics_gate.ELIGIBLE_EVIDENCE_TYPES
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
    _write_yaml(raw_manifest_path, raw_manifest)
    raw_manifest_sha256 = calculate_sha256(raw_manifest_path)

    intake_path = root / "validation/intake/gate_fixture.yaml"
    intake = {
        "manifest_schema_version": "2.0.0",
        "dataset_id": "GATE_FIXTURE",
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
    _write_yaml(intake_path, intake)
    intake_sha256 = calculate_sha256(intake_path)

    preregistration_file = root / "validation/preregistration/gate_fixture.yaml"
    _write_yaml(
        preregistration_file,
        {
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
            "calibration_ids": ["CAL_001"],
            "holdout_ids": ["HOLD_001"],
            "primary_metric": "normalized_rmse",
            "threshold": 0.25,
        },
    )
    _git(root, "add", preregistration_file.relative_to(root).as_posix())
    _git(root, "commit", "-q", "-m", "Freeze preregistration")
    preregistration_commit = _git(root, "rev-parse", "HEAD")
    preregistration_sha256 = calculate_sha256(preregistration_file)

    preregistration_record_path = (
        root / "validation/preregistration/gate_fixture_record.yaml"
    )
    _write_yaml(
        preregistration_record_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "GATE_FIXTURE",
            "raw_manifest_sha256": raw_manifest_sha256,
            "intake_manifest_sha256": intake_sha256,
            "preregistration_file": preregistration_file.relative_to(root).as_posix(),
            "preregistration_sha256": preregistration_sha256,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_001"],
            "holdout_ids": ["HOLD_001"],
            "primary_metric": "normalized_rmse",
            "thresholds": {"normalized_rmse": 0.25},
            "parameter_set": ["turnover_rate"],
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )

    parameters = {"turnover_rate": 0.1}
    parameter_hash = hashlib.sha256(
        json.dumps(
            parameters,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    config_hash = "1" * 64
    calibration_path = root / "validation/results/calibration.yaml"
    _write_yaml(
        calibration_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "GATE_FIXTURE",
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
    _write_yaml(
        identifiability_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "GATE_FIXTURE",
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
    model_output_path.write_text("sample_id,prediction\nHOLD_001,2\n", encoding="utf-8")
    holdout_path = root / "validation/results/holdout.yaml"
    _write_yaml(
        holdout_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "GATE_FIXTURE",
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
            "metrics": {"normalized_rmse": 0.2},
            "verdict": "PASS",
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
        _write_yaml(
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
    _write_yaml(
        bundle_path,
        {
            "schema_version": "1.0.0",
            "dataset_id": "GATE_FIXTURE",
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
    _write_yaml(
        config_path,
        {
            "schema_version": "2.0.0",
            "evidence_bundle_path": bundle_path.relative_to(root).as_posix(),
            "allowed_artifact_roots": ["validation", "docs/v3/gates"],
            "allowed_raw_data_roots": ["validation/external_local"],
            "required_regression_reports": {
                key: path.relative_to(root).as_posix()
                for key, path in report_paths.items()
            },
        },
    )
    (root / "docs/v3/gates").mkdir(parents=True)
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "Add holdout evidence")
    return config_path, {
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
    }


def test_physics_gate_rejects_nonexistent_manifest_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_root = tmp_path / "repository"
    (fake_root / "validation/cases").mkdir(parents=True)
    (fake_root / "validation/preregistration").mkdir(parents=True)
    (fake_root / "validation/cases/soybean_emras_template.yaml").write_text(
        "status: CLAIMED_COMPLETE\n",
        encoding="utf-8",
    )
    (
        fake_root
        / "validation/preregistration/soybean_emras_template.yaml"
    ).write_text("status: PREREGISTERED\n", encoding="utf-8")
    evidence = {name: True for name in physics_gate.REQUIRED_TRUE}
    evidence.update(
        {
            "external_case_manifest": "validation/missing-intake.yaml",
            "holdout_result_manifest": "validation/missing-holdout.yaml",
            "evidence": {
                "external_case": "PASS",
                "external_case_evidence_type": "EXTERNAL_EXPERIMENT",
                "preregistration": "PREREGISTERED",
                "calibration": "CALIBRATION_COMPLETE",
                "identifiability": "IDENTIFIABLE",
                "holdout": "PASS",
                "holdout_evidence_type": "EXTERNAL_EXPERIMENT",
            },
        }
    )
    evidence_path = fake_root / "gate.yaml"
    evidence_path.write_text(
        yaml.safe_dump(evidence, sort_keys=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(physics_gate, "ROOT", fake_root)

    result = physics_gate.evaluate_gate(evidence_path)

    assert result["status"] != "READY_FOR_BOUNDED_V3_PHYSICS"


def test_intake_rejects_non_numeric_air_hto(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    air_path = tmp_path / "air_hto.csv"
    air_path.write_text(
        "time_utc,air_hto_bq_m3\n"
        "2025-01-01T00:00:00Z,not-a-number\n"
        "2025-01-01T01:00:00Z,not-a-number\n"
        "2025-01-01T02:00:00Z,not-a-number\n",
        encoding="utf-8",
    )

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(
        "air_hto_bq_m3" in reason
        for reason in result["blocking_reasons"]
    )


def test_intake_rejects_empty_detection_limit_values(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    detection_path = tmp_path / "detection_limits.csv"
    detection_path.write_text(
        "observable,detection_limit,unit\n,,\n",
        encoding="utf-8",
    )

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(
        "detection_limit" in reason
        for reason in result["blocking_reasons"]
    )


@pytest.mark.parametrize("invalid", ["nan", "inf", "-inf"])
def test_intake_rejects_nan_and_inf(tmp_path: Path, invalid: str) -> None:
    create_synthetic_package(tmp_path)
    air_path = tmp_path / "air_hto.csv"
    air_path.write_text(
        "time_utc,air_hto_bq_m3\n"
        f"2025-01-01T00:00:00Z,{invalid}\n"
        "2025-01-01T01:00:00Z,1\n"
        "2025-01-01T02:00:00Z,0\n",
        encoding="utf-8",
    )
    _refresh_file_checksum(tmp_path, "air_hto")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("must be finite" in reason for reason in result["blocking_reasons"])


def test_intake_rejects_negative_detection_limit(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    path = tmp_path / "detection_limits.csv"
    path.write_text(
        "observable,detection_limit,unit\n"
        "observed_plant_water_hto_bq_l,-1,Bq L-1 plant water\n",
        encoding="utf-8",
    )
    _refresh_file_checksum(tmp_path, "detection_limits")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("must be >= 0.0" in reason for reason in result["blocking_reasons"])


def _assert_nonpositive_mixing_boundary(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    create_synthetic_package(tmp_path)
    path = tmp_path / "mixing_boundary.yaml"
    mixing = yaml.safe_load(path.read_text(encoding="utf-8"))
    mixing[field] = value
    path.write_text(yaml.safe_dump(mixing), encoding="utf-8")
    _refresh_file_checksum(tmp_path, "mixing_boundary")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(field in reason for reason in result["blocking_reasons"])


def test_intake_rejects_nonpositive_chamber_volume(tmp_path: Path) -> None:
    _assert_nonpositive_mixing_boundary(
        tmp_path,
        "chamber_volume_m3",
        "0",
    )


def test_intake_rejects_nonpositive_mixing_rate(tmp_path: Path) -> None:
    _assert_nonpositive_mixing_boundary(
        tmp_path,
        "ventilation_or_mixing_rate_s",
        "-0.01",
    )


@pytest.mark.parametrize(
    "replacement",
    [
        "2025-01-01T00:00:00Z",
        "2024-12-31T23:00:00Z",
    ],
)
def test_intake_rejects_duplicate_or_nonmonotonic_timestamps(
    tmp_path: Path,
    replacement: str,
) -> None:
    create_synthetic_package(tmp_path)
    path = tmp_path / "air_hto.csv"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "2025-01-01T01:00:00Z",
            replacement,
        ),
        encoding="utf-8",
    )
    _refresh_file_checksum(tmp_path, "air_hto")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(
        "strictly increasing and unique" in reason
        for reason in result["blocking_reasons"]
    )


def test_intake_rejects_incomplete_exposure_coverage(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    path = tmp_path / "meteorology.csv"
    path.write_text(
        "time_utc,temperature_k,relative_humidity_percent\n"
        "2025-01-01T01:00:00Z,294.15,61\n"
        "2025-01-01T02:00:00Z,295.15,62\n",
        encoding="utf-8",
    )
    _refresh_file_checksum(tmp_path, "meteorology")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(
        "does not cover the exposure interval" in reason
        for reason in result["blocking_reasons"]
    )


def test_intake_rejects_calibration_holdout_overlap(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    source = _load_source(tmp_path)
    source["holdout_sample_ids"] = ["CAL_001"]
    _write_source(tmp_path, source)

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("overlap" in reason for reason in result["blocking_reasons"])


def test_intake_rejects_checksum_mismatch(tmp_path: Path) -> None:
    create_synthetic_package(tmp_path)
    path = tmp_path / "air_hto.csv"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    result = validate_local_package(SYNTHETIC_CASE, tmp_path)

    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("checksum mismatch" in reason for reason in result["blocking_reasons"])


def test_source_checksum_unavailable_still_requires_local_checksum(
    tmp_path: Path,
) -> None:
    create_synthetic_package(tmp_path)
    source = _load_source(tmp_path)
    entry = next(item for item in source["files"] if item["role"] == "air_hto")
    entry["expected_sha256"] = "SOURCE_CHECKSUM_UNAVAILABLE"
    _write_source(tmp_path, source)

    accepted = validate_local_package(SYNTHETIC_CASE, tmp_path)
    assert accepted["status"] == "PASS_SYNTHETIC_CONTRACT_ONLY"

    source = _load_source(tmp_path)
    entry = next(item for item in source["files"] if item["role"] == "air_hto")
    entry["calculated_sha256"] = "0" * 64
    _write_source(tmp_path, source)
    rejected = validate_local_package(SYNTHETIC_CASE, tmp_path)
    assert rejected["status"] == "BLOCKED_EXTERNAL_DATA"


def test_complete_test_fixture_exercises_full_gate_logic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, _ = _build_gate_repository(tmp_path)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "READY_FOR_BOUNDED_V3_PHYSICS"
    assert all(value == "PASS" for value in result["diagnostics"].values())


def _assert_gate_rejects_evidence_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    evidence_type: str,
) -> None:
    config_path, _ = _build_gate_repository(
        tmp_path,
        evidence_type=evidence_type,
    )
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_synthetic_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_gate_rejects_evidence_type(
        tmp_path,
        monkeypatch,
        "SYNTHETIC_CONTRACT_TEST",
    )


def test_physics_gate_rejects_internal_reference_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_gate_rejects_evidence_type(
        tmp_path,
        monkeypatch,
        "INTERNAL_REFERENCE",
    )


@pytest.mark.parametrize("attack", ["directory", "empty", "invalid_schema"])
def test_physics_gate_rejects_invalid_bundle_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attack: str,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if attack == "directory":
        config["evidence_bundle_path"] = "validation/v3"
    elif attack == "empty":
        empty = tmp_path / "validation/v3/empty.yaml"
        empty.write_text("", encoding="utf-8")
        config["evidence_bundle_path"] = empty.relative_to(tmp_path).as_posix()
    else:
        bundle = yaml.safe_load(paths["bundle"].read_text(encoding="utf-8"))
        bundle.pop("dataset_id")
        _write_yaml(paths["bundle"], bundle)
    _write_yaml(config_path, config)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_raw_checksum_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    paths["raw_file"].write_text("tampered\n", encoding="utf-8")
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_checksum_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    raw_manifest = yaml.safe_load(
        paths["raw_manifest"].read_text(encoding="utf-8")
    )
    raw_manifest["files"][0]["expected_sha256"] = "0" * 64
    _write_yaml(paths["raw_manifest"], raw_manifest)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_manifest_not_validated_by_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    bundle = yaml.safe_load(paths["bundle"].read_text(encoding="utf-8"))
    bundle.pop("dataset_id")
    _write_yaml(paths["bundle"], bundle)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_missing_holdout_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    paths["holdout"].unlink()
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_uncommitted_preregistration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    paths["preregistration_file"].write_text(
        paths["preregistration_file"].read_text(encoding="utf-8") + "# changed\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_preregistration_committed_after_holdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    holdout_commit = _git(tmp_path, "rev-parse", "HEAD")
    for artifact_name in ("preregistration_record", "calibration", "holdout"):
        artifact = yaml.safe_load(
            paths[artifact_name].read_text(encoding="utf-8")
        )
        artifact["preregistration_commit"] = holdout_commit
        _write_yaml(paths[artifact_name], artifact)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_non_numeric_holdout_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, paths = _build_gate_repository(tmp_path)
    holdout = yaml.safe_load(paths["holdout"].read_text(encoding="utf-8"))
    holdout["metrics"]["normalized_rmse"] = "not-a-number"
    _write_yaml(paths["holdout"], holdout)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_manual_boolean_bypass_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, _ = _build_gate_repository(tmp_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for name in physics_gate.REQUIRED_TRUE:
        config[name] = True
    config["evidence_bundle_path"] = "validation/missing-bundle.yaml"
    _write_yaml(config_path, config)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def test_physics_gate_rejects_path_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, _ = _build_gate_repository(tmp_path)
    outside = tmp_path / "outside-bundle.yaml"
    outside.write_text(
        "schema_version: 1.0.0\ndataset_id: OUTSIDE\n",
        encoding="utf-8",
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["evidence_bundle_path"] = outside.as_posix()
    _write_yaml(config_path, config)
    monkeypatch.setattr(physics_gate, "ROOT", tmp_path)

    result = physics_gate.evaluate_gate(config_path)

    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
