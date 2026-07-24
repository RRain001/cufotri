import pytest

from cteas_ufotri.atmosphere.plume_rise import (
    effective_stack_height_m,
    simple_briggs_rise_m,
)


def test_briggs_rise_is_positive_and_temperature_sensitive():
    hot = simple_briggs_rise_m(2.0, 12.0, 373.15, 293.15, 3.0, 1000.0)
    isothermal = simple_briggs_rise_m(2.0, 12.0, 293.15, 293.15, 3.0, 1000.0)
    assert hot > isothermal > 0
    height = effective_stack_height_m(
        70.0,
        "briggs_simple",
        0.0,
        stack_diameter_m=2.0,
        exit_velocity_m_s=12.0,
        stack_temperature_k=373.15,
        ambient_temperature_k=293.15,
        wind_speed_m_s=3.0,
        downwind_distance_m=1000.0,
    )
    assert height == pytest.approx(70.0 + hot)


def test_unknown_plume_mode_fails_explicitly():
    with pytest.raises(ValueError):
        effective_stack_height_m(70.0, "unknown", 0.0)
