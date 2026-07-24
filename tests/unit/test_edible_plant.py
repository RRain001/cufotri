from __future__ import annotations

import pytest

from cteas_ufotri.config import load_configuration
from cteas_ufotri.coupling.integrator import advance
from cteas_ufotri.coupling.state import State
from cteas_ufotri.plant.edible import edible_concentrations


def _isolated():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    config["plant"]["obt_formation_rate_s"] = 0.0
    config["plant"]["obt_turnover_rate_s"] = 0.0
    config["physics"]["tritium_decay_constant_s"] = 0.0
    config["atmosphere"]["deposition_velocity_m_s"] = 0.0
    config["plant"]["leaf_exchange_mode"] = "off"
    return config


def test_edible_water_fresh_and_dry_units_are_explicit():
    values = edible_concentrations(80.0, 20.0, 2.0, 0.8, 1000.0)
    assert values.tfwt_bq_m3_water == pytest.approx(50_000.0)
    assert values.obt_bq_kg_fresh == pytest.approx(10.0)
    assert values.obt_bq_kg_dry == pytest.approx(50.0)


def test_whole_to_edible_transfers_are_internal_and_conservative():
    initial = State(0.01, 0.0, 100.0, 50.0)
    final, diagnostics = advance(
        initial,
        100.0,
        0.0,
        0.0,
        0.0,
        0.0,
        _isolated(),
        edible_allocation_rate_s=1.0e-4,
    )
    assert final.plant_tfwt_bq_m2 < initial.plant_tfwt_bq_m2
    assert final.plant_obt_bq_m2 < initial.plant_obt_bq_m2
    assert final.edible_tfwt_bq_m2 > 0.0
    assert final.edible_obt_bq_m2 > 0.0
    assert final.total_hto_bq_m2 == pytest.approx(initial.total_hto_bq_m2)
    assert diagnostics.surface_box_mass_closure.relative_error < 1.0e-12


def test_harvest_resets_plant_and_records_edible_boundaries():
    initial = State(
        0.01,
        0.0,
        5.0,
        2.0,
        edible_tfwt_bq_m2=20.0,
        edible_obt_bq_m2=10.0,
    )
    final, diagnostics = advance(
        initial,
        100.0,
        0.0,
        0.0,
        0.0,
        0.0,
        _isolated(),
        harvest_event=True,
        harvest_loss_fraction=0.1,
    )
    assert final.plant_tfwt_bq_m2 == pytest.approx(0.0)
    assert final.plant_obt_bq_m2 == pytest.approx(0.0)
    assert final.edible_tfwt_bq_m2 == pytest.approx(0.0)
    assert final.edible_obt_bq_m2 == pytest.approx(0.0)
    assert final.harvested_hto_bq_m2 == pytest.approx(18.0)
    assert final.harvested_obt_bq_m2 == pytest.approx(9.0)
    assert diagnostics.harvest_loss_bq_m2_s * 100.0 == pytest.approx(3.0)


def test_partial_cut_retains_perennial_plant_and_edible_inventory():
    config = _isolated()
    initial = State(
        soil_water_m=0.01,
        plant_tfwt_bq_m2=100.0,
        plant_obt_bq_m2=50.0,
        edible_tfwt_bq_m2=20.0,
        edible_obt_bq_m2=10.0,
    )
    final, diagnostics = advance(
        initial,
        100.0,
        0.0,
        0.0,
        0.0,
        0.0,
        config,
        harvest_event=True,
        harvest_fraction=0.5,
        harvest_loss_fraction=0.0,
    )
    assert final.plant_tfwt_bq_m2 == pytest.approx(50.0, rel=1.0e-5)
    assert final.plant_obt_bq_m2 == pytest.approx(25.0, rel=1.0e-5)
    assert final.edible_tfwt_bq_m2 == pytest.approx(10.0, rel=1.0e-5)
    assert final.edible_obt_bq_m2 == pytest.approx(5.0, rel=1.0e-5)
    assert final.cut_plant_hto_bq_m2 == pytest.approx(50.0)
    assert final.cut_plant_obt_bq_m2 == pytest.approx(25.0)
    assert diagnostics.surface_box_mass_closure.relative_error < 1.0e-12
