"""Opt-in UFOTRI-native primary atmospheric transport core.

This module reconstructs the directly recoverable KfK 4605 primary-dispersion
semantics without depending on CTEAS-Atmos.  It intentionally remains an
isolated fidelity path and does not change the retained RC1/default atmosphere.

Recovered manual semantics in this stage:

* HT and HTO remain distinct chemical forms in the primary atmosphere;
* source durations longer than one hour are divided into one-hour releases;
* the primary path is Gaussian and uses the S.C.K./C.E.N. Mol power-law
  dispersion coefficients for Pasquill classes A-F;
* vertical spread is limited to ``0.8 * mixing_lid``;
* dry deposition is species-specific;
* HT wet deposition is negligible and therefore disabled;
* HTO washout may be represented only by an explicit caller-supplied
  scavenging coefficient;
* atmospheric HT->HTO conversion is disabled for the KfK 4605 fidelity path.

KfK 4605 Appendix B also prints an ITER benchmark input named
``Oxidation rate in air = 0.5 %/d``.  Section 2.2, however, explicitly states
that conversion of tritium gas to HTO in the atmosphere is *not included in
the program* because the conversion is slow.  This module preserves that
source conflict as evidence and does not silently activate the benchmark
number.

The unavailable original MUSEMET source-depletion discretisation and complete
hourly bent-trajectory numerics are outside this first native-atmosphere core.
The source-depletion helper below is therefore explicitly identified as a
controlled compatibility approximation rather than original-executable
numerical equivalence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import math


class UFOTRINativeAtmosphereError(ValueError):
    """Fail-closed error for the UFOTRI-native atmospheric fidelity path."""


class TritiumAtmosphericForm(str, Enum):
    HT = "HT"
    HTO = "HTO"


@dataclass(frozen=True)
class MolDispersionCoefficients:
    p_y: float
    q_y: float
    p_z: float
    q_z: float


# KfK 4605 Appendix B, Table 9.  x and sigma are in metres.
MOL_SMOOTH_TERRAIN_COEFFICIENTS: dict[str, MolDispersionCoefficients] = {
    "A": MolDispersionCoefficients(0.946, 0.796, 1.321, 0.711),
    "B": MolDispersionCoefficients(0.826, 0.796, 0.950, 0.711),
    "C": MolDispersionCoefficients(0.586, 0.796, 0.700, 0.711),
    "D": MolDispersionCoefficients(0.418, 0.796, 0.520, 0.711),
    "E": MolDispersionCoefficients(0.297, 0.796, 0.382, 0.711),
    "F": MolDispersionCoefficients(0.235, 0.796, 0.311, 0.711),
}


KFK4605_ITER_HT_DRY_DEPOSITION_VELOCITY_M_S = 0.05e-2
KFK4605_ITER_HTO_DRY_DEPOSITION_VELOCITY_M_S = 1.8e-2
KFK4605_ITER_AIR_OXIDATION_FRACTION_D_1 = 0.005


def _finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UFOTRINativeAtmosphereError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise UFOTRINativeAtmosphereError(f"{field} must be finite")
    return result


def _nonnegative(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result < 0.0:
        raise UFOTRINativeAtmosphereError(f"{field} must be non-negative")
    return result


def _positive(value: float, *, field: str) -> float:
    result = _finite(value, field=field)
    if result <= 0.0:
        raise UFOTRINativeAtmosphereError(f"{field} must be positive")
    return result


def _utc(value: datetime, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise UFOTRINativeAtmosphereError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise UFOTRINativeAtmosphereError(f"{field} must be UTC")
    return value.astimezone(timezone.utc)


def mol_sigma_m(
    downwind_distance_m: float,
    stability_class: str,
    *,
    mixing_lid_m: float | None = None,
) -> tuple[float, float]:
    """Return KfK 4605 / Mol power-law ``sigma_y, sigma_z`` in metres.

    The manual states that the dispersion parameters are power functions of
    distance.  Appendix B Table 9 supplies ``p_y, q_y, p_z, q_z`` for A-F;
    the corresponding form is ``sigma = p * x**q``.  Section 2.1 limits
    vertical spread to ``0.8 h`` where ``h`` is the mixing-layer height.
    """

    distance = _positive(downwind_distance_m, field="downwind_distance_m")
    if not isinstance(stability_class, str):
        raise UFOTRINativeAtmosphereError("stability_class must be A-F")
    key = stability_class.upper()
    try:
        c = MOL_SMOOTH_TERRAIN_COEFFICIENTS[key]
    except KeyError as exc:
        raise UFOTRINativeAtmosphereError(
            f"unsupported Mol stability class: {stability_class!r}"
        ) from exc

    sigma_y = c.p_y * distance**c.q_y
    sigma_z = c.p_z * distance**c.q_z
    if mixing_lid_m is not None:
        lid = _positive(mixing_lid_m, field="mixing_lid_m")
        sigma_z = min(sigma_z, 0.8 * lid)
    return sigma_y, sigma_z


def wind_speed_power_law_m_s(
    reference_speed_m_s: float,
    reference_height_m: float,
    target_height_m: float,
    exponent: float,
) -> float:
    """KfK 4605 Appendix-B height-dependent wind relation.

    ``U = U0 * (h / h0)**a``
    """

    speed = _nonnegative(reference_speed_m_s, field="reference_speed_m_s")
    h0 = _positive(reference_height_m, field="reference_height_m")
    h = _positive(target_height_m, field="target_height_m")
    a = _nonnegative(exponent, field="exponent")
    return speed * (h / h0) ** a


def gaussian_concentration_bq_m3(
    emission_rate_bq_s: float,
    downwind_m: float,
    crosswind_m: float,
    wind_speed_m_s: float,
    effective_release_height_m: float,
    receptor_height_m: float,
    stability_class: str,
    *,
    mixing_lid_m: float | None = None,
) -> float:
    """Straight-segment Gaussian concentration for the native fidelity path.

    Ground reflection is represented by the ordinary image source.  This is
    the directly recoverable Gaussian role; complete original MUSEMET
    trajectory/building-wake numerics are not claimed here.
    """

    q = _nonnegative(emission_rate_bq_s, field="emission_rate_bq_s")
    x = _finite(downwind_m, field="downwind_m")
    y = _finite(crosswind_m, field="crosswind_m")
    u = _positive(wind_speed_m_s, field="wind_speed_m_s")
    h = _nonnegative(
        effective_release_height_m, field="effective_release_height_m"
    )
    z = _nonnegative(receptor_height_m, field="receptor_height_m")
    if q == 0.0 or x <= 0.0:
        return 0.0

    sigma_y, sigma_z = mol_sigma_m(x, stability_class, mixing_lid_m=mixing_lid_m)
    lateral = math.exp(-0.5 * (y / sigma_y) ** 2)
    vertical = math.exp(-0.5 * ((z - h) / sigma_z) ** 2) + math.exp(
        -0.5 * ((z + h) / sigma_z) ** 2
    )
    return q * lateral * vertical / (2.0 * math.pi * u * sigma_y * sigma_z)


@dataclass(frozen=True)
class NativeReleaseSlice:
    start_utc: datetime
    end_utc: datetime
    species: TritiumAtmosphericForm
    emission_rate_bq_s: float
    released_activity_bq: float
    source_id: str

    def __post_init__(self) -> None:
        start = _utc(self.start_utc, field="start_utc")
        end = _utc(self.end_utc, field="end_utc")
        if end <= start:
            raise UFOTRINativeAtmosphereError("release slice interval must be positive")
        if (end - start).total_seconds() > 3600.0 + 1.0e-12:
            raise UFOTRINativeAtmosphereError("release slices may not exceed one hour")
        if not isinstance(self.species, TritiumAtmosphericForm):
            raise UFOTRINativeAtmosphereError("species must be explicit HT or HTO")
        rate = _nonnegative(self.emission_rate_bq_s, field="emission_rate_bq_s")
        activity = _nonnegative(self.released_activity_bq, field="released_activity_bq")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise UFOTRINativeAtmosphereError("source_id is required")
        expected = rate * (end - start).total_seconds()
        if not math.isclose(activity, expected, rel_tol=1.0e-12, abs_tol=1.0e-9):
            raise UFOTRINativeAtmosphereError(
                "released_activity_bq must equal emission_rate * slice duration"
            )
        object.__setattr__(self, "start_utc", start)
        object.__setattr__(self, "end_utc", end)

    @property
    def duration_s(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds()


def split_release_into_hourly_slices(
    *,
    start_utc: datetime,
    duration_s: float,
    total_activity_bq: float,
    species: TritiumAtmosphericForm,
    source_id: str,
) -> tuple[NativeReleaseSlice, ...]:
    """Split a constant release into <=1 h pieces without changing activity."""

    start = _utc(start_utc, field="start_utc")
    duration = _positive(duration_s, field="duration_s")
    total = _nonnegative(total_activity_bq, field="total_activity_bq")
    if not isinstance(species, TritiumAtmosphericForm):
        raise UFOTRINativeAtmosphereError("species must be explicit HT or HTO")
    if not isinstance(source_id, str) or not source_id.strip():
        raise UFOTRINativeAtmosphereError("source_id is required")

    rate = total / duration
    remaining = duration
    cursor = start
    slices: list[NativeReleaseSlice] = []
    while remaining > 1.0e-12:
        dt = min(3600.0, remaining)
        end = cursor + timedelta(seconds=dt)
        slices.append(
            NativeReleaseSlice(
                start_utc=cursor,
                end_utc=end,
                species=species,
                emission_rate_bq_s=rate,
                released_activity_bq=rate * dt,
                source_id=source_id,
            )
        )
        cursor = end
        remaining -= dt

    # Close the cumulative ledger exactly to the requested total by adjusting
    # only the final stored activity at floating-point roundoff scale.
    if slices:
        before_last = sum(item.released_activity_bq for item in slices[:-1])
        last = slices[-1]
        exact_last_activity = total - before_last
        slices[-1] = NativeReleaseSlice(
            start_utc=last.start_utc,
            end_utc=last.end_utc,
            species=last.species,
            emission_rate_bq_s=last.emission_rate_bq_s,
            released_activity_bq=exact_last_activity,
            source_id=last.source_id,
        )
    return tuple(slices)


@dataclass(frozen=True)
class NativeSpeciesPolicy:
    species: TritiumAtmosphericForm
    dry_deposition_velocity_m_s: float
    hto_washout_coefficient_s_1: float = 0.0
    atmospheric_ht_to_hto_conversion_rate_s_1: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.species, TritiumAtmosphericForm):
            raise UFOTRINativeAtmosphereError("species must be explicit HT or HTO")
        _nonnegative(
            self.dry_deposition_velocity_m_s,
            field="dry_deposition_velocity_m_s",
        )
        washout = _nonnegative(
            self.hto_washout_coefficient_s_1,
            field="hto_washout_coefficient_s_1",
        )
        oxidation = _nonnegative(
            self.atmospheric_ht_to_hto_conversion_rate_s_1,
            field="atmospheric_ht_to_hto_conversion_rate_s_1",
        )
        if self.species is TritiumAtmosphericForm.HT and washout != 0.0:
            raise UFOTRINativeAtmosphereError(
                "KfK 4605 treats HT wet deposition as negligible"
            )
        if oxidation != 0.0:
            raise UFOTRINativeAtmosphereError(
                "KfK 4605 Section 2.2 excludes atmospheric HT->HTO conversion"
            )

    @property
    def wet_scavenging_rate_s_1(self) -> float:
        return (
            self.hto_washout_coefficient_s_1
            if self.species is TritiumAtmosphericForm.HTO
            else 0.0
        )


@dataclass(frozen=True)
class NativeSourceDepletion:
    source_before_bq_s: float
    source_after_bq_s: float
    dry_loss_bq_s: float
    wet_loss_bq_s: float
    travel_time_s: float

    @property
    def residual_bq_s(self) -> float:
        return (
            self.source_before_bq_s
            - self.source_after_bq_s
            - self.dry_loss_bq_s
            - self.wet_loss_bq_s
        )


def source_depletion_compatibility(
    source_bq_s: float,
    downwind_m: float,
    wind_speed_m_s: float,
    mixing_lid_m: float,
    policy: NativeSpeciesPolicy,
) -> NativeSourceDepletion:
    """Controlled source-depletion approximation with an explicit ledger.

    KfK 4605 identifies a source-depletion model but does not print the full
    original MUSEMET discretisation.  Until that source is recovered, the
    compatibility path uses a well-audited first-order removal rate
    ``v_d / h + Lambda_w`` over travel time ``x / u``.  The result must not be
    labelled original MUSEMET numerical equivalence.
    """

    before = _nonnegative(source_bq_s, field="source_bq_s")
    x = _nonnegative(downwind_m, field="downwind_m")
    u = _positive(wind_speed_m_s, field="wind_speed_m_s")
    lid = _positive(mixing_lid_m, field="mixing_lid_m")
    if not isinstance(policy, NativeSpeciesPolicy):
        raise UFOTRINativeAtmosphereError("policy must be NativeSpeciesPolicy")
    travel_time = x / u
    dry_rate = policy.dry_deposition_velocity_m_s / lid
    wet_rate = policy.wet_scavenging_rate_s_1
    total_rate = dry_rate + wet_rate
    if before == 0.0 or travel_time == 0.0 or total_rate == 0.0:
        return NativeSourceDepletion(before, before, 0.0, 0.0, travel_time)

    after = before * math.exp(-total_rate * travel_time)
    loss = before - after
    dry_loss = loss * dry_rate / total_rate
    wet_loss = loss * wet_rate / total_rate
    return NativeSourceDepletion(before, after, dry_loss, wet_loss, travel_time)


@dataclass(frozen=True)
class NativePrimaryTransportResult:
    species: TritiumAtmosphericForm
    air_concentration_bq_m3: float
    dry_surface_flux_bq_m2_s: float
    effective_source_bq_s: float
    dry_source_loss_bq_s: float
    wet_source_loss_bq_s: float
    atmospheric_ht_to_hto_generated_bq_s: float
    source_depletion_residual_bq_s: float


def transport_straight_segment(
    *,
    source_bq_s: float,
    downwind_m: float,
    crosswind_m: float,
    wind_speed_m_s: float,
    effective_release_height_m: float,
    receptor_height_m: float,
    stability_class: str,
    mixing_lid_m: float,
    policy: NativeSpeciesPolicy,
) -> NativePrimaryTransportResult:
    """Run one recovered straight hourly-segment transport calculation."""

    depletion = source_depletion_compatibility(
        source_bq_s,
        max(_finite(downwind_m, field="downwind_m"), 0.0),
        wind_speed_m_s,
        mixing_lid_m,
        policy,
    )
    concentration = gaussian_concentration_bq_m3(
        depletion.source_after_bq_s,
        downwind_m,
        crosswind_m,
        wind_speed_m_s,
        effective_release_height_m,
        receptor_height_m,
        stability_class,
        mixing_lid_m=mixing_lid_m,
    )
    dry_flux = policy.dry_deposition_velocity_m_s * concentration
    return NativePrimaryTransportResult(
        species=policy.species,
        air_concentration_bq_m3=concentration,
        dry_surface_flux_bq_m2_s=dry_flux,
        effective_source_bq_s=depletion.source_after_bq_s,
        dry_source_loss_bq_s=depletion.dry_loss_bq_s,
        wet_source_loss_bq_s=depletion.wet_loss_bq_s,
        atmospheric_ht_to_hto_generated_bq_s=0.0,
        source_depletion_residual_bq_s=depletion.residual_bq_s,
    )


def kfk4605_iter_benchmark_policy(species: TritiumAtmosphericForm) -> NativeSpeciesPolicy:
    """Expose Appendix-B deposition values without enabling air oxidation."""

    if species is TritiumAtmosphericForm.HT:
        return NativeSpeciesPolicy(
            species=species,
            dry_deposition_velocity_m_s=KFK4605_ITER_HT_DRY_DEPOSITION_VELOCITY_M_S,
        )
    if species is TritiumAtmosphericForm.HTO:
        return NativeSpeciesPolicy(
            species=species,
            dry_deposition_velocity_m_s=KFK4605_ITER_HTO_DRY_DEPOSITION_VELOCITY_M_S,
        )
    raise UFOTRINativeAtmosphereError("species must be HT or HTO")


@dataclass(frozen=True)
class AtmosphericOxidationEvidence:
    section22_program_includes_air_conversion: bool = False
    section22_reason: str = "conversion slow; half-time of some years"
    iter_benchmark_input_fraction_d_1: float = KFK4605_ITER_AIR_OXIDATION_FRACTION_D_1
    active_in_kfk4605_fidelity_path: bool = False
    source_conflict_preserved: bool = True


def atmospheric_oxidation_evidence() -> AtmosphericOxidationEvidence:
    return AtmosphericOxidationEvidence()


__all__ = [
    "AtmosphericOxidationEvidence",
    "KFK4605_ITER_AIR_OXIDATION_FRACTION_D_1",
    "KFK4605_ITER_HT_DRY_DEPOSITION_VELOCITY_M_S",
    "KFK4605_ITER_HTO_DRY_DEPOSITION_VELOCITY_M_S",
    "MOL_SMOOTH_TERRAIN_COEFFICIENTS",
    "MolDispersionCoefficients",
    "NativePrimaryTransportResult",
    "NativeReleaseSlice",
    "NativeSourceDepletion",
    "NativeSpeciesPolicy",
    "TritiumAtmosphericForm",
    "UFOTRINativeAtmosphereError",
    "atmospheric_oxidation_evidence",
    "gaussian_concentration_bq_m3",
    "kfk4605_iter_benchmark_policy",
    "mol_sigma_m",
    "source_depletion_compatibility",
    "split_release_into_hourly_slices",
    "transport_straight_segment",
    "wind_speed_power_law_m_s",
]
