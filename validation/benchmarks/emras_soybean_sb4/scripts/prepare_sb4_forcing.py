#!/usr/bin/env python3
"""Reuse SB1 ERA5 raw files and build two reconstructed SB4 forcing families."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import jsonschema
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb4"
SB1_BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
SB1_LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb4"
PROCESSED = LOCAL / "era5_processed"
GENERATED = LOCAL / "generated_forcing"
SB1_CHAMBER = (
    SB1_BENCHMARK / "published_tables" / "sb1_chamber_conditions_5min.csv"
)
EXPOSURE_START = pd.Timestamp("2001-08-09T09:30:00+09:00")
EXPOSURE_END = pd.Timestamp("2001-08-09T10:30:00+09:00")
FORCING_START = pd.Timestamp("2001-08-09T09:25:00+09:00")
FORCING_END = pd.Timestamp("2001-10-05T23:00:00+09:00")
REPORTED_MEAN = 52700.0
PROFILE_IDS = ("CONSTANT_REPORTED_MEAN", "SCALED_SB1_OBSERVED_SHAPE")
POINTS = (
    "CENTRE",
    "NORTH_0P25",
    "SOUTH_0P25",
    "EAST_0P25",
    "WEST_0P25",
)
SCENARIOS = (
    ("RUN_01", "CENTRE", "EXCESS_ABOVE_BACKGROUND", "ERA5_CHAMBER_MET"),
    (
        "RUN_02",
        "CENTRE",
        "EXCESS_ABOVE_BACKGROUND",
        "SB1_CHAMBER_MET_SHAPE_SENSITIVITY",
    ),
    ("RUN_03", "NORTH_0P25", "EXCESS_ABOVE_BACKGROUND", "ERA5_CHAMBER_MET"),
    ("RUN_04", "SOUTH_0P25", "EXCESS_ABOVE_BACKGROUND", "ERA5_CHAMBER_MET"),
    ("RUN_05", "CENTRE", "BACKGROUND_LOW", "ERA5_CHAMBER_MET"),
    ("RUN_06", "CENTRE", "BACKGROUND_MID", "ERA5_CHAMBER_MET"),
    ("RUN_07", "CENTRE", "BACKGROUND_HIGH", "ERA5_CHAMBER_MET"),
)


def load_sb1_preparer() -> Any:
    path = SB1_BENCHMARK / "scripts" / "prepare_sb1_era5.py"
    spec = importlib.util.spec_from_file_location("sb1_prepare_for_sb4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.RAW = SB1_LOCAL / "era5_raw"
    module.PROCESSED = PROCESSED
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_profile_configs() -> None:
    schema = json.loads(
        (
            BENCHMARK / "schemas" / "sb4_forcing_contract.schema.json"
        ).read_text(encoding="utf-8")
    )
    for path in sorted((BENCHMARK / "configs").glob("*.yaml")):
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)


def build_chamber_profiles() -> tuple[pd.DataFrame, dict[str, Any]]:
    minutes = np.arange(0, 61, 5, dtype=float)
    constant = np.full(len(minutes), REPORTED_MEAN, dtype=float)
    source = pd.read_csv(SB1_CHAMBER)
    source = source[
        source["minutes_from_exposure_start"].between(0, 60)
    ].copy()
    source = source.sort_values("minutes_from_exposure_start")
    if source["minutes_from_exposure_start"].tolist() != list(range(0, 61, 5)):
        raise ValueError("SB1 source profile does not contain 13 five-minute points")
    raw = source["air_moisture_hto_bq_ml_water"].to_numpy(
        dtype=float, copy=True
    )
    if not np.isnan(raw[0]):
        raise ValueError("SB1 09:30 source boundary must remain unreported")
    raw[0] = 0.0
    raw_mean = float(np.trapezoid(raw, minutes) / 60.0)
    scale = REPORTED_MEAN / raw_mean
    scaled = raw * scale
    profiles = []
    for profile_id, values, boundary in (
        (
            "CONSTANT_REPORTED_MEAN",
            constant,
            "CONSTANT_EQUALS_REPORTED_MEAN_AT_09_30",
        ),
        (
            "SCALED_SB1_OBSERVED_SHAPE",
            scaled,
            "SB1_09_30_UNREPORTED_ASSUMED_ZERO_BEFORE_SCALING",
        ),
    ):
        for minute, value in zip(minutes, values, strict=True):
            profiles.append(
                {
                    "profile_id": profile_id,
                    "minutes_from_exposure_start": int(minute),
                    "time_local": EXPOSURE_START
                    + pd.Timedelta(minutes=float(minute)),
                    "air_moisture_hto_bq_ml_water": float(value),
                    "profile_evidence_class": "RECONSTRUCTED",
                    "sb4_observed_curve_claim": False,
                    "mean_constraint_bq_ml_water": REPORTED_MEAN,
                    "boundary_assumption": boundary,
                }
            )
    frame = pd.DataFrame(profiles)
    summaries: dict[str, Any] = {}
    for profile_id, group in frame.groupby("profile_id"):
        mean = float(
            np.trapezoid(
                group["air_moisture_hto_bq_ml_water"],
                group["minutes_from_exposure_start"],
            )
            / 60.0
        )
        if not math_isclose(mean, REPORTED_MEAN, absolute=1.0e-9):
            raise ValueError(f"{profile_id} mean is {mean}, expected {REPORTED_MEAN}")
        summaries[profile_id] = {
            "trapezoid_mean_bq_ml_water": mean,
            "profile_evidence_class": "RECONSTRUCTED",
            "sb4_observed_curve_claim": False,
        }
    summaries["SCALED_SB1_OBSERVED_SHAPE"].update(
        {
            "sb1_raw_profile_mean_bq_ml_water": raw_mean,
            "scale_factor": scale,
            "source": "SB1_TABLE_I_4_6_SHAPE",
        }
    )
    GENERATED.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        GENERATED / "sb4_chamber_profiles.csv",
        index=False,
        date_format="%Y-%m-%dT%H:%M:%S%z",
    )
    (GENERATED / "sb4_chamber_profile_summary.json").write_text(
        json.dumps(summaries, indent=2) + "\n", encoding="utf-8"
    )
    return frame, summaries


def math_isclose(value: float, expected: float, absolute: float) -> bool:
    return abs(value - expected) <= absolute


def expand_to_five_minutes(hourly: pd.DataFrame) -> pd.DataFrame:
    start_utc = FORCING_START.tz_convert("UTC")
    end_utc = FORCING_END.tz_convert("UTC")
    target = pd.date_range(start_utc, end_utc, freq="5min", inclusive="both")
    source = hourly.copy().set_index("time_utc")
    state_columns = [
        "air_temperature_c",
        "dewpoint_temperature_c",
        "relative_humidity_percent",
        "surface_pressure_pa",
        "wind_u_10m_m_s",
        "wind_v_10m_m_s",
        "wind_speed_m_s",
        "wind_direction_deg",
        "longwave_down_w_m2",
        "total_cloud_cover_fraction",
    ]
    union = source.index.union(target)
    state = (
        source[state_columns]
        .reindex(union)
        .interpolate(method="time", limit_direction="both")
        .reindex(target)
    )
    interval = (
        source[["precipitation_mm_interval", "shortwave_down_w_m2"]]
        .reindex(union)
        .bfill()
        .reindex(target)
    )
    interval["precipitation_mm_interval"] /= 12.0
    result = state.join(interval)
    result.index.name = "time_utc"
    return result.reset_index()


def forcing_scenario(
    sb1_preparer: Any,
    hourly: pd.DataFrame,
    profile: pd.DataFrame,
    profile_id: str,
    run_id: str,
    point_id: str,
    hto_mode: str,
    chamber_met_mode: str,
) -> pd.DataFrame:
    forcing = expand_to_five_minutes(hourly)
    forcing["time_local"] = forcing["time_utc"].dt.tz_convert("Asia/Seoul")
    forcing["timezone"] = "Asia/Seoul"
    forcing["utc_offset_hours"] = 9
    forcing["phase"] = np.select(
        [
            forcing["time_local"] < EXPOSURE_START,
            forcing["time_local"] <= EXPOSURE_END,
        ],
        ["PRE_EXPOSURE_OUTDOOR", "CHAMBER_EXPOSURE"],
        default="POST_EXPOSURE_OUTDOOR",
    )
    forcing["hours_after_exposure"] = (
        forcing["time_utc"] - EXPOSURE_END.tz_convert("UTC")
    ).dt.total_seconds() / 3600.0
    chamber_rows = forcing["phase"] == "CHAMBER_EXPOSURE"
    chamber = profile.set_index("minutes_from_exposure_start")
    minutes = (
        forcing.loc[chamber_rows, "time_local"] - EXPOSURE_START
    ).dt.total_seconds() / 60.0
    selected = chamber.loc[minutes.astype(int)]

    if chamber_met_mode == "SB1_CHAMBER_MET_SHAPE_SENSITIVITY":
        sb1_chamber = pd.read_csv(SB1_CHAMBER)
        sb1_chamber = sb1_chamber[
            sb1_chamber["minutes_from_exposure_start"].between(0, 60)
        ].set_index("minutes_from_exposure_start")
        met = sb1_chamber.loc[minutes.astype(int)]
        forcing.loc[chamber_rows, "air_temperature_c"] = met[
            "air_temperature_c"
        ].to_numpy(float)
        forcing.loc[chamber_rows, "relative_humidity_percent"] = met[
            "relative_humidity_percent"
        ].to_numpy(float)
        forcing.loc[chamber_rows, "dewpoint_temperature_c"] = (
            sb1_preparer.dewpoint_from_temperature_rh(
                met["air_temperature_c"].to_numpy(float),
                met["relative_humidity_percent"].to_numpy(float),
            )
        )
        forcing.loc[chamber_rows, "shortwave_down_w_m2"] = (
            met["illuminance_klux"].to_numpy(float)
            * sb1_preparer.ILLUMINANCE_TO_W_M2
        )

    saturation, actual = sb1_preparer.saturation_and_actual_density(
        forcing["air_temperature_c"].to_numpy(float),
        forcing["relative_humidity_percent"].to_numpy(float),
    )
    forcing["saturation_vapour_density_g_m3"] = saturation
    forcing["actual_vapour_density_g_m3"] = actual
    background = sb1_preparer.background_air_hto(
        forcing["time_local"], hto_mode
    )
    post = forcing["phase"] == "POST_EXPOSURE_OUTDOOR"
    air = np.zeros(len(forcing), dtype=float)
    air[post.to_numpy()] = background[post.to_numpy()]
    moisture = np.divide(
        air, actual, out=np.zeros_like(air), where=actual > 0
    )
    chamber_moisture = selected[
        "air_moisture_hto_bq_ml_water"
    ].to_numpy(float)
    air[chamber_rows.to_numpy()] = (
        chamber_moisture * actual[chamber_rows.to_numpy()]
    )
    moisture[chamber_rows.to_numpy()] = chamber_moisture
    forcing["air_hto_bq_m3"] = air
    forcing["air_moisture_hto_bq_ml_water"] = moisture
    forcing["background_air_hto_bq_m3"] = np.where(
        post, background, 0.0
    )
    forcing["background_assumption"] = hto_mode
    forcing["era5_point_id"] = point_id
    forcing["chamber_profile"] = profile_id
    forcing["chamber_profile_evidence_class"] = "RECONSTRUCTED"
    forcing["sb4_observed_chamber_curve_claim"] = False
    forcing["chamber_meteorology_mode"] = chamber_met_mode
    forcing["forcing_source"] = np.where(
        chamber_rows,
        "RECONSTRUCTED_SB4_REPORTED_MEAN_CONSTRAINT",
        "ERA5_REANALYSIS_PLUS_DECLARED_HTO_BOUNDARY",
    )
    forcing["scenario_id"] = run_id
    forcing["precipitation_m_s"] = (
        forcing["precipitation_mm_interval"] / 1000.0 / 300.0
    )
    numeric = forcing.select_dtypes(include=[np.number])
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{profile_id} {run_id} contains NaN or Inf")
    if (numeric.to_numpy() < 0).any():
        negative_allowed = {
            "air_temperature_c",
            "dewpoint_temperature_c",
            "wind_u_10m_m_s",
            "wind_v_10m_m_s",
            "hours_after_exposure",
        }
        nonnegative = numeric.drop(
            columns=[
                name
                for name in negative_allowed
                if name in numeric.columns
            ]
        )
        if (nonnegative.to_numpy() < 0).any():
            raise ValueError(f"{profile_id} {run_id} has negative forcing")
    return forcing


def main() -> int:
    validate_profile_configs()
    sb1_preparer = load_sb1_preparer()
    frames: dict[str, pd.DataFrame] = {}
    raw_checksums: dict[str, str] = {}
    for point_id in POINTS:
        frame, summary = sb1_preparer.process_point(point_id)
        frames[point_id] = frame
        raw_checksums[point_id] = summary["raw_sha256"]
    profiles, profile_summary = build_chamber_profiles()
    manifest: dict[str, Any] = {
        "case_id": "EMRAS_SOYBEAN_SB4_PDF_ERA5_V1",
        "profile_count": 2,
        "forcing_scenarios_per_profile": 7,
        "total_forcing_files": 14,
        "era5_raw_reuse_case": "EMRAS_SOYBEAN_SB1_PDF_ERA5_V1",
        "era5_raw_checksums": raw_checksums,
        "profiles": profile_summary,
        "scenarios": {},
        "empirical_validation_claim": False,
        "production_gate_eligible": False,
    }
    for profile_id in PROFILE_IDS:
        profile = profiles[profiles["profile_id"] == profile_id]
        for run_id, point_id, hto_mode, chamber_met_mode in SCENARIOS:
            forcing = forcing_scenario(
                sb1_preparer,
                frames[point_id],
                profile,
                profile_id,
                run_id,
                point_id,
                hto_mode,
                chamber_met_mode,
            )
            profile_slug = profile_id.lower()
            path = GENERATED / f"sb4_{profile_slug}_{run_id.lower()}.csv"
            forcing.to_csv(
                path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z"
            )
            key = f"{profile_id}:{run_id}"
            manifest["scenarios"][key] = {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "rows": len(forcing),
                "era5_point_id": point_id,
                "post_exposure_hto_mode": hto_mode,
                "chamber_meteorology_mode": chamber_met_mode,
                "chamber_profile_evidence_class": "RECONSTRUCTED",
            }
    (GENERATED / "sb4_forcing_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("SB4_ERA5_RAW_REUSE_STATUS = PASS_5_CHECKSUMMED_FILES")
    print("SB4_CHAMBER_PROFILE_STATUS = PASS_2_RECONSTRUCTED")
    print("SB4_FORCING_FILE_COUNT = 14")
    print("SB4_FORCING_TIME_START = 2001-08-09T09:25:00+09:00")
    print("SB4_FORCING_TIME_END = 2001-10-05T23:00:00+09:00")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"SB4 forcing preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
