from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import pytest
import yaml

import scripts.verify_v3_physics_start_gate as gate
from validation.evidence_validation import calculate_sha256


READY = "READY_FOR_BOUNDED_V3_PHYSICS"
BLOCKED = "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _contract_hash(contract: list[dict[str, Any]]) -> str:
    normalized = []
    for item in sorted(contract, key=lambda value: str(value["name"])):
        normalized.append(
            {
                "name": item["name"],
                "unit": item["unit"],
                "lower_bound": float(item["lower_bound"]),
                "upper_bound": float(item["upper_bound"]),
                "lower_inclusive": item["lower_inclusive"],
                "upper_inclusive": item["upper_inclusive"],
                "transform": item["transform"],
            }
        )
    return _canonical_hash(normalized)


def _result_hash(parameters: dict[str, dict[str, Any]]) -> str:
    normalized = []
    for name in sorted(parameters):
        supplied = parameters[name]
        value = supplied["value"]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
        ):
            return "0" * 64
        normalized.append(
            {
                "name": name,
                "value": float(value),
                "unit": supplied.get("unit", ""),
                "transform": supplied.get("transform", ""),
            }
        )
    return _canonical_hash(normalized)


def _entry_projection(entry: dict[str, Any]) -> dict[str, Any]:
    projected = {
        key: value for key, value in entry.items() if key != "approval"
    }
    licence = dict(projected["licence_review"])
    licence.pop("review_record_sha256", None)
    projected["licence_review"] = licence
    return projected


def _default_contract() -> list[dict[str, Any]]:
    # Intentionally not sorted: parameter order has no physical meaning.
    return [
        {
            "name": "transfer_rate",
            "unit": "s-1",
            "lower_bound": 0.0,
            "upper_bound": 1.0,
            "lower_inclusive": True,
            "upper_inclusive": True,
            "transform": "IDENTITY",
        },
        {
            "name": "partition_fraction",
            "unit": "1",
            "lower_bound": 0.0,
            "upper_bound": 1.0,
            "lower_inclusive": False,
            "upper_inclusive": False,
            "transform": "LOGIT",
        },
    ]


def _default_parameters() -> dict[str, dict[str, Any]]:
    # Intentionally a different order from the frozen contract.
    return {
        "partition_fraction": {
            "value": 0.4,
            "unit": "1",
            "transform": "LOGIT",
        },
        "transfer_rate": {
            "value": 0.25,
            "unit": "s-1",
            "transform": "IDENTITY",
        },
    }


