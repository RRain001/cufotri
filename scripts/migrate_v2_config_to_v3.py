#!/usr/bin/env python3
"""Wrap a V2 YAML mapping in a lossless V3 v2_frozen envelope."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
from typing import Any

import yaml


SCHEMA_VERSION = "3.0.0"
MIGRATION_TOOL_VERSION = "1.0.0"
V2_CANDIDATE_ANCHOR = "f097115cbfc052baa18f1e49a1207fa6b3523cff"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_mapping_bytes(value: dict[str, Any]) -> bytes:
    return yaml.safe_dump(
        value,
        allow_unicode=True,
        sort_keys=True,
        default_flow_style=False,
    ).encode("utf-8")


def canonical_mapping_sha256(value: dict[str, Any]) -> str:
    return sha256_bytes(canonical_mapping_bytes(value))


def load_mapping(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    value = yaml.safe_load(raw)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value, sha256_bytes(raw)


def migrate_v2_mapping(
    value: dict[str, Any],
    *,
    original_config_sha256: str,
) -> dict[str, Any]:
    original = deepcopy(value)
    return {
        "schema_version": SCHEMA_VERSION,
        "model_version": "v3",
        "compatibility_mode": "v2_frozen",
        "enabled_modules": [],
        "parameter_package": None,
        "forcing_manifest": None,
        "source_scenario": None,
        "validation_claim": "NOT_SITE_CALIBRATED",
        "v2_compatibility": {
            "candidate_anchor": V2_CANDIDATE_ANCHOR,
            "migration_tool_version": MIGRATION_TOOL_VERSION,
            "original_config_sha256": original_config_sha256,
            "resolved_config_sha256": canonical_mapping_sha256(original),
            "original_config": original,
        },
    }


def resolve_v2_frozen_config(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported V3 configuration schema version")
    if value.get("compatibility_mode") != "v2_frozen":
        raise ValueError("Only v2_frozen resolution is implemented")
    if value.get("enabled_modules") != []:
        raise ValueError("v2_frozen configuration cannot enable V3 modules")
    compatibility = value.get("v2_compatibility")
    if not isinstance(compatibility, dict):
        raise ValueError("Missing v2_compatibility mapping")
    if compatibility.get("candidate_anchor") != V2_CANDIDATE_ANCHOR:
        raise ValueError("V2 candidate anchor changed")
    original = compatibility.get("original_config")
    if not isinstance(original, dict):
        raise ValueError("Missing original V2 configuration mapping")
    expected = compatibility.get("resolved_config_sha256")
    actual = canonical_mapping_sha256(original)
    if actual != expected:
        raise ValueError("Resolved V2 configuration hash mismatch")
    return deepcopy(original)


def migration_report(
    input_path: Path,
    output_path: Path,
    value: dict[str, Any],
    migrated: dict[str, Any],
) -> str:
    compatibility = migrated["v2_compatibility"]
    rows = [
        "| V2 field | V3 field | Mapping | Warning |",
        "|---|---|---|---|",
    ]
    for key in value:
        rows.append(
            f"| `{key}` | `v2_compatibility.original_config.{key}` "
            "| `IDENTITY` | none |"
        )
    return "\n".join(
        [
            "# V2 to V3 migration report",
            "",
            "```text",
            "MIGRATION_STATUS = PASS_V2_FROZEN_ENVELOPE",
            "NEW_V3_PHYSICS_ENABLED = NO",
            "INPUT_OVERWRITTEN = NO",
            "```",
            "",
            f"- Input: `{input_path}`",
            f"- Output: `{output_path}`",
            f"- Candidate anchor: `{V2_CANDIDATE_ANCHOR}`",
            f"- Exact input SHA-256: `{compatibility['original_config_sha256']}`",
            f"- Resolved mapping SHA-256: `{compatibility['resolved_config_sha256']}`",
            "- Warning: the envelope is architecture-only and executes no V3 physics.",
            "- Warning: `parameter_package`, `forcing_manifest`, and "
            "`source_scenario` remain null rather than being guessed.",
            "",
            *rows,
            "",
        ]
    )


def write_new(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace generated output/report, never the input file.",
    )
    arguments = parser.parse_args()
    input_path = arguments.input.resolve()
    output_path = arguments.output.resolve()
    report_path = arguments.report.resolve()
    if output_path == input_path or report_path == input_path:
        print("MIGRATION_STATUS = FAIL_INPUT_OVERWRITE_FORBIDDEN", file=sys.stderr)
        return 2
    try:
        value, exact_hash = load_mapping(input_path)
        migrated = migrate_v2_mapping(
            value,
            original_config_sha256=exact_hash,
        )
        resolved = resolve_v2_frozen_config(migrated)
        if canonical_mapping_bytes(resolved) != canonical_mapping_bytes(value):
            raise ValueError("Round-trip configuration mismatch")
        output_text = yaml.safe_dump(
            migrated,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        report_text = migration_report(input_path, output_path, value, migrated)
        write_new(output_path, output_text, force=arguments.force)
        write_new(report_path, report_text, force=arguments.force)
    except (FileNotFoundError, FileExistsError, ValueError, yaml.YAMLError) as exc:
        print(f"MIGRATION_STATUS = FAIL; reason={exc}", file=sys.stderr)
        return 1
    print("MIGRATION_STATUS = PASS_V2_FROZEN_ENVELOPE")
    print(f"ORIGINAL_CONFIG_SHA256 = {exact_hash}")
    print(f"RESOLVED_CONFIG_SHA256 = {migrated['v2_compatibility']['resolved_config_sha256']}")
    print("NEW_V3_PHYSICS_ENABLED = NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
