import pytest

from cteas_ufotri.reemission.fluxes import (
    calibrate_ufotri_empirical_reemission,
    ufotri_empirical_soil_reemission_bq_m2_s,
)


def empirical(*, elapsed=0.0, is_day=True, evaporation=2e-8):
    return ufotri_empirical_soil_reemission_bq_m2_s(
        1000.0,
        evaporation,
        0.010,
        0.0,
        elapsed,
        is_day,
        reference_evaporation_m_s=2e-8,
        reference_water_m=0.010,
        radiative_reference_fraction_h=0.10,
        diffusive_fraction_h=0.01,
        zt_half_life_h=24.0,
    )


def test_empirical_day_night_and_zt_behaviour():
    day = empirical(is_day=True)
    night = empirical(is_day=False)
    later = empirical(is_day=True, elapsed=24 * 3600)
    assert day > night > 0
    assert later == day / 2.0


def test_empirical_zero_inventory_or_evaporation_is_finite():
    no_evaporation = empirical(evaporation=0.0)
    assert no_evaporation > 0  # DIFF remains active
    zero = ufotri_empirical_soil_reemission_bq_m2_s(
        0.0, 2e-8, 0.01, 0, 0, True,
        reference_evaporation_m_s=2e-8,
        reference_water_m=0.01,
        radiative_reference_fraction_h=0.1,
        diffusive_fraction_h=0.01,
        zt_half_life_h=24,
    )
    assert zero == 0.0


def test_empirical_calibration_matches_manual_reference_rates():
    calibration = calibrate_ufotri_empirical_reemission(2e-8, 0.01)
    assert calibration.c1_dimensionless * (2e-8 / 0.01) * 3600 == pytest.approx(0.10)
    assert calibration.diffusive_rate_s * 3600 == pytest.approx(0.01)
    assert empirical(is_day=True) == pytest.approx((0.10 + 0.01) / 3600 * 1000.0)
    assert empirical(is_day=False) == pytest.approx(0.01 / 3600 * 1000.0)
