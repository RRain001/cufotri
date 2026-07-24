from __future__ import annotations

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.foodchain.model import (
    AnimalState,
    plant_food_outputs,
    step_animal,
)


def _animal_config():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    return config["foodchain"]


def test_animal_inventory_closes_with_feed_water_milk_and_excretion():
    initial = AnimalState(100.0, 25.0)
    final, diagnostics = step_animal(
        initial,
        600.0,
        10.0,
        4.0,
        2.0,
        _animal_config(),
    )
    assert final.total_bq > 0.0
    assert diagnostics.feed_hto_input_bq_s > 0.0
    assert diagnostics.feed_obt_input_bq_s > 0.0
    assert diagnostics.water_hto_input_bq_s > 0.0
    assert diagnostics.milk_hto_output_bq_s > 0.0
    assert diagnostics.milk_obt_output_bq_s > 0.0
    assert diagnostics.excretion_output_bq_s > 0.0
    assert diagnostics.closure.relative_error < 1.0e-12


def test_slaughter_is_a_boundary_and_does_not_break_closure():
    final, diagnostics = step_animal(
        AnimalState(100.0, 50.0),
        600.0,
        0.0,
        0.0,
        0.0,
        _animal_config(),
        slaughter_event=True,
    )
    assert final.total_bq == pytest.approx(0.0)
    assert diagnostics.slaughter_output_bq_s * 600.0 == pytest.approx(150.0)
    assert diagnostics.closure.relative_error < 1.0e-12


@pytest.mark.parametrize(
    ("crop", "hto_key", "obt_key"),
    [
        ("leafy_vegetable", "leafy_tfwt_bq_kg_fresh", "leafy_obt_bq_kg_fresh"),
        ("root_vegetable", "root_crop_tfwt_bq_kg_fresh", "root_crop_obt_bq_kg_fresh"),
        ("cereal", "grain_tfwt_bq_kg_fresh", "grain_obt_bq_kg_fresh"),
        ("pasture", "pasture_tfwt_bq_kg_fresh", "pasture_obt_bq_kg_fresh"),
    ],
)
def test_plant_food_paths_are_explicit(crop, hto_key, obt_key):
    values = plant_food_outputs(crop, 1000.0, 20.0, 0.8, 1000.0)
    assert values[hto_key] == pytest.approx(0.8)
    assert values[obt_key] == pytest.approx(20.0)
    assert sum(value > 0 for value in values.values()) == 2

