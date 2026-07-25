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
from validation.adapters.soybean_emras_adapter import inspect_local_package


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
    assert "external_holdout_executed" in result["unmet"]
