"""Independent P3 R3 mixed-edition dynamic TFWT compatibility tests."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import math
from pathlib import Path

import pytest

from cteas_ufotri.plant.kfk5194_1993_canopy_et import kfk5194_1993_daylight_canopy
from cteas_ufotri.plant.kfk5194_1993_canopy_regimes import (
    KFK5194LeafRegime as Regime, kfk5194_1993_rain_night_canopy,
)
from cteas_ufotri.plant.kfk5194_1993_tfwt_compat import (
    KFK5194CouplingError, KFK5194LeafExchangeKernel as Kernel,
    KFK5194TFWTExposure, advance_kfk5194_tfwt_compatibility,
    advance_kfk5194_tfwt_intervals,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "configs/ufotri_1993_manual_source_profile.yaml"
KERNEL = Kernel.KFK4605_EQ27_30_COMPATIBILITY


def _profile():
    return load_1993_source_profile(PATH, selected_profile=PROFILE_ID)


def _state(concentration=20.0, area_basis="ground_area"):
    return TFWTState.from_inventory(
        plant_identifier="SYNTHETIC-P3-R3", crop="test-crop", growth_stage="synthetic",
        tfwt_inventory_bq_m2=concentration * 2.0,
        water_content_kg_m2=2.0,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=ForcingProvenance(
            source_id="P3_R3_SYNTHETIC", source_version="r1",
            artifact_sha256="a" * 64, spatial_reference="synthetic-plot",
            temporal_resolution_s=3600.0,
        ),
        area_basis=area_basis,
    )


def _day(p=None):
    return kfk5194_1993_daylight_canopy(
        profile=p or _profile(), regime="DAYLIGHT_DRY",
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


def _night(regime=Regime.NIGHT_DRY_EPIDERMAL):
    return kfk5194_1993_rain_night_canopy(
        profile=_profile(), regime=regime,
        reference_dry_day_stomatal_resistance_s_m=150.0,
        leaf_area_index=2.0, wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4, stanton_number=0.2,
        night_epidermal_resistance_s_m=1800.0,
    )


def _rain():
    return kfk5194_1993_rain_night_canopy(
        profile=_profile(),
        regime=Regime.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT,
        reference_dry_day_stomatal_resistance_s_m=150.0,
        leaf_area_index=2.0, wind_speed_at_reference_m_s=4.0,
        friction_velocity_m_s=0.4, stanton_number=0.2,
    )


def _exposure(canopy=None, air=20.0, dt=3600.0):
    return KFK5194TFWTExposure(
        canopy=_day() if canopy is None else canopy,
        air_hto_concentration_bq_m3=air,
        temperature_k=293.15,
        isotope_fractionation_liquid_to_vapour=1.1,
        interval_seconds=dt,
    )


def _step(state=None, exposure=None, **kwargs):
    args = dict(
        profile=_profile(),
        state=_state() if state is None else state,
        exposure=_exposure() if exposure is None else exposure,
        kernel=KERNEL,
    )
    args.update(kwargs)
    return advance_kfk5194_tfwt_compatibility(**args)


def test_1993_day_canopy_is_inserted_into_existing_tfwt_analytic_kernel():
    result = _step()
    assert result.canopy_total_resistance_s_m == pytest.approx(131.25)
    assert result.branch == "DAYLIGHT_DRY"
    assert result.leaf_activity_transfer_bq_m2 > 0
    assert result.state.tfwt_inventory_bq_m2 > 40.0
    assert result.residual_bq_m2 == pytest.approx(0.0, abs=1e-8)
    assert (result.state.tfwt_inventory_bq_m2 - 40.0 ==
            pytest.approx(result.leaf_activity_transfer_bq_m2))
    assert result.state.area_basis == "ground_area"
    p = result.provenance()
    assert p["mixed_edition_compatibility_not_1993_numerical_parity"] is True
    assert p["exact_original_1993_leaf_exchange"] == "NOT_ESTABLISHED"
    assert p["whole_1993_runtime_activated"] is False


def test_reemission_is_signed_with_no_negative_inventory():
    result = _step(state=_state(100.0), exposure=_exposure(air=0.0))
    assert result.leaf_activity_transfer_bq_m2 < 0
    assert 0 < result.state.tfwt_inventory_bq_m2 < 200.0
    assert result.state.tfwt_inventory_bq_m2 - 200.0 == pytest.approx(
        result.leaf_activity_transfer_bq_m2
    )
    assert result.residual_bq_m2 == pytest.approx(0.0, abs=1e-8)


def test_1993_canopy_regimes_change_leaf_transfer_rate():
    initial = _state()
    rain = _step(state=initial, exposure=_exposure(canopy=_rain()))
    day = _step(state=initial, exposure=_exposure(canopy=_day()))
    night = _step(state=initial, exposure=_exposure(canopy=_night()))
    assert rain.canopy_total_resistance_s_m < day.canopy_total_resistance_s_m
    assert day.canopy_total_resistance_s_m < night.canopy_total_resistance_s_m
    assert rain.leaf_activity_transfer_bq_m2 > day.leaf_activity_transfer_bq_m2
    assert day.leaf_activity_transfer_bq_m2 > night.leaf_activity_transfer_bq_m2


def test_night_rain_without_changed_canopy_has_identical_tfwt_exchange():
    dry = _step(exposure=_exposure(canopy=_night()))
    wet = _step(exposure=_exposure(
        canopy=_night(Regime.NIGHT_RAIN_EPIDERMAL)))
    assert wet.leaf_activity_transfer_bq_m2 == dry.leaf_activity_transfer_bq_m2
    assert wet.state.tfwt_inventory_bq_m2 == dry.state.tfwt_inventory_bq_m2


def test_multihour_regime_switch_and_integrated_activity_conservation():
    exposures = [
        _exposure(canopy=_day(), air=20.0),
        _exposure(canopy=_night(), air=0.0),
        _exposure(canopy=_rain(), air=8.0),
    ]
    results = advance_kfk5194_tfwt_intervals(
        profile=_profile(), initial_state=_state(),
        exposures=exposures, kernel=KERNEL,
    )
    assert [r.branch for r in results] == [
        "DAYLIGHT_DRY", "NIGHT_DRY_EPIDERMAL",
        "DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT",
    ]
    assert results[-1].state.time == _state().time + timedelta(hours=3)
    assert sum(x.leaf_activity_transfer_bq_m2 for x in results) == pytest.approx(
        results[-1].state.tfwt_inventory_bq_m2 - _state().tfwt_inventory_bq_m2,
        abs=1e-9,
    )
    assert all(abs(x.residual_bq_m2) < 1e-9 for x in results)


def test_interval_split_semigroup_for_constant_conditions():
    whole = _step(exposure=_exposure(dt=3600.0))
    half = advance_kfk5194_tfwt_intervals(
        profile=_profile(), initial_state=_state(),
        exposures=[_exposure(dt=1800.0), _exposure(dt=1800.0)], kernel=KERNEL,
    )
    assert half[-1].state.tfwt_inventory_bq_m2 == pytest.approx(
        whole.state.tfwt_inventory_bq_m2, rel=1e-12)
    assert sum(x.leaf_activity_transfer_bq_m2 for x in half) == pytest.approx(
        whole.leaf_activity_transfer_bq_m2, rel=1e-12)


@pytest.mark.parametrize("change", [
    {"air_hto_concentration_bq_m3": -1.0},
    {"air_hto_concentration_bq_m3": float("nan")},
    {"air_hto_concentration_bq_m3": float("inf")},
    {"temperature_k": 0.0}, {"isotope_fractionation_liquid_to_vapour": 0.0},
    {"interval_seconds": 0.0}, {"interval_seconds": -1.0},
])
def test_nonphysical_interval_forcing_fails_closed(change):
    with pytest.raises(KFK5194CouplingError):
        _step(exposure=replace(_exposure(), **change))


def test_missing_explicit_ground_area_and_invalid_profile_fail_closed():
    with pytest.raises(KFK5194CouplingError, match="ground_area"):
        _step(state=_state(area_basis="plant_area"))
    with pytest.raises(KFK5194CouplingError, match="1993 model identity"):
        _step(profile=replace(_profile(), profile_id="KFK4605_1990"))
    with pytest.raises(KFK5194CouplingError, match="explicit KFK4605"):
        _step(kernel="KFK4605_EQ27_30_COMPATIBILITY")
    with pytest.raises(KFK5194CouplingError):
        _step(exposure=replace(_exposure(), canopy=object()))


def test_no_default_solver_activation_or_mixed_edition_mislabeling():
    for file in (
        "src/cteas_ufotri/config.py", "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py",
        "src/cteas_ufotri/plant/leaf_ufotri_v4/model.py",
    ):
        assert "kfk5194_1993_tfwt_compat" not in (ROOT / file).read_text(encoding="utf-8")
    with pytest.raises(KFK5194CouplingError):
        advance_kfk5194_tfwt_intervals(
            profile=_profile(), initial_state=_state(),
            exposures=[], kernel=KERNEL,
        )
