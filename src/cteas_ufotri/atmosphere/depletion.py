from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DepletionBudget:
    source_before_bq_s: float
    source_after_bq_s: float
    dry_depletion_bq_s: float
    wet_depletion_bq_s: float


def segment_exponential_depletion(
    source_bq_s: float,
    downwind_m: float,
    effective_wind_m_s: float,
    deposition_velocity_m_s: float,
    mixing_height_m: float,
    segments: int,
    *,
    dry_enabled: bool = True,
    wet_enabled: bool = False,
    wet_scavenging_rate_s: float = 0.0,
) -> DepletionBudget:
    """Engineering source-depletion approximation, not manual Eq. (6) fidelity."""
    if min(effective_wind_m_s, mixing_height_m) <= 0 or segments < 1:
        raise ValueError("Depletion wind, mixing height, and segments must be positive")
    before = max(float(source_bq_s), 0.0)
    if before == 0 or downwind_m <= 0:
        return DepletionBudget(before, before, 0.0, 0.0)
    dry_rate = (
        max(float(deposition_velocity_m_s), 0.0) / mixing_height_m
        if dry_enabled
        else 0.0
    )
    wet_rate = max(float(wet_scavenging_rate_s), 0.0) if wet_enabled else 0.0
    segment_time = downwind_m / segments / effective_wind_m_s
    remaining = before
    dry_loss = 0.0
    wet_loss = 0.0
    total_rate = dry_rate + wet_rate
    for _ in range(segments):
        after = remaining * math.exp(-total_rate * segment_time)
        loss = remaining - after
        if total_rate > 0:
            dry_loss += loss * dry_rate / total_rate
            wet_loss += loss * wet_rate / total_rate
        remaining = after
    return DepletionBudget(before, remaining, dry_loss, wet_loss)
