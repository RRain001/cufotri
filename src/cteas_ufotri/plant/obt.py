from __future__ import annotations


def obt_fluxes_bq_m2_s(
    tfwt_inventory_bq_m2: float,
    obt_inventory_bq_m2: float,
    formation_rate_s: float,
    turnover_rate_s: float,
) -> tuple[float, float]:
    return (
        max(formation_rate_s, 0.0) * max(tfwt_inventory_bq_m2, 0.0),
        max(turnover_rate_s, 0.0) * max(obt_inventory_bq_m2, 0.0),
    )


def day_night_formation_rate_s(
    daily_average_rate_s: float,
    is_day: bool,
    enabled: bool,
    day_multiplier: float,
    night_multiplier: float,
) -> float:
    if min(daily_average_rate_s, day_multiplier, night_multiplier) < 0:
        raise ValueError("OBT formation rates and multipliers must be non-negative")
    if not enabled:
        return daily_average_rate_s
    return daily_average_rate_s * (day_multiplier if is_day else night_multiplier)
