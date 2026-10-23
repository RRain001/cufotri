"""KfK5194 (1993) P3 R2 night and rain canopy resistance regimes.

Authority: KfK 5194 (1993), section 5.2, printed page 5
(PDF zero-based index 14), with Eqs. (4)-(6), (10) on pp.4-5.

No historical parameter values, exact 'very small' rain resistance, or
original FORTRAN branch logic are inferred. This is an explicit-input
regime calculator independent from the legacy solver and CLI.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, Historical1993SourceProfile,
)
from .kfk5194_1993_canopy_et import (
    KFK5194P3InputError, KFK5194_SOURCE_URL,
)


class KFK5194LeafRegime(str, Enum):
    DAY_RAIN_EXPLICIT_FINITE = "DAY_RAIN_EXPLICIT_FINITE"
    DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT = "DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT"
    NIGHT_DRY_EPIDERMAL = "NIGHT_DRY_EPIDERMAL"
    NIGHT_RAIN_EPIDERMAL = "NIGHT_RAIN_EPIDERMAL"


@dataclass(frozen=True, slots=True)
class KFK5194P3RegimeResistance:
    """Flux-relevant plant/atmosphere resistance in s/m, velocity in m/s."""

    profile_id: str
    regime: KFK5194LeafRegime
    leaf_area_index: float
    reference_dry_day_stomatal_resistance_s_m: float
    leaf_or_epidermal_resistance_s_m: float
    aerodynamic_resistance_s_m: float
    boundary_layer_resistance_s_m: float
    canopy_resistance_s_m: float
    leaf_total_resistance_s_m: float
    canopy_total_resistance_s_m: float
    exchange_velocity_m_s: float
    source_status: str

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KfK 5194 (1993) §5.2, printed page 5 / PDF0 14",
            "equations": ["4", "5", "6", "10"],
            "profile_id": self.profile_id,
            "regime": self.regime.value,
            "parameter_source": "CALLER_EXPLICIT_NO_HISTORICAL_NUMERIC_DEFAULT",
            "rain_zero_limit": (
                "EXPLICIT_ATMOSPHERIC_ONLY_ASYMPTOTIC_APPROXIMATION"
                if self.regime is KFK5194LeafRegime.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT
                else "NOT_USED"
            ),
            "original_executable_equivalence": "NOT_ESTABLISHED",
            "whole_1993_runtime_activated": False,
        }


def _positive(value: float, field: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise KFK5194P3InputError(f"{field} must be a finite numeric SI quantity")
    value = float(value)
    if value <= 0.0:
        raise KFK5194P3InputError(f"{field} must be positive")
    return value


def kfk5194_1993_rain_night_canopy(
    *,
    profile: Historical1993SourceProfile,
    regime: KFK5194LeafRegime,
    reference_dry_day_stomatal_resistance_s_m: float,
    leaf_area_index: float,
    wind_speed_at_reference_m_s: float,
    friction_velocity_m_s: float,
    stanton_number: float,
    wet_day_leaf_resistance_s_m: float | None = None,
    night_epidermal_resistance_s_m: float | None = None,
) -> KFK5194P3RegimeResistance:
    """Build 1993 nighttime/precipitation resistance with explicit evidence gaps.

    The printed manual states that nighttime stomata close, and epidermal
    resistance is at least approximately 10-15 times daytime stomatal
    resistance; nighttime rain does not lower that epidermal resistance.
    For day rain, the manual says stomatal resistance becomes *very small*
    and atmosphere resistance dominates; it does not give a numeric value.

    Thus callers must either explicitly supply a small positive wet-leaf
    resistance, or explicitly select the zero-resistance mathematical LIMIT.
    Neither is claimed as original historical FORTRAN branch logic.
    """
    if not isinstance(profile, Historical1993SourceProfile):
        raise KFK5194P3InputError("explicit loaded typed KfK5194 profile required")
    if (profile.profile_id != PROFILE_ID or profile.source_url != KFK5194_SOURCE_URL
            or dict(profile.flag_defaults).get("IMODEL") != 1):
        raise KFK5194P3InputError("1993 IMODEL=1 source identity required")
    if not isinstance(regime, KFK5194LeafRegime):
        raise KFK5194P3InputError("explicit enumerated night/rain regime required")
    reference = _positive(
        reference_dry_day_stomatal_resistance_s_m,
        "reference_dry_day_stomatal_resistance_s_m",
    )
    lai = _positive(leaf_area_index, "leaf_area_index")
    wind = _positive(wind_speed_at_reference_m_s, "wind_speed_at_reference_m_s")
    ustar = _positive(friction_velocity_m_s, "friction_velocity_m_s")
    stanton = _positive(stanton_number, "stanton_number")

    if regime is KFK5194LeafRegime.DAY_RAIN_EXPLICIT_FINITE:
        if night_epidermal_resistance_s_m is not None:
            raise KFK5194P3InputError("night epidermal resistance is irrelevant by day")
        leaf = _positive(wet_day_leaf_resistance_s_m, "wet_day_leaf_resistance_s_m")
        if leaf >= reference:
            raise KFK5194P3InputError(
                "day-rain leaf resistance must be less than referenced dry-day value"
            )
        source_status = "SOURCE_QUALITATIVE_DAY_RAIN_CALLER_FINITE"
    elif regime is KFK5194LeafRegime.DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT:
        if wet_day_leaf_resistance_s_m is not None or night_epidermal_resistance_s_m is not None:
            raise KFK5194P3InputError("atmospheric-only limit must not hide input resistance")
        leaf = 0.0
        source_status = "SOURCE_LIMITED_DAY_RAIN_ZERO_RESISTANCE_ASYMPTOTIC_LIMIT"
    else:
        if wet_day_leaf_resistance_s_m is not None:
            raise KFK5194P3InputError("wet-day resistance cannot overwrite night epidermis")
        leaf = _positive(
            night_epidermal_resistance_s_m, "night_epidermal_resistance_s_m",
        )
        # The manual says "at least a factor of 10 to 15"; the lower
        # ratio 10 is only an explicit source-consistency screening bound.
        if leaf / reference < 10.0:
            raise KFK5194P3InputError(
                "night epidermal resistance must be at least 10 times dry-day reference"
            )
        source_status = "SOURCE_QUALITATIVE_NIGHT_EPIDERMIS_EXPLICIT_VALUE"

    rav = wind / (ustar * ustar)
    rbv = 1.0 / (ustar * stanton)
    rc = leaf / lai
    total_leaf = leaf + rav + rbv
    total_canopy = rc + rav + rbv
    velocity = 1.0 / total_canopy
    if not all(math.isfinite(v) and v >= 0 for v in (
        rav, rbv, rc, total_leaf, total_canopy, velocity
    )) or total_canopy <= 0:
        raise KFK5194P3InputError("regime resistance or exchange velocity invalid")
    return KFK5194P3RegimeResistance(
        profile_id=PROFILE_ID, regime=regime,
        leaf_area_index=lai,
        reference_dry_day_stomatal_resistance_s_m=reference,
        leaf_or_epidermal_resistance_s_m=leaf,
        aerodynamic_resistance_s_m=rav,
        boundary_layer_resistance_s_m=rbv,
        canopy_resistance_s_m=rc,
        leaf_total_resistance_s_m=total_leaf,
        canopy_total_resistance_s_m=total_canopy,
        exchange_velocity_m_s=velocity,
        source_status=source_status,
    )
