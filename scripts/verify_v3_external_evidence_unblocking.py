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
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_v3_physics_start_gate import evaluate_gate
from validation.evidence_validation import (
    EvidenceValidationError,
    validate_json_schema,
)
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
    "docs/v3/v3_external_evidence_unblocking_report.md",
    "docs/v3/gates/v3_external_evidence_adversarial_test_report.md",
    "docs/v3/v3_external_evidence_gate_remediation_report.md",
    "docs/v3/v3_external_evidence_gate_independent_review_package.md",
    "schemas/v3/external_evidence_intake.schema.json",
    "schemas/v3/external_raw_data_manifest.schema.json",
    "schemas/v3/external_intake_manifest.schema.json",
    "schemas/v3/external_preregistration_record.schema.json",
    "schemas/v3/external_calibration_result.schema.json",
    "schemas/v3/external_identifiability_result.schema.json",
    "schemas/v3/external_holdout_result.schema.json",
    "schemas/v3/v3_physics_gate_evidence_bundle.schema.json",
    "schemas/v3/external_regression_result.schema.json",
    "schemas/v3/v3_physics_gate_config.schema.json",
    "validation/evidence_validation.py",
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
            or len(result["calculated_checksums"]) != 6
        ):
            raise ValueError("Synthetic intake contract failed")
        manifest = Path(temporary) / "intake_manifest.yaml"
        report = Path(temporary) / "intake_report.md"
        write_intake_manifest(result, manifest)
        write_intake_report(result, report)
        payload = _load_yaml(manifest)
        if (
            payload.get("manifest_schema_version") != "2.0.0"
            or not report.is_file()
        ):
            raise ValueError("Synthetic manifest/report generation failed")


def _check_runtime_schema_validation() -> None:
    schema_path = ROOT / "schemas/v3/external_intake_manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    try:
        validate_json_schema(
            {"manifest_schema_version": "2.0.0"},
            schema_path,
        )
    except EvidenceValidationError:
        return
    raise ValueError("Runtime schema validation accepted an incomplete intake")


def _check_adversarial_intake() -> None:
    case = ROOT / "validation/cases/soybean_external_contract_synthetic.yaml"
    with tempfile.TemporaryDirectory(prefix="cteas_soybean_attacks_") as temporary:
        package = Path(temporary) / "package"

        create_synthetic_package(package)
        (package / "air_hto.csv").write_text(
            "time_utc,air_hto_bq_m3\n"
            "2025-01-01T00:00:00Z,text\n"
            "2025-01-01T01:00:00Z,text\n"
            "2025-01-01T02:00:00Z,text\n",
            encoding="utf-8",
        )
        nonnumeric = validate_local_package(case, package)
        if nonnumeric["status"] != "BLOCKED_EXTERNAL_DATA":
            raise ValueError("Non-numeric air HTO bypassed intake")

        create_synthetic_package(package)
        (package / "detection_limits.csv").write_text(
            "observable,detection_limit,unit\n,,\n",
            encoding="utf-8",
        )
        empty_detection = validate_local_package(case, package)
        if empty_detection["status"] != "BLOCKED_EXTERNAL_DATA":
            raise ValueError("Empty detection limit bypassed intake")

        create_synthetic_package(package)
        source_path = package / "source_manifest.yaml"
        source = _load_yaml(source_path)
        source["files"][0]["expected_sha256"] = "0" * 64
        source_path.write_text(
            yaml.safe_dump(source, sort_keys=False),
            encoding="utf-8",
        )
        checksum = validate_local_package(case, package)
        if checksum["status"] != "BLOCKED_EXTERNAL_DATA":
            raise ValueError("Raw checksum mismatch bypassed intake")


def _check_gate_attacks() -> None:
    baseline = _load_yaml(ROOT / "validation/v3/physics_start_gate.yaml")
    with tempfile.TemporaryDirectory(prefix="cteas_gate_attacks_") as temporary:
        directory = Path(temporary)
        nonexistent = dict(baseline)
        nonexistent["evidence_bundle_path"] = "validation/does-not-exist.yaml"
        path = directory / "nonexistent.yaml"
        path.write_text(yaml.safe_dump(nonexistent), encoding="utf-8")
        if evaluate_gate(path)["status"] == "READY_FOR_BOUNDED_V3_PHYSICS":
            raise ValueError("Nonexistent manifest path bypassed physics gate")

        boolean_bypass = dict(baseline)
        for name in (
            "complete_licensed_external_case",
            "data_schema_valid",
            "calibration_executed",
            "external_holdout_executed",
            "parameter_identifiability_assessed",
        ):
            boolean_bypass[name] = True
        path = directory / "booleans.yaml"
        path.write_text(yaml.safe_dump(boolean_bypass), encoding="utf-8")
        if evaluate_gate(path)["status"] == "READY_FOR_BOUNDED_V3_PHYSICS":
            raise ValueError("Diagnostic booleans bypassed physics gate")


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
        _check_runtime_schema_validation()
        _check_synthetic_contract()
        _check_adversarial_intake()
        _check_gate_attacks()
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
    print("SCHEMA_RUNTIME_VALIDATION_STATUS = PASS_EXECUTED")
    print("NONNUMERIC_AIR_HTO_ATTACK = BLOCKED")
    print("EMPTY_DETECTION_LIMIT_ATTACK = BLOCKED")
    print("CHECKSUM_TAMPER_ATTACK = BLOCKED")
    print("NONEXISTENT_MANIFEST_ATTACK = BLOCKED")
    print("BOOLEAN_BYPASS_ATTACK = BLOCKED")
    print(
        "V3_PHYSICS_START_GATE = "
        "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
