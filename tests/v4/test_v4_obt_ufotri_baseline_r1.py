"""V4 UFOTRI OBT baseline R1 tests."""

from __future__ import annotations

import math

from cteas_ufotri.plant.obt_v3 import (
    UFOTRI_OBT_DAYLIGHT_MULTIPLIER,
    UFOTRI_OBT_FORMATION_PER_HOUR,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    UFOTRI_OBT_LOSS_PER_HOUR,
    UFOTRI_OBT_NIGHTTIME_MULTIPLIER,
    ufotri_obt_baseline_parameters,
)


def test_ufotri_direct_rates_are_converted_without_reinterpretation() -> None:
    assert math.isclose(UFOTRI_OBT_FORMATION_PER_HOUR, 0.0006, rel_tol=0.0, abs_tol=0.0)
    assert math.isclose(UFOTRI_OBT_LOSS_PER_HOUR, 0.003, rel_tol=0.0, abs_tol=0.0)
    assert math.isclose(UFOTRI_OBT_KF_S * 3600.0, 0.0006, rel_tol=1e-15)
    assert math.isclose(UFOTRI_OBT_KR_S * 3600.0, 0.003, rel_tol=1e-15)


def test_ufotri_profile_preserves_daily_average_without_invented_day_night_split() -> None:
    params = ufotri_obt_baseline_parameters()
    assert params.kf_s == UFOTRI_OBT_KF_S
    assert params.kr_s == UFOTRI_OBT_KR_S
    assert params.daylight_multiplier == UFOTRI_OBT_DAYLIGHT_MULTIPLIER == 1.0
    assert params.nighttime_multiplier == UFOTRI_OBT_NIGHTTIME_MULTIPLIER == 1.0


def test_ufotri_profile_returns_fresh_immutable_parameter_records() -> None:
    left = ufotri_obt_baseline_parameters()
    right = ufotri_obt_baseline_parameters()
    assert left == right
    assert left is not right
