#!/usr/bin/env python3
"""Normalize five-point ERA5 files and build unified SB1 forcing scenarios."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
import xarray as xr


ROOT = Path(__file__).resolve().parents[4]
BENCHMARK = ROOT / "validation" / "benchmarks" / "emras_soybean_sb1"
LOCAL = ROOT / "validation" / "external_local" / "emras_soybean_sb1"
RAW = LOCAL / "era5_raw"
PROCESSED = LOCAL / "era5_processed"
GENERATED = LOCAL / "generated_forcing"
REPORTS = BENCHMARK / "reports"
CHAMBER = GENERATED / "sb1_chamber_profiles.csv"

sys.path.insert(0, str(ROOT / "src"))
from cteas_ufotri.meteorology.derived_variables import (  # noqa: E402
    relative_humidity,
    saturation_vapour_pressure_pa,
    wind_speed_direction,
)


POINTS = {
    "CENTRE": (36.425000, 127.373611),
    "NORTH_0P25": (36.675000, 127.373611),
    "SOUTH_0P25": (36.175000, 127.373611),
    "EAST_0P25": (36.425000, 127.623611),
    "WEST_0P25": (36.425000, 127.123611),
}
RAW_NAME = "era5_surface_2001-05-20_2001-10-06.nc"
DOWNLOAD_START_UTC = pd.Timestamp("2001-05-20T15:00:00Z")
DOWNLOAD_END_UTC = pd.Timestamp("2001-10-06T14:00:00Z")
FORCING_END_LOCAL = pd.Timestamp("2001-10-05T23:00:00+09:00")
EXPOSURE_START_LOCAL = pd.Timestamp("2001-07-02T09:30:00+09:00")
EXPOSURE_END_LOCAL = pd.Timestamp("2001-07-02T10:30:00+09:00")
WATER_VAPOUR_GAS_CONSTANT_J_KG_K = 461.5
ILLUMINANCE_TO_W_M2 = 4.75

REQUIRED = {"u10", "v10", "d2m", "t2m", "sp", "ssrd", "strd", "tcc", "tp"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_netcdf(raw_path: Path, output_path: Path) -> None:
    """Extract a CDS NetCDF ZIP response without modifying the raw bytes."""
    if zipfile.is_zipfile(raw_path):
        with zipfile.ZipFile(raw_path) as bundle:
            members = [
                name for name in bundle.namelist()
                if name.lower().endswith((".nc", ".netcdf"))
            ]
            if len(members) != 1:
                raise ValueError(
                    f"Expected one NetCDF member in {raw_path}, found {len(members)}"
                )
            content = bundle.read(members[0])
    else:
        content = raw_path.read_bytes()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.read_bytes() == content:
        return
    output_path.write_bytes(content)


def process_point(point_id: str) -> tuple[pd.DataFrame, dict]:
    raw_path = RAW / point_id / RAW_NAME
    if not raw_path.is_file():
        raise FileNotFoundError(raw_path)
    netcdf_path = PROCESSED / point_id / RAW_NAME
    extract_netcdf(raw_path, netcdf_path)
    with xr.open_dataset(netcdf_path, engine="netcdf4") as dataset:
        missing = sorted(REQUIRED - set(dataset.data_vars))
        if missing:
            raise ValueError(f"{point_id} missing ERA5 variables: {missing}")
        frame = dataset[list(sorted(REQUIRED))].to_dataframe().reset_index()
        source_latitude = float(dataset["latitude"].values)
        source_longitude = float(dataset["longitude"].values)

    frame["time_utc"] = pd.to_datetime(frame["valid_time"], utc=True)
    frame = frame[
        frame["time_utc"].between(DOWNLOAD_START_UTC, DOWNLOAD_END_UTC)
    ].copy()
    frame = frame.sort_values("time_utc").reset_index(drop=True)
    expected = pd.date_range(
        DOWNLOAD_START_UTC, DOWNLOAD_END_UTC, freq="1h", inclusive="both"
    )
    actual = pd.DatetimeIndex(frame["time_utc"])
    duplicates = int(actual.duplicated().sum())
    missing_times = expected.difference(actual)
    extra_times = actual.difference(expected)
    if duplicates or len(missing_times) or len(extra_times):
        raise ValueError(
            f"{point_id} time coverage failed: duplicates={duplicates}, "
            f"missing={len(missing_times)}, extra={len(extra_times)}"
        )

    numeric = frame[list(sorted(REQUIRED))].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError(f"{point_id} contains NaN or Inf")
    temperature_k = frame["t2m"].to_numpy(float)
    dewpoint_k = frame["d2m"].to_numpy(float)
    rh_percent = relative_humidity(temperature_k, dewpoint_k) * 100.0
    speed, direction = wind_speed_direction(
        frame["u10"].to_numpy(float), frame["v10"].to_numpy(float)
    )
    result = pd.DataFrame(
        {
            "time_utc": frame["time_utc"],
            "time_local": frame["time_utc"].dt.tz_convert("Asia/Seoul"),
            "timezone": "Asia/Seoul",
            "utc_offset_hours": 9,
            "air_temperature_c": temperature_k - 273.15,
            "dewpoint_temperature_c": dewpoint_k - 273.15,
            "relative_humidity_percent": rh_percent,
            "surface_pressure_pa": frame["sp"].to_numpy(float),
            "wind_u_10m_m_s": frame["u10"].to_numpy(float),
            "wind_v_10m_m_s": frame["v10"].to_numpy(float),
            "wind_speed_m_s": speed,
            "wind_direction_deg": direction,
            "precipitation_mm_interval": frame["tp"].to_numpy(float) * 1000.0,
            "shortwave_down_w_m2": frame["ssrd"].to_numpy(float) / 3600.0,
            "longwave_down_w_m2": frame["strd"].to_numpy(float) / 3600.0,
            "total_cloud_cover_fraction": frame["tcc"].to_numpy(float),
            "era5_point_id": point_id,
            "accumulation_semantics": "PREVIOUS_1H_INTERVAL_ENDING_AT_VALID_TIME",
        }
    )
    checks = {
        "relative_humidity": result["relative_humidity_percent"].between(0, 100).all(),
        "precipitation": (result["precipitation_mm_interval"] >= 0).all(),
        "shortwave": (result["shortwave_down_w_m2"] >= 0).all(),
        "longwave": (result["longwave_down_w_m2"] >= 0).all(),
        "wind_speed": (result["wind_speed_m_s"] >= 0).all(),
        "cloud_cover": result["total_cloud_cover_fraction"].between(0, 1).all(),
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"{point_id} physical ranges failed: {failed}")

    csv_path = PROCESSED / point_id / "era5_hourly_processed.csv"
    result.to_csv(csv_path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
    summary = {
        "point_id": point_id,
        "requested_latitude": POINTS[point_id][0],
        "requested_longitude": POINTS[point_id][1],
        "source_latitude": source_latitude,
        "source_longitude": source_longitude,
        "raw_path": str(raw_path.relative_to(ROOT)),
        "raw_sha256": sha256(raw_path),
        "extracted_netcdf_sha256": sha256(netcdf_path),
        "processed_csv_sha256": sha256(csv_path),
        "expected_hourly_timestamps": len(expected),
        "actual_hourly_timestamps": len(result),
        "duplicate_timestamp_count": duplicates,
        "missing_timestamp_count": len(missing_times),
        "nan_count": int(result.isna().sum().sum()),
        "inf_count": int(
            np.isinf(result.select_dtypes(include=[np.number]).to_numpy()).sum()
        ),
        "temperature_mean": float(result["air_temperature_c"].mean()),
        "relative_humidity_mean": float(result["relative_humidity_percent"].mean()),
        "precipitation_total": float(result["precipitation_mm_interval"].sum()),
        "shortwave_total": float(
            (result["shortwave_down_w_m2"] * 3600.0).sum() / 1.0e6
        ),
        "wind_speed_mean": float(result["wind_speed_m_s"].mean()),
        "summary_units": {
            "temperature_mean": "degC",
            "relative_humidity_mean": "percent",
            "precipitation_total": "mm",
            "shortwave_total": "MJ m-2",
            "wind_speed_mean": "m s-1",
        },
    }
    (PROCESSED / point_id / "era5_qa_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return result, summary


def expand_to_five_minutes(hourly: pd.DataFrame) -> pd.DataFrame:
    start = DOWNLOAD_START_UTC
    end = FORCING_END_LOCAL.tz_convert("UTC")
    five_time = pd.date_range(start, end, freq="5min", inclusive="both")
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
    union = source.index.union(five_time)
    state = source[state_columns].reindex(union).interpolate(
        method="time", limit_direction="both"
    ).reindex(five_time)
    interval_columns = [
        "precipitation_mm_interval",
        "shortwave_down_w_m2",
    ]
    interval = source[interval_columns].reindex(union).bfill().reindex(five_time)
    interval["precipitation_mm_interval"] /= 12.0
    result = state.join(interval)
    result.index.name = "time_utc"
    return result.reset_index()


def saturation_and_actual_density(
    temperature_c: np.ndarray, relative_humidity_percent: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    temperature_k = np.asarray(temperature_c, dtype=float) + 273.15
    saturation = (
        saturation_vapour_pressure_pa(temperature_k)
        / (WATER_VAPOUR_GAS_CONSTANT_J_KG_K * temperature_k)
        * 1000.0
    )
    actual = saturation * np.asarray(relative_humidity_percent, dtype=float) / 100.0
    return saturation, actual


def dewpoint_from_temperature_rh(
    temperature_c: np.ndarray, relative_humidity_percent: np.ndarray
) -> np.ndarray:
    """Invert the project's Magnus saturation relation without changing constants."""
    temperature_c = np.asarray(temperature_c, dtype=float)
    rh = np.asarray(relative_humidity_percent, dtype=float) / 100.0
    gamma = (
        np.log(np.clip(rh, np.finfo(float).tiny, 1.0))
        + 17.2694 * temperature_c / (temperature_c + 237.29)
    )
    return 237.29 * gamma / (17.2694 - gamma)


