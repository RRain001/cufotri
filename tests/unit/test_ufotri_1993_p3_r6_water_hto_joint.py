"""P3 R6 independent exact water and signed HTO budget tests."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import (
    kfk5194_1993_daylight_canopy, kfk5194_1993_monteith_et,
)
from cteas_ufotri.plant.kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis as Hypothesis,
    KFK5194WaterActivityError,
    KFK5194WaterActivityForcing,
    advance_kfk5194_water_hto_joint,
)
from cteas_ufotri.plant.kfk5194_1993_ground_leaf_budget import (
    KFK5194GroundWaterPool, advance_kfk5194_ground_leaf_budget,
)
from cteas_ufotri.plant.kfk5194_1993_leaf_eq1_3 import KFK5194LeafInterval
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile

ROOT = Path(__file__).resolve().parents[2]
ASSUMPTION = Hypothesis.WELL_MIXED_NO_ET_FRACTIONATION


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _canopy(vpd=5.0):
    return kfk5194_1993_daylight_canopy(
        profile=_profile(), regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100,
        radiation_balance_w_m2=300,
        half_response_radiation_w_m2=60,
        vapour_pressure_deficit_hpa=vpd,
        humidity_sensitivity_per_hpa=0.04, soil_water_factor=0.8,
        temperature_c=25, minimum_temperature_c=10,
        optimal_temperature_c=25, maximum_temperature_c=40,
        leaf_area_index=2,
        wind_speed_at_reference_m_s=4, friction_velocity_m_s=0.4,
        stanton_number=0.2,
    )


def _monteith(canopy, net=300.0):
    return kfk5194_1993_monteith_et(
        profile=_profile(), canopy=canopy,
        net_radiation_w_m2=net,
        soil_surface_resistance_s_m=150,
        vapour_pressure_slope_pa_k=180,
        psychrometric_constant_pa_k=65,
        air_volumetric_heat_capacity_j_m3_k=1200,
        latent_heat_vaporization_j_kg=2.45e6,
    )


def _state(water=3.0, conc=12.0, area="ground_area"):
    return TFWTState.from_inventory(
        plant_identifier="P3R6-SYNTH", crop="synthetic-crop",
        growth_stage="synthetic", tfwt_inventory_bq_m2=water*conc,
        water_content_kg_m2=water,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        area_basis=area,
        provenance=ForcingProvenance(
            source_id="P3_R6_SYNTHETIC",
            source_version="water-hto-joint-r1",
            artifact_sha256="d"*64,
            spatial_reference="test-ground-area",
            temporal_resolution_s=3600,
        ),
    )


def _forcing(canopy=None, air=100., root=0., root_c=0., dt=3600., net=300.):
    c = _canopy() if canopy is None else canopy
    return KFK5194WaterActivityForcing(
        monteith=_monteith(c, net=net),
        air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        root_water_delivery_kg_m2_ground_s=root,
        root_water_hto_concentration_bq_kg=root_c,
        interval_seconds=dt,
    )


def _args(**kwargs):
    c = kwargs.pop("canopy", _canopy())
    d = dict(profile=_profile(), canopy=c, state=_state(),
             forcing=_forcing(canopy=c), hypothesis=ASSUMPTION)
    d.update(kwargs)
    return d


def test_monteith_plant_transpiration_and_root_water_mass_budget():
    c = _canopy()
    f = _forcing(canopy=c, root=2e-5, root_c=100.)
    result = advance_kfk5194_water_hto_joint(**_args(canopy=c, forcing=f))
    et = f.monteith.plant_water_flux_kg_m2_s
    assert result.root_water_input_kg_m2_ground == pytest.approx(2e-5*3600)
    assert result.monteith_plant_water_loss_kg_m2_ground == pytest.approx(et*3600)
    assert result.final_leaf_water_kg_m2_ground == pytest.approx(
        3+(2e-5-et)*3600
    )
    assert result.final_hto_activity_bq_m2_ground == pytest.approx(
        36+result.air_leaf_hto_transfer_bq_m2_ground
        +result.root_hto_input_bq_m2_ground
        -result.transpired_hto_loss_bq_m2_ground
    )
    assert abs(result.water_balance_residual_kg_m2_ground) < 1e-10
    assert abs(result.hto_balance_residual_bq_m2_ground) < 1e-8
    assert result.state.tfwt_inventory_bq_m2 == result.final_hto_activity_bq_m2_ground
    assert result.state.area_basis == "ground_area"
    assert result.state.time == _state().time+timedelta(hours=1)
    assert result.provenance()["original_fortran_water_mass_coupling"] == "NOT_ESTABLISHED"
    assert result.provenance()["potential_overlap_of_vapour_exchange_and_transpiration"] == "SCIENTIFIC_REVIEW_REQUIRED"


def test_exact_equal_root_and_et_water_mass_with_independent_solution():
    canopy = _canopy()
    et = _monteith(canopy).plant_water_flux_kg_m2_s
    root_c = 50.
    forcing = _forcing(canopy=canopy, root=et, root_c=root_c)
    actual = advance_kfk5194_water_hto_joint(
        **_args(canopy=canopy, forcing=forcing))
    a = 2*0.017/(1.1*225.)
    ceq = 1.1*100/0.017
    cstar = (a*ceq+et*root_c)/(a+et)
    expected = cstar+(12-cstar)*math.exp(-(a+et)*3600/3)
    assert actual.final_leaf_water_kg_m2_ground == pytest.approx(3)
    assert actual.state.tfwt_concentration_bq_kg_water == pytest.approx(expected)
    assert actual.root_hto_input_bq_m2_ground == pytest.approx(et*root_c*3600)
    assert actual.hto_balance_residual_bq_m2_ground == pytest.approx(0, abs=1e-8)


def test_zero_et_and_root_recovers_direct_1993_p3_r5_leaf_equations():
    c = _canopy(vpd=0)
    zero = _monteith(c, net=0)
    assert zero.plant_water_flux_kg_m2_s == 0
    forcing = _forcing(canopy=c, net=0)
    result = advance_kfk5194_water_hto_joint(
        **_args(canopy=c, forcing=forcing))
    direct = advance_kfk5194_ground_leaf_budget(
        profile=_profile(), state=_state(),
        exposure=KFK5194LeafInterval(
            canopy=c, air_hto_concentration_bq_m3=100,
            saturated_vapour_density_kg_m3=0.017,
            isotope_fractionation_liquid_to_vapour=1.1, interval_seconds=3600,
        ),
        fixed_lai=2,
        water_pool=KFK5194GroundWaterPool.LEAF_WATER_ONLY,
    )
    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(
        direct.state.tfwt_inventory_bq_m2, rel=1e-12
    )
    assert result.air_leaf_hto_transfer_bq_m2_ground == pytest.approx(
        direct.ground_transfer_bq_m2, rel=1e-12
    )
    assert result.monteith_plant_water_loss_kg_m2_ground == 0
    assert result.root_water_input_kg_m2_ground == 0


def test_transpiration_with_no_root_reduces_water_and_removes_mixed_hto():
    c = _canopy()
    x = advance_kfk5194_water_hto_joint(**_args(
        canopy=c, state=_state(conc=100),
        forcing=_forcing(canopy=c, air=0),
    ))
    assert x.final_leaf_water_kg_m2_ground < 3
    assert x.transpired_hto_loss_bq_m2_ground > 0
    assert x.air_leaf_hto_transfer_bq_m2_ground < 0
    assert 0 <= x.final_hto_activity_bq_m2_ground < 300
    assert abs(x.hto_balance_residual_bq_m2_ground) < 1e-8


def test_instantaneous_ode_slope_oracle_for_both_conservation_laws():
    c = _canopy()
    f = _forcing(canopy=c, root=3e-5, root_c=40, dt=0.001)
    actual = advance_kfk5194_water_hto_joint(
        **_args(canopy=c, forcing=f))
    a = 2*0.017/(1.1*225)
    ceq = 1.1*100/0.017
    dI_dt = a*(ceq-12)+3e-5*40-f.monteith.plant_water_flux_kg_m2_s*12
    dW_dt = 3e-5-f.monteith.plant_water_flux_kg_m2_s
    assert actual.final_hto_activity_bq_m2_ground-36 == pytest.approx(
        dI_dt*0.001, rel=5e-6, abs=2e-10
    )
    assert actual.final_leaf_water_kg_m2_ground-3 == pytest.approx(
        dW_dt*0.001, rel=1e-6, abs=1e-12
    )


def test_two_half_steps_match_one_hour_with_constant_mass_forcing():
    c = _canopy()
    root = 2e-5
    one = advance_kfk5194_water_hto_joint(
        **_args(canopy=c, forcing=_forcing(canopy=c, root=root, root_c=200)))
    first = advance_kfk5194_water_hto_joint(
        **_args(canopy=c, forcing=_forcing(canopy=c, root=root, root_c=200, dt=1800)))
    second = advance_kfk5194_water_hto_joint(
        **_args(canopy=c, state=first.state,
                forcing=_forcing(canopy=c, root=root, root_c=200, dt=1800)))
    assert second.state.tfwt_inventory_bq_m2 == pytest.approx(
        one.state.tfwt_inventory_bq_m2, rel=1e-11
    )
    assert second.state.water_content_kg_m2 == pytest.approx(
        one.state.water_content_kg_m2, rel=1e-13
    )
    assert (first.air_leaf_hto_transfer_bq_m2_ground+
            second.air_leaf_hto_transfer_bq_m2_ground) == pytest.approx(
        one.air_leaf_hto_transfer_bq_m2_ground, rel=1e-11
    )
    assert second.state.time == _state().time + timedelta(hours=1)


@pytest.mark.parametrize("field,value", [
    ("root_water_delivery_kg_m2_ground_s",-0.01),
    ("root_water_delivery_kg_m2_ground_s",float("nan")),
    ("root_water_hto_concentration_bq_kg",-1),
    ("air_hto_concentration_bq_m3",-1),
    ("saturated_vapour_density_kg_m3",0),
    ("isotope_fractionation_liquid_to_vapour",0),
    ("interval_seconds",0),
    ("interval_seconds",float("inf")),
])
def test_invalid_external_rates_fail_closed(field,value):
    f = replace(_forcing(), **{field:value})
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(forcing=f))


def test_leaf_water_exhaustion_is_rejected_before_state_mutation():
    c = _canopy()
    with pytest.raises(KFK5194WaterActivityError, match="exhausts leaf water"):
        advance_kfk5194_water_hto_joint(**_args(
            canopy=c, state=_state(water=0.001),
            forcing=_forcing(canopy=c),
        ))


def test_profile_area_hypothesis_monteith_lai_and_ET_basis_fail_closed():
    c = _canopy()
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(
            state=_state(area="plant_area")))
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(
            profile=replace(_profile(), profile_id="KFK4605_1990")))
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(hypothesis="WELL_MIXED_NO_ET_FRACTIONATION"))
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(
            forcing=replace(_forcing(),monteith=replace(
                _monteith(c), soil_radiation_w_m2=1000))))
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(
            forcing=replace(_forcing(),monteith=replace(
                _monteith(c), plant_water_flux_kg_m2_s=1))))
    c_alt = _canopy(vpd=8)
    with pytest.raises(KFK5194WaterActivityError):
        advance_kfk5194_water_hto_joint(**_args(
            canopy=c_alt, forcing=_forcing(canopy=c_alt,
                  net=300) if False else _forcing(canopy=c_alt),
            hypothesis=None,
        ))


def test_opt_in_module_cannot_modify_default_1990_runtime():
    p = advance_kfk5194_water_hto_joint(**_args()).provenance()
    assert p["whole_1993_solver_runtime_activated"] is False
    assert p["soil_root_dynamics_obt_growth"] == "NOT_IMPLEMENTED"
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
        "src/cteas_ufotri/plant/kfk5194_1993_ground_leaf_budget.py",
    ):
        assert "kfk5194_1993_water_hto_joint" not in (
            ROOT/path).read_text(encoding="utf-8")
