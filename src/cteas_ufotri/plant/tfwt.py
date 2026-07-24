from __future__ import annotations


def plant_concentration_bq_m3(inventory_bq_m2: float, water_storage_m: float) -> float:
    if water_storage_m <= 0:
        raise ValueError("Plant water storage must be positive")
    return max(inventory_bq_m2, 0.0) / water_storage_m


def direct_leaf_flux_bq_m2_s(
    air_concentration_bq_m3: float, velocity_m_s: float, enabled: bool
) -> float:
    return max(air_concentration_bq_m3, 0.0) * max(velocity_m_s, 0.0) if enabled else 0.0
