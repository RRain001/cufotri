"""Independent source-weighted three-layer soil-root-leaf transfer tests."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    kfk5194_1993_daylight_canopy, kfk5194_1993_monteith_et,
)
from cteas_ufotri.plant.kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup as Group, KFK5194RootMixingHypothesis as Mixing,
)
from cteas_ufotri.plant.kfk5194_1993_soil_root_transfer import (
    KFK5194SoilEvolutionHypothesis as Evolution,
    KFK5194SoilLayerInventoryState,
    advance_kfk5194_1993_extraction_only_soil_root_leaf,
    advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis as LeafHyp,
    KFK5194WaterActivityError, KFK5194WaterActivityForcing,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState

ROOT = Path(__file__).resolve().parents[2]
START=datetime(2026,1,1,tzinfo=timezone.utc)
SOIL_MODEL=Evolution.EXTRACTION_ONLY_NO_RECHARGE_RESEARCH
MIXING=Mixing.INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH
LEAF_HYP=LeafHyp.BELOT_COMPOSITE_FIXED_LEAF_WATER


def _profile():
    return load_1993_source_profile(
        ROOT/"configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _canopy():
    return kfk5194_1993_daylight_canopy(
        profile=_profile(),regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.,
        radiation_balance_w_m2=300.,half_response_radiation_w_m2=60.,
        vapour_pressure_deficit_hpa=5.,humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8,temperature_c=25.,minimum_temperature_c=10.,
        optimal_temperature_c=25.,maximum_temperature_c=40.,leaf_area_index=2.,
        wind_speed_at_reference_m_s=4.,friction_velocity_m_s=0.4,
        stanton_number=0.2,
    )


def _leaf():
    return TFWTState.from_inventory(
        plant_identifier="P3_R6_SOIL_ROOT_TRANSFER",crop="synthetic",
        growth_stage="synthetic",tfwt_inventory_bq_m2=36.,
        water_content_kg_m2=3.,time=START,area_basis="ground_area",
        provenance=ForcingProvenance(
            source_id="P3R6_CROSS_CONTROL",source_version="RESEARCH_ONLY",
            artifact_sha256="a"*64,spatial_reference="m2-ground",
            temporal_resolution_s=3600.,
        ),
    )


def _soil(group=Group.AGRICULTURAL_PLANT):
    return KFK5194SoilLayerInventoryState(
        time=START,plant_group=group,
        water_kg_m2_ground=(3.,4.,5.) if group is Group.AGRICULTURAL_PLANT
                              else (3.,4.,0.),
        hto_bq_m2_ground=(30.,80.,200.) if group is Group.AGRICULTURAL_PLANT
                           else (30.,80.,0.),
    )


def _forcing(canopy=None,dt=3600.,air=100.):
    c=_canopy() if canopy is None else canopy
    et=kfk5194_1993_monteith_et(
        profile=_profile(),canopy=c,net_radiation_w_m2=300.,
        soil_surface_resistance_s_m=150.,vapour_pressure_slope_pa_k=180.,
        psychrometric_constant_pa_k=65.,
        air_volumetric_heat_capacity_j_m3_k=1200.,
        latent_heat_vaporization_j_kg=2.45e6,
    )
    return KFK5194WaterActivityForcing(
        monteith=et,air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        root_water_delivery_kg_m2_ground_s=et.plant_water_flux_kg_m2_s,
        root_water_hto_concentration_bq_kg=99999.,
        interval_seconds=dt,
    )


def _run(soil=None,leaf=None,canopy=None,forcing=None,**changes):
    c=_canopy() if canopy is None else canopy
    args=dict(profile=_profile(),soil=_soil() if soil is None else soil,
              leaf=_leaf() if leaf is None else leaf,
              canopy=c,forcing=_forcing(c) if forcing is None else forcing,
              evolution_hypothesis=SOIL_MODEL,
              root_mixing_hypothesis=MIXING,leaf_hypothesis=LEAF_HYP)
    args.update(changes)
    return advance_kfk5194_1993_extraction_only_soil_root_leaf(**args)


@pytest.mark.parametrize("group,weights",[
    (Group.AGRICULTURAL_PLANT,(0.2,0.4,0.4)),
    (Group.PASTURE_GRASS,(0.4,0.6,0.)),
])
def test_cross_soil_leaf_water_hto_inventory_closes_for_both_1993_groups(group,weights):
    original=_soil(group)
    result=_run(soil=original)
    root=result.root_leaf.leaf_water_hto_step
    w=root.root_water_input_kg_m2_ground
    assert result.root_leaf.boundary.root_water_fractions==weights
    assert result.next_soil.time==result.next_leaf.time==START+timedelta(hours=1)
    assert result.original_soil == original
    assert result.next_soil != original
    assert result.original_soil.time == START
    assert result.next_leaf.water_content_kg_m2 == pytest.approx(3.)
    for i in range(3):
        assert result.next_soil.water_kg_m2_ground[i] == pytest.approx(
            original.water_kg_m2_ground[i]-w*weights[i]
        )
        assert result.next_soil.hto_bq_m2_ground[i] == pytest.approx(
            original.hto_bq_m2_ground[i] -
            result.root_leaf.layer_withdrawal.layer_hto_bq_m2_ground[i]
        )
    assert math.fsum(result.root_leaf.layer_withdrawal.layer_hto_bq_m2_ground) == (
        pytest.approx(root.root_hto_input_bq_m2_ground)
    )
    assert result.cross_water_residual_kg_m2_ground == pytest.approx(0,abs=1e-10)
    assert result.cross_hto_residual_bq_m2_ground == pytest.approx(0,abs=1e-9)
    assert root.additional_et_hto_sink_bq_m2_ground == 0
    assert result.provenance()["original_fortran_soil_root_parity"]=="NOT_ESTABLISHED"


def test_two_consecutive_half_hours_equal_one_hour_with_no_recharge():
    c=_canopy()
    whole=_run(canopy=c,forcing=_forcing(c,3600.))
    first=_run(canopy=c,forcing=_forcing(c,1800.))
    second=_run(canopy=c,soil=first.next_soil,leaf=first.next_leaf,
                forcing=_forcing(c,1800.))
    assert second.next_soil.time == whole.next_soil.time
    assert second.next_leaf.time == whole.next_leaf.time
    assert second.next_soil.water_kg_m2_ground == pytest.approx(
        whole.next_soil.water_kg_m2_ground,rel=1e-12
    )
    assert second.next_soil.hto_bq_m2_ground == pytest.approx(
        whole.next_soil.hto_bq_m2_ground,rel=1e-12
    )
    assert second.next_leaf.tfwt_inventory_bq_m2 == pytest.approx(
        whole.next_leaf.tfwt_inventory_bq_m2,rel=1e-11
    )


def test_insufficient_upper_soil_layer_fails_before_any_soil_mutation():
    small=replace(_soil(),water_kg_m2_ground=(1e-9,4.,5.),
                  hto_bq_m2_ground=(1e-8,80.,200.))
    with pytest.raises(KFK5194WaterActivityError,match="insufficient soil-layer"):
        _run(soil=small)
    assert small.water_kg_m2_ground[0] == 1e-9
    assert small.time == START


def test_incompatible_soil_leaf_clock_rejected():
    with pytest.raises(KFK5194WaterActivityError,match="times must match"):
        _run(soil=replace(_soil(),time=START+timedelta(hours=1)))


def test_explicit_research_assumptions_are_required():
    with pytest.raises(KFK5194WaterActivityError,match="extraction-only"):
        _run(evolution_hypothesis="EXTRACTION_ONLY_NO_RECHARGE_RESEARCH")
    with pytest.raises(KFK5194WaterActivityError,match="mixing"):
        _run(root_mixing_hypothesis=None)


@pytest.mark.parametrize("bad_water,bad_hto",[
    ((0.,1.,1.),(1.,1.,1.)),
    ((float("nan"),1.,1.),(0.,1.,1.)),
    ((1.,1.,1.),(float("inf"),1.,1.)),
    ((1.,-1.,1.),(1.,1.,1.)),
])
def test_invalid_soil_inventory_never_instantiates(bad_water,bad_hto):
    with pytest.raises(KFK5194WaterActivityError):
        replace(_soil(),water_kg_m2_ground=bad_water,hto_bq_m2_ground=bad_hto)


def test_dry_grass_bottom_soil_layer_stays_exact_zero_after_transfer():
    grass=_soil(Group.PASTURE_GRASS)
    result=_run(soil=grass)
    assert result.next_soil.water_kg_m2_ground[2] == 0.
    assert result.next_soil.hto_bq_m2_ground[2] == 0.
    assert result.root_leaf.layer_withdrawal.layer_water_kg_m2_ground[2] == 0.


def test_non_activation_of_old_1990_solver():
    for path in (
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_soil_root_transfer" not in (
            ROOT/path
        ).read_text(encoding="utf-8")


@pytest.mark.parametrize("group", [
    Group.AGRICULTURAL_PLANT, Group.PASTURE_GRASS,
])
def test_six_consecutive_hours_telescope_exact_water_and_signed_HTO_budgets(group):
    c=_canopy()
    initial_soil=_soil(group)
    initial_leaf=_leaf()
    airs=(0.,100.,35.,0.,125.,0.)
    forcings=tuple(_forcing(c,3600.,air=x) for x in airs)
    series=advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
        profile=_profile(), initial_soil=initial_soil,
        initial_leaf=initial_leaf, canopy=c, intervals=forcings,
        evolution_hypothesis=SOIL_MODEL,
        root_mixing_hypothesis=MIXING, leaf_hypothesis=LEAF_HYP,
    )
    assert len(series.steps)==6
    assert series.final_soil.time==series.final_leaf.time==START+timedelta(hours=6)
    assert series.initial_soil==initial_soil
    assert initial_soil.time==START
    assert series.initial_leaf.time==START
    assert series.final_soil.water_kg_m2_ground!=initial_soil.water_kg_m2_ground
    assert all(step.original_soil.time==START+timedelta(hours=i)
               for i,step in enumerate(series.steps))
    assert all(step.next_soil==series.steps[i+1].original_soil
               for i,step in enumerate(series.steps[:-1]))
    assert all(step.next_leaf.time==series.steps[i+1].original_soil.time
               for i,step in enumerate(series.steps[:-1]))
    assert series.steps[0].root_leaf.leaf_water_hto_step.belot_composite_hto_exchange_bq_m2_ground < 0
    assert series.steps[1].root_leaf.leaf_water_hto_step.belot_composite_hto_exchange_bq_m2_ground > 0
    assert series.cumulative_root_water_transfer_kg_m2_ground==pytest.approx(
        series.cumulative_plant_transpired_water_kg_m2_ground,rel=1e-12
    )
    assert series.cumulative_root_hto_transfer_bq_m2_ground==pytest.approx(
        math.fsum(x.root_leaf.leaf_water_hto_step.root_hto_input_bq_m2_ground
                  for x in series.steps)
    )
    assert series.final_leaf.tfwt_inventory_bq_m2 == pytest.approx(
        initial_leaf.tfwt_inventory_bq_m2
        + series.cumulative_belot_hto_exchange_bq_m2_ground
        + series.cumulative_root_hto_transfer_bq_m2_ground,abs=1e-8
    )
    assert series.cross_hour_water_residual_kg_m2_ground == pytest.approx(0,abs=1e-10)
    assert series.cross_hour_hto_residual_bq_m2_ground == pytest.approx(0,abs=1e-8)
    assert series.provenance()["original_fortran_numeric_equivalence"]=="NOT_ESTABLISHED"


def test_cumulative_six_hour_result_matches_manual_one_step_replay():
    c=_canopy()
    f=tuple(_forcing(c,3600.,air=v) for v in (0.,20.,40.,60.,80.,100.))
    series=advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
        profile=_profile(),initial_soil=_soil(),initial_leaf=_leaf(),
        canopy=c,intervals=f,evolution_hypothesis=SOIL_MODEL,
        root_mixing_hypothesis=MIXING,leaf_hypothesis=LEAF_HYP,
    )
    s,l=_soil(),_leaf()
    for forcing in f:
        result=_run(soil=s,leaf=l,canopy=c,forcing=forcing)
        s,l=result.next_soil,result.next_leaf
    assert series.final_soil.water_kg_m2_ground==pytest.approx(s.water_kg_m2_ground)
    assert series.final_soil.hto_bq_m2_ground==pytest.approx(s.hto_bq_m2_ground)
    assert series.final_leaf.tfwt_inventory_bq_m2==pytest.approx(
        l.tfwt_inventory_bq_m2,rel=1e-12
    )


def test_multi_hour_rejects_invalid_typed_or_unsynchronized_initial_conditions():
    c=_canopy()
    args=dict(
        profile=_profile(),initial_soil=_soil(),initial_leaf=_leaf(),
        canopy=c, evolution_hypothesis=SOIL_MODEL,
        root_mixing_hypothesis=MIXING, leaf_hypothesis=LEAF_HYP,
    )
    for bad in ((), [_forcing(c)], (_forcing(c), None), (_forcing(c), "3600")):
        with pytest.raises(KFK5194WaterActivityError):
            advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
                **args,intervals=bad,
            )
    with pytest.raises(KFK5194WaterActivityError,match="clocks must match"):
        advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
            **{**args,"initial_leaf":replace(_leaf(),time=START+timedelta(hours=1))},
            intervals=(_forcing(c),),
        )


def test_second_hour_insufficient_upper_soil_stock_fails_without_input_mutation():
    c=_canopy()
    et=_forcing(c).root_water_delivery_kg_m2_ground_s
    water_first=0.2*et*3600.*1.5
    soil=replace(_soil(),
                 water_kg_m2_ground=(water_first,4.,5.),
                 hto_bq_m2_ground=(10.*water_first,80.,200.))
    with pytest.raises(KFK5194WaterActivityError,match="insufficient soil-layer"):
        advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
            profile=_profile(), initial_soil=soil, initial_leaf=_leaf(),
            canopy=c, intervals=(_forcing(c),_forcing(c)),
            evolution_hypothesis=SOIL_MODEL,
            root_mixing_hypothesis=MIXING, leaf_hypothesis=LEAF_HYP,
        )
    assert soil.time==START
    assert soil.water_kg_m2_ground[0]==water_first
