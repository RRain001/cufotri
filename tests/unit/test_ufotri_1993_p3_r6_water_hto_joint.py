"""P3 R6 scientific discrimination: no double-counted Belot transpiration loss.

Official KfK5194 (1993) p.7: leaf Belot re-emission already contains
tritium lost through transpiration; plant ET drives p.6 root-water
replacement. Tests verify the printed p.3 Eq.(3), not just self-consistent
bookkeeping of an invented second -E*C sink.
"""
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
HYPOTHESIS = Hypothesis.BELOT_COMPOSITE_FIXED_LEAF_WATER


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
        plant_identifier="P3R6-ORIGINAL-EQ3",
        crop="synthetic", growth_stage="synthetic",
        tfwt_inventory_bq_m2=water * conc,
        water_content_kg_m2=water,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        area_basis=area,
        provenance=ForcingProvenance(
            source_id="P3R6_DISCRIMINATING_ORACLE", source_version="R2",
            artifact_sha256="e" * 64, spatial_reference="ground-area-leaf-only",
            temporal_resolution_s=3600,
        ),
    )


def _forcing(canopy=None, air=100.0, root=None, root_c=0.0,
             dt=3600.0, net=300.0):
    c = _canopy() if canopy is None else canopy
    mono = _monteith(c, net=net)
    return KFK5194WaterActivityForcing(
        monteith=mono,
        air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        root_water_delivery_kg_m2_ground_s=(
            mono.plant_water_flux_kg_m2_s if root is None else root
        ),
        root_water_hto_concentration_bq_kg=root_c,
        interval_seconds=dt,
    )


def _args(**updates):
    canopy = updates.pop("canopy", _canopy())
    values = dict(
        profile=_profile(), canopy=canopy, state=_state(),
        forcing=_forcing(canopy=canopy), hypothesis=HYPOTHESIS,
    )
    values.update(updates)
    return values


def _run(**kwargs):
    return advance_kfk5194_water_hto_joint(**_args(**kwargs))


def test_R_equals_E_uses_plant_not_soil_evaporation_and_closes_both_budgets():
    c = _canopy()
    forcing = _forcing(c, root_c=60)
    x = _run(canopy=c, forcing=forcing)
    E = forcing.monteith.plant_water_flux_kg_m2_s
    assert E > 0
    assert forcing.monteith.soil_water_flux_kg_m2_s > 0
    assert x.initial_leaf_water_kg_m2_ground == 3
    assert x.final_leaf_water_kg_m2_ground == 3
    assert x.root_water_input_kg_m2_ground == pytest.approx(E * 3600)
    assert x.monteith_plant_water_loss_kg_m2_ground == pytest.approx(E * 3600)
    assert x.root_hto_input_bq_m2_ground == pytest.approx(E * 60 * 3600)
    assert x.additional_et_hto_sink_bq_m2_ground == 0.0
    assert x.final_hto_activity_bq_m2_ground == pytest.approx(
        x.initial_hto_activity_bq_m2_ground
        + x.belot_composite_hto_exchange_bq_m2_ground
        + x.root_hto_input_bq_m2_ground, abs=1e-8,
    )
    assert abs(x.water_balance_residual_kg_m2_ground) < 1e-12
    assert abs(x.hto_balance_residual_bq_m2_ground) < 1e-8
    assert x.state.area_basis == "ground_area"
    assert x.state.time == _state().time + timedelta(hours=1)


def test_printed_eq3_zero_air_and_zero_root_activity_even_when_ET_positive():
    c = _canopy()
    f = _forcing(c, air=0.0, root_c=0.0)
    assert f.monteith.plant_water_flux_kg_m2_s > 0
    result = _run(canopy=c, state=_state(conc=100), forcing=f)
    a = 2.0 * 0.017 / (1.1 * 225.0)
    expected_conc = 100 * math.exp(-a * 3600.0 / 3.0)
    assert result.state.tfwt_concentration_bq_kg_water == pytest.approx(
        expected_conc, rel=1e-12,
    )
    assert result.belot_composite_hto_exchange_bq_m2_ground < 0
    assert result.belot_composite_hto_exchange_bq_m2_ground == pytest.approx(
        3 * (expected_conc - 100), abs=1e-9,
    )
    assert result.root_hto_input_bq_m2_ground == 0
    assert result.additional_et_hto_sink_bq_m2_ground == 0
    assert result.hto_balance_residual_bq_m2_ground == pytest.approx(0, abs=1e-9)


