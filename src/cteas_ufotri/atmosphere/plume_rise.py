from __future__ import annotations

import math


def briggs_buoyancy_flux_m4_s3(
    stack_diameter_m: float,
    exit_velocity_m_s: float,
    stack_temperature_k: float,
    ambient_temperature_k: float,
) -> float:
    """Briggs buoyancy-flux parameter for a hot stack."""
    if min(stack_diameter_m, exit_velocity_m_s, stack_temperature_k, ambient_temperature_k) <= 0:
        raise ValueError("Briggs stack and temperature inputs must be positive")
    return (
        9.80665
        * exit_velocity_m_s
        * stack_diameter_m**2
        * max(stack_temperature_k - ambient_temperature_k, 0.0)
        / (4.0 * stack_temperature_k)
    )


def simple_briggs_rise_m(
    stack_diameter_m: float,
    exit_velocity_m_s: float,
    stack_temperature_k: float,
    ambient_temperature_k: float,
    wind_speed_m_s: float,
    downwind_distance_m: float,
) -> float:
    """Distance-dependent neutral/unstable Briggs-class engineering closure.

    The buoyant term follows ``1.6 F_b^(1/3) x^(2/3) / u``. A momentum term
    ``3 d v_s / u`` supplies a finite rise for an isothermal jet. This is an
    explicitly simplified option, not a stability-complete Briggs implementation.
    """
    if wind_speed_m_s <= 0 or downwind_distance_m <= 0:
        return 0.0
    flux = briggs_buoyancy_flux_m4_s3(
        stack_diameter_m,
        exit_velocity_m_s,
        stack_temperature_k,
        ambient_temperature_k,
    )
    buoyant = (
        1.6 * flux ** (1.0 / 3.0) * downwind_distance_m ** (2.0 / 3.0)
        / wind_speed_m_s
        if flux > 0
        else 0.0
    )
    momentum = 3.0 * stack_diameter_m * exit_velocity_m_s / wind_speed_m_s
    return max(buoyant, momentum)


def effective_stack_height_m(
    stack_height_m: float,
    mode: str,
    fixed_rise_m: float,
    *,
    stack_diameter_m: float | None = None,
    exit_velocity_m_s: float | None = None,
    stack_temperature_k: float | None = None,
    ambient_temperature_k: float | None = None,
    wind_speed_m_s: float | None = None,
    downwind_distance_m: float | None = None,
) -> float:
    if stack_height_m <= 0:
        raise ValueError("stack_height_m must be positive")
    if mode == "fixed":
        rise = max(fixed_rise_m, 0.0)
    elif mode == "briggs_simple":
        values = (
            stack_diameter_m,
            exit_velocity_m_s,
            stack_temperature_k,
            ambient_temperature_k,
            wind_speed_m_s,
            downwind_distance_m,
        )
        if any(value is None for value in values):
            raise ValueError("briggs_simple requires stack, ambient, wind, and distance inputs")
        rise = simple_briggs_rise_m(*values)  # type: ignore[arg-type]
    else:
        raise ValueError(f"Unsupported plume rise mode: {mode}")
    return stack_height_m + rise
