from __future__ import annotations

from copy import deepcopy

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


def _combined_deposition_case(wet_to_dry_area_ratio: float) -> dict:
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/test_case.yaml",
    )
    config = deepcopy(config)
    config["duration_hours"] = 2.0
    config["plant"]["leaf_exchange_mode"] = "off"
    config["atmosphere"]["reemission_feedback_mode"] = "off"
    config["atmosphere"]["depletion"]["dry_deposition_enabled"] = True
    config["atmosphere"]["depletion"]["wet_scavenging_mode"] = (
        "precipitation_power_law"
    )
    config["synthetic_forcing"].update(
        rain_start_hour=0.0,
        rain_end_hour=config["duration_hours"],
        rain_rate_m_s=2.0e-6,
    )
    dry_area_m2 = config["deposition"]["dry_footprint"]["area_m2"]
    config["deposition"]["wet_footprint"]["area_m2"] = (
        dry_area_m2 * wet_to_dry_area_ratio
    )
    return config


@pytest.mark.parametrize("wet_to_dry_area_ratio", (0.1, 1.0, 10.0))
def test_dry_wet_footprints_close_one_global_activity_ledger(
    wet_to_dry_area_ratio: float,
):
    frame = run_short_case(_combined_deposition_case(wet_to_dry_area_ratio))
    final = frame.iloc[-1]

    deposited_bq = (
        final["dry_surface_input_bq"] + final["wet_surface_input_bq"]
    )
    accounted_bq = (
        final["environmental_inventory_bq"]
        + final["environmental_boundary_output_bq"]
        + final["decay_loss_bq"]
    )

    assert final["dry_activity_bq"] == final["dry_surface_input_bq"]
    assert final["wet_activity_bq"] == final["wet_surface_input_bq"]
    assert final["total_deposition_activity_bq"] == deposited_bq
    assert accounted_bq == pytest.approx(deposited_bq, rel=1.0e-12)
    assert abs(deposited_bq - accounted_bq) / deposited_bq < 1.0e-12


def test_footprint_area_changes_flux_not_total_activity():
    results = {}
    for ratio in (0.1, 1.0, 10.0):
        final = run_short_case(_combined_deposition_case(ratio)).iloc[-1]
        results[ratio] = final

    for pathway in ("dry", "wet"):
        activities = [
            results[ratio][f"{pathway}_activity_bq"]
            for ratio in (0.1, 1.0, 10.0)
        ]
        assert activities[0] == pytest.approx(activities[1], rel=1.0e-14)
        assert activities[2] == pytest.approx(activities[1], rel=1.0e-14)

    wet_fluxes = {
        ratio: results[ratio]["wet_deposition_flux_bq_m2_s"]
        for ratio in (0.1, 1.0, 10.0)
    }
    assert wet_fluxes[0.1] == pytest.approx(10.0 * wet_fluxes[1.0])
    assert wet_fluxes[10.0] == pytest.approx(0.1 * wet_fluxes[1.0])
