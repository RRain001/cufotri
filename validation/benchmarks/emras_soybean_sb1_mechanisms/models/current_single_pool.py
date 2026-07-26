from __future__ import annotations


MECHANISM_ID = "H0_CURRENT_SINGLE_POOL"
NEW_FITTED_PARAMETER_COUNT = 0


def observed_inventory_bq_m2(fast_inventory_bq_m2: float) -> float:
    """Return the unchanged formal plant TFWT inventory."""
    return max(float(fast_inventory_bq_m2), 0.0)
