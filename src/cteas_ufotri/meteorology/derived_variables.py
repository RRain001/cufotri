from __future__ import annotations

import numpy as np


def kelvin_to_celsius(temperature_k):
    return np.asarray(temperature_k, dtype=float) - 273.15


def saturation_vapour_pressure_pa(temperature_k):
    t_c = kelvin_to_celsius(temperature_k)
    return 610.78 * np.exp(17.2694 * t_c / (t_c + 237.29))


def relative_humidity(temperature_k, dewpoint_k):
    rh = saturation_vapour_pressure_pa(dewpoint_k) / saturation_vapour_pressure_pa(temperature_k)
    return np.clip(rh, 0.0, 1.0)


def vapour_pressure_deficit_pa(temperature_k, dewpoint_k):
    return np.maximum(
        saturation_vapour_pressure_pa(temperature_k)
        - saturation_vapour_pressure_pa(dewpoint_k),
        0.0,
    )


def saturation_curve_slope_pa_k(temperature_k):
    t_c = kelvin_to_celsius(temperature_k)
    es = saturation_vapour_pressure_pa(temperature_k)
    return 4098.0 * es / (t_c + 237.29) ** 2


def wind_speed_direction(u_m_s, v_m_s):
    u = np.asarray(u_m_s, dtype=float)
    v = np.asarray(v_m_s, dtype=float)
    speed = np.hypot(u, v)
    direction_from_deg = (270.0 - np.degrees(np.arctan2(v, u))) % 360.0
    return speed, direction_from_deg


def wind_speed_at_height(speed_ref_m_s, height_m, reference_height_m=10.0, exponent=0.2):
    if height_m <= 0 or reference_height_m <= 0:
        raise ValueError("Wind heights must be positive")
    return np.asarray(speed_ref_m_s, dtype=float) * (height_m / reference_height_m) ** exponent


def accumulated_to_flux(accumulated_j_m2, interval_seconds):
    if interval_seconds <= 0:
        raise ValueError("Accumulation interval must be positive")
    return np.asarray(accumulated_j_m2, dtype=float) / interval_seconds


def net_radiation_w_m2(net_solar_j_m2, net_thermal_j_m2, interval_seconds):
    """ERA5 net components are positive downward; convert accumulated J/m2 to W/m2."""
    return accumulated_to_flux(
        np.asarray(net_solar_j_m2) + np.asarray(net_thermal_j_m2),
        interval_seconds,
    )
