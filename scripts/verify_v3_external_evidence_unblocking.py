#!/usr/bin/env python3
"""Verify the fail-closed V3 external-evidence unblocking work package."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_v3_physics_start_gate import evaluate_gate
from validation.adapters.soybean_emras_adapter import (
    create_synthetic_package,
    inspect_local_package,
    validate_local_package,
    write_intake_manifest,
    write_intake_report,
)


REQUIRED_FILES = (
    "docs/v3/gates/soybean_unblocking_manifest.md",
    "docs/v3/gates/soybean_data_request_package.md",
    "docs/v3/gates/external_data_freeze_protocol.md",
    "docs/v3/gates/soybean_calibration_parameter_contract.md",
    "docs/v3/gates/parameter_identifiability_protocol.md",
    "schemas/v3/external_evidence_intake.schema.json",
    "validation/external_local/README.md",
    "validation/external_local/.gitignore",
    "validation/adapters/soybean_emras_adapter.py",
    "validation/cases/soybean_emras_template.yaml",
    "validation/cases/soybean_external_contract_synthetic.yaml",
    "validation/preregistration/soybean_emras_template.yaml",
    "validation/v3/physics_start_gate.yaml",
)
PREREGISTRATION_FIELDS = {
    "scientific_question",
    "primary_observable",
    "secondary_observables",
    "calibration_dataset",
    "holdout_dataset",
    "calibration_period",
    "holdout_period",
    "fixed_parameters",
    "calibration_parameters",
    "parameter_bounds",
    "parameter_priors",
    "primary_metrics",
    "secondary_metrics",
    "acceptance_thresholds",
    "missing_data_policy",
    "detection_limit_policy",
    "uncertainty_policy",
    "exclusion_rules",
    "failure_criteria",
    "non_identifiability_criteria",
    "boundary_hit_criteria",
    "benchmark_regression_requirements",
    "V1_regression_requirements",
    "V2_acceptance_requirements",
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return value


def _check_scope() -> None:
    changed = set(
        filter(
            None,
            _git("diff", "--name-only", "main...HEAD").splitlines()
            + _git("diff", "--name-only").splitlines(),
        )
    )
    forbidden = sorted(
        name for name in changed if name.startswith(("src/", "configs/"))
    )
    if forbidden:
        raise ValueError(f"Formal model/config modified: {forbidden}")
    tracked_local = set(
        filter(None, _git("ls-files", "validation/external_local").splitlines())
    )
    allowed_local = {
        "validation/external_local/.gitignore",
        "validation/external_local/README.md",
    }
    if tracked_local - allowed_local:
        raise ValueError("Raw or derived external-local data is tracked")


def _check_preregistration() -> None:
    preregistration = _load_yaml(
        ROOT / "validation/preregistration/soybean_emras_template.yaml"
    )
    missing = sorted(PREREGISTRATION_FIELDS - set(preregistration))
    if missing:
        raise ValueError(f"Preregistration fields missing: {missing}")
    if (
        preregistration.get("status") != "DRAFT_NOT_PREREGISTERED"
        or preregistration.get("dataset_manifest_hash")
        != "NOT_AVAILABLE_BLOCKED_EXTERNAL_DATA"
        or preregistration.get("calibration_permitted") is not False
        or preregistration.get("holdout_execution_permitted") is not False
    ):
        raise ValueError("Preregistration overstates readiness without frozen data")
    if set(preregistration["calibration_dataset"]["sample_ids"]) & set(
        preregistration["holdout_dataset"]["sample_ids"]
    ):
        raise ValueError("Preregistration calibration/holdout identifiers overlap")


def _check_synthetic_contract() -> None:
    case = _load_yaml(
        ROOT / "validation/cases/soybean_external_contract_synthetic.yaml"
    )
    if (
        case.get("evidence_type") != "SYNTHETIC_CONTRACT_TEST"
        or case.get("empirical_validation") is not False
        or case.get("external_case_count_contribution") != 0
    ):
        raise ValueError("Synthetic contract is mislabeled as empirical evidence")
    with tempfile.TemporaryDirectory(prefix="cteas_soybean_contract_") as temporary:
        package = Path(temporary) / "package"
        create_synthetic_package(package)
        result = validate_local_package(
            ROOT / "validation/cases/soybean_external_contract_synthetic.yaml",
            package,
        )
        if (
            result["status"] != "PASS_SYNTHETIC_CONTRACT_ONLY"
            or result["empirical_validation"] is not False
            or result["metric_pipeline"]["status"] != "PASS"
            or len(result["checksums_sha256"]) != 6
        ):
            raise ValueError("Synthetic intake contract failed")
        manifest = Path(temporary) / "intake_manifest.yaml"
        report = Path(temporary) / "intake_report.md"
        write_intake_manifest(result, manifest)
        write_intake_report(result, report)
        payload = _load_yaml(manifest)
        if payload.get("manifest_version") != "1.0.0" or not report.is_file():
            raise ValueError("Synthetic manifest/report generation failed")


def main() -> int:
    try:
        missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
        if missing:
            raise ValueError(f"Unblocking files missing: {missing}")
        schema = json.loads(
            (
                ROOT / "schemas/v3/external_evidence_intake.schema.json"
            ).read_text(encoding="utf-8")
        )
        if (
            schema.get("$schema")
            != "https://json-schema.org/draft/2020-12/schema"
            or schema.get("additionalProperties") is not False
        ):
            raise ValueError("External-evidence intake schema is not fail-closed")
        _check_scope()
        _check_preregistration()
        _check_synthetic_contract()
        real = inspect_local_package(
            ROOT / "validation/cases/soybean_emras_template.yaml",
            ROOT / "validation/external_local",
        )
        if (
            real["status"] != "BLOCKED_EXTERNAL_DATA"
            or real["empirical_validation"] is not False
        ):
            raise ValueError("Absent real soybean package did not fail closed")
        reference = _load_yaml(
            ROOT / "validation/cases/independent_reference_case_001.yaml"
        )
        if reference.get("reference_type") != "REFERENCE_MODEL":
            raise ValueError("Internal reference evidence type changed")
        gate = evaluate_gate(ROOT / "validation/v3/physics_start_gate.yaml")
        if gate["status"] != "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA":
            raise ValueError("Physics gate passed without empirical evidence")
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        print(
            f"V3_EXTERNAL_EVIDENCE_UNBLOCKING_STATUS = FAIL; reason={exc}",
            file=sys.stderr,
        )
        return 1
    print(
        "V3_EXTERNAL_EVIDENCE_UNBLOCKING_STATUS = "
        "READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA"
    )
    print("SOYBEAN_UNBLOCKING_MANIFEST_STATUS = COMPLETE")
    print("DATA_REQUEST_PACKAGE_STATUS = COMPLETE_NOT_SENT")
    print("LOCAL_INTAKE_STATUS = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA")
    print("DATA_FREEZE_PROTOCOL_STATUS = COMPLETE_NOT_EXECUTED")
    print("PREREGISTRATION_TEMPLATE_STATUS = DRAFT_NOT_PREREGISTERED")
    print("CALIBRATION_CONTRACT_STATUS = COMPLETE_NOT_EXECUTED")
    print(
        "PARAMETER_IDENTIFIABILITY_STATUS = "
        "NOT_ASSESSED_NO_EXECUTABLE_EXTERNAL_CASE"
    )
    print("SYNTHETIC_CONTRACT_TEST_STATUS = PASS_NOT_EMPIRICAL")
    print(
        "V3_PHYSICS_START_GATE = "
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
