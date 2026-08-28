"""Opt-in UFOTRI cow/milk/beef compatibility path for KfK 4605 Eq. (82)-(105-2).

This module reconstructs the recoverable long-term animal food-chain transfer
roles without modifying the retained V2 animal model or the frozen V4 RC1
endpoint.  Manual rounded daily transfer rates are represented explicitly and
are not renormalized to erase rounding/equilibrium tensions in the manual.

The D4 state is area-normalized activity (Bq m-2) for grass HTO/OBT, cow
HTO/OBT, milk HTO/OBT, and an explicit beef activity receiver.  Atmospheric
cow uptake from Eq. (98) is a distinct animal input and is not public dose.
External V2 project feed/drinking-water assumptions, representative support
area, continuous herd turnover, and edible beef mass are not activated.

The numerical competing-hazard split used here is a post-RC1 implementation
choice.  It is not claimed to reproduce the unavailable original UFOTRI
discretization or executable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math

SECONDS_PER_DAY = 86400.0
MANUAL_REFERENCE_PROFILE = "KFK4605_EQ82_105_2_MANUAL_ROUNDED_R1"
MANUAL_GRASS_SURROGATE_ONLY = "MANUAL_EQ99_GRASS_SURROGATE_ONLY"


class UFOTRIAnimalInputError(ValueError):
    """Fail-closed D4 input/contract error."""


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UFOTRIAnimalInputError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise UFOTRIAnimalInputError(f"{field} must be finite")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise UFOTRIAnimalInputError(f"{field} must be non-negative")
    return result


@dataclass(frozen=True)
class UFOTRICowMilkBeefManualProfile:
    """Manual-rounded Eq. (82)-(105-2) transfer-rate evidence."""

    profile_id: str = MANUAL_REFERENCE_PROFILE

    cow_water_half_time_d: float = 3.5  # Eq. 82
    cow_water_to_atmosphere_d_1: float = 3.0e-2  # Eq. 83
    cow_water_to_soil1_d_1: float = 1.3e-1  # Eq. 84

    grass_obt_to_milk_obt_d_1: float = 1.7e-3  # Eq. 85
    cow_obt_to_milk_obt_d_1: float = 2.1e-3  # Eq. 86, role resolved by indices/context
    cow_hto_to_milk_hto_d_1: float = 3.9e-2  # Eq. 90
    cow_hto_to_milk_obt_d_1: float = 1.3e-3  # Eq. 91

    cow_obt_half_time_d: float = 40.0  # Eq. 92
    cow_obt_to_cow_hto_d_1: float = 1.5e-2  # Eq. 94
    cow_hto_to_cow_obt_d_1: float = 1.1e-3  # Eq. 96
    grass_obt_to_cow_obt_d_1: float = 3.3e-3  # Eq. 97

    cow_breathing_m3_per_cow_d: float = 130.0  # Eq. 98
    cow_count_per_reference_area: float = 250.0
    skin_absorption_multiplier: float = 1.5
    eq98_reference_area_m2: float = 1.0e6
    eq98_mixing_height_m: float = 1000.0
    atmosphere_to_cow_hto_manual_rounded_d_1: float = 4.9e-5

    grass_hto_to_cow_hto_d_1: float = 2.4e-2  # Eq. 103
    grass_obt_to_cow_hto_d_1: float = 2.1e-2  # Eq. 104
    grass_hto_to_grass_obt_d_1: float = 1.2e-2  # Eq. 105-1
    grass_obt_to_grass_hto_d_1: float = 4.3e-2  # Eq. 105-2
    grass_obt_overall_loss_d_1: float = 6.9e-2

    eq86_heading_ocr_ambiguous: bool = True
    eq86_role_resolved_from_compartment_indices_and_context: bool = True
    project_external_feed_activated: bool = False
    project_drinking_water_activated: bool = False
    project_support_area_normalization_activated: bool = False
    continuous_beef_turnover_activated: bool = False
    edible_beef_mass_default_activated: bool = False
    production_binding_authorized: bool = False
    original_numerical_discretization_recovered: bool = False

    def __post_init__(self) -> None:
        if self.profile_id != MANUAL_REFERENCE_PROFILE:
            raise UFOTRIAnimalInputError("D4 requires the explicit manual-reference profile")
        rate_fields = (
            "cow_water_to_atmosphere_d_1",
            "cow_water_to_soil1_d_1",
            "grass_obt_to_milk_obt_d_1",
            "cow_obt_to_milk_obt_d_1",
            "cow_hto_to_milk_hto_d_1",
            "cow_hto_to_milk_obt_d_1",
            "cow_obt_to_cow_hto_d_1",
            "cow_hto_to_cow_obt_d_1",
            "grass_obt_to_cow_obt_d_1",
            "atmosphere_to_cow_hto_manual_rounded_d_1",
            "grass_hto_to_cow_hto_d_1",
            "grass_obt_to_cow_hto_d_1",
            "grass_hto_to_grass_obt_d_1",
            "grass_obt_to_grass_hto_d_1",
            "grass_obt_overall_loss_d_1",
        )
        for field in rate_fields:
            _nonnegative(getattr(self, field), field=field)
        if _finite(self.cow_water_half_time_d, field="cow_water_half_time_d") <= 0.0:
            raise UFOTRIAnimalInputError("cow_water_half_time_d must be positive")
        if _finite(self.cow_obt_half_time_d, field="cow_obt_half_time_d") <= 0.0:
            raise UFOTRIAnimalInputError("cow_obt_half_time_d must be positive")
        for field in (
            "cow_breathing_m3_per_cow_d",
            "cow_count_per_reference_area",
            "skin_absorption_multiplier",
            "eq98_reference_area_m2",
            "eq98_mixing_height_m",
        ):
            if _finite(getattr(self, field), field=field) <= 0.0:
                raise UFOTRIAnimalInputError(f"{field} must be positive")
        if not self.eq86_heading_ocr_ambiguous:
            raise UFOTRIAnimalInputError("D4 must preserve the Eq.86 OCR-heading ambiguity")
        if not self.eq86_role_resolved_from_compartment_indices_and_context:
            raise UFOTRIAnimalInputError("Eq.86 role resolution provenance is required")
        forbidden = (
            self.project_external_feed_activated,
            self.project_drinking_water_activated,
            self.project_support_area_normalization_activated,
            self.continuous_beef_turnover_activated,
            self.edible_beef_mass_default_activated,
            self.production_binding_authorized,
            self.original_numerical_discretization_recovered,
        )
        if any(forbidden):
            raise UFOTRIAnimalInputError("D4 project/production/original-discretization flags must remain false")

    @property
    def cow_water_overall_loss_exact_d_1(self) -> float:
        return math.log(2.0) / self.cow_water_half_time_d

    @property
    def cow_obt_overall_loss_exact_d_1(self) -> float:
        return math.log(2.0) / self.cow_obt_half_time_d

    @property
    def atmosphere_to_cow_hto_eq98_exact_d_1(self) -> float:
        return (
            self.cow_breathing_m3_per_cow_d
            * self.cow_count_per_reference_area
            * self.skin_absorption_multiplier
            / (self.eq98_reference_area_m2 * self.eq98_mixing_height_m)
        )

    @property
    def cow_hto_total_hazard_d_1(self) -> float:
        return (
            self.cow_water_to_atmosphere_d_1
            + self.cow_water_to_soil1_d_1
            + self.cow_hto_to_milk_hto_d_1
            + self.cow_hto_to_milk_obt_d_1
            + self.cow_hto_to_cow_obt_d_1
        )

    @property
    def cow_obt_total_hazard_d_1(self) -> float:
        return self.cow_obt_to_cow_hto_d_1 + self.cow_obt_to_milk_obt_d_1

    @property
    def grass_obt_eq105_2_reconstructed_d_1(self) -> float:
        return self.grass_obt_overall_loss_d_1 - (
            self.grass_obt_to_cow_obt_d_1
            + self.grass_obt_to_cow_hto_d_1
            + self.grass_obt_to_milk_obt_d_1
        )


@dataclass(frozen=True)
class UFOTRICowMilkBeefForcing:
    """Explicit D4 forcing; V2 project feed/water assumptions fail closed."""

    atmosphere_hto_inventory_bq_m2: float = 0.0
    atmosphere_provenance: str = ""
    feed_mode: str = MANUAL_GRASS_SURROGATE_ONLY
    external_feed_hto_bq_m2_s: float = 0.0
    external_feed_obt_bq_m2_s: float = 0.0
    external_drinking_water_hto_bq_m2_s: float = 0.0

    def __post_init__(self) -> None:
        _nonnegative(
            self.atmosphere_hto_inventory_bq_m2,
            field="atmosphere_hto_inventory_bq_m2",
        )
        if not isinstance(self.atmosphere_provenance, str) or not self.atmosphere_provenance.strip():
            raise UFOTRIAnimalInputError("atmosphere_provenance is required")
        if self.feed_mode != MANUAL_GRASS_SURROGATE_ONLY:
            raise UFOTRIAnimalInputError(
                "D4 permits only the manual Eq.99 grass-surrogate feed mode"
            )
        for field in (
            "external_feed_hto_bq_m2_s",
            "external_feed_obt_bq_m2_s",
            "external_drinking_water_hto_bq_m2_s",
        ):
            value = _nonnegative(getattr(self, field), field=field)
            if value != 0.0:
                raise UFOTRIAnimalInputError(
                    f"{field} must remain zero; V2 project feed/drinking-water inputs are not D4 manual defaults"
                )


@dataclass(frozen=True)
class UFOTRICowMilkBeefState:
    """Area-normalized D4 activity inventories."""

    timestamp: datetime
    grass_hto_bq_m2: float = 0.0
    grass_obt_bq_m2: float = 0.0
    cow_hto_bq_m2: float = 0.0
    cow_obt_bq_m2: float = 0.0
    milk_hto_bq_m2: float = 0.0
    milk_obt_bq_m2: float = 0.0
    beef_hto_bq_m2: float = 0.0
    beef_obt_bq_m2: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None:
            raise UFOTRIAnimalInputError("timestamp must be timezone-aware")
        for field in self.__dataclass_fields__:
            if field == "timestamp":
                continue
            _nonnegative(getattr(self, field), field=field)

    @property
    def total_internal_bq_m2(self) -> float:
        return sum(
            (
                self.grass_hto_bq_m2,
                self.grass_obt_bq_m2,
                self.cow_hto_bq_m2,
                self.cow_obt_bq_m2,
                self.milk_hto_bq_m2,
                self.milk_obt_bq_m2,
                self.beef_hto_bq_m2,
                self.beef_obt_bq_m2,
            )
        )


@dataclass(frozen=True)
class UFOTRIAnimalTransferBalance:
    initial_internal_bq_m2: float
    eq98_atmosphere_input_bq_m2: float
    cow_to_atmosphere_boundary_bq_m2: float
    cow_to_soil1_boundary_bq_m2: float
    final_internal_bq_m2: float
    residual_bq_m2: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _finite(getattr(self, field), field=field)


@dataclass(frozen=True)
class UFOTRICowMilkBeefResult:
    state: UFOTRICowMilkBeefState
    balance: UFOTRIAnimalTransferBalance


@dataclass(frozen=True)
class UFOTRISlaughterBalance:
    fraction: float
    cow_activity_removed_bq_m2: float
    beef_activity_added_bq_m2: float
    total_residual_bq_m2: float


def _rate_s(rate_d_1: float) -> float:
    return rate_d_1 / SECONDS_PER_DAY


def _competing_transfers(
    inventory: float,
    dt_s: float,
    rates_d_1: dict[str, float],
) -> dict[str, float]:
    """Return integrated transfers from one source under constant competing hazards."""

    if inventory <= 0.0 or not rates_d_1:
        return {name: 0.0 for name in rates_d_1}
    rates_s = {name: _rate_s(_nonnegative(rate, field=name)) for name, rate in rates_d_1.items()}
    total_rate = sum(rates_s.values())
    if total_rate <= 0.0:
        return {name: 0.0 for name in rates_d_1}
    total_out = inventory * (-math.expm1(-total_rate * dt_s))
    return {name: total_out * rate / total_rate for name, rate in rates_s.items()}


class UFOTRICowMilkBeefSolver:
    """Conservative D4 transfer solver with caller-visible numerical substep."""

    def __init__(
        self,
        profile: UFOTRICowMilkBeefManualProfile,
        *,
        numerical_step_seconds: float = 3600.0,
    ) -> None:
        if not isinstance(profile, UFOTRICowMilkBeefManualProfile):
            raise UFOTRIAnimalInputError("explicit UFOTRICowMilkBeefManualProfile is required")
        numerical_step = _finite(numerical_step_seconds, field="numerical_step_seconds")
        if numerical_step <= 0.0:
            raise UFOTRIAnimalInputError("numerical_step_seconds must be positive")
        self.profile = profile
        self.numerical_step_seconds = numerical_step

    def advance(
        self,
        state: UFOTRICowMilkBeefState,
        forcing: UFOTRICowMilkBeefForcing,
        interval_seconds: float,
    ) -> UFOTRICowMilkBeefResult:
        if not isinstance(state, UFOTRICowMilkBeefState):
            raise UFOTRIAnimalInputError("state must be UFOTRICowMilkBeefState")
        if not isinstance(forcing, UFOTRICowMilkBeefForcing):
            raise UFOTRIAnimalInputError("forcing must be UFOTRICowMilkBeefForcing")
        interval = _finite(interval_seconds, field="interval_seconds")
        if interval <= 0.0:
            raise UFOTRIAnimalInputError("interval_seconds must be strictly positive")

        initial = state.total_internal_bq_m2
        values = {
            "grass_hto": state.grass_hto_bq_m2,
            "grass_obt": state.grass_obt_bq_m2,
            "cow_hto": state.cow_hto_bq_m2,
            "cow_obt": state.cow_obt_bq_m2,
            "milk_hto": state.milk_hto_bq_m2,
            "milk_obt": state.milk_obt_bq_m2,
            "beef_hto": state.beef_hto_bq_m2,
            "beef_obt": state.beef_obt_bq_m2,
        }
        eq98_input = 0.0
        atmosphere_boundary = 0.0
        soil_boundary = 0.0
        remaining = interval
        p = self.profile

        while remaining > 0.0:
            dt = min(self.numerical_step_seconds, remaining)

            grass_hto_out = _competing_transfers(
                values["grass_hto"],
                dt,
                {
                    "to_grass_obt": p.grass_hto_to_grass_obt_d_1,
                    "to_cow_hto": p.grass_hto_to_cow_hto_d_1,
                },
            )
            grass_obt_out = _competing_transfers(
                values["grass_obt"],
                dt,
                {
                    "to_grass_hto": p.grass_obt_to_grass_hto_d_1,
                    "to_cow_hto": p.grass_obt_to_cow_hto_d_1,
                    "to_cow_obt": p.grass_obt_to_cow_obt_d_1,
                    "to_milk_obt": p.grass_obt_to_milk_obt_d_1,
                },
            )
            cow_hto_out = _competing_transfers(
                values["cow_hto"],
                dt,
                {
                    "to_atmosphere": p.cow_water_to_atmosphere_d_1,
                    "to_soil1": p.cow_water_to_soil1_d_1,
                    "to_milk_hto": p.cow_hto_to_milk_hto_d_1,
                    "to_milk_obt": p.cow_hto_to_milk_obt_d_1,
                    "to_cow_obt": p.cow_hto_to_cow_obt_d_1,
                },
            )
            cow_obt_out = _competing_transfers(
                values["cow_obt"],
                dt,
                {
                    "to_cow_hto": p.cow_obt_to_cow_hto_d_1,
                    "to_milk_obt": p.cow_obt_to_milk_obt_d_1,
                },
            )

            eq98_step = (
                forcing.atmosphere_hto_inventory_bq_m2
                * _rate_s(p.atmosphere_to_cow_hto_manual_rounded_d_1)
                * dt
            )

            values["grass_hto"] += (
                grass_obt_out["to_grass_hto"]
                - sum(grass_hto_out.values())
            )
            values["grass_obt"] += (
                grass_hto_out["to_grass_obt"]
                - sum(grass_obt_out.values())
            )
            values["cow_hto"] += (
                grass_hto_out["to_cow_hto"]
                + grass_obt_out["to_cow_hto"]
                + cow_obt_out["to_cow_hto"]
                + eq98_step
                - sum(cow_hto_out.values())
            )
            values["cow_obt"] += (
                grass_obt_out["to_cow_obt"]
                + cow_hto_out["to_cow_obt"]
                - sum(cow_obt_out.values())
            )
            values["milk_hto"] += cow_hto_out["to_milk_hto"]
            values["milk_obt"] += (
                grass_obt_out["to_milk_obt"]
                + cow_hto_out["to_milk_obt"]
                + cow_obt_out["to_milk_obt"]
            )

            eq98_input += eq98_step
            atmosphere_boundary += cow_hto_out["to_atmosphere"]
            soil_boundary += cow_hto_out["to_soil1"]
            remaining -= dt

        tolerance = 1.0e-11 * max(1.0, initial + eq98_input)
        for name, value in values.items():
            if value < -tolerance:
                raise UFOTRIAnimalInputError(f"D4 numerical step produced negative {name}")
            values[name] = max(value, 0.0)

        final = UFOTRICowMilkBeefState(
            timestamp=state.timestamp + timedelta(seconds=interval),
            grass_hto_bq_m2=values["grass_hto"],
            grass_obt_bq_m2=values["grass_obt"],
            cow_hto_bq_m2=values["cow_hto"],
            cow_obt_bq_m2=values["cow_obt"],
            milk_hto_bq_m2=values["milk_hto"],
            milk_obt_bq_m2=values["milk_obt"],
            beef_hto_bq_m2=values["beef_hto"],
            beef_obt_bq_m2=values["beef_obt"],
        )
        residual = (
            initial
            + eq98_input
            - atmosphere_boundary
            - soil_boundary
            - final.total_internal_bq_m2
        )
        if abs(residual) > tolerance:
            raise UFOTRIAnimalInputError(f"D4 activity conservation failed: {residual}")
        return UFOTRICowMilkBeefResult(
            state=final,
            balance=UFOTRIAnimalTransferBalance(
                initial_internal_bq_m2=initial,
                eq98_atmosphere_input_bq_m2=eq98_input,
                cow_to_atmosphere_boundary_bq_m2=atmosphere_boundary,
                cow_to_soil1_boundary_bq_m2=soil_boundary,
                final_internal_bq_m2=final.total_internal_bq_m2,
                residual_bq_m2=residual,
            ),
        )


def slaughter_to_beef(
    state: UFOTRICowMilkBeefState,
    fraction: float,
) -> tuple[UFOTRICowMilkBeefState, UFOTRISlaughterBalance]:
    """Transfer an explicit fraction of cow activity to beef activity.

    This is an activity-boundary implementation for a caller-declared slaughter
    event.  It does not activate V2 continuous herd turnover, support-area
    normalization, or a default edible-meat mass.
    """

    if not isinstance(state, UFOTRICowMilkBeefState):
        raise UFOTRIAnimalInputError("state must be UFOTRICowMilkBeefState")
    frac = _finite(fraction, field="fraction")
    if frac < 0.0 or frac > 1.0:
        raise UFOTRIAnimalInputError("fraction must be within [0, 1]")

    removed_hto = state.cow_hto_bq_m2 * frac
    removed_obt = state.cow_obt_bq_m2 * frac
    removed = removed_hto + removed_obt
    final = UFOTRICowMilkBeefState(
        timestamp=state.timestamp,
        grass_hto_bq_m2=state.grass_hto_bq_m2,
        grass_obt_bq_m2=state.grass_obt_bq_m2,
        cow_hto_bq_m2=state.cow_hto_bq_m2 - removed_hto,
        cow_obt_bq_m2=state.cow_obt_bq_m2 - removed_obt,
        milk_hto_bq_m2=state.milk_hto_bq_m2,
        milk_obt_bq_m2=state.milk_obt_bq_m2,
        beef_hto_bq_m2=state.beef_hto_bq_m2 + removed_hto,
        beef_obt_bq_m2=state.beef_obt_bq_m2 + removed_obt,
    )
    residual = state.total_internal_bq_m2 - final.total_internal_bq_m2
    return final, UFOTRISlaughterBalance(
        fraction=frac,
        cow_activity_removed_bq_m2=removed,
        beef_activity_added_bq_m2=removed,
        total_residual_bq_m2=residual,
    )


def ufotri_cow_milk_beef_manual_profile() -> UFOTRICowMilkBeefManualProfile:
    """Return the explicit D4 manual-rounded transfer-rate profile."""

    return UFOTRICowMilkBeefManualProfile()


__all__ = [
    "MANUAL_GRASS_SURROGATE_ONLY",
    "MANUAL_REFERENCE_PROFILE",
    "SECONDS_PER_DAY",
    "UFOTRIAnimalInputError",
    "UFOTRIAnimalTransferBalance",
    "UFOTRICowMilkBeefForcing",
    "UFOTRICowMilkBeefManualProfile",
    "UFOTRICowMilkBeefResult",
    "UFOTRICowMilkBeefSolver",
    "UFOTRICowMilkBeefState",
    "UFOTRISlaughterBalance",
    "slaughter_to_beef",
    "ufotri_cow_milk_beef_manual_profile",
]
