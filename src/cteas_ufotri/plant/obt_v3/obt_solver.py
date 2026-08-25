"""Isolated V3 P6.2C TFWT-to-OBT inventory solver."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math

from ..tfwt_v3 import TFWTState
from .obt_state import OBTState
from .validation import (
    INTEGRATED_ACTIVITY_UNIT,
    OBTInputError,
    OBTParameterError,
    RATE_UNIT,
    require_finite,
    require_unit,
    validate_biological_forcing,
    validate_interval,
    validate_multiplier,
    validate_rate,
    validate_state,
)


@dataclass(frozen=True)
class PlantBiologicalForcing:
    """Biological forcing boundary for OBT formation.

    P6.2C uses only ``is_daylight``. The remaining fields are explicit
    extension points and do not silently alter the current equation.
    """

    is_daylight: bool
    temperature_k: float | None = None
    photosynthetic_activity: float | None = None
    growth_stage: str | None = None

    def __post_init__(self) -> None:
        validate_biological_forcing(self)


@dataclass(frozen=True)
class OBTParameters:
    """Explicit first-version rates; values are not read from UFOTRI data."""

    kf_s: float
    kr_s: float
    daylight_multiplier: float = 1.0
    nighttime_multiplier: float = 0.0
    rate_unit: str = RATE_UNIT

    def __post_init__(self) -> None:
        require_unit(self.rate_unit, RATE_UNIT, field="obt_rate")
        validate_rate(self.kf_s, field="kf_s")
        validate_rate(self.kr_s, field="kr_s")
        validate_multiplier(
            self.daylight_multiplier,
            field="daylight_multiplier",
        )
        validate_multiplier(
            self.nighttime_multiplier,
            field="nighttime_multiplier",
        )

    @property
    def formation_rate_s(self) -> float:
        """Descriptive alias for ``kf_s``."""

        return self.kf_s

    @property
    def turnover_rate_s(self) -> float:
        """Descriptive alias for ``kr_s``."""

        return self.kr_s


@dataclass(frozen=True)
class OBTStorageBalance:
    """Integrated TFWT-to-OBT transfer and OBT loss ledger."""

    tfwt_loss_bq_m2: float
    obt_formation_bq_m2: float
    obt_increase_bq_m2: float
    other_loss_bq_m2: float
    residual_bq_m2: float
    unit: str = INTEGRATED_ACTIVITY_UNIT

    def __post_init__(self) -> None:
        require_unit(self.unit, INTEGRATED_ACTIVITY_UNIT, field="obt_balance")
        for field in (
            "tfwt_loss_bq_m2",
            "obt_formation_bq_m2",
            "obt_increase_bq_m2",
            "other_loss_bq_m2",
            "residual_bq_m2",
        ):
            require_finite(getattr(self, field), field=field)
        if self.tfwt_loss_bq_m2 < 0.0:
            raise OBTInputError("tfwt_loss_bq_m2 must be non-negative")
        if self.obt_formation_bq_m2 < 0.0:
            raise OBTInputError("obt_formation_bq_m2 must be non-negative")
        if self.other_loss_bq_m2 < 0.0:
            raise OBTInputError("other_loss_bq_m2 must be non-negative")

    @property
    def turnover_bq_m2(self) -> float:
        """Compatibility name for the first-version OBT loss term."""

        return self.other_loss_bq_m2


@dataclass(frozen=True)
class OBTStepResult:
    """Updated OBT state plus an auditable inventory balance."""

    state: OBTState
    balance: OBTStorageBalance


class OBTSolver:
    """Advance the provisional TFWT-to-OBT inventory equation.

    The solver consumes only the public ``TFWTState.inventory()`` and
    ``TFWTState.activity_concentration()`` methods. It does not inspect TFWT
    fields, recompute resistance, or connect soil, foodchain, dose, or the
    UFOTRI parameter database.

    For one interval, TFWT inventory and biological forcing are held constant.
    The linear OBT equation is advanced analytically, while its integrated
    formation and loss terms are returned for conservation accounting.
    """

    def __init__(
        self,
        parameters: OBTParameters | None = None,
        *,
        kf_s: float | None = None,
        kr_s: float | None = None,
        kf: float | None = None,
        kr: float | None = None,
        daylight_multiplier: float | None = None,
        nighttime_multiplier: float | None = None,
    ) -> None:
        """Create a solver with explicit rates or an ``OBTParameters`` record.

        ``kf``/``kr`` are accepted as readable aliases for the equation's
        symbols. At least both rates must be supplied when ``parameters`` is
        omitted; there is no hidden production or UFOTRI default.
        """

        aliases = (kf_s, kr_s, kf, kr)
        if parameters is not None and any(value is not None for value in aliases):
            raise OBTParameterError(
                "parameters cannot be combined with explicit rate arguments"
            )
        if parameters is None:
            if kf_s is not None and kf is not None:
                raise OBTParameterError("supply only one of kf_s and kf")
            if kr_s is not None and kr is not None:
                raise OBTParameterError("supply only one of kr_s and kr")
            resolved_kf = kf_s if kf_s is not None else kf
            resolved_kr = kr_s if kr_s is not None else kr
            if resolved_kf is None or resolved_kr is None:
                raise OBTParameterError(
                    "explicit kf_s and kr_s rates are required"
                )
            parameters = OBTParameters(
                kf_s=resolved_kf,
                kr_s=resolved_kr,
                daylight_multiplier=(
                    1.0
                    if daylight_multiplier is None
                    else daylight_multiplier
                ),
                nighttime_multiplier=(
                    0.0
                    if nighttime_multiplier is None
                    else nighttime_multiplier
                ),
            )
        elif (
            daylight_multiplier is not None
            or nighttime_multiplier is not None
        ):
            raise OBTParameterError(
                "multipliers cannot be combined with parameters"
            )
        self.parameters = parameters

    def _tfwt_inventory(self, tfwt_state: TFWTState) -> float:
        """Read TFWT only through its two public activity methods."""

        if not isinstance(tfwt_state, TFWTState):
            raise OBTInputError("tfwt_state must be a V3 TFWTState")
        inventory = require_finite(
            tfwt_state.inventory(),
            field="tfwt_state.inventory()",
        )
        concentration = require_finite(
            tfwt_state.activity_concentration(),
            field="tfwt_state.activity_concentration()",
        )
        if inventory < 0.0 or concentration < 0.0:
            raise OBTInputError(
                "TFWT inventory and activity concentration must be non-negative"
            )
        return inventory

    def advance(
        self,
        tfwt_state: TFWTState,
        obt_state: OBTState,
        interval_seconds: float,
        biological_forcing: PlantBiologicalForcing,
    ) -> OBTStepResult:
        """Advance OBT from a public TFWT inventory for one interval."""

        validate_state(obt_state)
        interval = validate_interval(interval_seconds)
        validate_biological_forcing(biological_forcing)
        tfwt_inventory = self._tfwt_inventory(tfwt_state)

        multiplier = (
            self.parameters.daylight_multiplier
            if biological_forcing.is_daylight
            else self.parameters.nighttime_multiplier
        )
        effective_kf = self.parameters.kf_s * multiplier
        source_rate = effective_kf * tfwt_inventory
        formation = source_rate * interval
        initial_inventory = obt_state.inventory()
        kr_s = self.parameters.kr_s

        if kr_s == 0.0:
            next_inventory = initial_inventory + formation
            other_loss = 0.0
        else:
            decay_factor = math.exp(-kr_s * interval)
            equilibrium_inventory = source_rate / kr_s
            next_inventory = (
                equilibrium_inventory
                + (initial_inventory - equilibrium_inventory) * decay_factor
            )
            obt_increase = next_inventory - initial_inventory
            other_loss = formation - obt_increase

        if next_inventory < -1.0e-12:
            raise OBTInputError("OBT step would create a negative inventory")
        next_inventory = max(next_inventory, 0.0)
        obt_increase = next_inventory - initial_inventory
        other_loss = formation - obt_increase
        if other_loss < -1.0e-10:
            raise OBTInputError("OBT loss balance became negative")
        other_loss = max(other_loss, 0.0)

        next_state = obt_state.with_inventory(
            obt_inventory_bq_m2=next_inventory,
            timestamp=obt_state.timestamp + timedelta(seconds=interval),
        )
        balance = OBTStorageBalance(
            tfwt_loss_bq_m2=formation,
            obt_formation_bq_m2=formation,
            obt_increase_bq_m2=obt_increase,
            other_loss_bq_m2=other_loss,
            residual_bq_m2=(formation - obt_increase - other_loss),
        )
        return OBTStepResult(state=next_state, balance=balance)

    def step(
        self,
        tfwt_state: TFWTState,
        obt_state: OBTState,
        interval_seconds: float,
        biological_forcing: PlantBiologicalForcing,
    ) -> OBTState:
        """Return only the updated OBT state."""

        return self.advance(
            tfwt_state,
            obt_state,
            interval_seconds,
            biological_forcing,
        ).state


__all__ = [
    "OBTParameters",
    "OBTStepResult",
    "OBTStorageBalance",
    "OBTSolver",
    "PlantBiologicalForcing",
]
