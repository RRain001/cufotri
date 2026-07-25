#!/usr/bin/env python3
"""Evaluate the artifact-derived evidence gate for starting formal V3 physics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.evidence_validation import (
    EvidenceValidationError,
    calculate_sha256,
    find_first_commit_containing_file,
    load_json_or_yaml,
    resolve_artifact_path,
    validate_json_schema,
    verify_clean_git_paths,
    verify_commit_ancestry,
    verify_disjoint_ids,
    verify_git_commit_exists,
    verify_git_file_at_commit,
    verify_manifest_file_entries,
)


SCHEMA_ROOT = ROOT / "schemas/v3"

# Retained only for compatibility with older callers/tests. These names no
# longer authorize the gate and are rejected by the strict config schema.
REQUIRED_TRUE = (
    "complete_licensed_external_case",
    "raw_data_checksum_recorded",
    "data_schema_valid",
    "preregistration_committed_before_holdout",
    "calibration_holdout_separated",
    "calibration_executed",
    "parameter_identifiability_assessed",
    "V1_regression_pass",
    "V2_acceptance_pass",
    "validation_readiness_pass",
    "external_holdout_executed",
    "no_new_blocker_high",
)

ELIGIBLE_EVIDENCE_TYPES = {
    "CONTROLLED_EXPERIMENT",
    "MATCHED_FIELD_OBSERVATION",
    "LICENSED_EXTERNAL_HOLDOUT",
}
INELIGIBLE_EVIDENCE_TYPES = {
    "SYNTHETIC_CONTRACT_TEST",
    "INTERNAL_REFERENCE",
    "ANALYTIC_BENCHMARK",
    "INTEGRATION_SCENARIO",
    "REGRESSION_CASE",
    "ERA5_FORCING",
    "LITERATURE_COMPARISON",
}

DIAGNOSTIC_KEYS = (
    "RAW_MANIFEST_EXISTS",
    "RAW_MANIFEST_SCHEMA",
    "RAW_CHECKSUMS",
    "INTAKE_MANIFEST_SCHEMA",
    "PREREGISTRATION_TRACKED",
    "PREREGISTRATION_PRECEDES_HOLDOUT",
    "CALIBRATION_HOLDOUT_DISJOINT",
    "CALIBRATION_RESULT_VALID",
    "IDENTIFIABILITY_RESULT_VALID",
    "HOLDOUT_RESULT_VALID",
    "EVIDENCE_TYPE_ELIGIBLE",
    "V1_REGRESSION",
    "V2_ACCEPTANCE",
    "VALIDATION_READINESS",
)

ARTIFACT_SCHEMAS = {
    "bundle": "v3_physics_gate_evidence_bundle.schema.json",
    "raw": "external_raw_data_manifest.schema.json",
    "intake": "external_intake_manifest.schema.json",
    "preregistration": "external_preregistration_record.schema.json",
    "calibration": "external_calibration_result.schema.json",
    "identifiability": "external_identifiability_result.schema.json",
    "holdout": "external_holdout_result.schema.json",
    "regression": "external_regression_result.schema.json",
}


def _blocked(
    reason: str,
    diagnostics: dict[str, str] | None = None,
    *,
    detail: str | None = None,
) -> dict[str, Any]:
    values = {key: "NOT_EVALUATED" for key in DIAGNOSTIC_KEYS}
    if diagnostics:
        values.update(diagnostics)
    return {
        "status": "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "final_gate": f"BLOCKED_{reason}",
        "diagnostics": values,
        "blocking_reasons": [detail or reason],
        "unmet": [
            key for key, value in values.items() if value != "PASS"
        ],
    }


def _classify_failure(message: str) -> tuple[str, str]:
    lowered = message.lower()
    if "checksum" in lowered or "size_bytes" in lowered:
        return "CHECKSUM_MISMATCH", "RAW_CHECKSUMS"
    if "evidence type" in lowered or "licence" in lowered:
        return "INELIGIBLE_EVIDENCE_TYPE", "EVIDENCE_TYPE_ELIGIBLE"
    if "identifiability" in lowered:
        return "IDENTIFIABILITY_RESULT_INVALID", "IDENTIFIABILITY_RESULT_VALID"
    if "calibration" in lowered and (
        "holdout" not in lowered or "disjoint" not in lowered
    ):
        return "CALIBRATION_RESULT_INVALID", "CALIBRATION_RESULT_VALID"
    if "holdout" in lowered:
        return "HOLDOUT_RESULT_INVALID", "HOLDOUT_RESULT_VALID"
    if "preregistration" in lowered or "git verification" in lowered:
        return (
            "PREREGISTRATION_ORDER_OR_TRACKING_INVALID",
            "PREREGISTRATION_TRACKED",
        )
    if "intake" in lowered:
        return "INTAKE_MANIFEST_INVALID", "INTAKE_MANIFEST_SCHEMA"
    if "regression report v1" in lowered:
        return "V1_REGRESSION_INVALID", "V1_REGRESSION"
    if "regression report v2" in lowered:
        return "V2_ACCEPTANCE_INVALID", "V2_ACCEPTANCE"
    if "regression report validation_readiness" in lowered:
        return "VALIDATION_READINESS_INVALID", "VALIDATION_READINESS"
    if "schema validation" in lowered or "schema" in lowered:
        return "SCHEMA_VALIDATION_FAILED", "RAW_MANIFEST_SCHEMA"
    if (
        "does not exist" in lowered
        or "not a regular file" in lowered
        or "is empty" in lowered
    ):
        return "MISSING_OR_INVALID_ARTIFACT", "RAW_MANIFEST_EXISTS"
    return "EVIDENCE_VALIDATION_FAILED", "RAW_MANIFEST_EXISTS"


def _schema(name: str) -> Path:
    return SCHEMA_ROOT / ARTIFACT_SCHEMAS[name]


def _artifact(
    reference: str,
    *,
    repository_root: Path,
    allowed_roots: list[Path],
    schema_name: str,
) -> tuple[Path, dict[str, Any]]:
    path = resolve_artifact_path(
        reference,
        repository_root=repository_root,
        allowed_roots=allowed_roots,
    )
    document = load_json_or_yaml(path)
    validate_json_schema(document, _schema(schema_name))
    return path, document


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verify_finite_mapping(mapping: Any, label: str) -> None:
    if not isinstance(mapping, dict) or not mapping:
        raise EvidenceValidationError(f"{label} must be a non-empty mapping")
    for name, value in mapping.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise EvidenceValidationError(f"{label}.{name} must be numeric")
        if not math.isfinite(float(value)):
            raise EvidenceValidationError(f"{label}.{name} must be finite")


def _resolve_declared_path(
    reference: str,
    *,
    repository_root: Path,
    allowed_roots: list[Path],
) -> Path:
    return resolve_artifact_path(
        reference,
        repository_root=repository_root,
        allowed_roots=allowed_roots,
    )


def _verify_regression_reports(
    config: dict[str, Any],
    *,
    repository_root: Path,
    allowed_roots: list[Path],
    model_commit: str,
) -> dict[str, str]:
    expected_checks = {
        "v1": ("V1_RECOMPUTE", "V1_REGRESSION"),
        "v2": ("V2_ACCEPTANCE", "V2_ACCEPTANCE"),
        "validation_readiness": (
            "VALIDATION_READINESS",
            "VALIDATION_READINESS",
        ),
    }
    diagnostics: dict[str, str] = {}
    for key, (expected_check, diagnostic_key) in expected_checks.items():
        reference = config["required_regression_reports"].get(key)
        if not reference:
            raise EvidenceValidationError(f"missing regression report path: {key}")
        _, report = _artifact(
            reference,
            repository_root=repository_root,
            allowed_roots=allowed_roots,
            schema_name="regression",
        )
        if report["check"] != expected_check:
            raise EvidenceValidationError(
                f"regression report {key} has wrong check type"
            )
        if report["model_commit"] != model_commit:
            raise EvidenceValidationError(
                f"regression report {key} model_commit mismatch"
            )
        diagnostics[diagnostic_key] = "PASS"
    return diagnostics


def _evaluate_artifacts(
    config: dict[str, Any],
    *,
    repository_root: Path,
) -> dict[str, Any]:
    diagnostics = {key: "NOT_EVALUATED" for key in DIAGNOSTIC_KEYS}
    artifact_roots = [
        (repository_root / item).resolve(strict=True)
        for item in config["allowed_artifact_roots"]
    ]
    raw_roots = [
        (repository_root / item).resolve(strict=True)
        for item in config["allowed_raw_data_roots"]
    ]
    all_evidence_roots = list(dict.fromkeys(artifact_roots + raw_roots))

    bundle_path, bundle = _artifact(
        config["evidence_bundle_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="bundle",
    )
    del bundle_path

    raw_path, raw = _artifact(
        bundle["raw_manifest_path"],
        repository_root=repository_root,
        allowed_roots=all_evidence_roots,
        schema_name="raw",
    )
    diagnostics["RAW_MANIFEST_EXISTS"] = "PASS"
    diagnostics["RAW_MANIFEST_SCHEMA"] = "PASS"
    raw_checksums = verify_manifest_file_entries(
        raw,
        manifest_path=raw_path,
        allowed_raw_roots=raw_roots,
    )
    diagnostics["RAW_CHECKSUMS"] = "PASS"

    intake_path, intake = _artifact(
        bundle["intake_manifest_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="intake",
    )
    diagnostics["INTAKE_MANIFEST_SCHEMA"] = "PASS"
    preregistration_record_path, preregistration = _artifact(
        bundle["preregistration_record_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="preregistration",
    )
    del preregistration_record_path
    calibration_path, calibration = _artifact(
        bundle["calibration_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="calibration",
    )
    identifiability_path, identifiability = _artifact(
        bundle["identifiability_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="identifiability",
    )
    holdout_path, holdout = _artifact(
        bundle["holdout_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        schema_name="holdout",
    )

    dataset_ids = {
        bundle["dataset_id"],
        raw["dataset_id"],
        intake["dataset_id"],
        preregistration["dataset_id"],
        calibration["dataset_id"],
        identifiability["dataset_id"],
        holdout["dataset_id"],
    }
    if len(dataset_ids) != 1:
        raise EvidenceValidationError("dataset_id mismatch across evidence chain")

    evidence_type = raw["evidence_type"]
    if evidence_type in INELIGIBLE_EVIDENCE_TYPES:
        raise EvidenceValidationError(
            f"ineligible external evidence type: {evidence_type}"
        )
    if evidence_type not in ELIGIBLE_EVIDENCE_TYPES:
        raise EvidenceValidationError(f"unknown external evidence type: {evidence_type}")
    if holdout["evidence_type"] not in ELIGIBLE_EVIDENCE_TYPES:
        raise EvidenceValidationError(
            f"ineligible holdout evidence type: {holdout['evidence_type']}"
        )
    if holdout["evidence_type"] != evidence_type:
        raise EvidenceValidationError("raw and holdout evidence types differ")
    if not raw["local_use_allowed"] or raw["licence_status"] not in {
        "VERIFIED",
        "LOCAL_USE_ONLY",
    }:
        raise EvidenceValidationError("external evidence licence/local-use is not verified")
    diagnostics["EVIDENCE_TYPE_ELIGIBLE"] = "PASS"

    raw_sha256 = calculate_sha256(raw_path)
    intake_sha256 = calculate_sha256(intake_path)
    if intake["raw_manifest_sha256"] != raw_sha256:
        raise EvidenceValidationError("intake raw_manifest_sha256 mismatch")
    declared_raw_path = _resolve_declared_path(
        intake["raw_manifest_path"],
        repository_root=repository_root,
        allowed_roots=all_evidence_roots,
    )
    if declared_raw_path != raw_path:
        raise EvidenceValidationError("intake raw_manifest_path mismatch")
    if intake["calculated_checksums"] != raw_checksums:
        raise EvidenceValidationError("intake calculated checksums mismatch")
    if intake["checksums_sha256"] != raw_checksums:
        raise EvidenceValidationError("legacy intake checksum view mismatch")
    if intake["intake_status"] != "READY_FOR_PREREGISTRATION":
        raise EvidenceValidationError(
            f"intake is not empirical-ready: {intake['intake_status']}"
        )
    if intake["blocking_reasons"]:
        raise EvidenceValidationError("intake contains blocking reasons")
    if not all(intake["validation_summary"].values()):
        raise EvidenceValidationError("intake validation summary is incomplete")

    if preregistration["raw_manifest_sha256"] != raw_sha256:
        raise EvidenceValidationError("preregistration raw manifest hash mismatch")
    if preregistration["intake_manifest_sha256"] != intake_sha256:
        raise EvidenceValidationError("preregistration intake manifest hash mismatch")
    verify_disjoint_ids(
        preregistration["calibration_ids"],
        preregistration["holdout_ids"],
    )
    if preregistration["calibration_ids"] != intake["calibration_ids"]:
        raise EvidenceValidationError("frozen calibration IDs differ from intake")
    if preregistration["holdout_ids"] != intake["holdout_ids"]:
        raise EvidenceValidationError("frozen holdout IDs differ from intake")

    preregistration_file = _resolve_declared_path(
        preregistration["preregistration_file"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
    )
    if calculate_sha256(preregistration_file) != preregistration["preregistration_sha256"]:
        raise EvidenceValidationError("current preregistration file hash mismatch")
    verify_git_commit_exists(
        repository_root,
        preregistration["preregistration_commit"],
    )
    verify_git_file_at_commit(
        repository_root,
        preregistration_file,
        preregistration["preregistration_commit"],
        preregistration["preregistration_sha256"],
    )
    diagnostics["PREREGISTRATION_TRACKED"] = "PASS"

    preregistration_sha256 = preregistration["preregistration_sha256"]
    for label, artifact in (
        ("calibration", calibration),
        ("holdout", holdout),
    ):
        for key, expected in (
            ("raw_manifest_sha256", raw_sha256),
            ("intake_manifest_sha256", intake_sha256),
            ("preregistration_sha256", preregistration_sha256),
            (
                "preregistration_commit",
                preregistration["preregistration_commit"],
            ),
        ):
            if artifact[key] != expected:
                raise EvidenceValidationError(f"{label} {key} mismatch")
    if calibration["calibration_ids"] != preregistration["calibration_ids"]:
        raise EvidenceValidationError("calibration IDs differ from preregistration")
    if holdout["holdout_ids"] != preregistration["holdout_ids"]:
        raise EvidenceValidationError("holdout IDs differ from preregistration")
    verify_disjoint_ids(calibration["calibration_ids"], holdout["holdout_ids"])
    diagnostics["CALIBRATION_HOLDOUT_DISJOINT"] = "PASS"

    _verify_finite_mapping(calibration["parameters"], "calibration.parameters")
    _verify_finite_mapping(calibration["metrics"], "calibration.metrics")
    parameter_hash = _canonical_sha256(calibration["parameters"])
    if calibration["parameter_result_hash"] != parameter_hash:
        raise EvidenceValidationError("calibration parameter_result_hash mismatch")
    if calibration["model_commit"] != holdout["model_commit"]:
        raise EvidenceValidationError("calibration and holdout model commits differ")
    if calibration["config_hash"] != holdout["config_hash"]:
        raise EvidenceValidationError("calibration and holdout config hashes differ")
    if calibration["parameter_result_hash"] != holdout["parameter_result_hash"]:
        raise EvidenceValidationError("holdout did not use frozen calibration parameters")
    verify_git_commit_exists(repository_root, calibration["model_commit"])
    diagnostics["CALIBRATION_RESULT_VALID"] = "PASS"

    if identifiability["preregistration_sha256"] != preregistration_sha256:
        raise EvidenceValidationError("identifiability preregistration hash mismatch")
    if identifiability["parameter_result_hash"] != parameter_hash:
        raise EvidenceValidationError("identifiability parameter hash mismatch")
    for field in ("condition_number", "max_parameter_correlation"):
        value = identifiability[field]
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise EvidenceValidationError(f"identifiability {field} must be finite")
    diagnostics["IDENTIFIABILITY_RESULT_VALID"] = "PASS"

    _verify_finite_mapping(holdout["metrics"], "holdout.metrics")
    for relative, expected in holdout["result_file_checksums"].items():
        result_path = _resolve_declared_path(
            relative,
            repository_root=repository_root,
            allowed_roots=artifact_roots,
        )
        if calculate_sha256(result_path) != expected:
            raise EvidenceValidationError(
                f"holdout result checksum mismatch: {relative}"
            )
    if calculate_sha256(calibration_path) == calculate_sha256(holdout_path):
        raise EvidenceValidationError("holdout is a renamed calibration artifact")
    diagnostics["HOLDOUT_RESULT_VALID"] = "PASS"

    holdout_commit = find_first_commit_containing_file(repository_root, holdout_path)
    verify_commit_ancestry(
        repository_root,
        preregistration["preregistration_commit"],
        holdout_commit,
    )
    verify_clean_git_paths(
        repository_root,
        [preregistration_file, holdout_path],
    )
    diagnostics["PREREGISTRATION_PRECEDES_HOLDOUT"] = "PASS"

    regression_diagnostics = _verify_regression_reports(
        config,
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        model_commit=calibration["model_commit"],
    )
    diagnostics.update(regression_diagnostics)

    # These paths are opened above; keep explicit references so accidental
    # removal of any artifact from the chain remains observable in review.
    del identifiability_path
    return {
        "status": "READY_FOR_BOUNDED_V3_PHYSICS",
        "final_gate": "READY_FOR_BOUNDED_V3_PHYSICS",
        "diagnostics": diagnostics,
        "blocking_reasons": [],
        "unmet": [],
    }


def evaluate_gate(path: Path) -> dict[str, Any]:
    """Evaluate the gate from artifacts; declaration booleans have no authority."""

    repository_root = ROOT
    try:
        config = load_json_or_yaml(path)
        validate_json_schema(
            config,
            SCHEMA_ROOT / "v3_physics_gate_config.schema.json",
        )
        if not config["evidence_bundle_path"]:
            return _blocked("EXTERNAL_EXPERIMENT_OR_FIELD_DATA")
        return _evaluate_artifacts(config, repository_root=repository_root)
    except (
        EvidenceValidationError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as exc:
        code, diagnostic = _classify_failure(str(exc))
        return _blocked(
            code,
            {diagnostic: f"FAIL: {exc}"},
            detail=str(exc),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence",
        type=Path,
        default=ROOT / "validation/v3/physics_start_gate.yaml",
    )
    arguments = parser.parse_args()
    result = evaluate_gate(arguments.evidence.resolve())
    for key in DIAGNOSTIC_KEYS:
        print(f"{key} = {result['diagnostics'][key]}")
    print(f"FINAL_GATE = {result['final_gate']}")
    print(f"V3_PHYSICS_START_GATE = {result['status']}")
    if result["blocking_reasons"]:
        print("BLOCKING_REASONS = " + ", ".join(result["blocking_reasons"]))
    print("INTERNAL_REFERENCE_COUNTS_AS_EXPERIMENT = NO")
    print("V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED")
    if result["status"] == "READY_FOR_BOUNDED_V3_PHYSICS":
        return 0
    if result["final_gate"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
