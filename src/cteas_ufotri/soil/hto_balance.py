from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SoilHTOFluxes:
    deposition_bq_m2_s: float
    evaporation_bq_m2_s: float
    root_uptake_bq_m2_s: float
    drainage_bq_m2_s: float
    decay_bq_m2_s: float


def concentration_bq_m3(inventory_bq_m2: float, water_m: float, epsilon_m: float) -> float:
    return max(inventory_bq_m2, 0.0) / max(water_m, epsilon_m)


def limit_inventory_outflows(
    inventory: float, dt_s: float, **rates: float
) -> dict[str, float]:
    positive = {key: max(value, 0.0) for key, value in rates.items()}
    total = sum(positive.values())
    maximum = max(inventory, 0.0) / dt_s
    scale = min(1.0, maximum / total) if total > 0 else 1.0
    return {key: value * scale for key, value in positive.items()}
