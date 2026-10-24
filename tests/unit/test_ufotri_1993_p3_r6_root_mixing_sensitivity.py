"""Scientific discriminators for source-limited R6 instantaneous mixing.

These oracles compare a hand-derived tangent to independent black-box R6
runs; conservation alone is insufficient. They quantify *conditional*
sensitivity, not the physical truth of instantaneous root mixing.
"""
from dataclasses import replace
from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile
from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    kfk5194_1993_daylight_canopy, kfk5194_1993_monteith_et,
)
from cteas_ufotri.plant.kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup as Group,
    KFK5194RootMixingHypothesis as Mixing,
    advance_kfk5194_1993_soil_weighted_root_boundary,
)
from cteas_ufotri.plant.kfk5194_1993_root_mixing_sensitivity import (
    diagnose_kfk5194_1993_root_mixing_sensitivity,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis as LeafHyp,
    KFK5194WaterActivityError, KFK5194WaterActivityForcing,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState

ROOT=Path(__file__).resolve().parents[2]
MIX=Mixing.INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH
LEAF=LeafHyp.BELOT_COMPOSITE_FIXED_LEAF_WATER


def _profile():
    return load_1993_source_profile(
        ROOT/"configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _case(dt=3600., air=100., group=Group.AGRICULTURAL_PLANT):
    canopy=kfk5194_1993_daylight_canopy(
        profile=_profile(),regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.,
        radiation_balance_w_m2=300.,half_response_radiation_w_m2=60.,
        vapour_pressure_deficit_hpa=5.,humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8,temperature_c=25.,
        minimum_temperature_c=10.,optimal_temperature_c=25.,
        maximum_temperature_c=40.,leaf_area_index=2.,
        wind_speed_at_reference_m_s=4.,friction_velocity_m_s=0.4,
        stanton_number=0.2,
    )
    et=kfk5194_1993_monteith_et(
        profile=_profile(),canopy=canopy,net_radiation_w_m2=300.,
        soil_surface_resistance_s_m=150.,vapour_pressure_slope_pa_k=180.,
        psychrometric_constant_pa_k=65.,
        air_volumetric_heat_capacity_j_m3_k=1200.,
        latent_heat_vaporization_j_kg=2.45e6,
    )
    state=TFWTState.from_inventory(
        plant_identifier="KFK5194_R6_TANGENT",
        crop="research_oracle",growth_stage="fixed",
        tfwt_inventory_bq_m2=36.,water_content_kg_m2=3.,
        time=datetime(2026,1,1,tzinfo=timezone.utc),
        area_basis="ground_area",
        provenance=ForcingProvenance(
            source_id="R6_SENSITIVITY_ORACLE",source_version="v1",
            artifact_sha256="d"*64,
            spatial_reference="per-m2-ground",
            temporal_resolution_s=dt,
        ),
    )
    forcing=KFK5194WaterActivityForcing(
        monteith=et,air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        root_water_delivery_kg_m2_ground_s=et.plant_water_flux_kg_m2_s,
        root_water_hto_concentration_bq_kg=0.,
        interval_seconds=dt,
    )
    return dict(
        profile=_profile(),plant_group=group,
        soil_layer_water_hto_bq_kg=(10.,20.,40.),
        mixing_hypothesis=MIX,canopy=canopy,state=state,
        forcing=forcing,leaf_hypothesis=LEAF,
    )


def _final_activity(kwargs):
    return advance_kfk5194_1993_soil_weighted_root_boundary(
        **kwargs
    ).leaf_water_hto_step.final_hto_activity_bq_m2_ground


@pytest.mark.parametrize("group,weights", [
    (Group.AGRICULTURAL_PLANT, (0.2,0.4,0.4)),
    (Group.PASTURE_GRASS, (0.4,0.6,0.0)),
])
@pytest.mark.parametrize("dt", [1., 1800., 3600., 14400.])
def test_analytic_layer_tangent_matches_independent_finite_difference(
    group, weights, dt
):
    kwargs=_case(dt=dt,group=group)
    result=diagnose_kfk5194_1993_root_mixing_sensitivity(**kwargs)
    base=_final_activity(kwargs)
    for i, f in enumerate(weights):
        changed=list(kwargs["soil_layer_water_hto_bq_kg"])
        changed[i]+=1000.
        new=_final_activity({**kwargs,"soil_layer_water_hto_bq_kg":tuple(changed)})
        finite_difference=(new-base)/1000.
        expected=result.root_layer_final_activity_sensitivity_kg_m2_ground[i]
        assert finite_difference == pytest.approx(expected,rel=3e-9,abs=1e-10)
        if f==0:
            assert finite_difference==pytest.approx(0.,abs=1e-12)
    assert result.baseline.layer_withdrawal.total_hto_bq_m2_ground >= 0
    assert result.provenance()["root_transit_time"]=="NOT_ESTABLISHED"
    assert result.provenance()["original_fortran_numeric_equivalence"]=="NOT_ESTABLISHED"
    assert result.provenance()["production_runtime_activated"] is False


@pytest.mark.parametrize("air", [0., 25., 100., 250.])
def test_root_sensitivity_independent_of_background_air_hto(air):
    result=diagnose_kfk5194_1993_root_mixing_sensitivity(**_case(air=air))
    ref=diagnose_kfk5194_1993_root_mixing_sensitivity(**_case(air=0.))
    assert result.root_layer_final_activity_sensitivity_kg_m2_ground == pytest.approx(
        ref.root_layer_final_activity_sensitivity_kg_m2_ground, rel=1e-13
    )


def test_air_tangent_and_initial_inventory_memory_match_black_box():
    args=_case()
    diagnostic=diagnose_kfk5194_1993_root_mixing_sensitivity(**args)
    baseline=_final_activity(args)
    changed_air=replace(
        args["forcing"],
        air_hto_concentration_bq_m3=args["forcing"].air_hto_concentration_bq_m3+3.,
    )
    air_response=(_final_activity({**args,"forcing":changed_air})-baseline)/3.
    assert air_response==pytest.approx(
        diagnostic.air_hto_final_activity_sensitivity_m,rel=1e-11
    )
    changed_state=replace(
        args["state"],
        tfwt_inventory_bq_m2=args["state"].tfwt_inventory_bq_m2+15.,
        tfwt_concentration_bq_kg_water=(
            args["state"].tfwt_concentration_bq_kg_water+5.
        ),
    )
    initial_response=(
        _final_activity({**args,"state":changed_state})-baseline
    )/15.
    assert initial_response==pytest.approx(
        diagnostic.initial_hto_memory_fraction,rel=1e-11
    )
    a=diagnostic.baseline.leaf_water_hto_step.belot_exchange_water_equivalent_kg_m2_ground_s
    assert diagnostic.initial_hto_memory_fraction==pytest.approx(
        math.exp(-a*args["forcing"].interval_seconds/3.)
    )


def test_small_time_root_sensitivity_approaches_source_mass_flux():
    args=_case(dt=1e-3)
    x=diagnose_kfk5194_1993_root_mixing_sensitivity(**args)
    R=args["forcing"].root_water_delivery_kg_m2_ground_s
    for value, weight in zip(x.root_layer_final_activity_sensitivity_kg_m2_ground,
                              (0.2,0.4,0.4)):
        assert value == pytest.approx(R*weight*1e-3, rel=1e-7,abs=1e-14)


def test_cannot_diagnose_implicit_or_unverified_research_selection():
    args=_case()
    for key,bad in (
        ("mixing_hypothesis",None),
        ("mixing_hypothesis","INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH"),
        ("leaf_hypothesis","BELOT_COMPOSITE_FIXED_LEAF_WATER"),
        ("plant_group","AGRICULTURAL_PLANT"),
    ):
        with pytest.raises(KFK5194WaterActivityError):
            diagnose_kfk5194_1993_root_mixing_sensitivity(
                **{**args,key:bad}
            )


def test_legacy_config_and_cli_remain_disconnected_from_sensitivity_module():
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_root_mixing_sensitivity" not in (
            ROOT/path
        ).read_text(encoding="utf-8")