def test_ET_perturbation_must_NOT_add_second_isotope_decay_at_fixed_belot_rate():
    c = _canopy()
    low = _run(canopy=c, state=_state(conc=100),
               forcing=_forcing(c, air=0, root_c=0, net=0))
    high_f = _forcing(c, air=0, root_c=0, net=600)
    high = _run(canopy=c, state=_state(conc=100), forcing=high_f)
    assert high_f.monteith.plant_water_flux_kg_m2_s > (
        _forcing(c, air=0, net=0).monteith.plant_water_flux_kg_m2_s
    )
    assert high.state.tfwt_inventory_bq_m2 == pytest.approx(
        low.state.tfwt_inventory_bq_m2, rel=1e-12,
    )
    assert high.belot_composite_hto_exchange_bq_m2_ground == pytest.approx(
        low.belot_composite_hto_exchange_bq_m2_ground, rel=1e-12,
    )
    a = 2 * 0.017 / (1.1 * 225)
    incorrect_double_count = 300 * math.exp(
        -(a + high_f.monteith.plant_water_flux_kg_m2_s) * 3600 / 3
    )
    assert high.final_hto_activity_bq_m2_ground > incorrect_double_count
    assert high.additional_et_hto_sink_bq_m2_ground == 0


def test_explicit_root_HTO_added_once_and_independent_equilibrium_oracle():
    c = _canopy()
    root_c = 50.0
    f = _forcing(c, root_c=root_c)
    result = _run(canopy=c, forcing=f)
    a = 2 * 0.017 / (1.1 * 225)
    Ceq = 1.1 * 100 / 0.017
    Cstar = Ceq + f.root_water_delivery_kg_m2_ground_s * root_c / a
    expected = Cstar + (12 - Cstar) * math.exp(-a * 3600 / 3)
    assert result.state.tfwt_concentration_bq_kg_water == pytest.approx(
        expected, rel=1e-12,
    )
    assert result.root_hto_input_bq_m2_ground == pytest.approx(
        f.root_water_delivery_kg_m2_ground_s * root_c * 3600,
    )
    assert result.hto_balance_residual_bq_m2_ground == pytest.approx(0, abs=1e-8)


def test_zero_ET_and_root_reduces_exactly_to_prior_printed_1993_leaf_equations():
    c = _canopy(vpd=0)
    f = _forcing(c, net=0)
    assert f.monteith.plant_water_flux_kg_m2_s == 0
    result = _run(canopy=c, forcing=f)
    direct = advance_kfk5194_ground_leaf_budget(
        profile=_profile(), state=_state(),
        exposure=KFK5194LeafInterval(
            canopy=c, air_hto_concentration_bq_m3=100,
            saturated_vapour_density_kg_m3=0.017,
            isotope_fractionation_liquid_to_vapour=1.1,
            interval_seconds=3600,
        ),
        fixed_lai=2,
        water_pool=KFK5194GroundWaterPool.LEAF_WATER_ONLY,
    )
    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(
        direct.state.tfwt_inventory_bq_m2, rel=1e-12
    )
    assert result.belot_composite_hto_exchange_bq_m2_ground == pytest.approx(
        direct.ground_transfer_bq_m2, rel=1e-12,
    )


def test_small_time_derivative_for_composite_belot_plus_root_activity_only():
    c = _canopy()
    f = _forcing(c, root_c=80, dt=0.001)
    out = _run(canopy=c, forcing=f)
    a = 2 * 0.017 / (1.1 * 225)
    Ceq = 1.1 * 100 / 0.017
    initial_dIdt = a * (Ceq - 12) + f.root_water_delivery_kg_m2_ground_s * 80
    assert out.final_hto_activity_bq_m2_ground - 36 == pytest.approx(
        initial_dIdt * 0.001, rel=5e-6, abs=1e-10
    )
    assert out.final_leaf_water_kg_m2_ground == 3


