import numpy as np
import pandas as pd
import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


def test_short_case_is_finite_nonzero_and_balanced():
    config = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    config["duration_hours"] = 2
    frame = run_short_case(config)
    assert len(frame) == 12
    assert np.isfinite(frame.select_dtypes("number")).all().all()
    assert frame["air_hto_concentration"].max() > 0
    assert frame["soil_hto_inventory"].iloc[-1] > 0
    assert frame["mass_balance_relative_error"].max() < 1e-10


def test_three_hour_root_lag_delays_tfwt_uptake():
    immediate = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    immediate["duration_hours"] = 2
    delayed = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    delayed["duration_hours"] = 2
    delayed["soil"]["root_uptake_delay_seconds"] = 10800
    immediate_result = run_short_case(immediate)
    delayed_result = run_short_case(delayed)
    assert immediate_result["plant_tfwt_inventory"].iloc[-1] > 0
    assert delayed_result["plant_tfwt_inventory"].iloc[-1] == 0


def test_required_output_schema_is_complete():
    config = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    config["duration_hours"] = 1
    frame = run_short_case(config)
    required = {
        "air_hto_concentration",
        "soil_water_storage",
        "soil_hto_inventory",
        "soil_hto_concentration",
        "soil_evaporation",
        "plant_transpiration",
        "root_water_uptake",
        "deep_drainage",
        "plant_tfwt_inventory",
        "plant_tfwt_concentration",
        "plant_obt_inventory",
        "soil_reemission_flux",
        "plant_reemission_flux",
        "total_reemission_flux",
        "mass_balance_error",
    }
    assert required <= set(frame.columns)


def test_local_cartesian_receptor_matches_fixed_downwind_for_westerly_wind():
    fixed = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    fixed["duration_hours"] = 1
    local = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    local["duration_hours"] = 1
    local["site"]["receptor_mode"] = "local_cartesian"
    local["site"]["receptor_east_m"] = 1000.0
    local["site"]["receptor_north_m"] = 0.0
    a = run_short_case(fixed)
    b = run_short_case(local)
    assert np.allclose(a["air_hto_concentration"], b["air_hto_concentration"])


def test_dynamic_stability_and_boundary_layer_forcing_runs():
    config = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    config["duration_hours"] = 2
    config["atmosphere"]["stability_mode"] = "turner_simple"
    forcing = pd.DataFrame({
        "temperature_k": [293.15, 294.15],
        "dewpoint_k": [290.15, 291.15],
        "wind_m_s": [2.5, 4.0],
        "wind_from_deg": [270.0, 270.0],
        "net_radiation_w_m2": [500.0, -30.0],
        "precipitation_m_s": [0.0, 0.0],
        "boundary_layer_height_m": [600.0, 300.0],
        "total_cloud_cover_fraction": [0.2, 0.8],
    })
    frame = run_short_case(config, forcing)
    assert np.isfinite(frame.select_dtypes("number")).all().all()
    assert frame["air_hto_concentration"].gt(0).all()


def test_short_or_time_mismatched_forcing_is_rejected():
    config = load_configuration("configs/default_parameters.yaml", "configs/test_case.yaml")
    config["duration_hours"] = 2
    one_row = pd.DataFrame({
        "temperature_k": [293.15],
        "dewpoint_k": [290.15],
        "wind_m_s": [3.0],
        "wind_from_deg": [270.0],
        "net_radiation_w_m2": [100.0],
        "precipitation_m_s": [0.0],
    })
    with pytest.raises(ValueError, match="rows"):
        run_short_case(config, one_row)
    two_rows = pd.concat([one_row, one_row], ignore_index=True)
    two_rows["time"] = pd.to_datetime(
        ["2025-06-02T00:00:00Z", "2025-06-02T01:00:00Z"]
    )
    with pytest.raises(ValueError, match="start time"):
        run_short_case(config, two_rows)
