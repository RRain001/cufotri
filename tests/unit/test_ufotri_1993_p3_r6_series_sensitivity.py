"""Black-box oracles for conditional six-hour P3 R6 sensitivity.

These tests diagnose only the opted-in extraction-only instantaneous-mixing
research model, not its physical correctness or original FORTRAN equivalence.
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
)
from cteas_ufotri.plant.kfk5194_1993_soil_root_transfer import (
    KFK5194SoilEvolutionHypothesis as Evolution,
    KFK5194SoilLayerInventoryState,
    advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals,
)
from cteas_ufotri.plant.kfk5194_1993_series_sensitivity import (
    diagnose_kfk5194_1993_series_sensitivity,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis as LeafHyp,
    KFK5194WaterActivityError,
    KFK5194WaterActivityForcing,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState

ROOT = Path(__file__).resolve().parents[2]
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
MIX = Mixing.INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH
LEAF = LeafHyp.BELOT_COMPOSITE_FIXED_LEAF_WATER
SOIL = Evolution.EXTRACTION_ONLY_NO_RECHARGE_RESEARCH


def _case(group=Group.AGRICULTURAL_PLANT):
    profile = load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )
    canopy = kfk5194_1993_daylight_canopy(
        profile=profile, regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.,
        radiation_balance_w_m2=300., half_response_radiation_w_m2=60.,
        vapour_pressure_deficit_hpa=5., humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8, temperature_c=25.,
        minimum_temperature_c=10., optimal_temperature_c=25.,
        maximum_temperature_c=40., leaf_area_index=2.,
        wind_speed_at_reference_m_s=4., friction_velocity_m_s=0.4,
        stanton_number=0.2,
    )
    et = kfk5194_1993_monteith_et(
        profile=profile, canopy=canopy, net_radiation_w_m2=300.,
        soil_surface_resistance_s_m=150., vapour_pressure_slope_pa_k=180.,
        psychrometric_constant_pa_k=65.,
        air_volumetric_heat_capacity_j_m3_k=1200.,
        latent_heat_vaporization_j_kg=2.45e6,
    )
    water = (3., 4., 5.) if group is Group.AGRICULTURAL_PLANT else (3., 4., 0.)
    concentrations = (10., 20., 40.)
    soil = KFK5194SoilLayerInventoryState(
        time=START, plant_group=group, water_kg_m2_ground=water,
        hto_bq_m2_ground=tuple(w*c for w, c in zip(water, concentrations)),
    )
    leaf = TFWTState.from_inventory(
        plant_identifier="R6_SERIES_TANGENT",
        crop="synthetic", growth_stage="fixed",
        tfwt_inventory_bq_m2=36., water_content_kg_m2=3.,
        time=START, area_basis="ground_area",
        provenance=ForcingProvenance(
            source_id="R6_SERIES_TANGENT_ORACLE", source_version="v1",
            artifact_sha256="b"*64, spatial_reference="ground_area",
            temporal_resolution_s=3600.,
        ),
    )
    intervals = tuple(
        KFK5194WaterActivityForcing(
            monteith=et, air_hto_concentration_bq_m3=air,
            saturated_vapour_density_kg_m3=0.017 + (j % 2)*0.001,
            isotope_fractionation_liquid_to_vapour=1.1,
            root_water_delivery_kg_m2_ground_s=et.plant_water_flux_kg_m2_s,
            root_water_hto_concentration_bq_kg=99999.,
            interval_seconds=3600.,
        )
        for j, air in enumerate((0., 100., 35., 0., 125., 0.))
    )
    return dict(
        profile=profile, initial_soil=soil, initial_leaf=leaf,
        canopy=canopy, intervals=intervals, evolution_hypothesis=SOIL,
        root_mixing_hypothesis=MIX, leaf_hypothesis=LEAF,
    )


def _run(args):
    return advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(**args)


@pytest.mark.parametrize("group,weights", [
    (Group.AGRICULTURAL_PLANT, (0.2, 0.4, 0.4)),
    (Group.PASTURE_GRASS, (0.4, 0.6, 0.0)),
])
def test_six_hour_soil_tangents_match_independent_state_perturbations(group, weights):
    args = _case(group)
    tangent = diagnose_kfk5194_1993_series_sensitivity(**args)
    baseline = _run(args)
    assert tangent.baseline == baseline
    assert len(tangent.interval_air_concentration_to_final_leaf_activity_m) == 6
    for i, f in enumerate(weights):
        change = 10.
        stock = list(args["initial_soil"].hto_bq_m2_ground)
        stock[i] += change * args["initial_soil"].water_kg_m2_ground[i]
        perturbed_soil = replace(
            args["initial_soil"], hto_bq_m2_ground=tuple(stock)
        )
        alt = _run({**args, "initial_soil": perturbed_soil})
        leaf_slope = (
            alt.final_leaf.tfwt_inventory_bq_m2 -
            baseline.final_leaf.tfwt_inventory_bq_m2
        ) / change
        soil_slope = (
            alt.final_soil.hto_bq_m2_ground[i] -
            baseline.final_soil.hto_bq_m2_ground[i]
        ) / change
        belot_slope = (
            alt.cumulative_belot_hto_exchange_bq_m2_ground -
            baseline.cumulative_belot_hto_exchange_bq_m2_ground
        ) / change
        assert leaf_slope == pytest.approx(
            tangent.initial_soil_concentration_to_final_leaf_activity_kg_m2_ground[i],
            rel=3e-9, abs=2e-10,
        )
        assert soil_slope == pytest.approx(
            tangent.initial_soil_concentration_to_final_soil_activity_kg_m2_ground[i],
            rel=3e-9, abs=2e-10,
        )
        assert belot_slope == pytest.approx(
            tangent.initial_soil_concentration_to_cumulative_belot_activity_kg_m2_ground[i],
            rel=3e-9, abs=2e-10,
        )
        if f == 0.:
            assert leaf_slope == pytest.approx(0., abs=1e-12)
    assert tangent.provenance()["original_fortran_numeric_equivalence"] == "NOT_ESTABLISHED"
    assert tangent.provenance()["independent_scientific_validation"] == "NOT_ESTABLISHED"
    assert tangent.provenance()["production_runtime_activated"] is False


@pytest.mark.parametrize("j", range(6))
def test_each_hours_air_hto_has_independent_finite_difference_oracle(j):
    args = _case()
    base = _run(args).final_leaf.tfwt_inventory_bq_m2
    delta = 20.
    forcing = list(args["intervals"])
    forcing[j] = replace(
        forcing[j],
        air_hto_concentration_bq_m3=forcing[j].air_hto_concentration_bq_m3+delta,
    )
    trial = _run({**args, "intervals": tuple(forcing)})
    slope = (trial.final_leaf.tfwt_inventory_bq_m2-base)/delta
    model = diagnose_kfk5194_1993_series_sensitivity(**args)
    assert slope == pytest.approx(
        model.interval_air_concentration_to_final_leaf_activity_m[j],
        rel=3e-10, abs=1e-10,
    )


def test_initial_leaf_memory_and_interval_split_analytic_consistency():
    args = _case()
    model = diagnose_kfk5194_1993_series_sensitivity(**args)
    delta = 12.
    before = args["initial_leaf"]
    changed = replace(
        before,
        tfwt_inventory_bq_m2=before.tfwt_inventory_bq_m2 + delta,
        tfwt_concentration_bq_kg_water=(
            before.tfwt_concentration_bq_kg_water + delta / before.water_content_kg_m2
        ),
    )
    base = _run(args).final_leaf.tfwt_inventory_bq_m2
    trial = _run({**args, "initial_leaf": changed})
    assert (trial.final_leaf.tfwt_inventory_bq_m2-base)/delta == pytest.approx(
        model.initial_leaf_activity_memory_fraction, rel=1e-10,
    )
    # Splitting the first fixed-forcing hour preserves response to the
    # initial soil concentrations and initial leaf inventory. Its air
    # derivatives sum because both new half-hours share the same input.
    first = args["intervals"][0]
    halves = (replace(first, interval_seconds=1800.),) * 2
    split = diagnose_kfk5194_1993_series_sensitivity(
        **{**args, "intervals": halves + args["intervals"][1:]}
    )
    assert split.initial_soil_concentration_to_final_leaf_activity_kg_m2_ground == (
        pytest.approx(model.initial_soil_concentration_to_final_leaf_activity_kg_m2_ground, rel=1e-10)
    )
    assert split.initial_leaf_activity_memory_fraction == pytest.approx(
        model.initial_leaf_activity_memory_fraction, rel=1e-12
    )
    assert sum(split.interval_air_concentration_to_final_leaf_activity_m[:2]) == pytest.approx(
        model.interval_air_concentration_to_final_leaf_activity_m[0], rel=1e-12
    )


@pytest.mark.parametrize("field,bad", [
    ("root_mixing_hypothesis", None),
    ("root_mixing_hypothesis", "INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH"),
    ("leaf_hypothesis", "BELOT_COMPOSITE_FIXED_LEAF_WATER"),
    ("evolution_hypothesis", "EXTRACTION_ONLY_NO_RECHARGE_RESEARCH"),
    ("intervals", ()),
])
def test_missing_or_untyped_research_optin_fails_closed(field, bad):
    with pytest.raises(KFK5194WaterActivityError):
        diagnose_kfk5194_1993_series_sensitivity(**{**_case(), field: bad})


def test_numerical_zero_grass_bottom_layer_has_no_sensitivity():
    args = _case(Group.PASTURE_GRASS)
    tangent = diagnose_kfk5194_1993_series_sensitivity(**args)
    assert tangent.initial_soil_concentration_to_final_leaf_activity_kg_m2_ground[2] == 0.
    assert tangent.initial_soil_concentration_to_final_soil_activity_kg_m2_ground[2] == 0.


def test_old_default_entrypoints_do_not_activate_diagnostic():
    for name in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_series_sensitivity" not in (
            ROOT / name
        ).read_text(encoding="utf-8")
