"""Opt-in UFOTRI re-emission/area-source compatibility adapter.

This module implements only the recoverable Phase-F1 coupling semantics from
KfK 4605 and the E3 reconciliation. It does not replace the historical V1/V2
feedback path, generate a soil re-emission rate, or bind real CTEAS-Atmos.

Re-emission enters here as an already-accounted environmental inventory loss.
The atmospheric handoff moves the same activity and never creates a second
environmental activity term.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from ..atmosphere.dispersion_parameters import rural_pg_sigma
from ..plant.leaf_ufotri_v4.model import ufotri_manual_leaf_geometry


STAGE = "UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1"
SOURCE_HOUR_SECONDS = 3600
AREA_SOURCE_SIGMA_WIDTH_FACTOR = 4.3
EQ6_NORMALIZATION_CONVENTION = "PRINTED_SIGMA_Y_DENOMINATOR_SIGMA_YG_LATERAL_EXPONENT"

SOIL = "SOIL"
PLANT = "PLANT"
PRIMARY_HTO = "PRIMARY_HTO"
HT_DERIVED_HTO = "HT_DERIVED_HTO"
MIXED_HTO_ORIGIN = "MIXED_HTO_ORIGIN"
UNRESOLVED_HTO_ORIGIN = "UNRESOLVED_HTO_ORIGIN"
NO_ACTIVITY = "NO_ACTIVITY"

_ALLOWED_COMPARTMENTS = {SOIL, PLANT}
_ALLOWED_LOSS_ORIGINS = {
    PRIMARY_HTO,
    HT_DERIVED_HTO,
    MIXED_HTO_ORIGIN,
    UNRESOLVED_HTO_ORIGIN,
}
_ALLOWED_SOURCE_ORIGINS = _ALLOWED_LOSS_ORIGINS | {NO_ACTIVITY}


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _positive(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result <= 0.0:
        raise ValueError(f"{field} must be positive")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise ValueError(f"{field} must be non-negative")
    return result


def _fraction(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be within [0, 1]")
    return result


@dataclass(frozen=True)
class ManualAreaSourceGeometry:
    """Rectangular geometry for the recovered Eq. (5)/(6) approximation.

    KfK 4605 assumes one effective source height for soil and plant. Phase A
    recovered the area-source rule ``FLQH=0.8H`` with a minimum height of 1 m,
    so this fidelity object fails closed below 1 m rather than reverting to the
    historical ground-level source.
    """

    length_m: float
    width_m: float
    effective_height_m: float

    def __post_init__(self) -> None:
        _positive(self.length_m, field="length_m")
        _positive(self.width_m, field="width_m")
        height = _finite(self.effective_height_m, field="effective_height_m")
        if height < 1.0:
            raise ValueError("effective_height_m must be at least 1 m in the F1 fidelity path")

    @property
    def area_m2(self) -> float:
        return float(self.length_m) * float(self.width_m)

    @property
    def initial_sigma_y_m(self) -> float:
        return float(self.width_m) / AREA_SOURCE_SIGMA_WIDTH_FACTOR

    @classmethod
    def from_canopy_height(
        cls,
        *,
        length_m: float,
        width_m: float,
        canopy_height_m: float,
    ) -> "ManualAreaSourceGeometry":
        leaf_geometry = ufotri_manual_leaf_geometry(canopy_height_m)
        return cls(
            length_m=length_m,
            width_m=width_m,
            effective_height_m=leaf_geometry.area_source_emission_height_m,
        )


@dataclass(frozen=True)
class AccountedReemissionLoss:
    """One environmental loss already debited before atmospheric handoff."""

    compartment: str
    flux_bq_m2_s: float
    origin: str
    transfer_id: str
    origin_proof_id: str | None = None

    def __post_init__(self) -> None:
        if self.compartment not in _ALLOWED_COMPARTMENTS:
            raise ValueError(f"Unsupported re-emission compartment: {self.compartment}")
        _nonnegative(self.flux_bq_m2_s, field="flux_bq_m2_s")
        if self.origin not in _ALLOWED_LOSS_ORIGINS:
            raise ValueError(f"Unsupported HTO origin: {self.origin}")
        if not isinstance(self.transfer_id, str) or not self.transfer_id.strip():
            raise ValueError("transfer_id must be a non-empty string")
        if self.origin == HT_DERIVED_HTO and not (
            isinstance(self.origin_proof_id, str) and self.origin_proof_id.strip()
        ):
            raise ValueError(
                "HT_DERIVED_HTO attribution requires explicit origin_proof_id"
            )


@dataclass(frozen=True)
class HourlySecondarySource:
    """Activity from one completed source hour routed during the next hour."""

    compartment: str
    source_hour_index: int
    flux_bq_m2_s: float
    routed_activity_bq: float
    environmental_loss_activity_bq: float
    unrouted_activity_bq: float
    origin: str
    transfer_ids: tuple[str, ...]
    origin_proof_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.compartment not in _ALLOWED_COMPARTMENTS:
            raise ValueError(f"Unsupported source compartment: {self.compartment}")
        if self.source_hour_index < -1:
            raise ValueError("source_hour_index must be >= -1")
        for name in (
            "flux_bq_m2_s",
            "routed_activity_bq",
            "environmental_loss_activity_bq",
            "unrouted_activity_bq",
        ):
            _nonnegative(getattr(self, name), field=name)
        if self.origin not in _ALLOWED_SOURCE_ORIGINS:
            raise ValueError(f"Unsupported source origin: {self.origin}")
        if not math.isclose(
            self.environmental_loss_activity_bq,
            self.routed_activity_bq + self.unrouted_activity_bq,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError("F1 handoff activity ledger does not close")
        if self.routed_activity_bq > 0.0:
            if self.origin == NO_ACTIVITY:
                raise ValueError("positive routed activity cannot have NO_ACTIVITY origin")
            if not self.transfer_ids:
                raise ValueError("positive routed activity requires transfer_ids")
            if self.origin == HT_DERIVED_HTO and not self.origin_proof_ids:
                raise ValueError(
                    "HT_DERIVED_HTO secondary source requires explicit origin proof"
                )
        elif self.origin == NO_ACTIVITY and self.transfer_ids:
            raise ValueError("NO_ACTIVITY source cannot carry transfer_ids")

    @property
    def fully_routed(self) -> bool:
        return self.unrouted_activity_bq == 0.0


@dataclass(frozen=True)
class SecondaryConcentrationResult:
    primary_air_bq_m3: float
    soil_secondary_bq_m3: float
    plant_secondary_bq_m3: float

    @property
    def secondary_air_bq_m3(self) -> float:
        return self.soil_secondary_bq_m3 + self.plant_secondary_bq_m3

    @property
    def total_air_bq_m3(self) -> float:
        return self.primary_air_bq_m3 + self.secondary_air_bq_m3


def _combine_origins(
    events: Iterable[AccountedReemissionLoss],
) -> tuple[str, tuple[str, ...]]:
    active = [event for event in events if event.flux_bq_m2_s > 0.0]
    if not active:
        return NO_ACTIVITY, ()
    origins = {event.origin for event in active}
    proofs = tuple(
        sorted(
            {
                event.origin_proof_id
                for event in active
                if event.origin_proof_id is not None
            }
        )
    )
    if len(origins) == 1:
        return next(iter(origins)), proofs
    if UNRESOLVED_HTO_ORIGIN in origins:
        return UNRESOLVED_HTO_ORIGIN, proofs
    return MIXED_HTO_ORIGIN, proofs


def eq5_effective_sigma_y_m(sigma_y_m: float, source_width_m: float) -> float:
    """KfK 4605 Eq. (5), with ``sigma_y0 = source_width/4.3``."""

    sigma_y = _positive(sigma_y_m, field="sigma_y_m")
    width = _positive(source_width_m, field="source_width_m")
    sigma_y0 = width / AREA_SOURCE_SIGMA_WIDTH_FACTOR
    return math.sqrt(sigma_y * sigma_y + sigma_y0 * sigma_y0)


def eq6_equivalent_area_source_concentration_bq_m3(
    *,
    surface_flux_bq_m2_s: float,
    geometry: ManualAreaSourceGeometry,
    receptor_downwind_m: float,
    receptor_crosswind_m: float,
    wind_speed_m_s: float,
    stability_class: str,
    fallout_factor: float,
    washout_factor: float,
) -> float:
    """Printed KfK 4605 Eq. (5)/(6) centre-source compatibility form.

    The available manual text prints ``sigma_yg`` in the lateral exponential
    but ``sigma_y`` in the Eq. (6) normalization denominator. F1 reproduces
    that visible form instead of silently correcting it to ``sigma_yg``. This
    is therefore a printed-formula compatibility path, not evidence of exact
    original executable normalization.

    Coordinates are relative to the rectangle centre. Fallout and washout are
    explicit arguments so no depletion parameterization is silently imported.
    """

    flux = _nonnegative(surface_flux_bq_m2_s, field="surface_flux_bq_m2_s")
    downwind = _finite(receptor_downwind_m, field="receptor_downwind_m")
    crosswind = _finite(receptor_crosswind_m, field="receptor_crosswind_m")
    wind = _positive(wind_speed_m_s, field="wind_speed_m_s")
    fallout = _fraction(fallout_factor, field="fallout_factor")
    washout = _fraction(washout_factor, field="washout_factor")
    if flux == 0.0 or downwind <= 0.0:
        return 0.0
    sigma_y, sigma_z = rural_pg_sigma(downwind, stability_class)
    sigma_yg = eq5_effective_sigma_y_m(sigma_y, geometry.width_m)
    source_rate_bq_s = flux * geometry.area_m2
    lateral = math.exp(-0.5 * (crosswind / sigma_yg) ** 2)
    vertical = math.exp(-0.5 * (geometry.effective_height_m / sigma_z) ** 2)
    concentration = (
        source_rate_bq_s
        / (math.pi * wind * sigma_y * sigma_z)
        * lateral
        * vertical
        * fallout
        * washout
    )
    return max(float(concentration), 0.0)


def superpose_secondary_sources(
    *,
    primary_air_bq_m3: float,
    soil_source: HourlySecondarySource,
    plant_source: HourlySecondarySource,
    geometry: ManualAreaSourceGeometry,
    receptor_downwind_m: float,
    receptor_crosswind_m: float,
    wind_speed_m_s: float,
    stability_class: str,
    soil_fallout_factor: float,
    soil_washout_factor: float,
    plant_fallout_factor: float,
    plant_washout_factor: float,
) -> SecondaryConcentrationResult:
    """Evaluate soil/plant Eq. (6) separately and linearly superpose them."""

    primary = _nonnegative(primary_air_bq_m3, field="primary_air_bq_m3")
    if soil_source.compartment != SOIL or plant_source.compartment != PLANT:
        raise ValueError("soil_source and plant_source compartments are not aligned")
    common = dict(
        geometry=geometry,
        receptor_downwind_m=receptor_downwind_m,
        receptor_crosswind_m=receptor_crosswind_m,
        wind_speed_m_s=wind_speed_m_s,
        stability_class=stability_class,
    )
    soil = eq6_equivalent_area_source_concentration_bq_m3(
        surface_flux_bq_m2_s=soil_source.flux_bq_m2_s,
        fallout_factor=soil_fallout_factor,
        washout_factor=soil_washout_factor,
        **common,
    )
    plant = eq6_equivalent_area_source_concentration_bq_m3(
        surface_flux_bq_m2_s=plant_source.flux_bq_m2_s,
        fallout_factor=plant_fallout_factor,
        washout_factor=plant_washout_factor,
        **common,
    )
    return SecondaryConcentrationResult(primary, soil, plant)


class HourlyReemissionHandoffBuffer:
    """Conservative KfK-4605 ``hour N -> hour N+1`` handoff buffer."""

    def __init__(
        self,
        *,
        time_step_seconds: int,
        geometry: ManualAreaSourceGeometry,
    ) -> None:
        if isinstance(time_step_seconds, bool) or not isinstance(time_step_seconds, int):
            raise TypeError("time_step_seconds must be an integer number of seconds")
        if time_step_seconds <= 0 or SOURCE_HOUR_SECONDS % time_step_seconds != 0:
            raise ValueError("time_step_seconds must exactly divide 3600 seconds")
        self._dt_s = time_step_seconds
        self._geometry = geometry
        self._steps_per_hour = SOURCE_HOUR_SECONDS // time_step_seconds
        self._step_in_hour = 0
        self._source_hour_index = 0
        self._events: dict[str, list[AccountedReemissionLoss]] = {SOIL: [], PLANT: []}
        self._activities_bq = {SOIL: 0.0, PLANT: 0.0}
        self._active = {SOIL: self._zero_source(SOIL), PLANT: self._zero_source(PLANT)}

    @property
    def time_step_seconds(self) -> int:
        return self._dt_s

    @property
    def geometry(self) -> ManualAreaSourceGeometry:
        return self._geometry

    def _zero_source(self, compartment: str) -> HourlySecondarySource:
        return HourlySecondarySource(
            compartment=compartment,
            source_hour_index=-1,
            flux_bq_m2_s=0.0,
            routed_activity_bq=0.0,
            environmental_loss_activity_bq=0.0,
            unrouted_activity_bq=0.0,
            origin=NO_ACTIVITY,
            transfer_ids=(),
            origin_proof_ids=(),
        )

    def active_sources(self) -> tuple[HourlySecondarySource, HourlySecondarySource]:
        return self._active[SOIL], self._active[PLANT]

    def step(
        self,
        losses: Iterable[AccountedReemissionLoss],
    ) -> tuple[HourlySecondarySource, HourlySecondarySource]:
        """Return current lagged sources, then account this interval's losses."""

        current_sources = self.active_sources()
        for event in tuple(losses):
            self._events[event.compartment].append(event)
            self._activities_bq[event.compartment] += (
                event.flux_bq_m2_s * self._geometry.area_m2 * self._dt_s
            )

        self._step_in_hour += 1
        if self._step_in_hour == self._steps_per_hour:
            next_active: dict[str, HourlySecondarySource] = {}
            for compartment in (SOIL, PLANT):
                events = self._events[compartment]
                activity = self._activities_bq[compartment]
                origin, proofs = _combine_origins(events)
                transfer_ids = tuple(
                    sorted(
                        {
                            event.transfer_id
                            for event in events
                            if event.flux_bq_m2_s > 0.0
                        }
                    )
                )
                next_active[compartment] = HourlySecondarySource(
                    compartment=compartment,
                    source_hour_index=self._source_hour_index,
                    flux_bq_m2_s=(
                        activity / (self._geometry.area_m2 * SOURCE_HOUR_SECONDS)
                    ),
                    routed_activity_bq=activity,
                    environmental_loss_activity_bq=activity,
                    unrouted_activity_bq=0.0,
                    origin=origin,
                    transfer_ids=transfer_ids,
                    origin_proof_ids=proofs,
                )
            self._active = next_active
            self._source_hour_index += 1
            self._step_in_hour = 0
            self._events = {SOIL: [], PLANT: []}
            self._activities_bq = {SOIL: 0.0, PLANT: 0.0}
        return current_sources
