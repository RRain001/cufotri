from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WaterBalance:
    water_m: float
    evaporation_m_s: float
    transpiration_m_s: float
    root_uptake_m_s: float
    drainage_m_s: float
    runoff_m_s: float
    residual_m: float


def update_water_bucket(
    water_m: float,
    precipitation_m_s: float,
    requested_evaporation_m_s: float,
    requested_transpiration_m_s: float,
    dt_s: float,
    minimum_water_m: float,
    maximum_water_m: float,
    runoff_enabled: bool = False,
    infiltration_capacity_m_s: float | None = None,
) -> WaterBalance:
    if dt_s <= 0 or maximum_water_m <= minimum_water_m:
        raise ValueError("Invalid water bucket parameters")
    rain = max(precipitation_m_s, 0.0)
    runoff = 0.0
    if runoff_enabled and infiltration_capacity_m_s is not None:
        runoff = max(rain - infiltration_capacity_m_s, 0.0)
        rain -= runoff
    available = water_m + rain * dt_s
    requested = max(requested_evaporation_m_s, 0.0) + max(requested_transpiration_m_s, 0.0)
    allowed = max(available - minimum_water_m, 0.0) / dt_s
    scale = min(1.0, allowed / requested) if requested > 0 else 1.0
    evaporation = max(requested_evaporation_m_s, 0.0) * scale
    transpiration = max(requested_transpiration_m_s, 0.0) * scale
    after_losses = available - (evaporation + transpiration) * dt_s
    drainage = max(after_losses - maximum_water_m, 0.0) / dt_s
    new_water = after_losses - drainage * dt_s
    residual = new_water - (
        water_m + (rain - evaporation - transpiration - drainage) * dt_s
    )
    return WaterBalance(
        new_water, evaporation, transpiration, transpiration, drainage, runoff, residual
    )
