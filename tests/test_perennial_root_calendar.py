from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.case import run_short_case
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State
from cteas_ufotri.crop.phenology import (
    CropParameters,
    season_fraction_at_time,
)


def _isolated_config() -> dict:
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/test_case.yaml",
    )
    config["plant"]["leaf_exchange_mode"] = "off"
    config["plant"]["obt_formation_rate_s"] = 0.0
    config["plant"]["obt_turnover_rate_s"] = 0.0
    config["physics"]["tritium_decay_constant_s"] = 0.0
    return config


def _pasture() -> CropParameters:
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/test_case.yaml",
    )
    return CropParameters.from_mapping(
        "pasture",
        config["crops"]["parameters"]["pasture"],
    )


def test_partial_cut_removes_shoot_and_retains_root_inventory():
    initial = State(
        soil_water_m=0.01,
        plant_tfwt_bq_m2=100.0,
        plant_obt_bq_m2=50.0,
        root_tfwt_bq_m2=40.0,
        root_obt_bq_m2=20.0,
    )
    final, diagnostics = advance(
        initial,
        100.0,
        0.0,
        0.0,
        0.0,
        0.0,
        _isolated_config(),
        harvest_event=True,
        harvest_fraction=0.5,
        root_activity_fraction=0.4,
    )

    assert final.root_tfwt_bq_m2 == pytest.approx(40.0)
    assert final.root_obt_bq_m2 == pytest.approx(20.0)
    assert final.shoot_tfwt_bq_m2 == pytest.approx(30.0)
    assert final.shoot_obt_bq_m2 == pytest.approx(15.0)
    assert final.cut_plant_hto_bq_m2 == pytest.approx(30.0)
    assert final.cut_plant_obt_bq_m2 == pytest.approx(15.0)
    assert diagnostics.surface_box_mass_closure.relative_error < 1.0e-12


def test_multiyear_root_survives_year_crossing_and_shoot_regrowth_is_active():
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_pasture_multiyear_2y.yaml",
    )
    frame = run_short_case(config)
    first_year_end = frame.loc[
        frame["time"].dt.strftime("%Y-%m-%d") == "2025-12-31"
    ].iloc[-1]
    second_spring = frame.loc[
        frame["time"].dt.strftime("%Y-%m-%d") == "2026-05-15"
    ].iloc[-1]

    assert int(frame["harvest_event"].sum()) == 6
    assert first_year_end["root_tfwt_bq_m2"] > 0.0
    assert first_year_end["root_obt_bq_m2"] > 0.0
    assert second_spring["root_tfwt_bq_m2"] > 0.0
    assert second_spring["shoot_tfwt_bq_m2"] > 0.0
    assert second_spring["crop_lai"] > first_year_end["crop_lai"]
    assert frame["surface_box_relative_residual"].max() < 1.0e-12


@pytest.mark.parametrize(
    ("year", "days_in_year"),
    ((2025, 365), (2024, 366)),
)
def test_wrap_season_uses_actual_calendar_year_length(
    year: int,
    days_in_year: int,
):
    crop = replace(_pasture(), growth_start_doy=300, harvest_doy=60)
    december_31 = datetime(year, 12, 31, tzinfo=timezone.utc)
    january_1 = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    season_length = (days_in_year - 300) + 60

    december_fraction = season_fraction_at_time(december_31, crop)
    january_fraction = season_fraction_at_time(january_1, crop)

    assert december_fraction == pytest.approx(
        (days_in_year - 300) / season_length
    )
    assert january_fraction == pytest.approx(
        (days_in_year - 300 + 1) / season_length
    )
    assert january_fraction - december_fraction == pytest.approx(
        1.0 / season_length
    )
