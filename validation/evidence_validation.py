"""Shared fail-closed validation helpers for external empirical evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping, Sequence

import yaml

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError, ValidationError
except ImportError as exc:  # pragma: no cover - exercised by dependency check
    raise RuntimeError(
        "jsonschema is required for external-evidence validation"
    ) from exc


class EvidenceValidationError(ValueError):
    """Raised when an evidence artifact cannot be independently verified."""


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_regular_file(
    path: Path,
    *,
    allowed_roots: Sequence[Path] | None = None,
    nonempty: bool = True,
) -> Path:
    """Resolve a readable regular file and enforce its allowed location."""

    try:
        resolved = path.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise EvidenceValidationError(f"required file does not exist: {path}") from exc
    if not resolved.is_file():
        raise EvidenceValidationError(f"required path is not a regular file: {path}")
    if nonempty and resolved.stat().st_size <= 0:
        raise EvidenceValidationError(f"required file is empty: {path}")
    if allowed_roots:
        roots = [root.resolve(strict=True) for root in allowed_roots]
        if not any(resolved.is_relative_to(root) for root in roots):
            raise EvidenceValidationError(
                f"path escapes allowed evidence roots: {path}"
            )
    return resolved


def resolve_artifact_path(
    reference: str | Path,
    *,
    repository_root: Path,
    allowed_roots: Sequence[Path],
) -> Path:
    candidate = Path(reference)
    if not candidate.is_absolute():
        candidate = repository_root / candidate
    return require_regular_file(candidate, allowed_roots=allowed_roots)


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    checked = require_regular_file(path)
    try:
        if checked.suffix.lower() == ".json":
            value = json.loads(checked.read_text(encoding="utf-8"))
        elif checked.suffix.lower() in {".yaml", ".yml"}:
            value = yaml.safe_load(checked.read_text(encoding="utf-8"))
        else:
            raise EvidenceValidationError(
                f"unsupported evidence artifact format: {checked}"
            )
    except (json.JSONDecodeError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise EvidenceValidationError(
            f"cannot parse evidence artifact {checked}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise EvidenceValidationError(
            f"evidence artifact must contain a mapping: {checked}"
        )
    return value


def validate_json_schema(
    document: Mapping[str, Any],
    schema_path: Path,
) -> None:
    schema = load_json_or_yaml(schema_path)
    try:
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        errors = sorted(validator.iter_errors(document), key=lambda item: list(item.path))
    except SchemaError as exc:
        raise EvidenceValidationError(
            f"invalid JSON schema {schema_path}: {exc.message}"
        ) from exc
    if errors:
        error = errors[0]
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        raise EvidenceValidationError(
            f"schema validation failed at {location}: {error.message}"
        )


def verify_declared_checksum(path: Path, expected_sha256: str) -> str:
    calculated = calculate_sha256(path)
    if expected_sha256 != "SOURCE_CHECKSUM_UNAVAILABLE":
        if calculated != expected_sha256:
            raise EvidenceValidationError(
                f"checksum mismatch for {path}: expected {expected_sha256}, "
                f"calculated {calculated}"
            )
    return calculated


def verify_manifest_file_entries(
    manifest: Mapping[str, Any],
    *,
    manifest_path: Path,
    allowed_raw_roots: Sequence[Path],
) -> dict[str, str]:
    """Recompute all raw-file hashes and verify declared values."""

    calculated: dict[str, str] = {}
    seen_roles: set[str] = set()
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise EvidenceValidationError("raw manifest files must be a non-empty list")
    for entry in entries:
        if not isinstance(entry, dict):
            raise EvidenceValidationError("raw manifest file entry must be a mapping")
        role = str(entry.get("role", ""))
        if not role or role in seen_roles:
            raise EvidenceValidationError(f"raw manifest role is missing or duplicate: {role}")
        seen_roles.add(role)
        raw_path = Path(str(entry.get("path", "")))
        if not raw_path.is_absolute():
            raw_path = manifest_path.parent / raw_path
        checked = require_regular_file(raw_path, allowed_roots=allowed_raw_roots)
        actual = verify_declared_checksum(
            checked,
            str(entry.get("expected_sha256", "")),
        )
        if actual != entry.get("calculated_sha256"):
            raise EvidenceValidationError(
                f"calculated checksum record mismatch for raw role {role}"
            )
        if checked.stat().st_size != entry.get("size_bytes"):
            raise EvidenceValidationError(
                f"size_bytes mismatch for raw role {role}"
            )
        calculated[role] = actual
    return calculated


def _git(repository_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository_root,
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        stderr = ""
        if isinstance(exc, subprocess.CalledProcessError):
            stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        raise EvidenceValidationError(
            f"git verification failed: git {' '.join(arguments)}; {stderr}"
        ) from exc


def verify_git_commit_exists(repository_root: Path, commit: str) -> None:
    _git(repository_root, "cat-file", "-e", f"{commit}^{{commit}}")


def _repository_relative(repository_root: Path, path: Path) -> str:
    resolved_root = repository_root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_relative_to(resolved_root):
        raise EvidenceValidationError(f"Git artifact is outside repository: {path}")
    return resolved_path.relative_to(resolved_root).as_posix()


def verify_git_file_at_commit(
    repository_root: Path,
    path: Path,
    commit: str,
    expected_sha256: str,
) -> None:
    verify_git_commit_exists(repository_root, commit)
    relative = _repository_relative(repository_root, path)
    payload = _git(repository_root, "show", f"{commit}:{relative}").stdout
    calculated = hashlib.sha256(payload).hexdigest()
    if calculated != expected_sha256:
        raise EvidenceValidationError(
            f"Git artifact hash mismatch for {relative} at {commit}"
        )


def find_first_commit_containing_file(
    repository_root: Path,
    path: Path,
) -> str:
    relative = _repository_relative(repository_root, path)
    output = _git(
        repository_root,
        "log",
        "--diff-filter=A",
        "--reverse",
        "--format=%H",
        "--",
        relative,
    ).stdout.decode("utf-8").strip()
    commits = [line for line in output.splitlines() if line]
    if not commits:
        raise EvidenceValidationError(
            f"tracked artifact has no add commit: {relative}"
        )
    return commits[0]


def verify_commit_ancestry(
    repository_root: Path,
    older_commit: str,
    newer_commit: str,
) -> None:
    if older_commit == newer_commit:
        raise EvidenceValidationError(
            "preregistration and holdout commits must be different"
        )
    _git(repository_root, "merge-base", "--is-ancestor", older_commit, newer_commit)


def verify_clean_git_paths(
    repository_root: Path,
    paths: Iterable[Path],
) -> None:
    relative = [_repository_relative(repository_root, path) for path in paths]
    output = _git(
        repository_root,
        "status",
        "--porcelain",
        "--",
        *relative,
    ).stdout.decode("utf-8").strip()
    if output:
        raise EvidenceValidationError(
            f"evidence artifacts have uncommitted changes: {output}"
        )


def parse_finite_number(
    value: Any,
    *,
    label: str,
    minimum: float | None = None,
    maximum: float | None = None,
    exclusive_minimum: float | None = None,
) -> float:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise EvidenceValidationError(f"{label} must contain a numeric value")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{label} must be numeric") from exc
    if not math.isfinite(number):
        raise EvidenceValidationError(f"{label} must be finite")
    if minimum is not None and number < minimum:
        raise EvidenceValidationError(f"{label} must be >= {minimum}")
    if maximum is not None and number > maximum:
        raise EvidenceValidationError(f"{label} must be <= {maximum}")
    if exclusive_minimum is not None and number <= exclusive_minimum:
        raise EvidenceValidationError(f"{label} must be > {exclusive_minimum}")
    return number


def verify_clean_numeric_series(
    rows: Sequence[Mapping[str, str]],
    field_rules: Mapping[str, Mapping[str, float]],
    *,
    label: str,
) -> None:
    if not rows:
        raise EvidenceValidationError(f"{label} must contain data rows")
    for row_index, row in enumerate(rows, start=2):
        for field, rule in field_rules.items():
            parse_finite_number(
                row.get(field),
                label=f"{label}.{field} row {row_index}",
                minimum=rule.get("minimum"),
                maximum=rule.get("maximum"),
                exclusive_minimum=rule.get("exclusive_minimum"),
            )


def verify_disjoint_ids(
    calibration_ids: Sequence[str],
    holdout_ids: Sequence[str],
) -> None:
    if not calibration_ids or not holdout_ids:
        raise EvidenceValidationError(
            "calibration and holdout identifiers must both be non-empty"
        )
    if len(calibration_ids) != len(set(calibration_ids)):
        raise EvidenceValidationError("calibration identifiers contain duplicates")
    if len(holdout_ids) != len(set(holdout_ids)):
        raise EvidenceValidationError("holdout identifiers contain duplicates")
    overlap = sorted(set(calibration_ids) & set(holdout_ids))
    if overlap:
        raise EvidenceValidationError(
            f"calibration and holdout identifiers overlap: {overlap}"
        )


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    checked = require_regular_file(path)
    try:
        with checked.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise EvidenceValidationError(f"cannot parse CSV {checked}: {exc}") from exc
    if not fields or not rows:
        raise EvidenceValidationError(
            f"CSV must contain a header and data rows: {checked}"
        )
    return fields, rows
