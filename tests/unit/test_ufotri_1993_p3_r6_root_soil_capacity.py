"""Static soil supply feasibility is separate from KfK5194 original dynamics."""
from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup as Group,
    kfk5194_1993_root_soil_boundary,
    kfk5194_1993_root_layer_withdrawals,
)
from cteas_ufotri.plant.kfk5194_1993_root_soil_capacity import (
    audit_kfk5194_1993_root_soil_capacity,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import KFK5194WaterActivityError

ROOT = Path(__file__).resolve().parents[2]


def _source(group=Group.AGRICULTURAL_PLANT, c=(10.,20.,40.)):
    profile = load_1993_source_profile(
        ROOT/"configs"/"ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )
    boundary = kfk5194_1993_root_soil_boundary(
        profile=profile,plant_group=group,soil_layer_water_hto_bq_kg=c,
    )
    withdrawals = kfk5194_1993_root_layer_withdrawals(
        boundary=boundary,root_water_delivery_kg_m2_ground_s=0.001,
        interval_seconds=100.,
    )
    return boundary, withdrawals


@pytest.mark.parametrize("group,expected_water,expected_hto",[
    (Group.AGRICULTURAL_PLANT, (0.98,1.96,0.96), (9.8,39.2,38.4)),
    (Group.PASTURE_GRASS, (0.96,1.94,1.), (9.6,38.8,40.)),
])
def test_hand_calculated_static_water_and_activity_control_volume(
    group,expected_water,expected_hto
):
    boundary,w = _source(group)
    source_water=(1.,2.,1.)
    source_hto=(10.,40.,40.)
    r = audit_kfk5194_1993_root_soil_capacity(
        boundary=boundary,withdrawals=w,
        soil_water_available_kg_m2_ground=source_water,
        soil_hto_available_bq_m2_ground=source_hto,
    )
    assert r.water_after_kg_m2_ground == pytest.approx(expected_water)
    assert r.hto_after_bq_m2_ground == pytest.approx(expected_hto)
    assert sum(r.extracted_water_kg_m2_ground) == pytest.approx(0.1)
    assert sum(r.extracted_hto_bq_m2_ground) == pytest.approx(
        2.6 if group is Group.AGRICULTURAL_PLANT else 1.6
    )
    assert r.total_water_balance_residual_kg_m2_ground == pytest.approx(0,abs=1e-12)
    assert r.total_hto_balance_residual_bq_m2_ground == pytest.approx(0,abs=1e-12)
    assert r.provenance()["soil_inventory_mutated"] is False
    assert r.provenance()["1993_fortran_soil_code_equivalence"]=="NOT_ESTABLISHED"
    assert source_water == (1.,2.,1.)
    assert source_hto == (10.,40.,40.)


def test_inventory_exactly_at_withdrawal_is_allowed_without_negative_stock():
    b,w = _source()
    r = audit_kfk5194_1993_root_soil_capacity(
        boundary=b,withdrawals=w,
        soil_water_available_kg_m2_ground=w.layer_water_kg_m2_ground,
        soil_hto_available_bq_m2_ground=w.layer_hto_bq_m2_ground,
    )
    assert all(abs(x)<1e-15 for x in r.water_after_kg_m2_ground)
    assert all(abs(x)<1e-14 for x in r.hto_after_bq_m2_ground)


@pytest.mark.parametrize("water,hto",[
    ((0.001,2.,1.),(0.01,40.,40.)),
    ((1.,0.001,1.),(10.,0.02,40.)),
    ((1.,2.,1.),(10.,0.1,40.)),
    ((1.,2.,1.),(11.,40.,40.)),  # inconsistent water-stock concentration
    ((1.,2.,1.),(10.,40.,-1.)),
    ((1.,2.,float("nan")),(10.,40.,40.)),
    ((1.,2.,float("inf")),(10.,40.,40.)),
    ((1.,2.),(10.,40.,40.)),
])
def test_nonphysical_or_insufficient_soil_stock_fails_closed(water,hto):
    b,w = _source()
    with pytest.raises(KFK5194WaterActivityError):
        audit_kfk5194_1993_root_soil_capacity(
            boundary=b,withdrawals=w,
            soil_water_available_kg_m2_ground=water,
            soil_hto_available_bq_m2_ground=hto,
        )


def test_forged_effective_concentration_or_layer_extraction_is_rejected():
    b,w = _source()
    common=dict(
        soil_water_available_kg_m2_ground=(1.,2.,1.),
        soil_hto_available_bq_m2_ground=(10.,40.,40.),
    )
    for changed_b,changed_w in [
        (replace(b,effective_root_water_hto_bq_kg=30.),w),
        (b,replace(w,layer_water_kg_m2_ground=(0.01,0.05,0.04))),
        (b,replace(w,layer_hto_bq_m2_ground=(0.1,0.8,1.7))),
    ]:
        with pytest.raises(KFK5194WaterActivityError):
            audit_kfk5194_1993_root_soil_capacity(
                boundary=changed_b,withdrawals=changed_w,**common
            )


def test_zero_grass_third_layer_has_no_water_supply_requirement():
    b,w=_source(Group.PASTURE_GRASS)
    r=audit_kfk5194_1993_root_soil_capacity(
        boundary=b,withdrawals=w,
        soil_water_available_kg_m2_ground=(1.,2.,0.),
        soil_hto_available_bq_m2_ground=(10.,40.,0.),
    )
    assert r.water_after_kg_m2_ground[2] == 0
    assert r.hto_after_bq_m2_ground[2] == 0


def test_1990_default_and_1993_root_model_are_untouched():
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/kfk5194_1993_root_soil_boundary.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_root_soil_capacity" not in (
            ROOT/path
        ).read_text(encoding="utf-8")
