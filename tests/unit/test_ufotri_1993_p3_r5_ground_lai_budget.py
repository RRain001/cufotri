"""P3 R5 independent area conversion, conservation and non-activation checks."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import kfk5194_1993_daylight_canopy
from cteas_ufotri.plant.kfk5194_1993_canopy_regimes import (
    KFK5194LeafRegime as Regime, kfk5194_1993_rain_night_canopy,
)
from cteas_ufotri.plant.kfk5194_1993_leaf_eq1_3 import KFK5194LeafInterval
from cteas_ufotri.plant.kfk5194_1993_ground_leaf_budget import (
    KFK5194ProjectionError, KFK5194GroundWaterPool as Pool,
    advance_kfk5194_ground_leaf_budget, advance_kfk5194_ground_leaf_intervals,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID, load_1993_source_profile

ROOT = Path(__file__).resolve().parents[2]


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _state(c=12, water=3, basis="ground_area"):
    return TFWTState.from_inventory(
        plant_identifier="P3-R5-SYNTHETIC", crop="test-crop",
        growth_stage="synthetic", tfwt_inventory_bq_m2=water * c,
        water_content_kg_m2=water,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        area_basis=basis,
        provenance=ForcingProvenance(
            source_id="P3_R5_SYNTHETIC", source_version="1993-AREA-AUDIT",
            artifact_sha256="c"*64, spatial_reference="test-m2-ground",
            temporal_resolution_s=3600,
        ),
    )


def _day(lai=2):
    return kfk5194_1993_daylight_canopy(
        profile=_profile(), regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100,
        radiation_balance_w_m2=300, half_response_radiation_w_m2=60,
        vapour_pressure_deficit_hpa=5,
        humidity_sensitivity_per_hpa=0.04, soil_water_factor=0.8,
        temperature_c=25, minimum_temperature_c=10,
        optimal_temperature_c=25, maximum_temperature_c=40,
        leaf_area_index=lai, wind_speed_at_reference_m_s=4,
        friction_velocity_m_s=0.4, stanton_number=0.2,
    )


def _night():
    return kfk5194_1993_rain_night_canopy(
        profile=_profile(), regime=Regime.NIGHT_DRY_EPIDERMAL,
        reference_dry_day_stomatal_resistance_s_m=150,
        night_epidermal_resistance_s_m=1800,
        leaf_area_index=2, wind_speed_at_reference_m_s=4,
        friction_velocity_m_s=0.4, stanton_number=0.2,
    )


def _exp(canopy=None, air=100, dt=3600):
    return KFK5194LeafInterval(
        canopy=_day() if canopy is None else canopy,
        air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=0.017,
        isotope_fractionation_liquid_to_vapour=1.1,
        interval_seconds=dt,
    )


def _args(**changes):
    a = dict(
        profile=_profile(), state=_state(),
        exposure=_exp(), fixed_lai=2,
        water_pool=Pool.LEAF_WATER_ONLY,
    )
    a.update(changes)
    return a


def test_leaf_and_ground_mass_activity_projection_manual_oracle():
    r = advance_kfk5194_ground_leaf_budget(**_args())
    assert r.lai == 2
    assert r.leaf_water_kg_m2_leaf == pytest.approx(1.5)
    assert r.ground_water_kg_m2_ground == pytest.approx(3)
    assert r.leaf_result.state.area_basis == "leaf_area"
    assert r.state.area_basis == "ground_area"
    assert r.leaf_result.total_leaf_resistance_s_m == pytest.approx(225)
    assert r.leaf_result.original_tfwt_concentration_bq_kg_water == 12
    k = 0.017 / (1.1 * 1.5 * 225)
    target = 1.1 * 100 / 0.017
    next_c = target + (12 - target) * math.exp(-k * 3600)
    assert r.state.tfwt_concentration_bq_kg_water == pytest.approx(next_c)
    assert r.state.tfwt_inventory_bq_m2 == pytest.approx(3 * next_c)
    assert r.ground_transfer_bq_m2 == pytest.approx(3*(next_c-12))
    assert r.ground_transfer_bq_m2 == pytest.approx(
        2 * r.leaf_result.signed_leaf_transfer_bq_m2_leaf
    )
    assert r.ground_residual_bq_m2 == pytest.approx(0, abs=1e-9)


def test_signed_leaf_reemission_respects_ground_activity_ledger():
    r = advance_kfk5194_ground_leaf_budget(
        **_args(state=_state(c=100), exposure=_exp(air=0)))
    assert r.ground_transfer_bq_m2 < 0
    assert 0 < r.state.tfwt_inventory_bq_m2 < 300
    assert r.state.tfwt_inventory_bq_m2-300 == pytest.approx(
        r.ground_transfer_bq_m2, abs=1e-9,
    )
    assert r.ground_residual_bq_m2 == pytest.approx(0, abs=1e-9)


def test_lai_unity_is_identity_for_inventory_and_flux():
    r = advance_kfk5194_ground_leaf_budget(**_args(
        exposure=_exp(canopy=_day(lai=1)), fixed_lai=1))
    assert r.leaf_water_kg_m2_leaf == 3
    assert r.ground_transfer_bq_m2 == pytest.approx(
        r.leaf_result.signed_leaf_transfer_bq_m2_leaf
    )
    assert r.state.tfwt_inventory_bq_m2 == pytest.approx(
        r.leaf_result.state.tfwt_inventory_bq_m2
    )


def test_three_hour_canopy_time_advance_and_ground_closure():
    s = _state()
    rs = advance_kfk5194_ground_leaf_intervals(
        profile=_profile(), initial_state=s,
        exposures=[_exp(air=100), _exp(canopy=_night(), air=0), _exp(air=20)],
        fixed_lai=2, water_pool=Pool.LEAF_WATER_ONLY,
    )
    assert len(rs) == 3
    assert rs[-1].state.time == s.time + timedelta(hours=3)
    assert sum(x.ground_transfer_bq_m2 for x in rs) == pytest.approx(
        rs[-1].state.tfwt_inventory_bq_m2-s.tfwt_inventory_bq_m2,
        abs=1e-8,
    )
    assert all(x.ground_water_kg_m2_ground == 3 for x in rs)
    assert all(abs(x.ground_residual_bq_m2) < 1e-8 for x in rs)


def test_split_interval_semigroup_for_constant_canopy():
    whole = advance_kfk5194_ground_leaf_budget(**_args())
    half = advance_kfk5194_ground_leaf_intervals(
        profile=_profile(), initial_state=_state(),
        exposures=[_exp(dt=1800),_exp(dt=1800)],
        fixed_lai=2, water_pool=Pool.LEAF_WATER_ONLY,
    )
    assert half[-1].state.tfwt_inventory_bq_m2 == pytest.approx(
        whole.state.tfwt_inventory_bq_m2, rel=1e-12)


@pytest.mark.parametrize("changes", [
    {"fixed_lai": 0}, {"fixed_lai": -1},
    {"fixed_lai": float("nan")}, {"fixed_lai": float("inf")},
    {"fixed_lai": 1.5}, {"water_pool": "LEAF_WATER_ONLY"},
    {"water_pool": None},
    {"state": _state(basis="plant_area")},
    {"state": _state(basis="leaf_area")},
    {"exposure": _exp(canopy=_day(lai=4))},
])
def test_invalid_lai_or_area_contract_fails_closed(changes):
    with pytest.raises(KFK5194ProjectionError):
        advance_kfk5194_ground_leaf_budget(**_args(**changes))


def test_lai_growth_requires_explicit_growth_mass_budget():
    with pytest.raises(KFK5194ProjectionError, match="LAI mismatch"):
        advance_kfk5194_ground_leaf_intervals(
            profile=_profile(), initial_state=_state(),
            exposures=[_exp(canopy=_day(lai=2)), _exp(canopy=_day(lai=3))],
            fixed_lai=2, water_pool=Pool.LEAF_WATER_ONLY,
        )


def test_wrong_history_and_original_fortran_parity_not_claimed():
    with pytest.raises(ValueError):
        advance_kfk5194_ground_leaf_budget(**_args(
            profile=replace(_profile(), profile_id="KFK4605_1990")
        ))
    p = advance_kfk5194_ground_leaf_budget(**_args()).provenance()
    assert p["original_fortran_projection"] == "NOT_ESTABLISHED"
    assert p["whole_1993_runtime_activated"] is False
    assert p["root_or_monteith_water_mass_coupling"] == "NOT_IMPLEMENTED"
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/kfk5194_1993_leaf_eq1_3.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_ground_leaf_budget" not in (
            ROOT/path).read_text(encoding="utf-8")
