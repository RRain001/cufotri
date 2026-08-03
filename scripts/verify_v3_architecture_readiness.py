#!/usr/bin/env python3
"""Verify the V3 architecture-only baseline and lossless V2 boundary."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify_v3_compatibility import verify_compatibility
from validation.external_input_requirements import InputStatus, check_dataset
from validation.adapters.soybean_emras_adapter import inspect_local_package


V1_ANCHOR = "6918440faa3455b848f43589784672f3bfabfe3d"
V2_ANCHOR = "f097115cbfc052baa18f1e49a1207fa6b3523cff"
REQUIRED_FILES = (
    "docs/v3/architecture/v3_architecture_principles.md",
    "docs/v3/architecture/v3_system_context.md",
    "docs/v3/architecture/v3_component_architecture.md",
    "docs/v3/architecture/v3_dependency_rules.md",
    "docs/v3/architecture/long_forcing_architecture.md",
    "docs/v3/architecture/external_evidence_calibration_architecture.md",
    "docs/v3/architecture/advanced_reemission_architecture.md",
    "docs/v3/architecture/formal_three_box_soil_architecture.md",
    "docs/v3/architecture/dynamic_air_inventory_architecture.md",
    "docs/v3/contracts/v3_state_contract.md",
    "docs/v3/contracts/v3_flux_contract.md",
    "docs/v3/contracts/v3_activity_ledger_contract.md",
    "docs/v3/contracts/v3_configuration_contract.md",
    "docs/v3/contracts/v3_result_contract.md",
    "docs/v3/contracts/v3_provenance_contract.md",
    "docs/v3/contracts/v3_module_registry.yaml",
    "docs/v3/migration/v2_to_v3_field_matrix.csv",
    "docs/v3/gates/soybean_unblocking_manifest.md",
    "docs/v3/gates/soybean_data_request_package.md",
    "docs/v3/gates/external_data_freeze_protocol.md",
    "docs/v3/gates/soybean_calibration_parameter_contract.md",
    "docs/v3/gates/parameter_identifiability_protocol.md",
    "docs/v3/v3_architecture_only_report.md",
    "docs/implementation_status.md",
    "scripts/migrate_v2_config_to_v3.py",
    "scripts/verify_v3_compatibility.py",
    "scripts/verify_v3_physics_start_gate.py",
    "scripts/verify_v3_external_evidence_unblocking.py",
    "validation/cases/soybean_emras_template.yaml",
    "validation/cases/soybean_external_contract_synthetic.yaml",
    "validation/preregistration/soybean_emras_template.yaml",
)
ADR_NAMES = (
    "ADR-001-v2-immutable-anchor.md",
    "ADR-002-versioned-config-and-result-schemas.md",
    "ADR-003-explicit-module-ledgers.md",
    "ADR-004-opt-in-v3-physics.md",
    "ADR-005-v2-frozen-compatibility-mode.md",
    "ADR-006-external-evidence-before-physics.md",
    "ADR-007-no-dynamic-air-implementation-yet.md",
    "ADR-008-multibox-one-box-degeneration.md",
)
ADR_HEADINGS = (
    "## Context",
    "## Decision",
    "## Alternatives",
    "## Consequences",
    "## Validation requirement",
    "## Revisit condition",
)


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


def _check_required_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        raise ValueError(f"Missing architecture files: {missing}")
    for name in ADR_NAMES:
        path = ROOT / "docs/v3/adr" / name
        if not path.is_file():
            raise ValueError(f"Missing ADR: {name}")
        content = path.read_text(encoding="utf-8")
        missing_headings = [heading for heading in ADR_HEADINGS if heading not in content]
        if missing_headings:
            raise ValueError(f"Incomplete ADR {name}: {missing_headings}")


def _check_schemas() -> int:
    count = 0
    for path in sorted((ROOT / "schemas/v3").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ValueError(f"Unexpected schema dialect: {path}")
        if value.get("additionalProperties") is not False:
            raise ValueError(f"Root schema must fail closed: {path}")
        count += 1
    if count < 8:
        raise ValueError("Expected at least eight V3 schemas")
    return count


def _check_registry() -> int:
    registry = _load_yaml(ROOT / "docs/v3/contracts/v3_module_registry.yaml")
    allowed = set(registry["allowed_statuses"])
    modules = registry["modules"]
    identifiers = [item["module_id"] for item in modules]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate module_id in V3 registry")
    required_fields = {
        "module_id",
        "module_version",
        "status",
        "default_enabled",
        "compatibility",
        "evidence_gap_id",
        "validation_case_id",
        "scientific_question",
        "acceptance_gate",
        "required_evidence",
        "required_validation_cases",
        "state_inputs",
        "state_outputs",
        "ledger_contract",
    }
    for item in modules:
        missing = required_fields - set(item)
        if missing:
            raise ValueError(f"{item.get('module_id')}: missing registry fields {missing}")
        if item["status"] not in allowed:
            raise ValueError(f"{item['module_id']}: unsupported status")
        if item["module_id"] != "v2_environmental_pathways" and item["default_enabled"]:
            raise ValueError(f"{item['module_id']}: V3 candidate defaults on")
    if registry["compatibility_anchor"] != V2_ANCHOR:
        raise ValueError("Module registry candidate anchor mismatch")
    return len(modules)


def _check_mapping_matrix() -> int:
    path = ROOT / "docs/v3/migration/v2_to_v3_field_matrix.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    expected_columns = {
        "v2_path",
        "v3_path",
        "mapping_type",
        "unit_change",
        "default_policy",
        "semantic_change",
        "compatibility_risk",
        "test_case",
    }
    if not records or set(records[0]) != expected_columns:
        raise ValueError("V2-to-V3 field matrix columns mismatch")
    mapped = {record["v2_path"] for record in records}
    configuration_paths = [
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
        ROOT / "configs/advanced_test_case.yaml",
        *sorted((ROOT / "configs/v2").glob("*.yaml")),
    ]
    top_level = {
        str(key)
        for config_path in configuration_paths
        for key in _load_yaml(config_path)
    }
    missing = sorted(top_level - mapped)
    if missing:
        raise ValueError(f"Unmapped V2 top-level fields: {missing}")
    if any(
        record["mapping_type"] not in {
            "IDENTITY",
            "RENAME",
            "EXPLICIT_DEFAULT",
            "DERIVED",
            "UNSUPPORTED",
            "REQUIRES_USER_DECISION",
        }
        for record in records
    ):
        raise ValueError("Unsupported mapping type")
    if any(record["semantic_change"] not in {"NONE", "ENVELOPE_ONLY"} for record in records):
        raise ValueError("Silent semantic change in migration matrix")
    return len(records)


def _check_branch_boundary() -> None:
    if _git("rev-parse", "formal-minimal-baseline-v1^{}") != V1_ANCHOR:
        raise ValueError("V1 tag moved")
    if _git("rev-parse", "ufotri-environmental-pathways-v2-candidate^{}") != V2_ANCHOR:
        raise ValueError("V2 candidate tag moved")
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
        raise ValueError(f"Formal V2 source/config modified: {forbidden}")
    if (ROOT / "src/cteas_ufotri/v3").exists():
        raise ValueError("Formal V3 physics package exists before physics gate")


def _check_external_fail_closed() -> None:
    result = inspect_local_package(
        ROOT / "validation/cases/soybean_emras_template.yaml",
        ROOT / "validation/external_local",
    )
    if result["status"] != "BLOCKED_EXTERNAL_DATA":
        raise ValueError("Missing soybean evidence did not fail closed")
    preregistration = _load_yaml(
        ROOT / "validation/preregistration/soybean_emras_template.yaml"
    )
    if (
        preregistration.get("status") != "DRAFT_NOT_PREREGISTERED"
        or preregistration.get("calibration_permitted") is not False
        or preregistration.get("holdout_execution_permitted") is not False
    ):
        raise ValueError("Soybean preregistration template overstates readiness")


def main() -> int:
    input_check = check_dataset(ROOT, "ERA5_ACCEPTANCE")
    if input_check.status is not InputStatus.AVAILABLE:
        print("STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT")
        print("DATASET = ERA5_ACCEPTANCE")
        print(f"MISSING_FILES = {list(input_check.missing_files)!r}")
        return 2
    try:
        _check_required_files()
        schema_count = _check_schemas()
        module_count = _check_registry()
        mapping_count = _check_mapping_matrix()
        _check_branch_boundary()
        _check_external_fail_closed()
        compatibility = verify_compatibility()
        if compatibility["status"] != "PASS_BITWISE_WHERE_DETERMINISTIC":
            raise ValueError("Golden compatibility did not pass")
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        ValueError,
        yaml.YAMLError,
    ) as exc:
        print(f"V3_ARCHITECTURE_STATUS = FAIL; reason={exc}", file=sys.stderr)
        return 1
    print("V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY")
    print(f"V3_SCHEMA_STATUS = PASS_{schema_count}_PARSED_FAIL_CLOSED")
    print(f"V3_ADR_STATUS = PASS_{len(ADR_NAMES)}_COMPLETE")
    print(f"V3_MODULE_REGISTRY_STATUS = PASS_{module_count}_UNIQUE")
    print(f"V2_TO_V3_MAPPING_STATUS = PASS_{mapping_count}_ROWS_COMPLETE")
    print("V2_TO_V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC")
    print("V3_CANDIDATE_MODULES_DEFAULT = OFF")
    print("V3_FORMAL_PHYSICS_CODE_STATUS = NOT_PRESENT")
    print("EXTERNAL_DATA_MISSING_POLICY = PASS_FAIL_CLOSED")
    print("VALIDATION_CLAIM = ARCHITECTURE_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
