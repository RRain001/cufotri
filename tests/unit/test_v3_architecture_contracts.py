from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from scripts.migrate_v2_config_to_v3 import (
    canonical_mapping_sha256,
    migrate_v2_mapping,
    resolve_v2_frozen_config,
)
from scripts.verify_v3_physics_start_gate import evaluate_gate
from validation.adapters.soybean_emras_adapter import (
    create_synthetic_package,
    inspect_local_package,
    validate_local_package,
    write_intake_manifest,
    write_intake_report,
)


ROOT = Path(__file__).resolve().parents[2]


def test_v3_json_schemas_parse_and_fail_closed():
    paths = sorted((ROOT / "schemas/v3").glob("*.json"))
    assert len(paths) >= 8
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert value["additionalProperties"] is False


def test_v2_frozen_migration_roundtrip_and_tamper_detection():
    original = yaml.safe_load(
        (ROOT / "configs/v2/v2_era5_72h_wet_deposition.yaml").read_text(
            encoding="utf-8"
        )
    )
    migrated = migrate_v2_mapping(
        original,
        original_config_sha256=canonical_mapping_sha256(original),
    )
    assert migrated["enabled_modules"] == []
    assert migrated["compatibility_mode"] == "v2_frozen"
    assert resolve_v2_frozen_config(migrated) == original

    tampered = deepcopy(migrated)
    tampered["v2_compatibility"]["original_config"]["duration_hours"] = 999
    with pytest.raises(ValueError, match="hash mismatch"):
        resolve_v2_frozen_config(tampered)


def test_v2_frozen_roundtrip_preserves_short_case_bitwise():
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    config["duration_hours"] = 1
    migrated = migrate_v2_mapping(
        config,
        original_config_sha256=canonical_mapping_sha256(config),
    )
    resolved = resolve_v2_frozen_config(migrated)
    direct = run_short_case(deepcopy(config))
    roundtrip = run_short_case(deepcopy(resolved))
    pd.testing.assert_frame_equal(direct, roundtrip, check_exact=True)


def test_v3_module_registry_has_unique_default_off_candidates():
    registry = yaml.safe_load(
        (ROOT / "docs/v3/contracts/v3_module_registry.yaml").read_text(
            encoding="utf-8"
        )
    )
    modules = registry["modules"]
    identifiers = [item["module_id"] for item in modules]
    assert len(identifiers) == len(set(identifiers))
    assert all(item["status"] in registry["allowed_statuses"] for item in modules)
    assert all(
        not item["default_enabled"]
        for item in modules
        if item["module_id"] != "v2_environmental_pathways"
    )


def test_soybean_adapter_fails_closed_without_local_data(tmp_path):
    result = inspect_local_package(
        ROOT / "validation/cases/soybean_emras_template.yaml",
        tmp_path,
    )
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert result["calibration_permitted"] is False


def test_v3_physics_gate_stays_blocked_without_external_holdout():
    result = evaluate_gate(ROOT / "validation/v3/physics_start_gate.yaml")
    assert result["status"] == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    assert "complete_licensed_external_case" in result["unmet"]
    assert "raw_data_checksum_recorded" in result["unmet"]
    assert "data_schema_valid" in result["unmet"]
    assert "calibration_executed" in result["unmet"]
    assert "external_holdout_executed" in result["unmet"]


def _synthetic_case() -> Path:
    return ROOT / "validation/cases/soybean_external_contract_synthetic.yaml"


def _load_source(package: Path) -> dict:
    return yaml.safe_load(
        (package / "source_manifest.yaml").read_text(encoding="utf-8")
    )


def _write_source(package: Path, source: dict) -> None:
    (package / "source_manifest.yaml").write_text(
        yaml.safe_dump(source, sort_keys=False),
        encoding="utf-8",
    )


