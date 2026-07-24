from __future__ import annotations

import math


_COEFFICIENTS = {
    "A": (0.22, 0.20, 0.0),
    "B": (0.16, 0.12, 0.0),
    "C": (0.11, 0.08, 0.0002),
    "D": (0.08, 0.06, 0.0015),
    "E": (0.06, 0.03, 0.0003),
    "F": (0.04, 0.016, 0.0003),
}


def rural_pg_sigma(distance_m: float, stability_class: str) -> tuple[float, float]:
    """Turner-style rural Pasquill-Gifford approximation."""
    if distance_m <= 0:
        raise ValueError("Downwind distance must be positive")
    try:
        ay, az, bz = _COEFFICIENTS[stability_class.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported stability class: {stability_class}") from exc
    sigma_y = ay * distance_m / math.sqrt(1.0 + 0.0001 * distance_m)
    sigma_z = az * distance_m / math.sqrt(1.0 + bz * distance_m)
    return sigma_y, sigma_z


def classify_pasquill_gifford(
    wind_speed_m_s: float,
    net_radiation_w_m2: float,
    cloud_cover_fraction: float | None = None,
) -> str:
    """Simple Turner-style rural stability classifier (A through F)."""
    wind = max(wind_speed_m_s, 0.0)
    if net_radiation_w_m2 > 0:
        if net_radiation_w_m2 >= 400:
            column = 0  # strong insolation
        elif net_radiation_w_m2 >= 100:
            column = 1  # moderate
        else:
            column = 2  # slight
        if wind < 2:
            rows = ("A", "A", "B")
        elif wind < 3:
            rows = ("A", "B", "C")
        elif wind < 5:
            rows = ("B", "C", "C")
        elif wind < 6:
            rows = ("C", "D", "D")
        else:
            rows = ("C", "D", "D")
        return rows[column]
    cloud = 0.5 if cloud_cover_fraction is None else min(
        max(cloud_cover_fraction, 0.0), 1.0
    )
    if cloud >= 0.5 or wind >= 5:
        return "D"
    if wind < 2:
        return "F"
    if wind < 3:
        return "E"
    return "D"
