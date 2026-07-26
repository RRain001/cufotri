#!/usr/bin/env python3
"""Evaluate the fail-closed external-evidence gate for formal V3 physics."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Callable, Mapping

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
ROOT = RUNTIME_ROOT
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from validation.evidence_snapshot import EvidenceSnapshot
from validation.evidence_validation import (
    EvidenceValidationError,
    calculate_sha256,
    find_first_commit_containing_file,
    load_json_or_yaml,
    validate_json_schema,
    verify_clean_git_paths,
    verify_commit_ancestry,
    verify_disjoint_ids,
    verify_git_commit_exists,
    verify_git_file_at_commit,
    verify_manifest_file_entries,
)
from validation.holdout_verdict import (
    HoldoutEvaluation,
    derive_holdout_verdict,
    recompute_holdout_metrics,
)


RUNTIME_SCHEMA_ROOT = RUNTIME_ROOT / "schemas/v3"
TRUSTED_POLICY_PATH = Path(
    "validation/v3/policy/trusted_external_evidence_registry.yaml"
)
TRUSTED_LOCAL_REF = "refs/heads/main"
TRUSTED_REMOTE_REF = "refs/remotes/origin/main"
FIXED_ARTIFACT_ROOTS = ("validation", "docs/v3/gates")

# Compatibility surface only. Strict schemas reject these legacy switches.
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
    "TRUSTED_MAIN_ALIGNMENT_STATUS",
    "TRUSTED_REGISTRY_STATUS",
    "TRUSTED_REGISTRY_SCHEMA_STATUS",
    "EMPIRICAL_APPROVAL_ENTRY_STATUS",
    "APPROVAL_COMMIT_STATUS",
    "APPROVAL_PRECEDES_PREREGISTRATION_STATUS",
    "RAW_MANIFEST_EXISTS",
    "RAW_MANIFEST_SCHEMA",
    "RAW_CHECKSUMS",
    "INTAKE_MANIFEST_SCHEMA",
    "PREREGISTRATION_TRACKED",
    "PREREGISTRATION_PRECEDES_HOLDOUT",
    "CALIBRATION_HOLDOUT_DISJOINT",
    "CALIBRATION_RESULT_VALID",
    "IDENTIFIABILITY_RESULT_VALID",
    "DECLARED_HOLDOUT_VERDICT_STATUS",
    "DERIVED_HOLDOUT_VERDICT_STATUS",
    "HOLDOUT_METRIC_RECOMPUTE_STATUS",
    "HOLDOUT_RESULT_VALID",
    "EVIDENCE_TYPE_ELIGIBLE",
    "V1_REGRESSION",
    "V2_ACCEPTANCE",
    "VALIDATION_READINESS",
    "SNAPSHOT_CREATION_STATUS",
    "SNAPSHOT_FILE_COUNT",
    "SNAPSHOT_HASH_STATUS",
    "FINAL_SOURCE_RECHECK_STATUS",
    "SOURCE_IDENTITY_STATUS",
)

ARTIFACT_SCHEMAS = {
    "config": "v3_physics_gate_config.schema.json",
    "bundle": "v3_physics_gate_evidence_bundle.schema.json",
    "raw": "external_raw_data_manifest.schema.json",
    "intake": "external_intake_manifest.schema.json",
    "preregistration": "external_preregistration_record.schema.json",
    "preregistration_file": "external_preregistration_file.schema.json",
    "calibration": "external_calibration_result.schema.json",
    "identifiability": "external_identifiability_result.schema.json",
    "holdout": "external_holdout_result.schema.json",
    "regression": "external_regression_result.schema.json",
    "registry": "trusted_external_evidence_registry.schema.json",
}

TestHook = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class EvaluationOptions:
    allow_test_only: bool = False
    hooks: Mapping[str, TestHook] | None = None


class GateDecisionError(EvidenceValidationError):
    """A validated artifact chain that must produce a specific blocked verdict."""

    def __init__(self, code: str, message: str, diagnostic: str) -> None:
        super().__init__(message)
        self.code = code
        self.diagnostic = diagnostic


def _git(repository_root: Path, *arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository_root,
            check=True,
            capture_output=True,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        stderr = ""
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceValidationError(
            f"git verification failed: git {' '.join(arguments)}; {stderr}"
        ) from exc


def _git_text(repository_root: Path, *arguments: str) -> str:
    return _git(repository_root, *arguments).decode("utf-8").strip()


def _blocked(
    reason: str,
    diagnostics: dict[str, str] | None = None,
    *,
    detail: str | None = None,
    snapshot_file_count: int = 0,
    holdout_evaluation: HoldoutEvaluation | None = None,
) -> dict[str, Any]:
    values = {key: "NOT_EVALUATED" for key in DIAGNOSTIC_KEYS}
    if diagnostics:
        values.update(diagnostics)
    return {
        "status": "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
        "final_gate": f"BLOCKED_{reason}",
        "diagnostics": values,
        "blocking_reasons": [detail or reason],
        "unmet": [key for key, value in values.items() if value != "PASS"],
        "snapshot_file_count": snapshot_file_count,
        "holdout_evaluation": (
            holdout_evaluation.as_dict() if holdout_evaluation else None
        ),
    }


def _classify_failure(message: str) -> tuple[str, str]:
    lowered = message.lower()
    if (
        "changed during snapshot" in lowered
        or "evidence_changed_during_snapshot" in lowered
    ):
        return "EVIDENCE_CHANGED_DURING_SNAPSHOT", "SNAPSHOT_HASH_STATUS"
    if (
        "changed after snapshot" in lowered
        or "evidence_changed_after_snapshot" in lowered
    ):
        return "EVIDENCE_CHANGED_AFTER_SNAPSHOT", "FINAL_SOURCE_RECHECK_STATUS"
    if "trusted registry" in lowered or "approval" in lowered:
        return "TRUSTED_REGISTRY_INVALID", "TRUSTED_REGISTRY_STATUS"
    if "refs/heads/main" in lowered or "origin/main" in lowered:
        return "TRUSTED_MAIN_ALIGNMENT_INVALID", "TRUSTED_MAIN_ALIGNMENT_STATUS"
    if "checksum" in lowered or "size_bytes" in lowered:
        return "CHECKSUM_MISMATCH", "RAW_CHECKSUMS"
    if "evidence type" in lowered or "licence" in lowered or "test-only" in lowered:
        return "INELIGIBLE_EVIDENCE_TYPE", "EVIDENCE_TYPE_ELIGIBLE"
    if "identifiability" in lowered:
        return "IDENTIFIABILITY_RESULT_INVALID", "IDENTIFIABILITY_RESULT_VALID"
    if "calibration" in lowered and "disjoint" not in lowered:
        return "CALIBRATION_RESULT_INVALID", "CALIBRATION_RESULT_VALID"
    if "holdout" in lowered:
        return "HOLDOUT_RESULT_INVALID", "HOLDOUT_RESULT_VALID"
    if "preregistration" in lowered or "git verification" in lowered:
        return "PREREGISTRATION_ORDER_OR_TRACKING_INVALID", "PREREGISTRATION_TRACKED"
    if "intake" in lowered:
        return "INTAKE_MANIFEST_INVALID", "INTAKE_MANIFEST_SCHEMA"
    if "regression report v1" in lowered:
        return "V1_REGRESSION_INVALID", "V1_REGRESSION"
    if "regression report v2" in lowered:
        return "V2_ACCEPTANCE_INVALID", "V2_ACCEPTANCE"
    if "regression report validation_readiness" in lowered:
        return "VALIDATION_READINESS_INVALID", "VALIDATION_READINESS"
    if "schema" in lowered:
        return "SCHEMA_VALIDATION_FAILED", "RAW_MANIFEST_SCHEMA"
    return "EVIDENCE_VALIDATION_FAILED", "RAW_MANIFEST_EXISTS"


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def trusted_registry_entry_hash(entry: Mapping[str, Any]) -> str:
    """Hash eligibility content without the later commit-bound approval wrapper."""

    projection = {
        key: value for key, value in entry.items() if key != "approval"
    }
    licence = dict(projection.get("licence_review", {}))
    licence.pop("review_record_sha256", None)
    projection["licence_review"] = licence
    return _canonical_sha256(projection)


def trusted_registry_projection_hash(registry: Mapping[str, Any]) -> str:
    """Hash the approved policy projection without self-referential fields."""

    entries = registry.get("entries")
    if not isinstance(entries, list):
        raise EvidenceValidationError("trusted registry entries must be a list")
    projected_entries = []
    for entry in entries:
        projected = {
            key: value for key, value in entry.items() if key != "approval"
        }
        licence = dict(projected.get("licence_review", {}))
        licence.pop("review_record_sha256", None)
        projected["licence_review"] = licence
        projected_entries.append(projected)
    projection = {
        "schema_version": registry.get("schema_version"),
        "entries": projected_entries,
    }
    return _canonical_sha256(projection)


def _schema_snapshot(snapshot: EvidenceSnapshot, name: str) -> Path:
    schema = RUNTIME_SCHEMA_ROOT / ARTIFACT_SCHEMAS[name]
    return snapshot.add_path(
        schema,
        allowed_roots=[RUNTIME_SCHEMA_ROOT],
        label=f"schema_{name}",
    )


def _load_and_validate(
    snapshot_path: Path,
    *,
    snapshot: EvidenceSnapshot,
    schema_name: str,
) -> dict[str, Any]:
    document = load_json_or_yaml(snapshot_path)
    validate_json_schema(document, _schema_snapshot(snapshot, schema_name))
    return document


def _resolve_roots(repository_root: Path, config: Mapping[str, Any]) -> tuple[list[Path], list[Path]]:
    artifact_roots = [
        (repository_root / relative).resolve(strict=True)
        for relative in FIXED_ARTIFACT_ROOTS
    ]
    fixed_raw_root = (repository_root / "validation/external_local").resolve(
        strict=True
    )
    raw_roots: list[Path] = []
    for reference in config["allowed_raw_data_roots"]:
        candidate = (repository_root / reference).resolve(strict=True)
        if not candidate.is_relative_to(fixed_raw_root):
            raise EvidenceValidationError(
                "allowed_raw_data_roots must remain under validation/external_local"
            )
        raw_roots.append(candidate)
    return artifact_roots, raw_roots


def _snapshot_artifact(
    reference: str,
    *,
    repository_root: Path,
    allowed_roots: list[Path],
    snapshot: EvidenceSnapshot,
    label: str,
    schema_name: str,
) -> tuple[Path, Path, dict[str, Any]]:
    candidate = Path(reference)
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    live = Path(os.path.abspath(candidate))
    copied = snapshot.add_path(live, allowed_roots=allowed_roots, label=label)
    return live, copied, _load_and_validate(
        copied,
        snapshot=snapshot,
        schema_name=schema_name,
    )


def _verify_finite_mapping(mapping: Any, label: str) -> None:
    if not isinstance(mapping, dict) or not mapping:
        raise EvidenceValidationError(f"{label} must be a non-empty mapping")
    for name, value in mapping.items():
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
        ):
            raise EvidenceValidationError(f"{label}.{name} must be finite numeric")


def _trusted_refs(repository_root: Path) -> tuple[str, str]:
    local = _git_text(repository_root, "rev-parse", TRUSTED_LOCAL_REF)
    remote = _git_text(repository_root, "rev-parse", TRUSTED_REMOTE_REF)
    if local != remote:
        raise EvidenceValidationError(
            "refs/heads/main and refs/remotes/origin/main are not aligned"
        )
    return local, remote


def _registry_entry_commit(
    repository_root: Path,
    *,
    trusted_sha: str,
    expected_entry_hash: str,
) -> str:
    commits = _git_text(
        repository_root,
        "rev-list",
        "--reverse",
        trusted_sha,
        "--",
        TRUSTED_POLICY_PATH.as_posix(),
    ).splitlines()
    for commit in commits:
        try:
            payload = _git(
                repository_root,
                "show",
                f"{commit}:{TRUSTED_POLICY_PATH.as_posix()}",
            )
            registry = _load_bytes_mapping(payload, "registry history")
        except EvidenceValidationError:
            continue
        for entry in registry.get("entries", []):
            if (
                isinstance(entry, Mapping)
                and trusted_registry_entry_hash(entry) == expected_entry_hash
            ):
                return commit
    raise EvidenceValidationError(
        "trusted registry entry has no matching commit on protected main"
    )


def _load_bytes_mapping(payload: bytes, label: str) -> dict[str, Any]:
    try:
        import yaml

        value = yaml.safe_load(payload.decode("utf-8"))
    except Exception as exc:
        raise EvidenceValidationError(f"cannot parse {label}") from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError(f"{label} must be a mapping")
    return value


def _resolve_trusted_entry(
    *,
    repository_root: Path,
    snapshot: EvidenceSnapshot,
    dataset_id: str,
    raw_manifest_sha256: str,
    evidence_type: str,
    preregistration_commit: str,
    options: EvaluationOptions,
    diagnostics: dict[str, str],
) -> tuple[dict[str, Any], str, str]:
    trusted_sha, _ = _trusted_refs(repository_root)
    diagnostics["TRUSTED_MAIN_ALIGNMENT_STATUS"] = "PASS"
    policy_payload = _git(
        repository_root,
        "show",
        f"{trusted_sha}:{TRUSTED_POLICY_PATH.as_posix()}",
    )
    policy_snapshot = snapshot.add_bytes(
        policy_payload,
        label="trusted_registry",
        suffix=".yaml",
    )
    registry = _load_and_validate(
        policy_snapshot,
        snapshot=snapshot,
        schema_name="registry",
    )
    diagnostics["TRUSTED_REGISTRY_SCHEMA_STATUS"] = "PASS"
    matching_id = [
        entry
        for entry in registry["entries"]
        if entry["dataset_id"] == dataset_id
    ]
    if len(matching_id) != 1:
        raise EvidenceValidationError(
            "trusted registry must contain exactly one dataset entry"
        )
    entry = matching_id[0]
    if entry["raw_manifest_sha256"] != raw_manifest_sha256:
        raise EvidenceValidationError("trusted registry raw manifest hash mismatch")
    if entry["evidence_type"] != evidence_type:
        raise EvidenceValidationError("trusted registry evidence type mismatch")
    if entry["empirical_eligibility"] != "APPROVED":
        raise EvidenceValidationError("trusted registry eligibility is not APPROVED")
    if entry["test_only"] and not options.allow_test_only:
        raise EvidenceValidationError("trusted registry entry is test-only")
    if (
        not entry["test_only"]
        and options.allow_test_only
    ):
        raise EvidenceValidationError(
            "isolated test evaluator requires an explicit test-only registry entry"
        )
    if entry["licence_review"]["status"] not in {
        "APPROVED_LOCAL_USE",
        "APPROVED_REDISTRIBUTION",
    }:
        raise EvidenceValidationError("trusted registry licence is not approved")

    approval = entry["approval"]
    entry_hash = trusted_registry_entry_hash(entry)
    registry_hash = trusted_registry_projection_hash(registry)
    if approval["approved_entry_sha256"] != entry_hash:
        raise EvidenceValidationError("trusted registry approved entry hash mismatch")
    if approval["approved_registry_sha256"] != registry_hash:
        raise EvidenceValidationError("trusted registry projection hash mismatch")
    approval_commit = approval["approval_commit"]
    verify_git_commit_exists(repository_root, approval_commit)
    verify_commit_ancestry(repository_root, approval_commit, trusted_sha)
    diagnostics["APPROVAL_COMMIT_STATUS"] = "PASS"

    review_path = entry["licence_review"]["review_record_path"]
    review_reference = PurePosixPath(review_path)
    if review_reference.is_absolute() or ".." in review_reference.parts:
        raise EvidenceValidationError(
            "licence approval record path must be repository-relative"
        )
    review_payload = _git(
        repository_root,
        "show",
        f"{approval_commit}:{review_path}",
    )
    if hashlib.sha256(review_payload).hexdigest() != entry["licence_review"][
        "review_record_sha256"
    ]:
        raise EvidenceValidationError("licence approval record hash mismatch")
    review_snapshot = snapshot.add_bytes(
        review_payload,
        label="licence_approval_record",
        suffix=Path(review_path).suffix,
    )
    review = load_json_or_yaml(review_snapshot)
    if (
        review.get("dataset_id") != dataset_id
        or review.get("decision") != "APPROVED"
        or review.get("approved_entry_sha256") != entry_hash
        or review.get("approved_registry_sha256") != registry_hash
    ):
        raise EvidenceValidationError(
            "approval commit record does not match trusted registry entry"
        )

    entry_commit = _registry_entry_commit(
        repository_root,
        trusted_sha=trusted_sha,
        expected_entry_hash=entry_hash,
    )
    verify_commit_ancestry(repository_root, approval_commit, entry_commit)
    verify_commit_ancestry(repository_root, approval_commit, preregistration_commit)
    verify_commit_ancestry(repository_root, entry_commit, preregistration_commit)
    diagnostics["APPROVAL_PRECEDES_PREREGISTRATION_STATUS"] = "PASS"
    diagnostics["TRUSTED_REGISTRY_STATUS"] = "PASS"
    diagnostics["EMPIRICAL_APPROVAL_ENTRY_STATUS"] = "PASS"
    return entry, trusted_sha, entry_commit


def _verify_source_crosscheck(
    raw: Mapping[str, Any],
    bundle: Mapping[str, Any],
    entry: Mapping[str, Any],
    *,
    allow_test_only: bool,
) -> None:
    source = raw["source"]
    expected_source = entry["source_authority"]
    if (
        source["authority"] != expected_source["organization"]
        or source["title"] != expected_source["dataset_title"]
        or source["reference"] != expected_source["reference"]
    ):
        raise EvidenceValidationError(
            "untrusted source declaration differs from approved registry"
        )
    if bundle["test_only"] if "test_only" in bundle else False:
        if not allow_test_only:
            raise EvidenceValidationError("bundle is test-only")
    if raw.get("test_only") is True and not allow_test_only:
        raise EvidenceValidationError("raw manifest is test-only")
    if not allow_test_only:
        text = json.dumps(
            {
                "source": source,
                "raw_artifact_purpose": raw.get("artifact_purpose"),
                "raw_origin_class": raw.get("origin_class"),
                "bundle_artifact_purpose": bundle.get("artifact_purpose"),
                "bundle_origin_class": bundle.get("origin_class"),
            },
            sort_keys=True,
        )
        if re.search(
            r"test[-_ ]?only|pytest|fixture|synthetic|not empirical",
            text,
            flags=re.IGNORECASE,
        ):
            raise EvidenceValidationError(
                "test-only or synthetic source text cannot authorize production"
            )


def _call_hook(
    options: EvaluationOptions,
    name: str,
    context: dict[str, Any],
) -> None:
    if options.hooks and name in options.hooks:
        options.hooks[name](context)


def _evaluate_artifacts(
    config: dict[str, Any],
    *,
    config_live: Path,
    repository_root: Path,
    snapshot: EvidenceSnapshot,
    options: EvaluationOptions,
) -> dict[str, Any]:
    diagnostics = {key: "NOT_EVALUATED" for key in DIAGNOSTIC_KEYS}
    artifact_roots, raw_roots = _resolve_roots(repository_root, config)
    all_roots = list(dict.fromkeys(artifact_roots + raw_roots))

    bundle_live, _, bundle = _snapshot_artifact(
        config["evidence_bundle_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="evidence_bundle",
        schema_name="bundle",
    )
    raw_live, _, raw = _snapshot_artifact(
        bundle["raw_manifest_path"],
        repository_root=repository_root,
        allowed_roots=all_roots,
        snapshot=snapshot,
        label="raw_manifest",
        schema_name="raw",
    )
    diagnostics["RAW_MANIFEST_EXISTS"] = "PASS"
    diagnostics["RAW_MANIFEST_SCHEMA"] = "PASS"

    raw_snapshot_paths: dict[str, Path] = {}
    normalized_manifest = json.loads(json.dumps(raw))
    for entry in normalized_manifest["files"]:
        candidate = Path(entry["path"])
        if not candidate.is_absolute():
            candidate = raw_live.parent / candidate
        live = Path(os.path.abspath(candidate))
        copied = snapshot.add_path(
            live,
            allowed_roots=raw_roots,
            label=f"raw_{entry['role']}",
        )
        raw_snapshot_paths[entry["role"]] = copied
        entry["path"] = copied.as_posix()
    raw_checksums = verify_manifest_file_entries(
        normalized_manifest,
        manifest_path=snapshot.directory / "normalized_raw_manifest.yaml",
        allowed_raw_roots=[snapshot.directory],
    )
    diagnostics["RAW_CHECKSUMS"] = "PASS"
    raw_sha256 = calculate_sha256(
        next(
            record.snapshot_path
            for record in snapshot.records
            if record.source_path == raw_live
        )
    )
    if bundle["raw_manifest_sha256"] != raw_sha256:
        raise EvidenceValidationError("bundle raw manifest checksum mismatch")

    intake_live, intake_snapshot, intake = _snapshot_artifact(
        bundle["intake_manifest_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="intake_manifest",
        schema_name="intake",
    )
    diagnostics["INTAKE_MANIFEST_SCHEMA"] = "PASS"
    prereg_record_live, _, preregistration = _snapshot_artifact(
        bundle["preregistration_record_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="preregistration_record",
        schema_name="preregistration",
    )
    calibration_live, calibration_snapshot, calibration = _snapshot_artifact(
        bundle["calibration_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="calibration_result",
        schema_name="calibration",
    )
    identifiability_live, _, identifiability = _snapshot_artifact(
        bundle["identifiability_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="identifiability_result",
        schema_name="identifiability",
    )
    holdout_live, holdout_snapshot, holdout = _snapshot_artifact(
        bundle["holdout_result_path"],
        repository_root=repository_root,
        allowed_roots=artifact_roots,
        snapshot=snapshot,
        label="holdout_result",
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
    if (
        evidence_type not in ELIGIBLE_EVIDENCE_TYPES
        or bundle["evidence_type"] != evidence_type
        or intake["evidence_type"] != evidence_type
        or holdout["evidence_type"] != evidence_type
    ):
        raise EvidenceValidationError("evidence type mismatch or ineligible type")

    trusted_entry, trusted_sha, _ = _resolve_trusted_entry(
        repository_root=repository_root,
        snapshot=snapshot,
        dataset_id=bundle["dataset_id"],
        raw_manifest_sha256=raw_sha256,
        evidence_type=evidence_type,
        preregistration_commit=preregistration["preregistration_commit"],
        options=options,
        diagnostics=diagnostics,
    )
    _verify_source_crosscheck(
        raw,
        bundle,
        trusted_entry,
        allow_test_only=options.allow_test_only,
    )
    if (
        raw["local_use_allowed"] is not True
        or raw["licence_status"] not in {"VERIFIED", "LOCAL_USE_ONLY"}
    ):
        raise EvidenceValidationError(
            "raw licence declaration conflicts with approved local use"
        )
    diagnostics["EVIDENCE_TYPE_ELIGIBLE"] = "PASS"

    intake_sha256 = calculate_sha256(intake_snapshot)
    if intake["raw_manifest_sha256"] != raw_sha256:
        raise EvidenceValidationError("intake raw_manifest_sha256 mismatch")
    declared_raw = Path(intake["raw_manifest_path"])
    if not declared_raw.is_absolute():
        declared_raw = repository_root / declared_raw
    declared_raw = Path(os.path.abspath(declared_raw))
    if declared_raw != raw_live:
        raise EvidenceValidationError("intake raw_manifest_path mismatch")
    if (
        intake["calculated_checksums"] != raw_checksums
        or intake["checksums_sha256"] != raw_checksums
    ):
        raise EvidenceValidationError("intake checksum views mismatch")
    if (
        intake["intake_status"] != "READY_FOR_PREREGISTRATION"
        or intake["blocking_reasons"]
        or not all(intake["validation_summary"].values())
    ):
        raise EvidenceValidationError("intake is not empirical-ready")

    if (
        preregistration["raw_manifest_sha256"] != raw_sha256
        or preregistration["intake_manifest_sha256"] != intake_sha256
    ):
        raise EvidenceValidationError("preregistration evidence hashes mismatch")
    verify_disjoint_ids(
        preregistration["calibration_ids"],
        preregistration["holdout_ids"],
    )
    if (
        preregistration["calibration_ids"] != intake["calibration_ids"]
        or preregistration["holdout_ids"] != intake["holdout_ids"]
    ):
        raise EvidenceValidationError("frozen IDs differ from intake")

    preregistration_file_live = Path(preregistration["preregistration_file"])
    if not preregistration_file_live.is_absolute():
        preregistration_file_live = repository_root / preregistration_file_live
    preregistration_file_live = Path(os.path.abspath(preregistration_file_live))
    preregistration_file_snapshot = snapshot.add_path(
        preregistration_file_live,
        allowed_roots=artifact_roots,
        label="preregistration_file",
    )
    if calculate_sha256(preregistration_file_snapshot) != preregistration[
        "preregistration_sha256"
    ]:
        raise EvidenceValidationError("current preregistration file hash mismatch")
    frozen_preregistration = _load_and_validate(
        preregistration_file_snapshot,
        snapshot=snapshot,
        schema_name="preregistration_file",
    )
    for key in (
        "dataset_id",
        "calibration_ids",
        "holdout_ids",
        "primary_metrics",
        "parameter_set",
        "status",
    ):
        if frozen_preregistration[key] != preregistration[key]:
            raise EvidenceValidationError(
                f"preregistration record differs from frozen file: {key}"
            )
    verify_git_file_at_commit(
        repository_root,
        preregistration_file_live,
        preregistration["preregistration_commit"],
        preregistration["preregistration_sha256"],
    )
    diagnostics["PREREGISTRATION_TRACKED"] = "PASS"

    prereg_sha = preregistration["preregistration_sha256"]
    for label, artifact in (("calibration", calibration), ("holdout", holdout)):
        for key, expected in (
            ("raw_manifest_sha256", raw_sha256),
            ("intake_manifest_sha256", intake_sha256),
            ("preregistration_sha256", prereg_sha),
            ("preregistration_commit", preregistration["preregistration_commit"]),
        ):
            if artifact[key] != expected:
                raise EvidenceValidationError(f"{label} {key} mismatch")
    if (
        calibration["calibration_ids"] != preregistration["calibration_ids"]
        or holdout["holdout_ids"] != preregistration["holdout_ids"]
    ):
        raise EvidenceValidationError("calibration or holdout IDs are not frozen")
    verify_disjoint_ids(calibration["calibration_ids"], holdout["holdout_ids"])
    diagnostics["CALIBRATION_HOLDOUT_DISJOINT"] = "PASS"

    _verify_finite_mapping(calibration["parameters"], "calibration.parameters")
    _verify_finite_mapping(calibration["metrics"], "calibration.metrics")
    parameter_hash = _canonical_sha256(calibration["parameters"])
    if calibration["parameter_result_hash"] != parameter_hash:
        raise EvidenceValidationError("calibration parameter hash mismatch")
    if (
        calibration["model_commit"] != holdout["model_commit"]
        or calibration["config_hash"] != holdout["config_hash"]
        or calibration["parameter_result_hash"] != holdout["parameter_result_hash"]
    ):
        raise EvidenceValidationError("holdout did not use frozen calibration state")
    verify_git_commit_exists(repository_root, calibration["model_commit"])
    diagnostics["CALIBRATION_RESULT_VALID"] = "PASS"

    if (
        identifiability["preregistration_sha256"] != prereg_sha
        or identifiability["parameter_result_hash"] != parameter_hash
    ):
        raise EvidenceValidationError("identifiability hashes mismatch")
    for field in ("condition_number", "max_parameter_correlation"):
        value = identifiability[field]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
        ):
            raise EvidenceValidationError(f"identifiability {field} is not finite")
    diagnostics["IDENTIFIABILITY_RESULT_VALID"] = "PASS"

    result_live_paths: list[Path] = []
    result_snapshot_paths: dict[str, Path] = {}
    for relative, expected in holdout["result_file_checksums"].items():
        result_live = Path(relative)
        if not result_live.is_absolute():
            result_live = repository_root / result_live
        result_live = Path(os.path.abspath(result_live))
        result_snapshot = snapshot.add_path(
            result_live,
            allowed_roots=artifact_roots,
            label="holdout_result_file",
        )
        result_live_paths.append(result_live)
        result_snapshot_paths[relative] = result_snapshot
        if calculate_sha256(result_snapshot) != expected:
            raise EvidenceValidationError(
                f"holdout result checksum mismatch: {relative}"
            )
    if calculate_sha256(calibration_snapshot) == calculate_sha256(holdout_snapshot):
        raise EvidenceValidationError("holdout is a renamed calibration artifact")

    declared = holdout["declared_verdict"]
    diagnostics["DECLARED_HOLDOUT_VERDICT_STATUS"] = declared
    if declared == "FAIL":
        raise GateDecisionError(
            "EXTERNAL_HOLDOUT_FAILED",
            "external holdout declared verdict is FAIL",
            "DECLARED_HOLDOUT_VERDICT_STATUS",
        )
    if declared == "INCONCLUSIVE":
        raise GateDecisionError(
            "EXTERNAL_HOLDOUT_INCONCLUSIVE",
            "external holdout declared verdict is INCONCLUSIVE",
            "DECLARED_HOLDOUT_VERDICT_STATUS",
        )
    try:
        recomputed_metrics = recompute_holdout_metrics(
            frozen_preregistration,
            raw_files=raw_snapshot_paths,
            result_files=result_snapshot_paths,
            holdout_ids=holdout["holdout_ids"],
        )
    except ValueError as exc:
        raise EvidenceValidationError(
            f"holdout metric recomputation failed: {exc}"
        ) from exc
    reported_metrics = {
        metric["metric_id"]: metric for metric in holdout["metrics"]
    }
    if len(reported_metrics) != len(holdout["metrics"]):
        raise EvidenceValidationError("duplicate reported holdout metric")
    for recomputed in recomputed_metrics:
        reported = reported_metrics.get(recomputed["metric_id"])
        if (
            reported is None
            or reported["value_unit"] != recomputed["value_unit"]
            or not math.isclose(
                float(reported["value"]),
                float(recomputed["value"]),
                rel_tol=1.0e-12,
                abs_tol=1.0e-12,
            )
        ):
            raise GateDecisionError(
                "HOLDOUT_METRIC_RECOMPUTE_MISMATCH",
                "reported holdout metric differs from snapshot recomputation",
                "HOLDOUT_METRIC_RECOMPUTE_STATUS",
            )
    diagnostics["HOLDOUT_METRIC_RECOMPUTE_STATUS"] = "PASS"
    try:
        holdout_evaluation = derive_holdout_verdict(
            frozen_preregistration,
            holdout["metrics"],
        )
    except ValueError as exc:
        raise EvidenceValidationError(
            f"holdout verdict derivation failed: {exc}"
        ) from exc
    diagnostics["DERIVED_HOLDOUT_VERDICT_STATUS"] = (
        holdout_evaluation.derived_verdict
    )
    if holdout_evaluation.derived_verdict != "PASS":
        raise GateDecisionError(
            "HOLDOUT_VERDICT_MISMATCH",
            "declared PASS does not match derived holdout verdict "
            f"{holdout_evaluation.derived_verdict}",
            "DERIVED_HOLDOUT_VERDICT_STATUS",
        )
    diagnostics["DECLARED_HOLDOUT_VERDICT_STATUS"] = "PASS"
    diagnostics["DERIVED_HOLDOUT_VERDICT_STATUS"] = "PASS"
    diagnostics["HOLDOUT_RESULT_VALID"] = "PASS"

    holdout_commit = find_first_commit_containing_file(
        repository_root,
        holdout_live,
    )
    verify_commit_ancestry(
        repository_root,
        preregistration["preregistration_commit"],
        holdout_commit,
    )
    diagnostics["PREREGISTRATION_PRECEDES_HOLDOUT"] = "PASS"

    expected_reports = {
        "v1": ("V1_RECOMPUTE", "V1_REGRESSION"),
        "v2": ("V2_ACCEPTANCE", "V2_ACCEPTANCE"),
        "validation_readiness": (
            "VALIDATION_READINESS",
            "VALIDATION_READINESS",
        ),
    }
    regression_live_paths: list[Path] = []
    for key, (expected_check, diagnostic) in expected_reports.items():
        reference = config["required_regression_reports"].get(key)
        if not reference:
            raise EvidenceValidationError(f"missing regression report path: {key}")
        report_live, _, report = _snapshot_artifact(
            reference,
            repository_root=repository_root,
            allowed_roots=artifact_roots,
            snapshot=snapshot,
            label=f"regression_{key}",
            schema_name="regression",
        )
        regression_live_paths.append(report_live)
        if (
            report["check"] != expected_check
            or report["model_commit"] != calibration["model_commit"]
        ):
            raise EvidenceValidationError(
                f"regression report {key} does not match frozen model"
            )
        diagnostics[diagnostic] = "PASS"

    diagnostics["SNAPSHOT_CREATION_STATUS"] = "PASS"
    diagnostics["SNAPSHOT_FILE_COUNT"] = "PASS"
    diagnostics["SNAPSHOT_HASH_STATUS"] = "PASS"
    context = {
        "repository_root": repository_root,
        "config": config_live,
        "bundle": bundle_live,
        "raw_manifest": raw_live,
        "raw_files": raw_snapshot_paths,
        "intake": intake_live,
        "preregistration_record": prereg_record_live,
        "preregistration_file": preregistration_file_live,
        "calibration": calibration_live,
        "identifiability": identifiability_live,
        "holdout": holdout_live,
        "holdout_result_files": result_live_paths,
        "regression_reports": regression_live_paths,
    }
    _call_hook(options, "after_snapshot_validation", context)

    verify_clean_git_paths(
        repository_root,
        [
            config_live,
            repository_root / TRUSTED_POLICY_PATH,
            bundle_live,
            intake_live,
            prereg_record_live,
            preregistration_file_live,
            calibration_live,
            identifiability_live,
            holdout_live,
            *result_live_paths,
            *regression_live_paths,
        ],
    )
    _call_hook(options, "before_final_source_recheck", context)
    current_trusted_sha, _ = _trusted_refs(repository_root)
    if current_trusted_sha != trusted_sha:
        raise EvidenceValidationError(
            "protected main changed after trusted policy snapshot"
        )
    snapshot.final_recheck()
    diagnostics["FINAL_SOURCE_RECHECK_STATUS"] = "PASS"
    diagnostics["SOURCE_IDENTITY_STATUS"] = "PASS"
    return {
        "status": "READY_FOR_BOUNDED_V3_PHYSICS",
        "final_gate": "READY_FOR_BOUNDED_V3_PHYSICS",
        "diagnostics": diagnostics,
        "blocking_reasons": [],
        "unmet": [],
        "snapshot_file_count": snapshot.source_file_count,
        "holdout_evaluation": holdout_evaluation.as_dict(),
    }


def _evaluate(
    path: Path,
    *,
    repository_root: Path,
    options: EvaluationOptions,
) -> dict[str, Any]:
    diagnostics: dict[str, str] = {}
    holdout_evaluation: HoldoutEvaluation | None = None
    snapshot_count = 0

    def copy_hook(label: str, source: Path, bytes_copied: int) -> None:
        _call_hook(
            options,
            "during_snapshot_copy",
            {
                "label": label,
                "source": source,
                "bytes_copied": bytes_copied,
            },
        )

    try:
        with EvidenceSnapshot(copy_hook=copy_hook) as snapshot:
            try:
                config_live = Path(os.path.abspath(os.fspath(path)))
                config_snapshot = snapshot.add_path(
                    config_live,
                    allowed_roots=[config_live.parent],
                    label="gate_configuration",
                )
                config = _load_and_validate(
                    config_snapshot,
                    snapshot=snapshot,
                    schema_name="config",
                )
                if not config["evidence_bundle_path"]:
                    snapshot.final_recheck()
                    return _blocked(
                        "EXTERNAL_EXPERIMENT_OR_FIELD_DATA",
                        {
                            "SNAPSHOT_CREATION_STATUS": "PASS",
                            "SNAPSHOT_FILE_COUNT": "PASS",
                            "SNAPSHOT_HASH_STATUS": "PASS",
                            "FINAL_SOURCE_RECHECK_STATUS": "PASS",
                            "SOURCE_IDENTITY_STATUS": "PASS",
                        },
                        snapshot_file_count=snapshot.source_file_count,
                    )
                result = _evaluate_artifacts(
                    config,
                    config_live=config_live,
                    repository_root=repository_root,
                    snapshot=snapshot,
                    options=options,
                )
                return result
            except Exception:
                snapshot_count = snapshot.source_file_count
                raise
    except GateDecisionError as exc:
        diagnostics[exc.diagnostic] = f"FAIL: {exc}"
        return _blocked(
            exc.code,
            diagnostics,
            detail=str(exc),
            snapshot_file_count=snapshot_count,
            holdout_evaluation=holdout_evaluation,
        )
    except (
        EvidenceValidationError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as exc:
        code, diagnostic = _classify_failure(str(exc))
        diagnostics[diagnostic] = f"FAIL: {exc}"
        return _blocked(
            code,
            diagnostics,
            detail=str(exc),
            snapshot_file_count=snapshot_count,
            holdout_evaluation=holdout_evaluation,
        )


def evaluate_gate(path: Path) -> dict[str, Any]:
    """Production evaluator with fixed policy path and no test override."""

    return _evaluate(
        path,
        repository_root=ROOT,
        options=EvaluationOptions(allow_test_only=False),
    )


def evaluate_gate_for_test(
    path: Path,
    *,
    repository_root: Path,
    hooks: Mapping[str, TestHook] | None = None,
) -> dict[str, Any]:
    """Explicit isolated evaluator for test-only protected-ref fixtures."""

    return _evaluate(
        path,
        repository_root=repository_root,
        options=EvaluationOptions(allow_test_only=True, hooks=hooks),
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
    print(f"SNAPSHOT_FILE_COUNT_VALUE = {result['snapshot_file_count']}")
    if result["holdout_evaluation"] is not None:
        print(
            "DERIVED_HOLDOUT_VERDICT_VALUE = "
            f"{result['holdout_evaluation']['derived_verdict']}"
        )
    print(f"FINAL_GATE = {result['final_gate']}")
    print(f"V3_PHYSICS_START_GATE = {result['status']}")
    if result["blocking_reasons"]:
        print("BLOCKING_REASONS = " + ", ".join(result["blocking_reasons"]))
    print("TRUSTED_POLICY_PATH = " + TRUSTED_POLICY_PATH.as_posix())
    print(
        "TOCTOU_BOUNDARY = "
        "SNAPSHOT_BASED_WITH_FINAL_IDENTITY_AND_HASH_RECHECK"
    )
    print("INTERNAL_REFERENCE_COUNTS_AS_EXPERIMENT = NO")
    print("V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED")
    if result["status"] == "READY_FOR_BOUNDED_V3_PHYSICS":
        return 0
    if result["final_gate"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
