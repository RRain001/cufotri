import pandas as pd
import xarray as xr

from cteas_ufotri.config import load_yaml
from cteas_ufotri.meteorology.era5_reader import (
    deaccumulate_with_resets,
    prepare_hourly_forcing,
    read_era5,
)


def test_csv_mapping_and_utc_order():
    mapping = load_yaml("configs/era5_mapping.yaml")
    frame = read_era5("tests/data/era5_minimal.csv", mapping)
    assert list(frame["temperature_k"]) == [293.15, 294.15]
    assert list(frame["wind_u_10m_m_s"]) == [3.0, 0.0]
    assert str(frame["time"].dt.tz) == "UTC"
    forcing = prepare_hourly_forcing(frame, 0.77, 50.0)
    assert forcing["wind_m_s"].iloc[0] == 5.0
    assert forcing["precipitation_m_s"].iloc[1] > 0
    assert "provisional" in forcing["radiation_method"].iloc[0]


def test_netcdf_mapping(tmp_path):
    path = tmp_path / "era5.nc"
    xr.Dataset(
        {"t2m": ("valid_time", [293.15, 294.15])},
        coords={"valid_time": pd.date_range("2025-06-01", periods=2, freq="h")},
    ).to_netcdf(path)
    frame = read_era5(path, load_yaml("configs/era5_mapping.yaml"))
    assert list(frame["temperature_k"]) == [293.15, 294.15]
    assert str(frame["time"].dt.tz) == "UTC"


def test_deaccumulation_detects_resets():
    values = deaccumulate_with_resets([1.0, 3.0, 6.0, 0.5, 2.0])
    assert list(values) == [1.0, 2.0, 3.0, 0.5, 1.5]


def test_cumulative_forcing_is_converted_to_interval_rates():
    mapping = load_yaml("configs/era5_mapping.yaml")
    frame = read_era5("tests/data/era5_minimal.csv", mapping)
    frame["solar_down_j_m2"] = [360000.0, 720000.0]
    frame["precipitation_m"] = [0.001, 0.003]
    forcing = prepare_hourly_forcing(
        frame, 1.0, 0.0, accumulation_semantics="cumulative_with_resets"
    )
    assert list(forcing["precipitation_m_s"]) == [
        0.001 / 3600.0,
        0.002 / 3600.0,
    ]
    assert list(forcing["net_radiation_w_m2"]) == [100.0, 100.0]