def background_air_hto(local_time: pd.Series, mode: str) -> np.ndarray:
    ranges = {
        7: (0.016, 0.069),
        8: (0.013, 0.049),
        9: (0.040, 0.060),
        10: (0.040, 0.060),
    }
    if mode == "EXCESS_ABOVE_BACKGROUND":
        return np.zeros(len(local_time), dtype=float)
    selector = {
        "BACKGROUND_LOW": 0,
        "BACKGROUND_MID": 2,
        "BACKGROUND_HIGH": 1,
    }[mode]
    values = []
    for timestamp in local_time:
        if timestamp.month not in ranges:
            values.append(0.0)
            continue
        low, high = ranges[timestamp.month]
        values.append((low + high) / 2.0 if selector == 2 else (low, high)[selector])
    return np.asarray(values, dtype=float)


def forcing_scenario(
    hourly: pd.DataFrame,
    point_id: str,
    chamber_profile: str,
    hto_mode: str,
    scenario_id: str,
) -> pd.DataFrame:
    forcing = expand_to_five_minutes(hourly)
    forcing["time_local"] = forcing["time_utc"].dt.tz_convert("Asia/Seoul")
    forcing["timezone"] = "Asia/Seoul"
    forcing["utc_offset_hours"] = 9
    forcing["phase"] = np.select(
        [
            forcing["time_local"] < EXPOSURE_START_LOCAL,
            forcing["time_local"] <= EXPOSURE_END_LOCAL,
        ],
        ["PRE_EXPOSURE_OUTDOOR", "CHAMBER_EXPOSURE"],
        default="POST_EXPOSURE_OUTDOOR",
    )
    forcing["hours_after_exposure"] = (
        forcing["time_utc"] - EXPOSURE_END_LOCAL.tz_convert("UTC")
    ).dt.total_seconds() / 3600.0

    chamber = pd.read_csv(CHAMBER)
    chamber["time_local"] = pd.to_datetime(chamber["time_local"], utc=True).dt.tz_convert(
        "Asia/Seoul"
    )
    chamber = chamber.set_index("time_local")
    chamber_rows = forcing["phase"] == "CHAMBER_EXPOSURE"
    chamber_times = forcing.loc[chamber_rows, "time_local"]
    selected = chamber.loc[chamber_times]
    forcing.loc[chamber_rows, "air_temperature_c"] = (
        selected["air_temperature_c"].to_numpy()
    )
    forcing.loc[chamber_rows, "relative_humidity_percent"] = (
        selected["relative_humidity_percent"].to_numpy()
    )
    forcing.loc[chamber_rows, "dewpoint_temperature_c"] = (
        dewpoint_from_temperature_rh(
            selected["air_temperature_c"].to_numpy(),
            selected["relative_humidity_percent"].to_numpy(),
        )
    )
    forcing.loc[chamber_rows, "wind_u_10m_m_s"] = 0.0
    forcing.loc[chamber_rows, "wind_v_10m_m_s"] = 0.0
    forcing.loc[chamber_rows, "wind_speed_m_s"] = 0.0
    forcing.loc[chamber_rows, "wind_direction_deg"] = 0.0
    forcing.loc[chamber_rows, "precipitation_mm_interval"] = 0.0
    forcing.loc[chamber_rows, "shortwave_down_w_m2"] = (
        selected["illuminance_klux"].to_numpy() * ILLUMINANCE_TO_W_M2
    )

    saturation, actual = saturation_and_actual_density(
        forcing["air_temperature_c"].to_numpy(),
        forcing["relative_humidity_percent"].to_numpy(),
    )
    forcing["saturation_vapour_density_g_m3"] = saturation
    forcing["actual_vapour_density_g_m3"] = actual
    air = background_air_hto(forcing["time_local"], hto_mode)
    post_exposure = forcing["phase"] == "POST_EXPOSURE_OUTDOOR"
    air[~post_exposure.to_numpy()] = 0.0
    moisture = np.divide(
        air,
        actual,
        out=np.zeros_like(air),
        where=actual > 0,
    )
    chamber_value_column = (
        "raw_air_moisture_hto_bq_ml_water"
        if chamber_profile == "PUBLISHED_RAW_PROFILE"
        else "mean_constrained_air_moisture_hto_bq_ml_water"
    )
    chamber_moisture = selected[chamber_value_column].to_numpy(float)
    chamber_actual = forcing.loc[
        chamber_rows, "actual_vapour_density_g_m3"
    ].to_numpy(float)
    air[chamber_rows.to_numpy()] = chamber_moisture * chamber_actual
    moisture[chamber_rows.to_numpy()] = chamber_moisture
    forcing["air_hto_bq_m3"] = air
    forcing["air_moisture_hto_bq_ml_water"] = moisture
    forcing["illuminance_klux"] = np.nan
    forcing.loc[chamber_rows, "illuminance_klux"] = (
        selected["illuminance_klux"].to_numpy()
    )
    forcing["forcing_source"] = np.where(
        chamber_rows,
        "IAEA_TABLE_I_4_6",
        "ERA5_REANALYSIS_PLUS_DECLARED_HTO_BOUNDARY",
    )
    forcing["forcing_quality"] = np.where(
        chamber_rows,
        "PUBLISHED_T_RH_ILLUMINANCE_HTO; WIND_UNREPORTED_FORMAL_MINIMUM_CLAMP",
        "ERA5_REANALYSIS_SUBSTITUTION; HTO_BOUNDARY_NOT_HOURLY_OBSERVATION",
    )
    forcing["background_source"] = (
        "IAEA Appendix I.4.3.3 monthly range" if "BACKGROUND" in hto_mode
        else "increment-above-background definition"
    )
    forcing["background_assumption"] = hto_mode
    forcing["background_month"] = forcing["time_local"].dt.month
    background = background_air_hto(forcing["time_local"], hto_mode)
    background[~post_exposure.to_numpy()] = 0.0
    forcing["background_air_hto_bq_m3"] = background
    forcing["era5_point_id"] = point_id
    forcing["chamber_profile"] = chamber_profile
    forcing["scenario_id"] = scenario_id
    forcing["conversion_formula_version"] = (
        "SB1_MOISTURE_ACTIVITY_TO_AIR_VOLUME_V1"
    )
    forcing["precipitation_m_s"] = (
        forcing["precipitation_mm_interval"] / 1000.0 / 300.0
    )

    numeric = forcing.select_dtypes(include=[np.number]).drop(
        columns=["illuminance_klux"]
    )
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError(f"{scenario_id} forcing contains NaN or Inf")
    if (forcing["air_hto_bq_m3"] < 0).any():
        raise ValueError(f"{scenario_id} forcing contains negative HTO")
    return forcing


