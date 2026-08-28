"""Manual resistance state for the opt-in UFOTRI leaf compatibility path.

The frozen RC1 ``ResistanceChain`` requires every component to be strictly
positive.  Recoverable UFOTRI canopy semantics, however, set daytime-rain
canopy resistance to exactly zero.  This module keeps that physical/manual zero
explicit and offers RC1 resistance-chain projection only when the frozen
contract can represent the state without numerical substitution.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..leaf_exchange_resistance import ResistanceChain
from .model import (
    UFOTRILeafResistanceResult,
    UFOTRIWindProfileResult,
    manual_canopy_resistance_s_m,
    ufotri_eq21_boundary_resistance_s_m,
    ufotri_eq25_wind_profile,
)


@dataclass(frozen=True)
class UFOTRIManualResistanceState:
    """Manual-faithful ``r_a + r_b + r_c`` state allowing ``r_c == 0``."""

    aerodynamic_resistance_s_m: float
    boundary_layer_resistance_s_m: float
    canopy_resistance_s_m: float
    total_resistance_s_m: float
    exchange_velocity_m_s: float
    wind: UFOTRIWindProfileResult

    @property
    def rc1_projection_available(self) -> bool:
        """Whether the frozen strictly-positive RC1 component contract can encode it."""

        return self.canopy_resistance_s_m > 0.0

    def as_rc1_resistance_chain(self) -> ResistanceChain:
        """Project without approximation when the frozen RC1 contract permits it.

        Daytime rain has ``r_c == 0`` in the recovered manual. RC1 rejects a
        zero component, so this method fails closed for that state rather than
        replacing zero with an arbitrary epsilon.

        RC1's frozen state validator compares ``total_resistance`` against the
        literal left-associative expression ``r_a + r_b + r_c`` using exact
        float equality. Its factory computes the same mathematical sum via
        ``sum(...)``, which can differ by one ulp for valid inputs. This opt-in
        projection therefore constructs the frozen state with the validator's
        exact arithmetic order; no physical value or RC1 source is changed.
        """

        if not self.rc1_projection_available:
            raise ValueError(
                "Frozen RC1 ResistanceChain cannot represent UFOTRI daytime-rain "
                "canopy resistance r_c=0 without changing its contract; no epsilon "
                "substitution is allowed"
            )
        total = (
            self.aerodynamic_resistance_s_m
            + self.boundary_layer_resistance_s_m
            + self.canopy_resistance_s_m
        )
        return ResistanceChain(
            aerodynamic_resistance=self.aerodynamic_resistance_s_m,
            boundary_layer_resistance=self.boundary_layer_resistance_s_m,
            canopy_resistance=self.canopy_resistance_s_m,
            total_resistance=total,
            exchange_velocity=1.0 / total,
        )


def build_ufotri_eq7_25_manual_resistance_state(
    *,
    lai: float,
    is_day: bool,
    soil_available_water_exhausted: bool,
    precipitation_m_s: float,
    stomatal_resistance_day_s_m: float,
    stomatal_resistance_night_s_m: float,
    station_wind_speed_m_s: float,
    station_height_m: float,
    station_to_100m_power_exponent: float,
    canopy_height_m: float,
    explicit_monin_obukhov_length_m: float | None = None,
    monin_obukhov_source_id: str | None = None,
    monin_obukhov_source_version: str | None = None,
    monin_obukhov_estimator_id: str | None = None,
    stability_class: str | None = None,
    von_karman_constant: float = 0.4,
) -> UFOTRIManualResistanceState:
    """Build the complete manual resistance state without altering zero branches."""

    canopy = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=is_day,
        soil_available_water_exhausted=soil_available_water_exhausted,
        precipitation_m_s=precipitation_m_s,
        stomatal_resistance_day_s_m=stomatal_resistance_day_s_m,
        stomatal_resistance_night_s_m=stomatal_resistance_night_s_m,
    )
    wind = ufotri_eq25_wind_profile(
        station_wind_speed_m_s=station_wind_speed_m_s,
        station_height_m=station_height_m,
        station_to_100m_power_exponent=station_to_100m_power_exponent,
        canopy_height_m=canopy_height_m,
        explicit_monin_obukhov_length_m=explicit_monin_obukhov_length_m,
        monin_obukhov_source_id=monin_obukhov_source_id,
        monin_obukhov_source_version=monin_obukhov_source_version,
        monin_obukhov_estimator_id=monin_obukhov_estimator_id,
        stability_class=stability_class,
        von_karman_constant=von_karman_constant,
    )
    boundary = ufotri_eq21_boundary_resistance_s_m(
        wind.friction_velocity_m_s,
        von_karman_constant=von_karman_constant,
    )
    total = wind.aerodynamic_resistance_s_m + boundary + canopy
    if total <= 0.0:
        raise ValueError("UFOTRI total leaf resistance must be positive")
    return UFOTRIManualResistanceState(
        aerodynamic_resistance_s_m=wind.aerodynamic_resistance_s_m,
        boundary_layer_resistance_s_m=boundary,
        canopy_resistance_s_m=canopy,
        total_resistance_s_m=total,
        exchange_velocity_m_s=1.0 / total,
        wind=wind,
    )


def build_ufotri_eq7_25_resistance_chain(**kwargs: object) -> UFOTRILeafResistanceResult:
    """Project a manual state onto RC1 only when RC1 can represent it exactly.

    This is the package-level compatibility builder. It deliberately routes
    through :class:`UFOTRIManualResistanceState`, so the daytime-rain ``r_c=0``
    state fails closed instead of being altered to satisfy RC1.
    """

    state = build_ufotri_eq7_25_manual_resistance_state(**kwargs)
    return UFOTRILeafResistanceResult(
        chain=state.as_rc1_resistance_chain(),
        wind=state.wind,
        canopy_resistance_s_m=state.canopy_resistance_s_m,
        boundary_layer_resistance_s_m=state.boundary_layer_resistance_s_m,
    )


__all__ = [
    "UFOTRIManualResistanceState",
    "build_ufotri_eq7_25_manual_resistance_state",
    "build_ufotri_eq7_25_resistance_chain",
]
