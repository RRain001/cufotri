#!/usr/bin/env python3
"""Fail-closed completeness validator for the V4 production-case input manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
AUDIT = ROOT / "docs/v4/governance/v4_production_input_readiness_audit_r1.yaml"
SCHEMA = ROOT / "schemas/v4/v4_production_case_input_manifest.schema.json"

READY_DIRECT = {"READY_CONTROLLED", "READY_PROVENANCED_SOURCE"}
READY_DERIVED = "DERIVED_FROM_READY_STATE"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def authority_records(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for domain, block in audit["input_registry"].items():
        if not isinstance(block, dict):
            continue
        for name, record in block.items():
            if isinstance(record, dict) and "classification" in record and "readiness" in record:
                records[f"{domain}.{name}"] = record
    return records


def source_is_provenanced(record: dict[str, Any]) -> bool:
    source = record.get("source")
    return bool(
        isinstance(source, dict)
        and source.get("artifact")
        and source.get("revision")
    )


def zero_policy_is_evidenced(record: dict[str, Any]) -> bool:
    zero = record["explicit_zero"]
    if not zero["declared"]:
        return True
    return bool(zero["evidence_artifact"] and zero["evidence_revision"] and zero["rationale"])


def evaluate(manifest: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda e: list(e.path))
    if schema_errors:
        return {
            "schema_valid": False,
            "inventory_complete": False,
            "production_complete": False,
            "status": "FAIL_CLOSED_SCHEMA_INVALID",
            "issues": [f"schema:{'/'.join(map(str, err.path))}:{err.message}" for err in schema_errors],
        }

    audit = load_yaml(AUDIT)
    authority = authority_records(audit)
    entries = manifest["inputs"]
    ids = [entry["quantity_id"] for entry in entries]
    by_id = {entry["quantity_id"]: entry for entry in entries}
    issues: list[str] = []

    duplicates = sorted({qid for qid in ids if ids.count(qid) > 1})
    if duplicates:
        issues.extend(f"duplicate:{qid}" for qid in duplicates)

    missing = sorted(set(authority) - set(ids))
    extra = sorted(set(ids) - set(authority))
    issues.extend(f"missing_inventory:{qid}" for qid in missing)
    issues.extend(f"unknown_inventory:{qid}" for qid in extra)

    for qid, frozen in authority.items():
        record = by_id.get(qid)
        if record is None:
            continue
        if record["required"] is not bool(frozen.get("required", False)):
            issues.append(f"required_flag_mismatch:{qid}")
        if record["classification"] != frozen["classification"]:
            issues.append(f"classification_mismatch:{qid}")
        frozen_unit = frozen.get("canonical_unit")
        if frozen_unit is not None and record["canonical_unit"] != frozen_unit:
            issues.append(f"unit_mismatch:{qid}")

    inventory_complete = not any(
        issue.startswith(("duplicate:", "missing_inventory:", "unknown_inventory:", "required_flag_mismatch:", "classification_mismatch:", "unit_mismatch:"))
        for issue in issues
    )

    ready_cache: dict[str, bool] = {}

    def record_ready(qid: str, stack: tuple[str, ...] = ()) -> bool:
        if qid in ready_cache:
            return ready_cache[qid]
        if qid in stack or qid not in by_id:
            return False
        record = by_id[qid]
        if not record["required"]:
            ready_cache[qid] = True
            return True
        if not record["production_use_authorized"]:
            ready_cache[qid] = False
            return False
        if not zero_policy_is_evidenced(record):
            ready_cache[qid] = False
            return False

        readiness = record["readiness"]
        if readiness == "READY_CONTROLLED":
            ok = source_is_provenanced(record)
        elif readiness == "READY_PROVENANCED_SOURCE":
            ok = source_is_provenanced(record) and bool(record["missing_data_policy"])
            if record["classification"] in {"EXPLICIT_EXTERNAL_SCENARIO_INPUT", "REAL_UPSTREAM_DATA_PREREQUISITE"}:
                ok = ok and bool(record["temporal_support"]) and bool(record["spatial_support"]) and bool(record["identity_support"])
        elif readiness == READY_DERIVED:
            derivation = record["derivation"]
            deps = derivation["dependencies"]
            ok = bool(derivation["evidence_complete"] and deps) and all(
                record_ready(dep, stack + (qid,)) for dep in deps
            )
        else:
            ok = False
        ready_cache[qid] = ok
        return ok

    for qid, frozen in authority.items():
        if not frozen.get("required", False) or qid not in by_id:
            continue
        record = by_id[qid]
        if record["explicit_zero"]["declared"] and not zero_policy_is_evidenced(record):
            issues.append(f"unevidenced_explicit_zero:{qid}")
        if record["readiness"] not in READY_DIRECT | {READY_DERIVED}:
            issues.append(f"non_ready_state:{qid}:{record['readiness']}")
        elif not record_ready(qid):
            issues.append(f"readiness_evidence_incomplete:{qid}")

    if manifest["case_identity"]["mode"] != "PRODUCTION_CANDIDATE":
        issues.append("case_mode_not_production_candidate")
    if manifest["production_claim"] is not True:
        issues.append("production_claim_false")

    production_complete = inventory_complete and not issues
    return {
        "schema_valid": True,
        "inventory_complete": inventory_complete,
        "production_complete": production_complete,
        "status": "PASS_PRODUCTION_COMPLETE" if production_complete else "FAIL_CLOSED_INCOMPLETE",
        "required_input_count": sum(bool(r.get("required", False)) for r in authority.values()),
        "manifest_input_count": len(entries),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expect-incomplete", action="store_true")
    args = parser.parse_args()
    result = evaluate(load_yaml(args.manifest))
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.expect_incomplete:
        return 0 if result["schema_valid"] and result["inventory_complete"] and not result["production_complete"] else 1
    return 0 if result["production_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