def main() -> int:
    frames: dict[str, pd.DataFrame] = {}
    summaries: list[dict] = []
    for point_id in POINTS:
        frame, summary = process_point(point_id)
        frames[point_id] = frame
        summaries.append(summary)

    spatial_columns = [
        "point_id",
        "requested_latitude",
        "requested_longitude",
        "source_latitude",
        "source_longitude",
        "temperature_mean",
        "relative_humidity_mean",
        "precipitation_total",
        "shortwave_total",
        "wind_speed_mean",
        "expected_hourly_timestamps",
        "actual_hourly_timestamps",
        "duplicate_timestamp_count",
        "missing_timestamp_count",
        "nan_count",
        "inf_count",
    ]
    spatial = pd.DataFrame(summaries)[spatial_columns]
    low_point = spatial.loc[spatial["shortwave_total"].idxmin(), "point_id"]
    high_point = spatial.loc[spatial["shortwave_total"].idxmax(), "point_id"]
    spatial["meteorology_envelope_role"] = "SPATIAL_CHECK"
    spatial.loc[spatial["point_id"] == "CENTRE", "meteorology_envelope_role"] = "CENTRE"
    spatial.loc[spatial["point_id"] == low_point, "meteorology_envelope_role"] += (
        ";MET_LOW_BY_SHORTWAVE_TOTAL"
    )
    spatial.loc[spatial["point_id"] == high_point, "meteorology_envelope_role"] += (
        ";MET_HIGH_BY_SHORTWAVE_TOTAL"
    )
    REPORTS.mkdir(parents=True, exist_ok=True)
    spatial.to_csv(REPORTS / "era5_spatial_sensitivity.csv", index=False)

    scenarios = [
        ("RUN_01", "CENTRE", "PUBLISHED_RAW_PROFILE", "EXCESS_ABOVE_BACKGROUND"),
        ("RUN_02", "CENTRE", "MEAN_CONSTRAINED_PROFILE", "EXCESS_ABOVE_BACKGROUND"),
        ("RUN_03", low_point, "PUBLISHED_RAW_PROFILE", "EXCESS_ABOVE_BACKGROUND"),
        ("RUN_04", high_point, "PUBLISHED_RAW_PROFILE", "EXCESS_ABOVE_BACKGROUND"),
        ("RUN_05", "CENTRE", "PUBLISHED_RAW_PROFILE", "BACKGROUND_LOW"),
        ("RUN_06", "CENTRE", "PUBLISHED_RAW_PROFILE", "BACKGROUND_MID"),
        ("RUN_07", "CENTRE", "PUBLISHED_RAW_PROFILE", "BACKGROUND_HIGH"),
    ]
    GENERATED.mkdir(parents=True, exist_ok=True)
    forcing_manifest = {}
    for run_id, point_id, profile, hto_mode in scenarios:
        forcing = forcing_scenario(
            frames[point_id], point_id, profile, hto_mode, run_id
        )
        filename = (
            "sb1_forcing_primary.csv"
            if run_id == "RUN_01"
            else f"sb1_forcing_{run_id.lower()}.csv"
        )
        path = GENERATED / filename
        forcing.to_csv(path, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
        forcing_manifest[run_id] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "era5_point_id": point_id,
            "chamber_profile": profile,
            "post_exposure_hto_mode": hto_mode,
            "rows": len(forcing),
        }
    (GENERATED / "sb1_forcing_manifest.json").write_text(
        json.dumps(
            {
                "five_point_spatial_sensitivity": True,
                "met_low_definition": "minimum seasonal shortwave total",
                "met_low_point": low_point,
                "met_high_definition": "maximum seasonal shortwave total",
                "met_high_point": high_point,
                "scenarios": forcing_manifest,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"EXPECTED_HOURLY_TIMESTAMPS = {summaries[0]['expected_hourly_timestamps']}")
    print(f"ACTUAL_HOURLY_TIMESTAMPS = {summaries[0]['actual_hourly_timestamps']}")
    print("DUPLICATE_TIMESTAMP_COUNT = 0")
    print("MISSING_TIMESTAMP_COUNT = 0")
    print("NAN_COUNT = 0")
    print("INF_COUNT = 0")
    print("FIVE_POINT_ERA5_SPATIAL_SENSITIVITY = PASS")
    print(f"MET_LOW = {low_point}")
    print(f"MET_HIGH = {high_point}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"SB1 ERA5 preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
