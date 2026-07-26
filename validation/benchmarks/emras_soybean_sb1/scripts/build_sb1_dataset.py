#!/usr/bin/env python3
"""Build and checksum the tracked SB1 publication-table dataset."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import jsonschema
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
TABLES = BENCHMARK / "published_tables"
SCHEMAS = BENCHMARK / "schemas"
GENERATED = LOCAL / "generated_forcing"
PDF = LOCAL / "references" / "IAEA-emras-tritium-wg.pdf"
REPORTED_MEAN = 7.77e4
WATER_VAPOUR_GAS_CONSTANT_J_KG_K = 461.5

sys.path.insert(0, str(ROOT / "src"))
from cteas_ufotri.meteorology.derived_variables import (  # noqa: E402
    saturation_vapour_pressure_pa,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def combined_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def nullable_record(row: pd.Series) -> dict[str, Any]:
    return {
        key: (None if pd.isna(value) else value)
        for key, value in row.to_dict().items()
    }


def validate_rows(csv_path: Path, schema_path: Path) -> None:
    frame = pd.read_csv(csv_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        errors = sorted(
            validator.iter_errors(nullable_record(row)),
            key=lambda error: list(error.path),
        )
        if errors:
            messages = "; ".join(error.message for error in errors)
            raise ValueError(f"{csv_path.name} row {row_number}: {messages}")


def chamber_profiles() -> dict[str, float]:
    frame = pd.read_csv(TABLES / "sb1_chamber_conditions_5min.csv")
    exposure = frame[
        frame["minutes_from_exposure_start"].between(0, 60)
    ].copy()
    if exposure["minutes_from_exposure_start"].tolist() != list(range(0, 61, 5)):
        raise ValueError("SB1 chamber exposure timestamps are not complete 5-minute points")
    if pd.notna(exposure.iloc[0]["air_moisture_hto_bq_ml_water"]):
        raise ValueError("The published 09:30 HTO cell must remain missing")
    exposure.loc[
        exposure["minutes_from_exposure_start"] == 0,
        "air_moisture_hto_bq_ml_water",
    ] = 0.0
    exposure["boundary_assumption"] = "PUBLISHED_VALUE"
    exposure.loc[
        exposure["minutes_from_exposure_start"] == 0,
        "boundary_assumption",
    ] = "ASSUMED_ZERO_AT_EVAPORATION_START"

    temperature_k = exposure["air_temperature_c"].to_numpy(float) + 273.15
    rh_fraction = exposure["relative_humidity_percent"].to_numpy(float) / 100.0
    saturation_density = (
        saturation_vapour_pressure_pa(temperature_k)
        / (WATER_VAPOUR_GAS_CONSTANT_J_KG_K * temperature_k)
        * 1000.0
    )
    actual_density = saturation_density * rh_fraction
    exposure["saturation_vapour_density_g_m3"] = saturation_density
    exposure["actual_vapour_density_g_m3"] = actual_density
    exposure["air_hto_bq_m3_air"] = (
        exposure["air_moisture_hto_bq_ml_water"].to_numpy(float)
        * actual_density
    )
    exposure["conversion_formula_version"] = (
        "SB1_MOISTURE_ACTIVITY_TO_AIR_VOLUME_V1"
    )

    minutes = exposure["minutes_from_exposure_start"].to_numpy(float)
    raw_values = exposure["air_moisture_hto_bq_ml_water"].to_numpy(float)
    raw_mean = float(np.trapezoid(raw_values, minutes) / 60.0)
    relative_difference = (raw_mean - REPORTED_MEAN) / REPORTED_MEAN
    if abs(relative_difference) > 0.05:
        raise ValueError(
            "Raw chamber profile mean differs from the reported mean by more than 5%"
        )
    scale = REPORTED_MEAN / raw_mean
    exposure["raw_air_moisture_hto_bq_ml_water"] = raw_values
    exposure["mean_constrained_air_moisture_hto_bq_ml_water"] = (
        raw_values * scale
    )
    exposure["mean_constrained_air_hto_bq_m3_air"] = (
        exposure["air_hto_bq_m3_air"] * scale
    )

    GENERATED.mkdir(parents=True, exist_ok=True)
    exposure.to_csv(GENERATED / "sb1_chamber_profiles.csv", index=False)
    summary = {
        "chamber_profile": "PUBLISHED_RAW_AND_MEAN_CONSTRAINED",
        "integration_method": "trapezoidal over 09:30-10:30 local",
        "start_boundary_assumption_bq_ml_water": 0.0,
        "raw_profile_mean_bq_ml_water": raw_mean,
        "reported_mean_bq_ml_water": REPORTED_MEAN,
        "mean_constrained_scale_factor": scale,
        "relative_difference": relative_difference,
        "relative_difference_percent": relative_difference * 100.0,
    }
    (GENERATED / "sb1_chamber_profile_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def build_manifest() -> dict[str, Any]:
    if not PDF.is_file():
        raise FileNotFoundError(PDF)
    table_paths = sorted(TABLES.glob("*"))
    table_paths = [path for path in table_paths if path.is_file()]
    raw_checksums = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in sorted((LOCAL / "era5_raw").glob("*/*"))
        if path.is_file()
    }
    request_contract = {
        "dataset": "reanalysis-era5-single-levels-timeseries",
        "download_dates_utc": ["2001-05-20", "2001-10-06"],
        "trimmed_window_utc": [
            "2001-05-20T15:00:00Z",
            "2001-10-06T14:00:00Z",
        ],
        "points": {
            "CENTRE": [36.425000, 127.373611],
            "NORTH_0P25": [36.675000, 127.373611],
            "SOUTH_0P25": [36.175000, 127.373611],
            "EAST_0P25": [36.425000, 127.623611],
            "WEST_0P25": [36.425000, 127.123611],
        },
        "variables": [
            "2m_temperature",
            "2m_dewpoint_temperature",
            "surface_pressure",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
            "total_precipitation",
            "surface_solar_radiation_downwards",
            "surface_thermal_radiation_downwards",
            "total_cloud_cover",
        ],
    }
    request_hash = hashlib.sha256(
        json.dumps(request_contract, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    primary_forcing = GENERATED / "sb1_forcing_primary.csv"
    config = BENCHMARK / "configs" / "sb1_pdf_era5_primary.yaml"
    observations = [
        TABLES / "sb1_tfwt_observations.csv",
        TABLES / "sb1_obt_harvest.csv",
    ]
    return {
        "case_id": "EMRAS_SOYBEAN_SB1_PDF_ERA5_V1",
        "case_version": "1.0.0",
        "evidence_type": "HYBRID_LITERATURE_REANALYSIS",
        "production_gate_eligible": False,
        "trusted_registry_eligible": False,
        "source_document_sha256": sha256(PDF),
        "site_coordinate": {"latitude": 36.425, "longitude": 127.373611},
        "coordinate_status": "PROVISIONAL_INSTITUTIONAL_LOCATION",
        "timezone": "Asia/Seoul",
        "published_table_checksums": {
            path.name: sha256(path) for path in table_paths
        },
        "era5_request_hash": request_hash,
        "era5_raw_file_checksums": raw_checksums,
        "processed_forcing_checksum": (
            sha256(primary_forcing) if primary_forcing.is_file() else None
        ),
        "config_checksum": sha256(config),
        "observation_checksum": combined_hash(observations),
        "generation_commit": git_head(),
    }


def main() -> int:
    validate_rows(
        TABLES / "sb1_chamber_conditions_5min.csv",
        SCHEMAS / "sb1_chamber_conditions.schema.json",
    )
    validate_rows(
        TABLES / "sb1_tfwt_observations.csv",
        SCHEMAS / "sb1_tfwt_observations.schema.json",
    )
    summary = chamber_profiles()
    manifest = build_manifest()
    schema = json.loads(
        (SCHEMAS / "sb1_case_manifest.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(manifest)
    manifest_path = BENCHMARK / "sb1_case_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("SB1 publication dataset: PASS")
    print(
        "RAW_PROFILE_MEAN = "
        f"{summary['raw_profile_mean_bq_ml_water']:.6g} Bq/mL water"
    )
    print(
        "MEAN_CONSTRAINED_SCALE_FACTOR = "
        f"{summary['mean_constrained_scale_factor']:.12g}"
    )
    print(f"CASE_MANIFEST = {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
