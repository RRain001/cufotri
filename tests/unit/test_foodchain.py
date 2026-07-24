from __future__ import annotations

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.foodchain.model import (
    AnimalState,
    BeefProductState,
    plant_food_outputs,
    step_animal,
    step_beef_product,
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
    assert diagnostics.slaughter_hto_output_bq_s * 600.0 == pytest.approx(100.0)
    assert diagnostics.slaughter_obt_output_bq_s * 600.0 == pytest.approx(50.0)
    assert diagnostics.closure.relative_error < 1.0e-12


def test_no_slaughter_produces_no_beef_product():
    final, diagnostics = step_beef_product(
        BeefProductState(),
        600.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
    )
    assert final == BeefProductState()
    assert diagnostics.produced_hto_bq_m2_s == 0.0
    assert diagnostics.consumed_mass_kg_m2_s == 0.0
    assert diagnostics.activity_closure.relative_error == 0.0


def test_continuous_turnover_moves_animal_activity_to_beef_once():
    dt_s = 600.0
    slaughter_rate_s = 0.002 / 86400.0
    animal_final, animal_diag = step_animal(
        AnimalState(100.0, 50.0),
        dt_s,
        0.0,
        0.0,
        0.0,
        _animal_config(),
        slaughter_rate_s=slaughter_rate_s,
    )
    product_final, product_diag = step_beef_product(
        BeefProductState(),
        dt_s,
        animal_diag.slaughter_hto_output_bq_s,
        animal_diag.slaughter_obt_output_bq_s,
        slaughter_rate_s * 200.0 / 4000.0,
        0.0,
        0.0,
    )
    animal_loss = (
        animal_diag.slaughter_hto_output_bq_s
        + animal_diag.slaughter_obt_output_bq_s
    ) * dt_s
    assert product_final.total_bq_m2 == pytest.approx(animal_loss)
    assert product_diag.activity_closure.input_bq == pytest.approx(animal_loss)
    assert animal_final.total_bq + animal_loss < 150.0
    assert animal_diag.closure.relative_error < 1.0e-12
    assert product_diag.activity_closure.relative_error < 1.0e-12


def test_beef_consumption_is_limited_by_product_inventory():
    final, diagnostics = step_beef_product(
        BeefProductState(10.0, 5.0, 1.0),
        60.0,
        0.0,
        0.0,
        0.0,
        10.0,
        0.0,
    )
    assert final == BeefProductState()
    assert diagnostics.consumed_mass_kg_m2_s * 60.0 == pytest.approx(1.0)
    assert diagnostics.consumed_hto_bq_m2_s * 60.0 == pytest.approx(10.0)
    assert diagnostics.consumed_obt_bq_m2_s * 60.0 == pytest.approx(5.0)
    assert diagnostics.activity_closure.relative_error < 1.0e-12
    assert diagnostics.mass_residual_kg_m2 == pytest.approx(0.0)


def test_stopping_beef_production_does_not_create_new_activity():
    initial = BeefProductState(10.0, 5.0, 1.0)
    final, diagnostics = step_beef_product(
        initial,
        60.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    )
    assert final == initial
    assert diagnostics.produced_hto_bq_m2_s == 0.0
    assert diagnostics.produced_obt_bq_m2_s == 0.0
    assert diagnostics.activity_closure.relative_error == 0.0


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