def test_two_half_hours_preserve_concentration_and_component_Hto_budgets():
    c = _canopy()
    f = _forcing(c, root_c=200)
    once = _run(canopy=c, forcing=f)
    first = _run(canopy=c, forcing=replace(f, interval_seconds=1800))
    second = _run(canopy=c, state=first.state,
                  forcing=replace(f, interval_seconds=1800))
    assert second.state.tfwt_inventory_bq_m2 == pytest.approx(
        once.state.tfwt_inventory_bq_m2, rel=1e-12
    )
    assert second.state.water_content_kg_m2 == 3
    assert (first.belot_composite_hto_exchange_bq_m2_ground
            + second.belot_composite_hto_exchange_bq_m2_ground) == pytest.approx(
                once.belot_composite_hto_exchange_bq_m2_ground, rel=1e-11
            )
    assert first.root_hto_input_bq_m2_ground + second.root_hto_input_bq_m2_ground == pytest.approx(
        once.root_hto_input_bq_m2_ground, rel=1e-12
    )


def test_nonzero_ET_without_matching_root_water_must_fail_closed():
    c = _canopy()
    no_root = _forcing(c, root=0.0)
    assert no_root.monteith.plant_water_flux_kg_m2_s > 0
    with pytest.raises(KFK5194WaterActivityError, match="R=Monteith E"):
        _run(canopy=c, forcing=no_root)
    with pytest.raises(KFK5194WaterActivityError, match="R=Monteith E"):
        _run(canopy=c, forcing=_forcing(c, root=1e-3))


@pytest.mark.parametrize("field,value", [
    ("root_water_delivery_kg_m2_ground_s", -1),
    ("root_water_delivery_kg_m2_ground_s", float("nan")),
    ("root_water_hto_concentration_bq_kg", -1),
    ("air_hto_concentration_bq_m3", -1),
    ("saturated_vapour_density_kg_m3", 0),
    ("isotope_fractionation_liquid_to_vapour", 0),
    ("interval_seconds", 0),
    ("interval_seconds", float("inf")),
])
def test_invalid_forcing_fails_closed(field, value):
    f = replace(_forcing(), **{field: value})
    with pytest.raises(KFK5194WaterActivityError):
        _run(forcing=f)


def test_profile_area_hypothesis_monteith_lai_et_basis_fail_closed():
    c = _canopy()
    with pytest.raises(KFK5194WaterActivityError):
        _run(state=_state(area="plant_area"))
    with pytest.raises(KFK5194WaterActivityError):
        _run(profile=replace(_profile(), profile_id="KFK4605_1990"))
    with pytest.raises(KFK5194WaterActivityError):
        _run(hypothesis="BELOT_COMPOSITE_FIXED_LEAF_WATER")
    with pytest.raises(KFK5194WaterActivityError):
        _run(forcing=replace(_forcing(), monteith=replace(
            _monteith(c), soil_radiation_w_m2=1000
        )))
    with pytest.raises(KFK5194WaterActivityError):
        _run(forcing=replace(_forcing(), monteith=replace(
            _monteith(c), plant_water_flux_kg_m2_s=1
        )))
    # Radiative LAI attached to a different canopy is disallowed.
    other = _canopy(vpd=10)
    other_result = _monteith(other)
    with pytest.raises(KFK5194WaterActivityError):
        _run(canopy=replace(c, leaf_area_index=3), forcing=replace(
            _forcing(), monteith=other_result
        ))


def test_source_scope_and_no_legacy_runtime_change():
    r = _run()
    meta = r.provenance()
    assert meta["belot_hto_loss_already_includes_transpiration"] is True
    assert meta["extra_transpiration_hto_sink"] == "PROHIBITED_TO_PREVENT_DOUBLE_COUNT"
    assert meta["dynamic_water_mass"] == "REJECTED_NOT_SOURCE_QUALIFIED"
    assert meta["original_fortran_water_mass_coupling"] == "NOT_ESTABLISHED"
    assert meta["whole_1993_solver_runtime_activated"] is False
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
        "src/cteas_ufotri/plant/kfk5194_1993_ground_leaf_budget.py",
    ):
        assert "kfk5194_1993_water_hto_joint" not in (
            ROOT / path
        ).read_text(encoding="utf-8")
