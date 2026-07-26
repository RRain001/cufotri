from __future__ import annotations

from dataclasses import dataclass


MECHANISM_ID = "H2_PARALLEL_FAST_SLOW_RESIDUAL"
NEW_FITTED_PARAMETER_COUNT = 2


@dataclass(frozen=True)
class TransferResult:
    fast_inventory_bq_m2: float
    slow_inventory_bq_m2: float
    capture_bq_m2: float
    release_bq_m2: float
    slow_decay_bq_m2: float
    internal_transfer_residual_bq_m2: float


def transfer(
    fast_inventory_bq_m2: float,
    slow_inventory_bq_m2: float,
    positive_leaf_uptake_bq_m2_s: float,
    slow_capture_fraction: float,
    slow_release_rate_s: float,
    decay_constant_s: float,
    dt_s: float,
) -> TransferResult:
    fast_before = max(float(fast_inventory_bq_m2), 0.0)
    slow_before = max(float(slow_inventory_bq_m2), 0.0)
    capture = min(
        fast_before,
        max(float(slow_capture_fraction), 0.0)
        * max(float(positive_leaf_uptake_bq_m2_s), 0.0)
        * dt_s,
    )
    release = min(
        slow_before,
        max(float(slow_release_rate_s), 0.0) * slow_before * dt_s,
    )
    fast_after_transfer = fast_before - capture + release
    slow_after_transfer = slow_before + capture - release
    transfer_residual = (
        fast_after_transfer + slow_after_transfer - fast_before - slow_before
    )
    slow_decay = min(
        slow_after_transfer,
        max(float(decay_constant_s), 0.0) * slow_after_transfer * dt_s,
    )
    return TransferResult(
        fast_inventory_bq_m2=max(fast_after_transfer, 0.0),
        slow_inventory_bq_m2=max(slow_after_transfer - slow_decay, 0.0),
        capture_bq_m2=capture,
        release_bq_m2=release,
        slow_decay_bq_m2=slow_decay,
        internal_transfer_residual_bq_m2=transfer_residual,
    )
