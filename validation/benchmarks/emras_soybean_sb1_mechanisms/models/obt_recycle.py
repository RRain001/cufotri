from __future__ import annotations

from copy import deepcopy
from typing import Any


MECHANISM_ID = "H4_OBT_MEDIATED_RECYCLE"
NEW_FITTED_PARAMETER_COUNT = 2


def apply_multipliers(
    config: dict[str, Any],
    formation_multiplier: float,
    turnover_multiplier: float,
) -> dict[str, Any]:
    if min(formation_multiplier, turnover_multiplier) < 0:
        raise ValueError("OBT multipliers must be non-negative")
    candidate = deepcopy(config)
    candidate["plant"]["obt_formation_rate_s"] *= float(formation_multiplier)
    candidate["plant"]["obt_turnover_rate_s"] *= float(turnover_multiplier)
    return candidate
