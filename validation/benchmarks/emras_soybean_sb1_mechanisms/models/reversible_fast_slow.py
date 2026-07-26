from __future__ import annotations

from dataclasses import dataclass


MECHANISM_ID = "H3_REVERSIBLE_FAST_SLOW_EXCHANGE"
NEW_FITTED_PARAMETER_COUNT = 2


@dataclass(frozen=True)
class TransferResult:
    fast_inventory_bq_m2: float
    slow_inventory_bq_m2: float
    fast_to_slow_bq_m2: float
    slow_to_fast_bq_m2: float
    slow_decay_bq_m2: float
    internal_transfer_residual_bq_m2: float


def transfer(
    fast_inventory_bq_m2: float,
    slow_inventory_bq_m2: float,
    fast_to_slow_rate_s: float,
    slow_to_fast_rate_s: float,
    decay_constant_s: float,
    dt_s: float,
) -> TransferResult:
    fast_before = max(float(fast_inventory_bq_m2), 0.0)
    slow_before = max(float(slow_inventory_bq_m2), 0.0)
    fast_to_slow = min(
        fast_before,
        max(float(fast_to_slow_rate_s), 0.0) * fast_before * dt_s,
    )
    slow_to_fast = min(
        slow_before,
        max(float(slow_to_fast_rate_s), 0.0) * slow_before * dt_s,
    )
    fast_after_transfer = fast_before - fast_to_slow + slow_to_fast
    slow_after_transfer = slow_before + fast_to_slow - slow_to_fast
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
        fast_to_slow_bq_m2=fast_to_slow,
        slow_to_fast_bq_m2=slow_to_fast,
        slow_decay_bq_m2=slow_decay,
        internal_transfer_residual_bq_m2=transfer_residual,
    )
