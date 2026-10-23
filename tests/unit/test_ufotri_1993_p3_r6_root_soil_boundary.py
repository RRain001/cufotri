"""Original KfK5194 1993 printed p.15 root-layer source-boundary oracles."""
from dataclasses import replace
from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup as Group,
    KFK5194RootMixingHypothesis as Mix,
    kfk5194_1993_root_soil_boundary,
    advance_kfk5194_1993_soil_weighted_root_boundary,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis as LeafHypothesis,
    KFK5194WaterActivityError, KFK5194WaterActivityForcing,
    advance_kfk5194_water_hto_joint,
)
from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    kfk5194_1993_daylight_canopy, kfk5194_1993_monteith_et,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]
MIX = Mix.INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH


def _profile():
    return load_1993_source_profile(
        ROOT/"configs"/"ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _boundary(group=Group.AGRICULTURAL_PLANT, layers=(10.,20.,40.)):
    return kfk5194_1993_root_soil_boundary(
        profile=_profile(), plant_group=group,
        soil_layer_water_hto_bq_kg=layers,
    )


@pytest.mark.parametrize("group,expected_fractions,expected_concentration", [
    (Group.AGRICULTURAL_PLANT, (0.2,0.4,0.4), 26.0),
    (Group.PASTURE_GRASS, (0.4,0.6,0.0), 16.0),
])
def test_original_1993_p15_fraction_and_weighted_concentration_oracle(
    group, expected_fractions, expected_concentration
):
    result=_boundary(group)
    assert result.soil_layer_intervals_cm==((0,5),(5,15),(15,30))
    assert result.root_water_fractions==expected_fractions
    assert sum(result.root_water_fractions)==pytest.approx(1.0)
    assert result.effective_root_water_hto_bq_kg==pytest.approx(
        expected_concentration
    )
    assert result.provenance()["root_to_leaf_mixing_rate"]=="NOT_ESTABLISHED"


def test_root_layer_constancy_and_plant_specific_third_layer():
    for kind in Group:
        assert _boundary(kind,(17.,17.,17.)).effective_root_water_hto_bq_kg == (
            pytest.approx(17.0)
        )
    assert _boundary(Group.PASTURE_GRASS, (10.,20.,1e9)).effective_root_water_hto_bq_kg == (
        pytest.approx(16.0)
    )
    assert _boundary(Group.AGRICULTURAL_PLANT, (0.,0.,100.)).effective_root_water_hto_bq_kg == (
        pytest.approx(40.0)
    )


@pytest.mark.parametrize("group,layers", [
    ("AGRICULTURAL_PLANT", (1.,2.,3.)),
    (None, (1.,2.,3.)),
    (Group.AGRICULTURAL_PLANT, (1.,2.)),
    (Group.AGRICULTURAL_PLANT, [1.,2.,3.]),
    (Group.AGRICULTURAL_PLANT, (1.,2.,float("nan"))),
    (Group.PASTURE_GRASS, (1.,2.,float("inf"))),
    (Group.AGRICULTURAL_PLANT, (1.,-1.,3.)),
    (Group.AGRICULTURAL_PLANT, (1.,2.,"3")),
])
def test_invalid_soil_boundaries_fail_closed(group,layers):
    with pytest.raises(KFK5194WaterActivityError):
        _boundary(group,layers)


def test_wrong_1993_profile_cannot_bind_soil_concentration():
    with pytest.raises(KFK5194WaterActivityError):
        kfk5194_1993_root_soil_boundary(
            profile=replace(_profile(),profile_id="KFK4605_1990"),
            plant_group=Group.AGRICULTURAL_PLANT,
            soil_layer_water_hto_bq_kg=(10.,20.,40.),
        )


def _physical_state_and_forcing():
    c = kfk5194_1993_daylight_canopy(
        profile=_profile(),regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.,
        radiation_balance_w_m2=300.,
        half_response_radiation_w_m2=60.,
        vapour_pressure_deficit_hpa=5.,
        humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8,
        temperature_c=25.,minimum_temperature_c=10.,
        optimal_temperature_c=25.,maximum_temperature_c=40.,
        leaf_area_index=2.,wind_speed_at_reference_m_s=4.,
        friction_velocity_m_s=0.4,stanton_number=0.2,
    )
    et = kfk5194_1993_monteith_et(
        profile=_profile(),canopy=c,
        net_radiation_w_m2=300.,soil_surface_resistance_s_m=150.,
        vapour_pressure_slope_pa_k=180.,psychrometric_constant_pa_k=65.,
        air_volumetric_heat_capacity_j_m3_k=1200.,
        latent_heat_vaporization_j_kg=2.45e6,
    )
    state=TFWTState.from_inventory(
        plant_identifier="P3R6-SOIL-ROOT",crop="test-crop",
        growth_stage="synthetic",
        tfwt_inventory_bq_m2=36.,water_content_kg_m2=3.,
        time=datetime(2026,1,1,tzinfo=timezone.utc),
        area_basis="ground_area",
        provenance=ForcingProvenance(
            source_id="KFK5194_R6_ROOT_BOUNDARY",source_version="p15",
            artifact_sha256="f"*64,spatial_reference="synthetic",
            temporal_resolution_s=3600.,
        ),
    )
    forcing=KFK5194WaterActivityForcing(
        monteith=et,air_hto_concentration_bq_m3=100.,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        root_water_delivery_kg_m2_ground_s=et.plant_water_flux_kg_m2_s,
        root_water_hto_concentration_bq_kg=99999.,  # must be replaced
        interval_seconds=3600.,
    )
    return c,state,forcing


@pytest.mark.parametrize("group,layers,expected", [
    (Group.AGRICULTURAL_PLANT,(10.,20.,40.),26.),
    (Group.PASTURE_GRASS,(10.,20.,40.),16.),
])
def test_three_layer_root_boundary_matches_explicit_single_root_forcing(
    group,layers,expected
):
    c,state,forcing=_physical_state_and_forcing()
    wrapped=advance_kfk5194_1993_soil_weighted_root_boundary(
        profile=_profile(),plant_group=group,
        soil_layer_water_hto_bq_kg=layers,
        mixing_hypothesis=MIX,
        canopy=c,state=state,forcing=forcing,
        leaf_hypothesis=LeafHypothesis.BELOT_COMPOSITE_FIXED_LEAF_WATER,
    )
    direct=advance_kfk5194_water_hto_joint(
        profile=_profile(),canopy=c,state=state,
        forcing=replace(forcing,root_water_hto_concentration_bq_kg=expected),
        hypothesis=LeafHypothesis.BELOT_COMPOSITE_FIXED_LEAF_WATER,
    )
    step=wrapped.leaf_water_hto_step
    assert wrapped.boundary.effective_root_water_hto_bq_kg==pytest.approx(expected)
    assert step.root_hto_input_bq_m2_ground==pytest.approx(
        expected*forcing.root_water_delivery_kg_m2_ground_s*3600.
    )
    assert step.state.tfwt_inventory_bq_m2==pytest.approx(
        direct.state.tfwt_inventory_bq_m2,rel=1e-12
    )
    assert step.additional_et_hto_sink_bq_m2_ground==0
    assert abs(step.hto_balance_residual_bq_m2_ground)<1e-8
    assert wrapped.provenance()["assumption"]=="SOURCE_LIMITED_INSTANT_MIXING"


def test_coupled_root_boundary_requires_explicit_mixing_and_fixed_water():
    c,state,f=_physical_state_and_forcing()
    args=dict(
        profile=_profile(),plant_group=Group.AGRICULTURAL_PLANT,
        soil_layer_water_hto_bq_kg=(10.,20.,40.),
        canopy=c,state=state,forcing=f,
        leaf_hypothesis=LeafHypothesis.BELOT_COMPOSITE_FIXED_LEAF_WATER,
    )
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_1993_soil_weighted_root_boundary(
            **args,mixing_hypothesis="INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH"
        )
    with pytest.raises(KFK5194WaterActivityError, match="R=Monteith E"):
        advance_kfk5194_1993_soil_weighted_root_boundary(
            **{**args,"forcing":replace(f,root_water_delivery_kg_m2_ground_s=0.0)},
            mixing_hypothesis=MIX,
        )


def test_original_1990_default_is_unmodified():
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_root_soil_boundary" not in (
            ROOT/path
        ).read_text(encoding="utf-8")
