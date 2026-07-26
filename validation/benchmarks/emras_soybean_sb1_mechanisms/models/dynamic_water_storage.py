from __future__ import annotations

import math


MECHANISM_ID = "H1_DYNAMIC_WATER_STORAGE"
NEW_FITTED_PARAMETER_COUNT = 0
EXPOSURE_WATER_STORAGE_M = 0.0007882
HARVEST_WATER_STORAGE_M = 0.0026568


def water_storage_m(
    elapsed_since_exposure_end_s: float,
    total_growth_duration_s: float,
    shape: str = "LINEAR_EXPOSURE_TO_HARVEST",
) -> float:
    fraction = min(
        max(float(elapsed_since_exposure_end_s) / total_growth_duration_s, 0.0),
        1.0,
    )
    if shape == "LINEAR_EXPOSURE_TO_HARVEST":
        shaped = fraction
    elif shape == "SQRT_TIME_EXPOSURE_TO_HARVEST":
        shaped = math.sqrt(fraction)
    else:
        raise ValueError(f"Unsupported storage shape: {shape}")
    return EXPOSURE_WATER_STORAGE_M + shaped * (
        HARVEST_WATER_STORAGE_M - EXPOSURE_WATER_STORAGE_M
    )


def concentration_bq_l(
    inventory_bq_m2: float,
    elapsed_since_exposure_end_s: float,
    total_growth_duration_s: float,
    shape: str = "LINEAR_EXPOSURE_TO_HARVEST",
) -> float:
    storage = water_storage_m(
        elapsed_since_exposure_end_s, total_growth_duration_s, shape
    )
    return max(float(inventory_bq_m2), 0.0) / storage / 1000.0