def test_soybean_synthetic_contract_exercises_pipeline_without_empirical_claim(
    tmp_path,
):
    create_synthetic_package(tmp_path)
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "PASS_SYNTHETIC_CONTRACT_ONLY"
    assert result["empirical_validation"] is False
    assert result["calibration_permitted"] is False
    assert result["holdout_execution_permitted"] is False
    assert result["metric_pipeline"]["status"] == "PASS"
    assert len(result["checksums_sha256"]) == 6


@pytest.mark.parametrize("role", ["meteorology", "air_hto", "mixing_boundary"])
def test_soybean_missing_required_input_fails_closed(tmp_path, role):
    create_synthetic_package(tmp_path)
    source = _load_source(tmp_path)
    (tmp_path / source["files"][role]).unlink()
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(role in reason for reason in result["blocking_reasons"])


def test_soybean_invalid_unit_fails_closed(tmp_path):
    create_synthetic_package(tmp_path)
    source = _load_source(tmp_path)
    source["units"]["air_hto"]["air_hto_bq_m3"] = "Bq L-1"
    _write_source(tmp_path, source)
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("unit must be explicit" in reason for reason in result["blocking_reasons"])


def test_soybean_discontinuous_air_series_fails_closed(tmp_path):
    create_synthetic_package(tmp_path)
    air_path = tmp_path / "air_hto.csv"
    air_path.write_text(
        air_path.read_text(encoding="utf-8").replace(
            "2025-01-01T01:00:00Z",
            "2025-01-01T01:30:00Z",
        ),
        encoding="utf-8",
    )
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any("discontinuous" in reason for reason in result["blocking_reasons"])


def test_missing_detection_limit_downgrades_to_blocked_external_data(tmp_path):
    create_synthetic_package(tmp_path)
    (tmp_path / "detection_limits.csv").unlink()
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert result["empirical_validation"] is False
    assert any(
        "detection_limits" in reason for reason in result["blocking_reasons"]
    )


def test_soybean_adapter_writes_metadata_manifest_and_report_only(tmp_path):
    package = tmp_path / "package"
    create_synthetic_package(package)
    result = validate_local_package(_synthetic_case(), package)
    manifest = tmp_path / "intake_manifest.yaml"
    report = tmp_path / "intake_report.md"
    write_intake_manifest(result, manifest)
    write_intake_report(result, report)
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert set(payload["checksums_sha256"]) == {
        "meteorology",
        "air_hto",
        "plant_observations",
        "mixing_boundary",
        "uncertainty",
        "detection_limits",
    }
    assert "1000" not in manifest.read_text(encoding="utf-8")
    assert "PASS_SYNTHETIC_CONTRACT_ONLY" in report.read_text(encoding="utf-8")


def test_holdout_inspection_before_preregistration_fails_closed(tmp_path):
    create_synthetic_package(tmp_path)
    source = _load_source(tmp_path)
    source["holdout_inspected_before_preregistration"] = True
    _write_source(tmp_path, source)
    result = validate_local_package(_synthetic_case(), tmp_path)
    assert result["status"] == "BLOCKED_EXTERNAL_DATA"
    assert any(
        "holdout inspected before preregistration" in reason
        for reason in result["blocking_reasons"]
    )


def test_internal_reference_cannot_satisfy_external_holdout_gate(tmp_path):
    evidence = yaml.safe_load(
        (ROOT / "validation/v3/physics_start_gate.yaml").read_text(
            encoding="utf-8"
        )
    )
    evidence["external_holdout_executed"] = True
    evidence["evidence"]["holdout_evidence_type"] = "REFERENCE_MODEL"
    path = tmp_path / "gate.yaml"
    path.write_text(yaml.safe_dump(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="cannot satisfy holdout gate"):
        evaluate_gate(path)


def test_preregistration_gate_cannot_finalize_without_frozen_data(tmp_path):
    evidence = yaml.safe_load(
        (ROOT / "validation/v3/physics_start_gate.yaml").read_text(
            encoding="utf-8"
        )
    )
    evidence["preregistration_committed_before_holdout"] = True
    path = tmp_path / "gate.yaml"
    path.write_text(yaml.safe_dump(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="contradicts tracked evidence"):
        evaluate_gate(path)