def _parameter_results(
    parameters: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name, supplied in parameters.items():
        value = supplied.get("value")
        numeric = (
            float(value)
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            else 0.0
        )
        results[name] = {
            "status": "IDENTIFIABLE",
            "lower_interval": numeric - 0.01,
            "upper_interval": numeric + 0.01,
            "boundary_hit": False,
        }
    return results


def _build_review3_chain(
    repository: Path,
    *,
    contract: list[dict[str, Any]] | None = None,
    parameters: dict[str, dict[str, Any]] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Build an independent two-parameter protected-ref evidence chain."""

    contract = deepcopy(contract if contract is not None else _default_contract())
    parameters = deepcopy(
        parameters if parameters is not None else _default_parameters()
    )
    contract_digest = _contract_hash(contract)
    result_digest = _result_hash(parameters)

    _git(repository, "init", "-q", "-b", "main")
    _git(repository, "config", "user.email", "review3@example.invalid")
    _git(repository, "config", "user.name", "Third Independent Reviewer")

    dataset_id = "REVIEW3_PARAMETER_CONTRACT"
    raw_directory = (
        repository / "validation/external_local/review3_parameter_contract"
    )
    raw_directory.mkdir(parents=True)
    observations = raw_directory / "observations.csv"
    observations.write_text(
        "case_id,observed_bq\nCAL_R3,10\nHOLD_R3,20\n",
        encoding="utf-8",
    )
    observations_hash = calculate_sha256(observations)
    source = {
        "title": "Third independent parameter-contract review chain",
        "authority": "Independent review fixture authority",
        "reference": "test://independent-review-3/parameter-contract",
    }
    raw_manifest = raw_directory / "raw_manifest.yaml"
    _write_yaml(
        raw_manifest,
        {
            "manifest_schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "dataset_version": "review3-1",
            "artifact_purpose": "THIRD_INDEPENDENT_REVIEW_ONLY",
            "test_only": True,
            "origin_class": "INDEPENDENT_REVIEW_3",
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "source": source,
            "licence_status": "VERIFIED",
            "local_use_allowed": True,
            "redistribution_allowed": False,
            "exposure_start_utc": "2026-03-01T00:00:00Z",
            "exposure_end_utc": "2026-03-01T01:00:00Z",
            "expected_time_step_seconds": 3600,
            "files": [
                {
                    "path": observations.name,
                    "role": "review3_observations",
                    "expected_sha256": observations_hash,
                    "calculated_sha256": observations_hash,
                    "size_bytes": observations.stat().st_size,
                    "format": "csv",
                }
            ],
            "units": {
                "review3_observations": {"observed_bq": "Bq"}
            },
            "calibration_sample_ids": ["CAL_R3"],
            "holdout_sample_ids": ["HOLD_R3"],
            "holdout_inspected_before_preregistration": False,
        },
    )
    raw_manifest_hash = calculate_sha256(raw_manifest)

    approval_record = (
        repository
        / "validation/v3/policy/approvals/review3_parameter_approval.yaml"
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
    entry_digest = _canonical_hash(_entry_projection(entry_core))
    registry_digest = _canonical_hash(
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
            "approved_entry_sha256": entry_digest,
            "approved_registry_sha256": registry_digest,
        },
    )
    _git(repository, "add", approval_record.relative_to(repository).as_posix())
    _git(repository, "commit", "-q", "-m", "Approve review3 test chain")
    approval_commit = _git(repository, "rev-parse", "HEAD")

    entry = {
        **entry_core,
        "licence_review": {
            **entry_core["licence_review"],
            "review_record_sha256": calculate_sha256(approval_record),
        },
        "approval": {
            "approval_commit": approval_commit,
            "approved_registry_sha256": registry_digest,
            "approved_entry_sha256": entry_digest,
        },
    }
    registry = repository / gate.TRUSTED_POLICY_PATH
    _write_yaml(registry, {"schema_version": "1.0", "entries": [entry]})
    _git(repository, "add", registry.relative_to(repository).as_posix())
    _git(repository, "commit", "-q", "-m", "Publish review3 test policy")
    protected_main = _git(repository, "rev-parse", "HEAD")
    _git(repository, "update-ref", gate.TRUSTED_REMOTE_REF, protected_main)
    _git(repository, "switch", "-q", "-c", "review3-evidence")

    intake = repository / "validation/review3/intake.yaml"
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
                "review3_observations": {"observed_bq": "observed_bq"}
            },
            "unit_mapping": {
                "review3_observations": {
                    "observed_bq": {
                        "declared_unit": "Bq",
                        "canonical_unit": "Bq",
                        "conversion": "identity",
                    }
                }
            },
            "time_coverage": {},
            "exposure_coverage": {
                "start_utc": "2026-03-01T00:00:00Z",
                "end_utc": "2026-03-01T01:00:00Z",
                "forcing_complete": True,
            },
            "calibration_ids": ["CAL_R3"],
            "holdout_ids": ["HOLD_R3"],
            "validation_summary": {
                "schema_validated": True,
                "numeric_content_validated": True,
                "checksums_recomputed": True,
            },
            "generated_files": [],
            "calculated_checksums": {
                "review3_observations": observations_hash
            },
            "intake_status": "READY_FOR_PREREGISTRATION",
            "status": "READY_FOR_PREREGISTRATION",
            "checksums_sha256": {
                "review3_observations": observations_hash
            },
            "field_mappings": {
                "review3_observations": {"observed_bq": "observed_bq"}
            },
            "calibration_sample_ids": ["CAL_R3"],
            "holdout_sample_ids": ["HOLD_R3"],
            "empirical_validation": False,
            "calibration_permitted": False,
            "holdout_execution_permitted": False,
            "blocking_reasons": [],
            "metric_pipeline": {"status": "NOT_RUN_NO_MODEL_OUTPUT"},
        },
    )
    intake_hash = calculate_sha256(intake)
    prediction_reference = "validation/review3/predictions.csv"
    metric = {
        "metric_id": "review3_nrmse",
        "required": True,
        "comparator": "LE",
        "threshold": 0.3,
        "value_unit": "1",
        "missing_policy": "FAIL",
        "calculation": {
            "method": "NORMALIZED_RMSE",
            "observation_role": "review3_observations",
            "observation_id_column": "case_id",
            "observation_value_column": "observed_bq",
            "result_file": prediction_reference,
            "prediction_id_column": "case_id",
            "prediction_value_column": "predicted_bq",
        },
    }
    frozen = repository / "validation/review3/frozen_preregistration.yaml"
    _write_yaml(
        frozen,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "calibration_ids": ["CAL_R3"],
            "holdout_ids": ["HOLD_R3"],
            "primary_metrics": [metric],
            "parameter_contract": contract,
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )
    _git(repository, "add", frozen.relative_to(repository).as_posix())
    _git(repository, "commit", "-q", "-m", "Freeze review3 parameter contract")
    preregistration_commit = _git(repository, "rev-parse", "HEAD")
    frozen_hash = calculate_sha256(frozen)

    preregistration = repository / "validation/review3/preregistration.yaml"
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
            "calibration_ids": ["CAL_R3"],
            "holdout_ids": ["HOLD_R3"],
            "primary_metrics": [metric],
            "parameter_contract": deepcopy(contract),
            "parameter_contract_hash": contract_digest,
            "status": "FROZEN_BEFORE_HOLDOUT_INSPECTION",
        },
    )
    config_hash = "4" * 64
    calibration = repository / "validation/review3/calibration.yaml"
    _write_yaml(
        calibration,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_hash,
            "intake_manifest_sha256": intake_hash,
            "preregistration_sha256": frozen_hash,
            "preregistration_commit": preregistration_commit,
            "calibration_ids": ["CAL_R3"],
            "parameter_contract_hash": contract_digest,
            "parameter_result_hash": result_digest,
            "config_hash": config_hash,
            "model_commit": preregistration_commit,
            "parameters": deepcopy(parameters),
            "metrics": {"review3_nrmse": 0.1},
            "status": "CALIBRATION_COMPLETE",
            "generated_at": "2026-03-02T00:00:00Z",
        },
    )
    identifiability = repository / "validation/review3/identifiability.yaml"
    _write_yaml(
        identifiability,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "preregistration_sha256": frozen_hash,
            "parameter_contract_hash": contract_digest,
            "parameter_result_hash": result_digest,
            "parameter_results": _parameter_results(parameters),
            "methods": ["profile_likelihood"],
            "condition_number": 1.3,
            "max_parameter_correlation": 0.2,
            "boundary_hits": [],
            "status": "IDENTIFIABLE",
            "generated_at": "2026-03-02T00:00:00Z",
        },
    )
    predictions = repository / prediction_reference
    predictions.write_text(
        "case_id,predicted_bq\nHOLD_R3,24\n",
        encoding="utf-8",
    )
    holdout = repository / "validation/review3/holdout.yaml"
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
            "parameter_contract_hash": contract_digest,
            "parameter_result_hash": result_digest,
            "parameters": deepcopy(parameters),
            "holdout_ids": ["HOLD_R3"],
            "result_file_checksums": {
                prediction_reference: calculate_sha256(predictions)
            },
            "metrics": [
                {
                    "metric_id": "review3_nrmse",
                    "value": 0.2,
                    "value_unit": "1",
                }
            ],
            "declared_verdict": "PASS",
            "generated_at": "2026-03-03T00:00:00Z",
        },
    )
    reports: dict[str, Path] = {}
    for name, check in (
        ("v1", "V1_RECOMPUTE"),
        ("v2", "V2_ACCEPTANCE"),
        ("validation_readiness", "VALIDATION_READINESS"),
    ):
        report = repository / f"validation/review3/{name}.yaml"
        _write_yaml(
            report,
            {
                "schema_version": "1.0.0",
                "check": check,
                "status": "PASS",
                "model_commit": preregistration_commit,
                "generated_at": "2026-03-03T00:00:00Z",
            },
        )
        reports[name] = report
    bundle = repository / "validation/review3/bundle.yaml"
    _write_yaml(
        bundle,
        {
            "schema_version": "1.0.0",
            "dataset_id": dataset_id,
            "raw_manifest_sha256": raw_manifest_hash,
            "evidence_type": "CONTROLLED_EXPERIMENT",
            "artifact_purpose": "THIRD_INDEPENDENT_REVIEW_ONLY",
            "test_only": True,
            "origin_class": "INDEPENDENT_REVIEW_3",
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
    config = repository / "validation/review3/gate.yaml"
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
    _git(repository, "commit", "-q", "-m", "Commit review3 holdout chain")
    return config, {
        "approval_commit": approval_commit,
        "protected_main": protected_main,
        "raw_file": observations,
        "raw_manifest": raw_manifest,
        "registry": registry,
        "intake": intake,
        "frozen": frozen,
        "preregistration": preregistration,
        "calibration": calibration,
        "identifiability": identifiability,
        "predictions": predictions,
        "holdout": holdout,
        "reports": reports,
        "bundle": bundle,
        "config": config,
        "contract": contract,
        "parameters": parameters,
    }


def _commit(repository: Path, message: str, *paths: Path) -> None:
    _git(
        repository,
        "add",
        *(path.relative_to(repository).as_posix() for path in paths),
    )
    _git(repository, "commit", "-q", "-m", message)


def _evaluate(repository: Path, config: Path, *, hooks=None) -> dict[str, Any]:
    return gate.evaluate_gate_for_test(
        config,
        repository_root=repository,
        hooks=hooks,
    )


def _assert_blocked(result: dict[str, Any]) -> None:
    assert result["status"] == BLOCKED
    assert result["final_gate"] != READY


def _rehash_parameter_chain(
    repository: Path,
    paths: dict[str, Any],
    parameters: dict[str, dict[str, Any]],
) -> None:
    digest = _result_hash(parameters)
    calibration = _load(paths["calibration"])
    calibration["parameters"] = deepcopy(parameters)
    calibration["parameter_result_hash"] = digest
    _write_yaml(paths["calibration"], calibration)

    identifiability = _load(paths["identifiability"])
    identifiability["parameter_result_hash"] = digest
    identifiability["parameter_results"] = _parameter_results(parameters)
    identifiability["boundary_hits"] = []
    _write_yaml(paths["identifiability"], identifiability)

    holdout = _load(paths["holdout"])
    holdout["parameters"] = deepcopy(parameters)
    holdout["parameter_result_hash"] = digest
    _write_yaml(paths["holdout"], holdout)
    _commit(
        repository,
        "Apply synchronized parameter-chain attack",
        paths["calibration"],
        paths["identifiability"],
        paths["holdout"],
    )


def _mutate_artifact(
    repository: Path,
    path: Path,
    transform,
    message: str,
) -> None:
    value = _load(path)
    transform(value)
    _write_yaml(path, value)
    _commit(repository, message, path)


def test_positive_chain_is_order_independent(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    assert [item["name"] for item in paths["contract"]] != list(
        paths["parameters"]
    )
    result = _evaluate(tmp_path, config)
    assert result["status"] == READY
    assert result["diagnostics"]["PARAMETER_CONTRACT_HASH_STATUS"] == "PASS"
    assert result["diagnostics"]["HOLDOUT_PARAMETER_CONTRACT_STATUS"] == "PASS"


@pytest.mark.parametrize(
    ("attack", "replacement"),
    [
        ("replace", "renamed_transfer"),
        ("case", "Transfer_rate"),
        ("unicode", "transfer_ｒate"),
    ],
)
def test_rejects_synchronized_parameter_name_replacement(
    tmp_path: Path,
    attack: str,
    replacement: str,
) -> None:
    config, paths = _build_review3_chain(tmp_path)
    parameters = deepcopy(paths["parameters"])
    parameters[replacement] = parameters.pop("transfer_rate")
    _rehash_parameter_chain(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_synchronized_extra_parameter(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    parameters = deepcopy(paths["parameters"])
    parameters["extra_rate"] = {
        "value": 0.3,
        "unit": "s-1",
        "transform": "IDENTITY",
    }
    _rehash_parameter_chain(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_synchronized_missing_parameter(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    parameters = deepcopy(paths["parameters"])
    parameters.pop("partition_fraction")
    _rehash_parameter_chain(tmp_path, paths, parameters)
    _assert_blocked(_evaluate(tmp_path, config))


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("transfer_rate", -0.01),
        ("transfer_rate", 1.01),
        ("partition_fraction", 0.0),
        ("partition_fraction", 1.0),
        ("transfer_rate", True),
        ("transfer_rate", float("nan")),
        ("transfer_rate", float("inf")),
    ],
)
def test_rejects_parameter_range_and_numeric_attacks(
    tmp_path: Path,
    name: str,
    value: object,
) -> None:
    config, paths = _build_review3_chain(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameters"][name]["value"] = value
    _write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Mutate parameter numeric value", paths["calibration"])
    _assert_blocked(_evaluate(tmp_path, config))


@pytest.mark.parametrize(("name", "value"), [("transfer_rate", 0.0), ("transfer_rate", 1.0)])
def test_accepts_inclusive_parameter_boundaries(
    tmp_path: Path,
    name: str,
    value: float,
) -> None:
    parameters = _default_parameters()
    parameters[name]["value"] = value
    config, _ = _build_review3_chain(tmp_path, parameters=parameters)
    assert _evaluate(tmp_path, config)["status"] == READY


def test_rejects_reversed_frozen_bounds(tmp_path: Path) -> None:
    contract = _default_contract()
    contract[0]["lower_bound"] = 2.0
    contract[0]["upper_bound"] = 1.0
    config, _ = _build_review3_chain(tmp_path, contract=contract)
    _assert_blocked(_evaluate(tmp_path, config))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("unit", "h-1"),
        ("transform", "LOG"),
    ],
)
def test_rejects_calibration_unit_or_transform_mismatch(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    config, paths = _build_review3_chain(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameters"]["transfer_rate"][field] = value
    _write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Mutate calibration contract field", paths["calibration"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_missing_calibration_unit(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    calibration = _load(paths["calibration"])
    calibration["parameters"]["transfer_rate"].pop("unit")
    _write_yaml(paths["calibration"], calibration)
    _commit(tmp_path, "Remove calibration unit", paths["calibration"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_holdout_transform_mismatch(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    holdout = _load(paths["holdout"])
    holdout["parameters"]["partition_fraction"]["transform"] = "IDENTITY"
    holdout["parameter_result_hash"] = _result_hash(holdout["parameters"])
    _write_yaml(paths["holdout"], holdout)
    _commit(tmp_path, "Mutate holdout transform", paths["holdout"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_rehashed_post_holdout_preregistration_change(
    tmp_path: Path,
) -> None:
    config, paths = _build_review3_chain(tmp_path)
    frozen = _load(paths["frozen"])
    frozen["parameter_contract"][0]["unit"] = "h-1"
    _write_yaml(paths["frozen"], frozen)
    _commit(tmp_path, "Change frozen contract after holdout", paths["frozen"])
    late_preregistration_commit = _git(tmp_path, "rev-parse", "HEAD")
    frozen_hash = calculate_sha256(paths["frozen"])
    contract = frozen["parameter_contract"]
    contract_digest = _contract_hash(contract)

    preregistration = _load(paths["preregistration"])
    preregistration["preregistration_sha256"] = frozen_hash
    preregistration["preregistration_commit"] = late_preregistration_commit
    preregistration["parameter_contract"] = deepcopy(contract)
    preregistration["parameter_contract_hash"] = contract_digest
    _write_yaml(paths["preregistration"], preregistration)
    for key in ("calibration", "holdout"):
        artifact = _load(paths[key])
        artifact["preregistration_sha256"] = frozen_hash
        artifact["preregistration_commit"] = late_preregistration_commit
        artifact["parameter_contract_hash"] = contract_digest
        _write_yaml(paths[key], artifact)
    identifiability = _load(paths["identifiability"])
    identifiability["preregistration_sha256"] = frozen_hash
    identifiability["parameter_contract_hash"] = contract_digest
    _write_yaml(paths["identifiability"], identifiability)
    _commit(
        tmp_path,
        "Synchronize late preregistration hashes",
        paths["preregistration"],
        paths["calibration"],
        paths["identifiability"],
        paths["holdout"],
    )
    _assert_blocked(_evaluate(tmp_path, config))


@pytest.mark.parametrize(
    "attack",
    ["missing", "extra", "renamed", "result_hash", "contract_hash"],
)
def test_rejects_identifiability_coverage_and_hash_attacks(
    tmp_path: Path,
    attack: str,
) -> None:
    config, paths = _build_review3_chain(tmp_path)
    identifiability = _load(paths["identifiability"])
    if attack == "missing":
        identifiability["parameter_results"].pop("transfer_rate")
    elif attack == "extra":
        identifiability["parameter_results"]["extra_rate"] = {
            "status": "IDENTIFIABLE",
            "lower_interval": 0.0,
            "upper_interval": 1.0,
            "boundary_hit": False,
        }
    elif attack == "renamed":
        identifiability["parameter_results"]["renamed_rate"] = (
            identifiability["parameter_results"].pop("transfer_rate")
        )
    elif attack == "result_hash":
        identifiability["parameter_result_hash"] = "0" * 64
    else:
        identifiability["parameter_contract_hash"] = "0" * 64
    _write_yaml(paths["identifiability"], identifiability)
    _commit(tmp_path, "Attack identifiability coverage", paths["identifiability"])
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_omitted_non_identifiable_parameter(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    identifiability = _load(paths["identifiability"])
    identifiability["status"] = "NON_IDENTIFIABLE"
    identifiability["parameter_results"].pop("partition_fraction")
    _write_yaml(paths["identifiability"], identifiability)
    _commit(
        tmp_path,
        "Omit non-identifiable parameter",
        paths["identifiability"],
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_production_test_only_masquerade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = _build_review3_chain(tmp_path)
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    _assert_blocked(gate.evaluate_gate(config))


def test_rejects_same_size_raw_replacement(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)

    def attack(_: dict[str, Any]) -> None:
        original = paths["raw_file"].read_text(encoding="utf-8")
        replacement = original.replace("CAL_R3,10", "CAL_R3,99")
        assert len(replacement) == len(original)
        paths["raw_file"].write_text(replacement, encoding="utf-8")

    result = _evaluate(
        tmp_path,
        config,
        hooks={"before_final_source_recheck": attack},
    )
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EVIDENCE_CHANGED_AFTER_SNAPSHOT"


def test_rejects_declared_holdout_fail(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    _mutate_artifact(
        tmp_path,
        paths["holdout"],
        lambda value: value.update(declared_verdict="FAIL"),
        "Declare failed holdout",
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_production_policy_override(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    value = _load(config)
    value["trusted_registry_path"] = paths["registry"].relative_to(
        tmp_path
    ).as_posix()
    _write_yaml(config, value)
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_untrusted_feature_branch_registry(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    _git(
        tmp_path,
        "update-ref",
        gate.TRUSTED_LOCAL_REF,
        paths["approval_commit"],
    )
    _git(
        tmp_path,
        "update-ref",
        gate.TRUSTED_REMOTE_REF,
        paths["approval_commit"],
    )
    assert paths["registry"].exists()
    _assert_blocked(_evaluate(tmp_path, config))


def test_rejects_preregistration_chronology_attack(tmp_path: Path) -> None:
    config, paths = _build_review3_chain(tmp_path)
    late_commit = _git(tmp_path, "rev-parse", "HEAD")
    for key in ("preregistration", "calibration", "holdout"):
        artifact = _load(paths[key])
        artifact["preregistration_commit"] = late_commit
        _write_yaml(paths[key], artifact)
    _commit(
        tmp_path,
        "Move preregistration commit after holdout",
        paths["preregistration"],
        paths["calibration"],
        paths["holdout"],
    )
    _assert_blocked(_evaluate(tmp_path, config))


def test_production_null_bundle_remains_blocked() -> None:
    production_config = gate.ROOT / "validation/v3/physics_start_gate.yaml"
    result = gate.evaluate_gate(production_config)
    _assert_blocked(result)
    assert result["final_gate"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
