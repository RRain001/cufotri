import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


def test_two_year_pasture_preserves_state_and_closes_cutting_boundaries():
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_pasture_multiyear_2y.yaml",
    )
    frame = run_short_case(config)
    events = frame.loc[frame["harvest_event"]]
    assert len(events) == 6
    assert set(events["harvest_fraction"]) == {0.5}
    assert frame["crop_lai"].min() == pytest.approx(0.25)
    assert frame["crop_lai"].max() > 3.9
    assert frame["cut_plant_hto_bq_m2"].iloc[-1] > 0.0
    assert frame["harvested_hto_bq_m2"].iloc[-1] > 0.0
    assert frame["plant_tfwt_inventory"].min() >= 0.0
    assert frame["plant_obt_inventory"].min() >= 0.0
    assert frame["edible_tfwt_inventory_bq_m2"].min() >= 0.0
    assert frame["edible_obt_inventory_bq_m2"].min() >= 0.0
    assert frame["surface_box_relative_residual"].max() < 1.0e-12

    first_year_end = frame.loc[
        frame["time"].dt.strftime("%Y-%m-%d") == "2025-12-31"
    ].iloc[-1]
    assert first_year_end["plant_tfwt_inventory"] > 0.0
    assert first_year_end["crop_lai"] == pytest.approx(0.25)
    second_spring = frame.loc[
        frame["time"].dt.strftime("%Y-%m-%d") == "2026-05-15"
    ].iloc[-1]
    assert second_spring["crop_lai"] > first_year_end["crop_lai"]
