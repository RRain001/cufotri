#!/usr/bin/env python3
"""Evaluate the evidence gate for starting formal V3 physics."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
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


def _load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def evaluate_gate(path: Path) -> dict[str, Any]:
    evidence = _load_mapping(path)
    missing_fields = [name for name in REQUIRED_TRUE if name not in evidence]
    if missing_fields:
        raise ValueError(f"Physics gate fields missing: {missing_fields}")
    if any(not isinstance(evidence[name], bool) for name in REQUIRED_TRUE):
        raise ValueError("Physics gate prerequisites must be booleans")

    soybean = _load_mapping(ROOT / "validation/cases/soybean_emras_template.yaml")
    preregistration = _load_mapping(
        ROOT / "validation/preregistration/soybean_emras_template.yaml"
    )
    if (
        evidence["complete_licensed_external_case"]
        and soybean.get("status") == "DRAFT_NOT_PREREGISTERED"
    ):
        raise ValueError("Template evidence cannot satisfy external-case gate")
    if (
        evidence["preregistration_committed_before_holdout"]
        and preregistration.get("status") != "PREREGISTERED"
    ):
        raise ValueError("Preregistration gate contradicts tracked evidence")
    evidence_labels = evidence.get("evidence", {})
    if not isinstance(evidence_labels, dict):
        raise ValueError("Physics gate evidence must be a mapping")
    internal_types = {
        "REFERENCE_MODEL",
        "INTERNAL_REGRESSION",
        "SYNTHETIC_CONTRACT_TEST",
    }
    if (
        evidence["complete_licensed_external_case"]
        and evidence_labels.get("external_case_evidence_type") in internal_types
    ):
        raise ValueError("Internal or synthetic evidence cannot satisfy external-case gate")
    if (
        evidence["external_holdout_executed"]
        and evidence_labels.get("holdout_evidence_type") in internal_types
    ):
        raise ValueError("Internal or synthetic evidence cannot satisfy holdout gate")
    if evidence["raw_data_checksum_recorded"] and not evidence.get(
        "external_case_manifest"
    ):
        raise ValueError("Checksum gate requires an external_case_manifest")
    if evidence["data_schema_valid"] and not evidence.get("external_case_manifest"):
        raise ValueError("Schema gate requires an external_case_manifest")
    if (
        evidence["calibration_executed"]
        and evidence_labels.get("calibration") != "CALIBRATION_COMPLETE"
    ):
        raise ValueError("Calibration execution gate contradicts tracked evidence")
    unmet = [name for name in REQUIRED_TRUE if evidence[name] is not True]
    return {
        "status": (
            "READY_FOR_BOUNDED_V3_PHYSICS"
            if not unmet
            else "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
        ),
        "unmet": unmet,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence",
        type=Path,
        default=ROOT / "validation/v3/physics_start_gate.yaml",
    )
    arguments = parser.parse_args()
    try:
        result = evaluate_gate(arguments.evidence.resolve())
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"V3_PHYSICS_START_GATE = FAIL_CLOSED; reason={exc}", file=sys.stderr)
        return 1
    print(f"V3_PHYSICS_START_GATE = {result['status']}")
    if result["unmet"]:
        print("UNMET_PREREQUISITES = " + ", ".join(result["unmet"]))
    print("INTERNAL_REFERENCE_COUNTS_AS_EXPERIMENT = NO")
    print("V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
