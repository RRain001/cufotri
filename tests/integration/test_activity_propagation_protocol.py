from copy import deepcopy
from pathlib import Path

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ACTIVITY_FIELDS = {
    "external_stack_input_bq",
    "dry_plume_loss_bq",
    "wet_plume_loss_bq",
    "dry_surface_input_bq",
    "wet_surface_input_bq",
    "environmental_inventory_bq",
    "harvested_activity_bq",
    "milk_activity_bq",
    "beef_activity_bq",
    "excreted_activity_bq",
    "deep_loss_bq",
    "runoff_bypass_bq",
    "decay_loss_bq",
    "activity_residual_bq",
}


@pytest.mark.parametrize(
    "case_name",
    [
        "v2_era5_72h_wet_deposition.yaml",
        "v2_accident_plant_obt_14d.yaml",
        "v2_crop_ingestion_season.yaml",
        "v2_pasture_milk_pathway.yaml",
        "v2_full_adult_dose.yaml",
        "v2_leaf_exchange_food_dose_72h.yaml",
        "v2_pasture_multiyear_2y.yaml",
    ],
)
def test_formal_cases_report_closed_activity_protocol(case_name):
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2" / case_name,
    )
    frame = run_short_case(config)
    assert REQUIRED_ACTIVITY_FIELDS <= set(frame.columns)
    final = frame.iloc[-1]
    assert final["dry_plume_loss_bq"] == final["dry_surface_input_bq"]
    assert final["wet_plume_loss_bq"] == final["wet_surface_input_bq"]
    assert final["activity_relative_residual"] < 1.0e-12
    assert final["accounted_environmental_activity_bq"] <= (
        final["external_stack_input_bq"] * (1.0 + 1.0e-12) + 1.0e-6
    )


def test_zero_external_sources_allow_only_conservative_internal_transfer():
    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    config = deepcopy(config)
    config["plant"]["leaf_exchange_mode"] = "off"
    config["physics"]["tritium_decay_constant_s"] = 0.0
    initial = State(
        soil_water_m=0.01,
        plant_tfwt_bq_m2=100.0,
        plant_obt_bq_m2=50.0,
    )
    final, diagnostics = advance(
        initial,
        60.0,
        0.0,
        0.0,
        0.0,
        0.0,
        config,
        edible_allocation_rate_s=1.0e-5,
    )
    assert final.total_hto_bq_m2 == pytest.approx(initial.total_hto_bq_m2)
    assert diagnostics.surface_box_mass_closure.external_input_bq_m2 == 0.0
    assert diagnostics.surface_box_mass_closure.relative_error < 1.0e-12
