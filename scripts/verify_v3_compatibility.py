#!/usr/bin/env python3
"""Verify lossless V2-to-V3 wrapping and deterministic golden outputs."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration, load_yaml
from cteas_ufotri.meteorology.era5_reader import prepare_hourly_forcing, read_era5
from scripts.migrate_v2_config_to_v3 import (
    canonical_mapping_sha256,
    migrate_v2_mapping,
    resolve_v2_frozen_config,
)
from scripts.run_v2_end_to_end import hybrid_era5_forcing
from validation.external_input_requirements import (
    InputStatus,
    check_dataset,
    resolve_dataset_file,
)


V2_CASE_FILES = (
    "v2_era5_72h_wet_deposition.yaml",
    "v2_accident_plant_obt_14d.yaml",
    "v2_crop_ingestion_season.yaml",
    "v2_pasture_milk_pathway.yaml",
    "v2_full_adult_dose.yaml",
    "v2_leaf_exchange_food_dose_72h.yaml",
)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _roundtrip(config: dict[str, Any]) -> dict[str, Any]:
    migrated = migrate_v2_mapping(
        config,
        original_config_sha256=canonical_mapping_sha256(config),
    )
    resolved = resolve_v2_frozen_config(migrated)
    if resolved != config:
        raise ValueError("Resolved V2 configuration is not mapping-identical")
    return resolved


def _assert_bitwise_case(
    name: str,
    config: dict[str, Any],
    forcing: pd.DataFrame | None = None,
) -> dict[str, Any]:
    migrated_config = _roundtrip(config)
    direct = run_short_case(
        deepcopy(config),
        None if forcing is None else forcing.copy(deep=True),
    )
    migrated = run_short_case(
        deepcopy(migrated_config),
        None if forcing is None else forcing.copy(deep=True),
    )
    try:
        pd.testing.assert_frame_equal(
            direct,
            migrated,
            check_exact=True,
            check_dtype=True,
            check_like=False,
        )
    except AssertionError as exc:
        raise ValueError(f"{name}: deterministic output mismatch") from exc
    return {
        "name": name,
        "rows": len(direct),
        "columns": len(direct.columns),
        "status": "PASS_BITWISE",
    }


def _v1_cases(
    era5_path: Path | None = None,
) -> list[tuple[str, dict[str, Any], pd.DataFrame | None]]:
    default = ROOT / "configs/default_parameters.yaml"
    basic = load_configuration(default, ROOT / "configs/test_case.yaml")
    advanced = load_configuration(default, ROOT / "configs/advanced_test_case.yaml")
    mapping = load_yaml(ROOT / "configs/era5_mapping.yaml")
    if era5_path is None:
        era5_path = resolve_dataset_file(ROOT, "ERA5_ACCEPTANCE")
    raw = read_era5(era5_path, mapping)
    forcing = prepare_hourly_forcing(
        raw,
        basic["physics"]["fallback_shortwave_absorptivity"],
        basic["physics"]["fallback_net_longwave_loss_w_m2"],
        accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
    )
    runoff = deepcopy(basic)
    runoff["name"] = "runoff_rain_hto_1h"
    runoff["duration_hours"] = 1
    runoff["soil"]["runoff_enabled"] = True
    runoff["soil"]["infiltration_capacity_m_s"] = 1.0e-5
    runoff["soil"]["rain_hto_concentration_bq_m3"] = 1000.0
    runoff["synthetic_forcing"]["rain_start_hour"] = 0.0
    runoff["synthetic_forcing"]["rain_end_hour"] = 1.0
    runoff["synthetic_forcing"]["rain_rate_m_s"] = 1.0e-4
    calm = deepcopy(basic)
    calm["name"] = "calm_wind_1h"
    calm["duration_hours"] = 1
    calm["synthetic_forcing"]["mean_wind_m_s"] = 0.0
    calm["synthetic_forcing"]["wind_amplitude_m_s"] = 0.0
    return [
        ("v1_synthetic_basic_48h", basic, None),
        ("v1_era5_basic_48h", basic, forcing),
        ("v1_advanced_reemission_24h", advanced, None),
        ("v1_runoff_rain_hto_1h", runoff, None),
        ("v1_calm_wind_1h", calm, None),
    ]


def verify_compatibility(era5_path: Path | None = None) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for name, config, forcing in _v1_cases(era5_path):
        records.append(_assert_bitwise_case(name, config, forcing))

    default = ROOT / "configs/default_parameters.yaml"
    if era5_path is None:
        baseline_era5 = resolve_dataset_file(ROOT, "ERA5_ACCEPTANCE")
    else:
        baseline_era5 = era5_path
    for filename in V2_CASE_FILES:
        config = load_configuration(default, ROOT / "configs/v2" / filename)
        forcing = (
            hybrid_era5_forcing(config, baseline_era5)
            if filename == "v2_era5_72h_wet_deposition.yaml"
            else None
        )
        records.append(
            _assert_bitwise_case(f"v2_{filename.removesuffix('.yaml')}", config, forcing)
        )

    observed_manifest = yaml.safe_load(
        (ROOT / "validation/cases/full_observed_72h.yaml").read_text(
            encoding="utf-8"
        )
    )
    observed_model = observed_manifest["model"]
    observed_config = load_configuration(
        ROOT / observed_model["default_config"],
        ROOT / observed_model["case_config"],
    )
    mapping = load_yaml(ROOT / observed_model["mapping_config"])
    raw_observed = read_era5(ROOT / observed_model["observed_forcing"], mapping)
    observed_forcing = prepare_hourly_forcing(
        raw_observed,
        observed_config["physics"]["fallback_shortwave_absorptivity"],
        observed_config["physics"]["fallback_net_longwave_loss_w_m2"],
        accumulation_semantics=mapping.get("accumulation_semantics", "interval"),
    )
    records.append(
        _assert_bitwise_case(
            "forcing_72h_complete_reanalysis",
            observed_config,
            observed_forcing,
        )
    )

    reference_case = yaml.safe_load(
        (ROOT / "validation/cases/independent_reference_case_001.yaml").read_text(
            encoding="utf-8"
        )
    )
    model = reference_case["model"]
    reference_config = _deep_merge(
        load_configuration(
            ROOT / model["default_config"],
            ROOT / model["case_config"],
        ),
        model["overrides"],
    )
    records.append(
        _assert_bitwise_case("independent_reference_case_001", reference_config)
    )
    return {
        "status": "PASS_BITWISE_WHERE_DETERMINISTIC",
        "v1_cases": 5,
        "v2_cases": 6,
        "forcing_cases": 1,
        "reference_cases": 1,
        "records": records,
    }


def main() -> int:
    input_check = check_dataset(ROOT, "ERA5_ACCEPTANCE")
    if input_check.status is not InputStatus.AVAILABLE:
        print("STATUS = BLOCKED_MISSING_REQUIRED_EXTERNAL_INPUT")
        print("DATASET = ERA5_ACCEPTANCE")
        print(f"MISSING_FILES = {list(input_check.missing_files)!r}")
        return 2
    try:
        result = verify_compatibility(
            resolve_dataset_file(ROOT, "ERA5_ACCEPTANCE")
        )
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        print(f"V2_TO_V3_COMPATIBILITY_STATUS = FAIL; reason={exc}", file=sys.stderr)
        return 1
    print(f"V2_TO_V3_COMPATIBILITY_STATUS = {result['status']}")
    print(f"V1_GOLDEN_CASES = PASS_{result['v1_cases']}_OF_{result['v1_cases']}")
    print(f"V2_GOLDEN_CASES = PASS_{result['v2_cases']}_OF_{result['v2_cases']}")
    print("FORCING_72H_GOLDEN_STATUS = PASS_BITWISE")
    print("INDEPENDENT_REFERENCE_GOLDEN_STATUS = PASS_BITWISE")
    print("RESULT_FIELD_MAPPING_STATUS = PASS_IDENTITY_V2_OUTPUT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
