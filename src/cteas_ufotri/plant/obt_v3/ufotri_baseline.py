"""UFOTRI-derived baseline parameters for the V3/V4 OBT solver.

Only numerical values stated directly in the recovered UFOTRI manual are
admitted here. The manual gives a daily-average OBT uptake rate of 0.06 %/h
of plant HTO and a mean OBT loss rate of 0.3 %/h. It states that daytime
formation is increased and nighttime formation reduced, but does not provide
an unambiguous normalized multiplier pair in the recovered text. Therefore
this baseline preserves the stated daily-average rate with both multipliers
set to 1.0 rather than inventing a split.
"""

from __future__ import annotations

from .obt_solver import OBTParameters


UFOTRI_OBT_FORMATION_PER_HOUR = 0.0006
UFOTRI_OBT_LOSS_PER_HOUR = 0.003
SECONDS_PER_HOUR = 3600.0

UFOTRI_OBT_KF_S = UFOTRI_OBT_FORMATION_PER_HOUR / SECONDS_PER_HOUR
UFOTRI_OBT_KR_S = UFOTRI_OBT_LOSS_PER_HOUR / SECONDS_PER_HOUR

UFOTRI_OBT_DAYLIGHT_MULTIPLIER = 1.0
UFOTRI_OBT_NIGHTTIME_MULTIPLIER = 1.0


def ufotri_obt_baseline_parameters() -> OBTParameters:
    """Return the controlled UFOTRI daily-average OBT parameter profile."""

    return OBTParameters(
        kf_s=UFOTRI_OBT_KF_S,
        kr_s=UFOTRI_OBT_KR_S,
        daylight_multiplier=UFOTRI_OBT_DAYLIGHT_MULTIPLIER,
        nighttime_multiplier=UFOTRI_OBT_NIGHTTIME_MULTIPLIER,
    )


__all__ = [
    "SECONDS_PER_HOUR",
    "UFOTRI_OBT_DAYLIGHT_MULTIPLIER",
    "UFOTRI_OBT_FORMATION_PER_HOUR",
    "UFOTRI_OBT_KF_S",
    "UFOTRI_OBT_KR_S",
    "UFOTRI_OBT_LOSS_PER_HOUR",
    "UFOTRI_OBT_NIGHTTIME_MULTIPLIER",
    "ufotri_obt_baseline_parameters",
]
