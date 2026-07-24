from __future__ import annotations

from pathlib import Path

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


ROOT = Path(__file__).resolve().parents[2]
V2_CASES = (
    "v2_era5_72h_wet_deposition.yaml",
    "v2_accident_plant_obt_14d.yaml",
    "v2_crop_ingestion_season.yaml",
    "v2_pasture_milk_pathway.yaml",
    "v2_full_adult_dose.yaml",
)


def _base(duration_h: float = 2.0) -> dict:
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    config["duration_hours"] = duration_h
    config["atmosphere"]["reemission_feedback_mode"] = "off"
    return config


def _enable_rain(config: dict) -> None:
    config["synthetic_forcing"].update(
        rain_start_hour=0.0,
        rain_end_hour=config["duration_hours"],
        rain_rate_m_s=2.0e-6,
    )
    config["atmosphere"]["depletion"]["wet_scavenging_mode"] = (
        "precipitation_power_law"
    )


def _assert_interface_closure(frame) -> None:
    assert frame["dry_interface_residual_bq_s"].abs().max() == 0.0
    assert frame["wet_interface_residual_bq_s"].abs().max() == 0.0
    assert frame["combined_deposition_interface_residual_bq_s"].abs().max() == 0.0
    final = frame.iloc[-1]
    assert final["surface_dry_input_bq"] == final["plume_dry_loss_bq"]
    assert final["surface_wet_input_bq"] == final["plume_wet_loss_bq"]
    assert (
        final["plume_dry_loss_bq"] + final["plume_wet_loss_bq"]
        <= final["stack_release_bq"]
    )


def test_audited_72h_case_repairs_dry_ratio_from_8_94_to_one():
    era5_path = ROOT / "data/era5/era5_surface_2025-06-01_2025-06-02.csv"
    if not era5_path.is_file():
        pytest.skip("Local read-only ERA5 audit forcing is not available")
    from scripts.run_v2_end_to_end import hybrid_era5_forcing

    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_era5_72h_wet_deposition.yaml",
    )
    forcing = hybrid_era5_forcing(config, era5_path)
    frame = run_short_case(config, forcing)
    final = frame.iloc[-1]
    assert final["plume_dry_loss_bq"] > 0.0
    assert final["surface_dry_input_bq"] / final["plume_dry_loss_bq"] == 1.0
    assert final["surface_wet_input_bq"] / final["plume_wet_loss_bq"] == 1.0
    _assert_interface_closure(frame)


@pytest.mark.parametrize("case_name", V2_CASES)
def test_all_formal_v2_cases_share_the_plume_loss_ledger(case_name):
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2" / case_name,
    )
    frame = run_short_case(config)
    _assert_interface_closure(frame)


def test_footprint_area_only_rescales_local_flux():
    outputs = []
    for factor in (0.1, 1.0, 10.0):
        config = _base(1.0)
        config["deposition"]["dry_footprint"]["area_m2"] *= factor
        frame = run_short_case(config)
        outputs.append(
            (
                frame["surface_dry_input_bq"].iloc[-1],
                frame["dry_deposition_flux_bq_m2_s"].iloc[0],
            )
        )
    assert outputs[0][0] == outputs[1][0] == outputs[2][0]
    assert outputs[0][1] == pytest.approx(outputs[1][1] * 10.0)
    assert outputs[2][1] == pytest.approx(outputs[1][1] / 10.0)


@pytest.mark.parametrize(
    ("dry_enabled", "wet_enabled", "vd_m_s", "rain_enabled"),
    (
        (False, False, 0.005, False),
        (True, False, 0.005, False),
        (False, True, 0.005, True),
        (True, True, 0.005, True),
        (True, False, 0.0, False),
        (True, True, 0.005, False),
    ),
)
def test_dry_wet_on_off_and_zero_limits(
    dry_enabled,
    wet_enabled,
    vd_m_s,
    rain_enabled,
):
    config = _base(1.0)
    config["atmosphere"]["deposition_velocity_m_s"] = vd_m_s
    config["atmosphere"]["depletion"]["dry_deposition_enabled"] = dry_enabled
    if wet_enabled and rain_enabled:
        _enable_rain(config)
    elif wet_enabled:
        config["atmosphere"]["depletion"]["wet_scavenging_mode"] = (
            "precipitation_power_law"
        )
    elif rain_enabled:
        raise AssertionError("Invalid test setup")
    frame = run_short_case(config)
    final = frame.iloc[-1]
    _assert_interface_closure(frame)
    assert (final["plume_dry_loss_bq"] > 0.0) == (
        dry_enabled and vd_m_s > 0.0
    )
    assert (final["plume_wet_loss_bq"] > 0.0) == (
        wet_enabled and rain_enabled
    )


@pytest.mark.parametrize("segments", (1, 2, 10, 100))
def test_segment_count_preserves_combined_loss_and_partition(segments):
    config = _base(1.0)
    _enable_rain(config)
    config["atmosphere"]["depletion"]["segments"] = segments
    frame = run_short_case(config)
    _assert_interface_closure(frame)
    final = frame.iloc[-1]
    assert (
        final["plume_dry_loss_bq"] + final["plume_wet_loss_bq"]
        <= final["stack_release_bq"]
    )


def test_surface_inventory_and_boundary_outputs_do_not_exceed_input():
    config = _base(4.0)
    _enable_rain(config)
    frame = run_short_case(config)
    final = frame.iloc[-1]
    area = config["deposition"]["dry_footprint"]["area_m2"]
    allocated_input = (
        final["surface_dry_input_bq"] + final["surface_wet_input_bq"]
    )
    accounted = area * (
        final["surface_environmental_inventory_bq_m2"]
        + final["surface_boundary_output_bq_m2"]
        + final["surface_decay_loss_bq_m2"]
    )
    assert accounted == pytest.approx(allocated_input, rel=1.0e-12)
    assert final["surface_environmental_inventory_bq_m2"] * area <= allocated_input
