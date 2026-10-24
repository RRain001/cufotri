"""H4 reconciliation for the UFOTRI-native atmospheric process path.

This module supersedes the H1 controlled source-depletion approximation for
H4-and-later native-atmosphere execution while retaining the H1 helper as
historical compatibility evidence.

Directly recovered in H4:

* KfK 4332 Eq. (2.20) source-depletion relation for dry deposition;
* KfK 4332 Eq. (2.27) exponential wet-scavenging correction;
* KfK 5194 ``IWASH=0`` three-class HTO washout coefficients and relative
  precipitation durations;
* KfK 5194 ``IWASH=1`` HTO washout power law.

The original MUSEMET closed-form three-case source-depletion discretisation,
the complete building-wake numerics, the numerical LIFTOF Eq. (3.22), and the
PLRISE/RISEFX plume-rise numerics remain source-limited. They are not replaced
with modern surrogate models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .ufotri_native_v4 import (
    MOL_SMOOTH_TERRAIN_COEFFICIENTS,
    NativePrimaryTransportResult,
    NativeSourceDepletion,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    UFOTRINativeAtmosphereError,
    _finite,
    _nonnegative,
    _positive,
    gaussian_concentration_bq_m3,
)


class KFK5194HTOWashoutMode(str, Enum):
    PRECALCULATED_CLASSES = "IWASH_0_PRECALCULATED_CLASSES"
    POWER_LAW = "IWASH_1_POWER_LAW"


@dataclass(frozen=True)
class KFK5194WashoutResult:
    species: TritiumAtmosphericForm
    mode: KFK5194HTOWashoutMode
    precipitation_mm_h: float
    coefficient_s_1: float
    mean_relative_precipitation_duration: float | None
    source_status: str


@dataclass(frozen=True)
class KFK4332LiftOffEvidence:
    threshold_lp: float = 30.0
    thermal_buoyancy_dominates_above_threshold: bool = True
    numeric_equation_322_recovered: bool = False
    building_wake_complete_numerics_recovered: bool = False
    plume_rise_complete_numerics_recovered: bool = False
    status: str = "SOURCE_LIMITED_EQ322_OCR_AMBIGUOUS"




def kfk5194_washout(
    *,
    species: TritiumAtmosphericForm,
    precipitation_mm_h: float,
    mode: KFK5194HTOWashoutMode,
) -> KFK5194WashoutResult:
    """Return the directly recovered KfK 5194 HTO washout parameterisation.

    ``IWASH=0``:
      * I < 1 mm/h: 6e-5 s^-1, REGTIM=0.5
      * 1 <= I < 3 mm/h: 1e-4 s^-1, REGTIM=0.75
      * I >= 3 mm/h: 4e-4 s^-1, REGTIM=0.72

    ``IWASH=1``:
      ``lambda = 9e-5 * I**0.6`` for HTO.

    The KfK 5194 listing prints ``REGTIM(NN,1): see above`` for the power-law
    option but does not expose an unambiguous numeric default in the recovered
    evidence. H4 therefore returns ``None`` rather than inventing one.
    """

    if not isinstance(species, TritiumAtmosphericForm):
        raise UFOTRINativeAtmosphereError("species must be explicit HT or HTO")
    if not isinstance(mode, KFK5194HTOWashoutMode):
        raise UFOTRINativeAtmosphereError("mode must be KFK5194HTOWashoutMode")
    intensity = _nonnegative(precipitation_mm_h, field="precipitation_mm_h")

    if mode is KFK5194HTOWashoutMode.PRECALCULATED_CLASSES:
        if intensity < 1.0:
            hto_coefficient = 6.0e-5
            hto_duration = 0.5
        elif intensity < 3.0:
            hto_coefficient = 1.0e-4
            hto_duration = 0.75
        else:
            hto_coefficient = 4.0e-4
            hto_duration = 0.72
        if species is TritiumAtmosphericForm.HT:
            return KFK5194WashoutResult(
                species=species,
                mode=mode,
                precipitation_mm_h=intensity,
                coefficient_s_1=0.0,
                mean_relative_precipitation_duration=0.0,
                source_status="RECOVERED_KFK5194_IWASH0_HT_ZERO",
            )
        return KFK5194WashoutResult(
            species=species,
            mode=mode,
            precipitation_mm_h=intensity,
            coefficient_s_1=0.0 if intensity == 0.0 else hto_coefficient,
            mean_relative_precipitation_duration=hto_duration,
            source_status="RECOVERED_KFK5194_IWASH0",
        )

    if species is TritiumAtmosphericForm.HT:
        return KFK5194WashoutResult(
            species=species,
            mode=mode,
            precipitation_mm_h=intensity,
            coefficient_s_1=0.0,
            mean_relative_precipitation_duration=None,
            source_status="RECOVERED_KFK5194_IWASH1_HT_ZERO_REGTIM_SOURCE_LIMITED",
        )

    coefficient = 0.0 if intensity == 0.0 else 9.0e-5 * intensity**0.6
    return KFK5194WashoutResult(
        species=species,
        mode=mode,
        precipitation_mm_h=intensity,
        coefficient_s_1=coefficient,
        mean_relative_precipitation_duration=None,
        source_status="RECOVERED_KFK5194_IWASH1_REGTIM_SOURCE_LIMITED",
    )


def kfk5194_species_policy(
    *,
    species: TritiumAtmosphericForm,
    dry_deposition_velocity_m_s: float,
    precipitation_mm_h: float,
    mode: KFK5194HTOWashoutMode,
) -> NativeSpeciesPolicy:
    washout = kfk5194_washout(
        species=species,
        precipitation_mm_h=precipitation_mm_h,
        mode=mode,
    )
    return NativeSpeciesPolicy(
        species=species,
        dry_deposition_velocity_m_s=dry_deposition_velocity_m_s,
        hto_washout_coefficient_s_1=washout.coefficient_s_1,
    )


def _simpson_regularised_uncapped_integral(
    *,
    x_end_m: float,
    release_height_m: float,
    p_z: float,
    q_z: float,
    panels: int = 512,
) -> float:
    """Integrate Eq. (2.20)'s uncapped term after regularising x=0.

    With ``t=x**(1-q_z)``, the integrand becomes finite at the source:
    ``exp(-H^2/(2 sigma_z^2)) / (p_z * (1-q_z))``.
    """

    if x_end_m <= 0.0:
        return 0.0
    if panels <= 0 or panels % 2:
        raise UFOTRINativeAtmosphereError(
            "integration panels must be positive and even"
        )

    one_minus_q = 1.0 - q_z
    t_end = x_end_m**one_minus_q
    dt = t_end / panels

    def f(t: float) -> float:
        if t == 0.0:
            attenuation = 1.0 if release_height_m == 0.0 else 0.0
            return attenuation / (p_z * one_minus_q)
        x = t ** (1.0 / one_minus_q)
        sigma_z = p_z * x**q_z
        attenuation = math.exp(-0.5 * (release_height_m / sigma_z) ** 2)
        return attenuation / (p_z * one_minus_q)

    total = f(0.0) + f(t_end)
    for index in range(1, panels):
        total += (4.0 if index % 2 else 2.0) * f(index * dt)
    return total * dt / 3.0


def kfk4332_source_depletion_integral_m(
    *,
    downwind_m: float,
    effective_release_height_m: float,
    stability_class: str,
    mixing_lid_m: float,
) -> float:
    """Evaluate the direct KfK 4332 Eq. (2.20) integral.

    ``I = integral_0^x exp(-H^2/(2 sigma_z^2)) / sigma_z dx``.

    H4 uses the already qualified Mol ``sigma_z`` power law and its KfK 4605
    ``0.8 hmix`` cap. This recovers the printed depletion equation without
    claiming the unavailable original MUSEMET closed-form three-case code.
    """

    x = _nonnegative(downwind_m, field="downwind_m")
    h = _nonnegative(
        effective_release_height_m, field="effective_release_height_m"
    )
    lid = _positive(mixing_lid_m, field="mixing_lid_m")
    if x == 0.0:
        return 0.0
    if not isinstance(stability_class, str):
        raise UFOTRINativeAtmosphereError("stability_class must be A-F")
    key = stability_class.upper()
    try:
        coefficients = MOL_SMOOTH_TERRAIN_COEFFICIENTS[key]
    except KeyError as exc:
        raise UFOTRINativeAtmosphereError(
            f"unsupported Mol stability class: {stability_class!r}"
        ) from exc

    sigma_cap = 0.8 * lid
    x_cap = (sigma_cap / coefficients.p_z) ** (1.0 / coefficients.q_z)
    uncapped_end = min(x, x_cap)
    integral = _simpson_regularised_uncapped_integral(
        x_end_m=uncapped_end,
        release_height_m=h,
        p_z=coefficients.p_z,
        q_z=coefficients.q_z,
    )
    if x > x_cap:
        attenuation = math.exp(-0.5 * (h / sigma_cap) ** 2)
        integral += (x - x_cap) * attenuation / sigma_cap
    return integral


def source_depletion_kfk4332(
    *,
    source_bq_s: float,
    downwind_m: float,
    wind_speed_m_s: float,
    effective_release_height_m: float,
    stability_class: str,
    mixing_lid_m: float,
    policy: NativeSpeciesPolicy,
) -> NativeSourceDepletion:
    """Recovered KfK 4332 dry Eq. (2.20) + wet Eq. (2.27) depletion.

    Dry and wet correction factors are independent multiplicative factors.
    For an auditable activity ledger, H4 applies the dry factor first and the
    wet factor second; the final source strength is independent of that
    bookkeeping order.
    """

    before = _nonnegative(source_bq_s, field="source_bq_s")
    x = _nonnegative(downwind_m, field="downwind_m")
    u = _positive(wind_speed_m_s, field="wind_speed_m_s")
    if not isinstance(policy, NativeSpeciesPolicy):
        raise UFOTRINativeAtmosphereError("policy must be NativeSpeciesPolicy")

    integral = kfk4332_source_depletion_integral_m(
        downwind_m=x,
        effective_release_height_m=effective_release_height_m,
        stability_class=stability_class,
        mixing_lid_m=mixing_lid_m,
    )
    dry_exponent = (
        math.sqrt(2.0 / math.pi)
        * policy.dry_deposition_velocity_m_s
        / u
        * integral
    )
    wet_exponent = policy.wet_scavenging_rate_s_1 * x / u
    after_dry = before * math.exp(-dry_exponent)
    after = after_dry * math.exp(-wet_exponent)
    return NativeSourceDepletion(
        source_before_bq_s=before,
        source_after_bq_s=after,
        dry_loss_bq_s=before - after_dry,
        wet_loss_bq_s=after_dry - after,
        travel_time_s=x / u,
    )


def transport_straight_segment_reconciled(
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
    """H4-and-later authoritative straight-segment native transport."""

    x = _finite(downwind_m, field="downwind_m")
    depletion = source_depletion_kfk4332(
        source_bq_s=source_bq_s,
        downwind_m=max(x, 0.0),
        wind_speed_m_s=wind_speed_m_s,
        effective_release_height_m=effective_release_height_m,
        stability_class=stability_class,
        mixing_lid_m=mixing_lid_m,
        policy=policy,
    )
    concentration = gaussian_concentration_bq_m3(
        depletion.source_after_bq_s,
        x,
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


def kfk4332_liftoff_evidence() -> KFK4332LiftOffEvidence:
    """Expose the recovered threshold without inventing ambiguous Eq. (3.22)."""

    return KFK4332LiftOffEvidence()


__all__ = [
    "KFK4332LiftOffEvidence",
    "KFK5194HTOWashoutMode",
    "KFK5194WashoutResult",
    "kfk4332_liftoff_evidence",
    "kfk4332_source_depletion_integral_m",
    "kfk5194_species_policy",
    "kfk5194_washout",
    "source_depletion_kfk4332",
    "transport_straight_segment_reconciled",
]
