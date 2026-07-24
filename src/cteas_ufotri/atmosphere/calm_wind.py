from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CalmWindResolution:
    raw_wind_speed_m_s: float
    effective_wind_speed_m_s: float
    applied: bool
    skip_gaussian: bool


def resolve_calm_wind(raw_wind_speed_m_s: float, config: dict) -> CalmWindResolution:
    """Apply the configured explicit policy before any Gaussian calculation."""
    raw = float(raw_wind_speed_m_s)
    if not math.isfinite(raw) or raw < 0:
        raise ValueError("Wind speed must be finite and non-negative")
    threshold = float(config["threshold_m_s"])
    effective = float(config["effective_wind_m_s"])
    if threshold <= 0 or effective <= 0:
        raise ValueError("Calm-wind threshold and effective speed must be positive")
    if raw >= threshold:
        return CalmWindResolution(raw, raw, False, False)
    mode = config["mode"]
    if mode == "minimum_effective_wind":
        return CalmWindResolution(raw, max(raw, effective), True, False)
    if mode == "skip_gaussian":
        return CalmWindResolution(raw, effective, True, True)
    if mode == "error":
        raise ValueError(
            f"Calm wind {raw:g} m/s is below threshold {threshold:g} m/s"
        )
    raise ValueError(f"Unsupported calm-wind mode: {mode}")
