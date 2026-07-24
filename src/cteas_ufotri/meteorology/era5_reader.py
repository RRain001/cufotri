from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import xarray as xr

from .derived_variables import accumulated_to_flux, wind_speed_direction


def _rename_first(frame: pd.DataFrame, target: str, candidates: list[str]) -> None:
    for name in candidates:
        if name in frame.columns:
            frame.rename(columns={name: target}, inplace=True)
            return


def read_era5(path: str | Path, mapping: dict[str, Any]) -> pd.DataFrame:
    """Read an ERA5 CSV/NetCDF without modifying the source file."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() == ".csv":
        frame = pd.read_csv(source)
    elif source.suffix.lower() in {".nc", ".netcdf"}:
        with xr.open_dataset(source) as dataset:
            frame = dataset.to_dataframe().reset_index()
    else:
        raise ValueError(f"Unsupported ERA5 format: {source.suffix}")
    for target, candidates in mapping["variables"].items():
        _rename_first(frame, target, candidates)
    time_name = mapping.get("time", "valid_time")
    if time_name not in frame and "time" in frame:
        time_name = "time"
    if time_name not in frame:
        raise ValueError("ERA5 input has no mapped time column")
    frame["time"] = pd.to_datetime(frame[time_name], utc=True)
    return frame.sort_values("time").reset_index(drop=True)


def prepare_hourly_forcing(
    frame: pd.DataFrame,
    shortwave_absorptivity: float,
    fallback_net_longwave_loss_w_m2: float,
    accumulation_seconds: float = 3600.0,
    accumulation_semantics: str = "interval",
) -> pd.DataFrame:
    """Convert mapped ERA5 hourly fields to the coupling forcing contract.

    If true net solar and net thermal components are both present, their ERA5
    downward-positive accumulated values are used. Otherwise an explicit
    shortwave-absorption/fixed-net-longwave fallback is used; downward thermal
    radiation alone is never mislabelled as net radiation.
    """
    required = {
        "time", "temperature_k", "dewpoint_k", "wind_u_10m_m_s",
        "wind_v_10m_m_s", "precipitation_m", "solar_down_j_m2",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Mapped ERA5 forcing lacks: {', '.join(missing)}")
    if len(frame) == 0:
        raise ValueError("ERA5 forcing is empty")
    speed, direction = wind_speed_direction(
        frame["wind_u_10m_m_s"], frame["wind_v_10m_m_s"]
    )
    interval_seconds = _interval_seconds(frame["time"], accumulation_seconds)

    def interval_amount(name: str):
        values = frame[name].astype(float).to_numpy()
        if accumulation_semantics == "interval":
            return values
        if accumulation_semantics == "cumulative_with_resets":
            return deaccumulate_with_resets(values)
        raise ValueError(f"Unsupported accumulation semantics: {accumulation_semantics}")

    if {"net_solar_j_m2", "net_thermal_j_m2"} <= set(frame.columns):
        radiation = (
            interval_amount("net_solar_j_m2")
            + interval_amount("net_thermal_j_m2")
        ) / interval_seconds
        radiation_method = "ERA5 net solar + net thermal (downward positive)"
    else:
        radiation = (
            shortwave_absorptivity
            * interval_amount("solar_down_j_m2") / interval_seconds
            - fallback_net_longwave_loss_w_m2
        )
        radiation_method = "provisional absorbed shortwave minus fixed net longwave loss"
    result = pd.DataFrame({
        "time": frame["time"],
        "temperature_k": frame["temperature_k"].astype(float),
        "dewpoint_k": frame["dewpoint_k"].astype(float),
        "wind_m_s": speed,
        "wind_from_deg": direction,
        "net_radiation_w_m2": radiation,
        "precipitation_m_s": interval_amount("precipitation_m") / interval_seconds,
        "radiation_method": radiation_method,
    })
    for optional in ("boundary_layer_height_m", "total_cloud_cover_fraction"):
        if optional in frame:
            result[optional] = frame[optional].astype(float)
    return result


def deaccumulate_with_resets(values) -> Any:
    """Convert a cumulative series to interval amounts.

    Negative increments are treated as forecast/day resets, for which the
    current cumulative value is the new interval amount.
    """
    import numpy as np

    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError("Accumulated values must be one-dimensional")
    if len(array) == 0:
        return array
    if np.any(array < 0):
        raise ValueError("Accumulated values cannot be negative")
    result = np.empty_like(array)
    result[0] = array[0]
    differences = np.diff(array)
    result[1:] = np.where(differences >= 0.0, differences, array[1:])
    return result


def _interval_seconds(time: pd.Series, default_seconds: float):
    import numpy as np

    if default_seconds <= 0:
        raise ValueError("Default accumulation interval must be positive")
    timestamps = pd.to_datetime(time, utc=True)
    if len(timestamps) == 1:
        return np.array([default_seconds], dtype=float)
    differences = timestamps.diff().dt.total_seconds().to_numpy(copy=True)
    if np.any(differences[1:] <= 0):
        raise ValueError("ERA5 time must be strictly increasing")
    differences[0] = differences[1]
    return differences.astype(float)
