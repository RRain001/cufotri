"""Opt-in KfK 5194 (1993) IWASH=0 physical source-depletion budget.

Published source: W. Raskob, KfK 5194 (1993), section 7.3.3,
printed pages 46-47 (PDF zero-based 55-56). The published defaults
are distinct from the numerical assumption about how REGTIM is applied.
This routine is not used by the legacy configuration or CLI.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID,
    Historical1993SourceProfile,
)

from .ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode,
    kfk5194_washout,
    source_depletion_kfk4332,
)
from .ufotri_native_v4 import (
    NativeSourceDepletion,
    NativeSpeciesPolicy,
    TritiumAtmosphericForm,
    UFOTRINativeAtmosphereError,
)


class KFK5194DurationTreatment(str, Enum):
    """Explicit research choices; original FORTRAN REGTIM handling is unknown."""

    MEAN_FRACTION_OF_TRAVEL = "MEAN_FRACTION_OF_TRAVEL"
    FULL_RAIN_TRAVEL_UPPER_BOUND = "FULL_RAIN_TRAVEL_UPPER_BOUND"


@dataclass(frozen=True)
class KFK5194IWash0Budget:
    species: TritiumAtmosphericForm
    profile_id: str
    rain_mm_h: float
    rain_class: int | None
    documented_coefficient_s_1: float
    documented_relative_rain_duration: float
    effective_wet_removal_rate_s_1: float
    applied_travel_rain_fraction: float
    duration_treatment: KFK5194DurationTreatment
    depletion: NativeSourceDepletion

    @property
    def residual_bq_s(self) -> float:
        return self.depletion.residual_bq_s

    def provenance(self) -> dict[str, object]:
        return {
            "source_version": self.profile_id,
            "document": "KfK 5194 (1993), section 7.3.3, pp. 46-47",
            "source_pdf_zero_based_pages": [55, 56],
            "mode": "IWASH=0_THREE_PRECIPITATION_CLASSES",
            "regtim_treatment": self.duration_treatment.value,
            "original_regtim_application": "SOURCE_LIMITED_NOT_ESTABLISHED",
            "original_executable_numeric_equivalence": "NOT_ESTABLISHED",
            "integration": "KfK 4332 Eq. (2.27) reconstructed exponential wet factor",
            "scope": "EXPLICIT_OPT_IN_BUDGET_NOT_DEFAULT_RUNTIME",
        }


def _require_p1_profile(profile: Historical1993SourceProfile) -> None:
    """Refuse fabricated direct dataclass instances as source authority."""
    if not isinstance(profile, Historical1993SourceProfile):
        raise UFOTRINativeAtmosphereError("KfK5194 typed P1 profile is required")
    if (
        profile.profile_id != PROFILE_ID
        or profile.source_url !=
        "https://publikationen.bibliothek.kit.edu/270034158/3813483"
        or profile.nuclides != ("HT", "HTO")
        or profile.washout_mode != 0
        or profile.deposition_velocity_m_s != (0.0005, 0.005)
        or profile.washout_class_boundaries_mm_h != (1.0, 3.0)
        or profile.washout_hto_rates_per_s != (6.0e-5, 1.0e-4, 4.0e-4)
        or profile.washout_hto_duration_fraction != (0.5, 0.75, 0.72)
    ):
        raise UFOTRINativeAtmosphereError(
            "1993 source profile differs from approved KfK5194 IWASH=0 values"
        )


def kfk5194_iwash0_profiled_source_budget(
    *,
    profile: Historical1993SourceProfile,
    species: TritiumAtmosphericForm,
    precipitation_mm_h: float,
    source_bq_s: float,
    downwind_m: float,
    wind_speed_m_s: float,
    effective_release_height_m: float,
    stability_class: str,
    mixing_lid_m: float,
    duration_treatment: KFK5194DurationTreatment,
) -> KFK5194IWash0Budget:
    """Calculate 1993 opt-in dry/wet loss with separately identified REGTIM choice.

    Lambda [s^-1] and REGTIM [-] are documented KfK5194 class defaults.
    The effective wet exponent uses Lambda * (x/u) * f, where x/u is
    travel time in seconds. f=REGTIM is a **reconstruction assumption**;
    f=1 provides a defined full-rain upper-exposure comparison. The 1993
    source does not establish exact original FORTRAN REGTIM application.

    All source and removal quantities are Bq/s. Source depletion uses
    the independently recovered KfK4332 Eq.(2.20)/(2.27) machinery.
    This function does not alter an existing solver's default selection.
    """
    _require_p1_profile(profile)
    if not isinstance(species, TritiumAtmosphericForm):
        raise UFOTRINativeAtmosphereError("explicit HT or HTO species required")
    if not isinstance(duration_treatment, KFK5194DurationTreatment):
        raise UFOTRINativeAtmosphereError(
            "explicit, named mean-rain-duration reconstruction required"
        )
    washout = kfk5194_washout(
        species=species,
        precipitation_mm_h=precipitation_mm_h,
        mode=KFK5194HTOWashoutMode.PRECALCULATED_CLASSES,
    )
    rain = washout.precipitation_mm_h
    rain_class = None if rain == 0 else (1 if rain < 1 else (2 if rain < 3 else 3))
    dry_index = profile.nuclides.index(species.value)
    dry_velocity = profile.deposition_velocity_m_s[dry_index]

    if species is TritiumAtmosphericForm.HT or rain_class is None:
        documented_fraction = 0.0 if species is TritiumAtmosphericForm.HT else (
            profile.washout_hto_duration_fraction[0]
        )
        applied_fraction = 0.0
    else:
        documented_fraction = profile.washout_hto_duration_fraction[rain_class - 1]
        if not math.isclose(
            documented_fraction, washout.mean_relative_precipitation_duration,
            rel_tol=0, abs_tol=1e-14,
        ):
            raise UFOTRINativeAtmosphereError("P1 REGTIM/H4 source mismatch")
        if not math.isclose(
            washout.coefficient_s_1,
            profile.washout_hto_rates_per_s[rain_class - 1],
            rel_tol=0, abs_tol=1e-14,
        ):
            raise UFOTRINativeAtmosphereError("P1 AMDA/H4 source mismatch")
        applied_fraction = (
            documented_fraction
            if duration_treatment is KFK5194DurationTreatment.MEAN_FRACTION_OF_TRAVEL
            else 1.0
        )
    effective_rate = washout.coefficient_s_1 * applied_fraction
    policy = NativeSpeciesPolicy(
        species=species,
        dry_deposition_velocity_m_s=dry_velocity,
        hto_washout_coefficient_s_1=effective_rate,
    )
    budget = source_depletion_kfk4332(
        source_bq_s=source_bq_s,
        downwind_m=downwind_m,
        wind_speed_m_s=wind_speed_m_s,
        effective_release_height_m=effective_release_height_m,
        stability_class=stability_class,
        mixing_lid_m=mixing_lid_m,
        policy=policy,
    )
    return KFK5194IWash0Budget(
        species=species,
        profile_id=profile.profile_id,
        rain_mm_h=rain,
        rain_class=rain_class,
        documented_coefficient_s_1=washout.coefficient_s_1,
        documented_relative_rain_duration=documented_fraction,
        effective_wet_removal_rate_s_1=effective_rate,
        applied_travel_rain_fraction=applied_fraction,
        duration_treatment=duration_treatment,
        depletion=budget,
    )
