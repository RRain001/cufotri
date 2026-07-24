from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration


ROOT = Path(__file__).resolve().parents[2]


def _formal_leaf_case() -> dict:
    return load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/v2/v2_leaf_exchange_food_dose_72h.yaml",
    )


def test_formal_leaf_case_reaches_tfwt_obt_food_and_ingestion_dose():
    config = _formal_leaf_case()
    frame = run_short_case(config)
    final = frame.iloc[-1]
    assert frame["leaf_uptake_flux"].max() > 0.0
    assert final["soil_hto_inventory"] == 0.0
    assert final["plant_tfwt_inventory"] > 0.0
    assert final["plant_obt_inventory"] > 0.0
    assert final["edible_tfwt_inventory_bq_m2"] > 0.0
    assert final["edible_obt_inventory_bq_m2"] > 0.0
    assert final["leafy_tfwt_bq_kg_fresh"] > 0.0
    assert final["leafy_obt_bq_kg_fresh"] > 0.0
    assert final["plant_ingestion_dose_sv"] > 0.0
    assert frame["surface_box_relative_residual"].abs().max() < 1.0e-12


def test_leaf_off_control_removes_the_isolated_plant_and_food_pathway():
    enabled = _formal_leaf_case()
    disabled = deepcopy(enabled)
    disabled["plant"]["leaf_exchange_mode"] = "off"
    enabled_final = run_short_case(enabled).iloc[-1]
    disabled_final = run_short_case(disabled).iloc[-1]
    assert enabled_final["plant_ingestion_dose_sv"] > 0.0
    assert disabled_final["plant_tfwt_inventory"] == 0.0
    assert disabled_final["plant_obt_inventory"] == 0.0
    assert disabled_final["edible_tfwt_inventory_bq_m2"] == 0.0
    assert disabled_final["edible_obt_inventory_bq_m2"] == 0.0
    assert disabled_final["plant_ingestion_dose_sv"] == 0.0


def test_formal_leaf_case_converges_from_600_to_60_seconds():
    keys = (
        "plant_tfwt_inventory",
        "plant_obt_inventory",
        "edible_tfwt_inventory_bq_m2",
        "edible_obt_inventory_bq_m2",
        "plant_ingestion_dose_sv",
    )
    results = {}
    for dt_s in (600, 300, 120, 60):
        config = _formal_leaf_case()
        config["time_step_seconds"] = dt_s
        final = run_short_case(config).iloc[-1]
        results[dt_s] = {key: float(final[key]) for key in keys}
    for key in keys:
        assert results[60][key] > 0.0
        assert results[600][key] == pytest.approx(results[60][key], rel=0.01)
