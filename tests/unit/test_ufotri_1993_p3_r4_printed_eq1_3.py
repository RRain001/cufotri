"""Numerical hand-oracles for original printed KfK5194 (1993) Eqs.(1)-(3)."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import kfk5194_1993_daylight_canopy
from cteas_ufotri.plant.kfk5194_1993_canopy_regimes import (
    KFK5194LeafRegime as Regime, kfk5194_1993_rain_night_canopy,
)
from cteas_ufotri.plant.kfk5194_1993_leaf_eq1_3 import (
    KFK5194Eq1To3Error, KFK5194LeafInterval,
    advance_kfk5194_1993_leaf_eq1_to3, advance_kfk5194_1993_leaf_intervals,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _state(conc=0.0, basis="leaf_area"):
    return TFWTState.from_inventory(
        plant_identifier="1993_EQ1TO3_TEST", crop="synthetic", growth_stage="synthetic",
        tfwt_inventory_bq_m2=1.5 * conc,
        water_content_kg_m2=1.5,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=ForcingProvenance(
            source_id="KFK5194_P3_R4_SYNTHETIC", source_version="1993_EQ1_3",
            artifact_sha256="b" * 64,
            spatial_reference="synthetic-m2-leaf",
            temporal_resolution_s=3600.0,
        ),
        area_basis=basis,
    )


def _day():
    return kfk5194_1993_daylight_canopy(
        profile=_profile(), regime="DAYLIGHT_DRY",
        minimum_stomatal_resistance_s_m=100.0,
        radiation_balance_w_m2=300.0,
        half_response_radiation_w_m2=60.0,
        vapour_pressure_deficit_hpa=5.0,
        humidity_sensitivity_per_hpa=0.04,
        soil_water_factor=0.8,
        temperature_c=25.0, minimum_temperature_c=10.0,
        optimal_temperature_c=25.0, maximum_temperature_c=40.0,
        leaf_area_index=2.0, wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4, stanton_number=0.2,
    )


def _regime(regime):
    return kfk5194_1993_rain_night_canopy(
        profile=_profile(), regime=regime,
        reference_dry_day_stomatal_resistance_s_m=150.0,
        leaf_area_index=2.0, wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4, stanton_number=0.2,
        night_epidermal_resistance_s_m=(
            1800.0 if regime in (Regime.NIGHT_DRY_EPIDERMAL,
                                 Regime.NIGHT_RAIN_EPIDERMAL) else None
        ),
    )


def _exposure(canopy=None, air=100.0, rho=0.017, dt=3600.0, alpha=1.1):
    return KFK5194LeafInterval(
        canopy=_day() if canopy is None else canopy,
        air_hto_concentration_bq_m3=air,
        saturated_vapour_density_kg_m3=rho,
        isotope_fractionation_liquid_to_vapour=alpha,
        interval_seconds=dt,
    )


def _step(conc=0.0, exposure=None, state=None, profile=None):
    return advance_kfk5194_1993_leaf_eq1_to3(
        profile=_profile() if profile is None else profile,
        state=_state(conc) if state is None else state,
        exposure=_exposure() if exposure is None else exposure,
    )


def test_printed_eq1_uptake_zero_initial_concentration_independent_oracle():
    r = _step()
    # Eq. (1) pure uptake and Eq. (2) l [s^-1], computed without module helper.
    k = 0.017 / (1.1 * 1.5 * 225.0)
    target = 1.1 * 100.0 / 0.017
    fraction = 1.0 - math.exp(-k * 3600)
    expected = target * fraction
    assert r.total_leaf_resistance_s_m == pytest.approx(225.0)
    assert r.equilibration_rate_s_1 == pytest.approx(k)
    assert r.equilibrium_tfwt_concentration_bq_kg_water == pytest.approx(target)
    assert r.analytic_tfwt_concentration_bq_kg_water == pytest.approx(expected)
    assert r.eq1_zero_initial_uptake_bq_kg_water == pytest.approx(expected)
    assert r.signed_leaf_transfer_bq_m2_leaf == pytest.approx(1.5 * expected)
    assert r.state.tfwt_concentration_bq_kg_water == pytest.approx(expected)
    assert r.activity_balance_residual_bq_m2_leaf == pytest.approx(0.0, abs=1e-9)


def test_printed_eq3_zero_air_loss_recovers_pure_exponential():
    r = _step(conc=100.0, exposure=_exposure(air=0.0))
    k = 0.017 / (1.1 * 1.5 * 225.0)
    expected = 100.0 * math.exp(-k * 3600)
    assert r.analytic_tfwt_concentration_bq_kg_water == pytest.approx(expected)
    assert r.eq3_zero_air_retained_fraction == pytest.approx(
        math.exp(-k * 3600)
    )
    assert r.signed_leaf_transfer_bq_m2_leaf == pytest.approx(
        1.5 * (expected - 100.0)
    )
    assert 0 < r.state.tfwt_inventory_bq_m2 < 150.0
    assert r.activity_balance_residual_bq_m2_leaf == pytest.approx(0.0, abs=1e-9)


def test_superposition_of_published_eq1_and_eq3_with_nonzero_initial():
    initial = 50.0
    exposure = _exposure(air=5.0)
    r = _step(conc=initial, exposure=exposure)
    survival = math.exp(-r.equilibration_rate_s_1 * 3600.0)
    expected = initial * survival + (1 - survival) * (1.1 * 5.0 / 0.017)
    assert r.analytic_tfwt_concentration_bq_kg_water == pytest.approx(expected)
    assert r.state.tfwt_inventory_bq_m2 - 1.5 * initial == pytest.approx(
        r.signed_leaf_transfer_bq_m2_leaf, abs=1e-8
    )


def test_exact_zero_gradient_no_transfer_or_mass_creation():
    original = 1.1 * 100.0 / 0.017
    r = _step(conc=original)
    assert r.signed_leaf_transfer_bq_m2_leaf == pytest.approx(0, abs=1e-12)
    assert r.state.tfwt_inventory_bq_m2 == pytest.approx(1.5 * original)


def test_leaf_area_normalization_rejects_ground_area_without_implicit_lai():
    with pytest.raises(KFK5194Eq1To3Error, match="leaf_area"):
        _step(state=_state(1.0, basis="ground_area"))
    with pytest.raises(KFK5194Eq1To3Error, match="leaf_area"):
        _step(state=_state(1.0, basis="plant_area"))


def test_1993_night_and_wet_leaf_regime_changes_exchange_without_old_kernel():
    rain = _step(exposure=_exposure(
        canopy=_regime(Regime.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT)))
    day = _step()
    night = _step(exposure=_exposure(
        canopy=_regime(Regime.NIGHT_DRY_EPIDERMAL)))
    assert rain.total_leaf_resistance_s_m < day.total_leaf_resistance_s_m
    assert day.total_leaf_resistance_s_m < night.total_leaf_resistance_s_m
    assert rain.signed_leaf_transfer_bq_m2_leaf > day.signed_leaf_transfer_bq_m2_leaf
    assert day.signed_leaf_transfer_bq_m2_leaf > night.signed_leaf_transfer_bq_m2_leaf


def test_night_rain_and_night_dry_same_epidermal_exchange():
    night = _step(exposure=_exposure(
        canopy=_regime(Regime.NIGHT_DRY_EPIDERMAL)))
    wet = _step(exposure=_exposure(
        canopy=_regime(Regime.NIGHT_RAIN_EPIDERMAL)))
    assert night.total_leaf_resistance_s_m == wet.total_leaf_resistance_s_m
    assert night.signed_leaf_transfer_bq_m2_leaf == wet.signed_leaf_transfer_bq_m2_leaf


def test_semigroup_interval_splitting_and_multi_hour_activity_telescope():
    whole = _step(conc=5.0)
    half = advance_kfk5194_1993_leaf_intervals(
        profile=_profile(), initial_state=_state(5.0),
        exposures=[_exposure(dt=1800.0), _exposure(dt=1800.0)],
    )
    assert half[-1].state.tfwt_concentration_bq_kg_water == pytest.approx(
        whole.state.tfwt_concentration_bq_kg_water, rel=1e-12
    )
    multi = advance_kfk5194_1993_leaf_intervals(
        profile=_profile(), initial_state=_state(5.0),
        exposures=[
            _exposure(air=100.0),
            _exposure(canopy=_regime(Regime.NIGHT_DRY_EPIDERMAL), air=0.0),
            _exposure(canopy=_regime(Regime.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT),
                      air=20.0),
        ],
    )
    assert multi[-1].state.time == _state().time + timedelta(hours=3)
    assert sum(x.signed_leaf_transfer_bq_m2_leaf for x in multi) == pytest.approx(
        multi[-1].state.tfwt_inventory_bq_m2 - _state(5.0).tfwt_inventory_bq_m2,
        abs=1e-8,
    )
    assert all(abs(r.activity_balance_residual_bq_m2_leaf) < 1e-8 for r in multi)
    assert all(r.provenance()["whole_1993_solver_activation"] is False for r in multi)


@pytest.mark.parametrize("changes", [
    {"air_hto_concentration_bq_m3": -1.0},
    {"air_hto_concentration_bq_m3": float("nan")},
    {"air_hto_concentration_bq_m3": float("inf")},
    {"saturated_vapour_density_kg_m3": 0.0},
    {"saturated_vapour_density_kg_m3": float("nan")},
    {"isotope_fractionation_liquid_to_vapour": 0.0},
    {"isotope_fractionation_liquid_to_vapour": float("inf")},
    {"interval_seconds": -1.0},
    {"interval_seconds": 0.0},
])
def test_invalid_interval_inputs_fail_closed(changes):
    with pytest.raises(KFK5194Eq1To3Error):
        _step(exposure=replace(_exposure(), **changes))


def test_profile_and_canopy_identity_fail_closed():
    changed = replace(_profile(), profile_id="KFK4605_1990")
    with pytest.raises(KFK5194Eq1To3Error):
        _step(profile=changed)
    with pytest.raises(KFK5194Eq1To3Error):
        _step(exposure=replace(_exposure(), canopy=object()))


def test_no_default_legacy_import_and_no_fortran_parity_claim():
    for path in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/kfk5194_1993_tfwt_compat.py",
        "src/cteas_ufotri/plant/leaf_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
    ):
        assert "kfk5194_1993_leaf_eq1_3" not in (ROOT / path).read_text(encoding="utf-8")
    p = _step().provenance()
    assert p["source"] == "KfK5194_1993_SECTION5_2_PRINTED_P3_PDF0_12"
    assert p["original_1993_fortran_numeric_equivalence"] == "NOT_ESTABLISHED"
    assert p["normalization"] == "PER_LEAF_AREA_NOT_GROUND_AREA"
    assert "KFK4605" not in p["physics_kernel"]
