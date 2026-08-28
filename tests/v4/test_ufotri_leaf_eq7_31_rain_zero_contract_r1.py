import math

import pytest

from cteas_ufotri.plant.leaf_ufotri_v4 import (
    build_ufotri_eq7_25_manual_resistance_state,
    ufotri_eq27_30_analytic_interval_transfer,
)


def _build(*, precipitation_m_s: float):
    return build_ufotri_eq7_25_manual_resistance_state(
        lai=2.0,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=precipitation_m_s,
        stomatal_resistance_day_s_m=100.0,
        stomatal_resistance_night_s_m=1500.0,
        station_wind_speed_m_s=5.0,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.2,
        canopy_height_m=2.0,
        explicit_monin_obukhov_length_m=math.inf,
        monin_obukhov_source_id="MANUAL_TEST_NEUTRAL",
        monin_obukhov_source_version="r1",
    )


def test_dry_manual_state_projects_exactly_to_frozen_rc1_chain():
    state = _build(precipitation_m_s=0.0)
    assert state.canopy_resistance_s_m == pytest.approx(50.0)
    assert state.rc1_projection_available is True
    chain = state.as_rc1_resistance_chain()
    assert chain.aerodynamic_resistance == pytest.approx(
        state.aerodynamic_resistance_s_m
    )
    assert chain.boundary_layer_resistance == pytest.approx(
        state.boundary_layer_resistance_s_m
    )
    assert chain.canopy_resistance == pytest.approx(state.canopy_resistance_s_m)
    assert chain.total_resistance == pytest.approx(state.total_resistance_s_m)


def test_daytime_rain_keeps_exact_zero_and_refuses_epsilon_rc1_projection():
    state = _build(precipitation_m_s=1.0e-6)
    assert state.canopy_resistance_s_m == 0.0
    assert state.total_resistance_s_m == pytest.approx(
        state.aerodynamic_resistance_s_m + state.boundary_layer_resistance_s_m
    )
    assert state.exchange_velocity_m_s == pytest.approx(
        1.0 / state.total_resistance_s_m
    )
    assert state.rc1_projection_available is False
    with pytest.raises(ValueError, match="no epsilon substitution"):
        state.as_rc1_resistance_chain()


def test_daytime_rain_total_resistance_remains_usable_by_analytic_eq27_30_path():
    state = _build(precipitation_m_s=1.0e-6)
    transfer = ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=100.0,
        initial_tfwt_concentration_bq_kg_water=10.0,
        plant_water_content_kg_m2=1.5,
        temperature_k=293.15,
        total_resistance_s_m=state.total_resistance_s_m,
        isotope_fractionation_liquid_to_vapour=1.1,
        interval_seconds=3600.0,
    )
    assert transfer.exchange_rate_constant_s_1 > 0.0
    assert transfer.leaf_transfer_bq_m2 > 0.0
