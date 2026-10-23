"""P2 R4: opt-in *conditional* Eq.(32) day/night activity-budget diagnostic.

KfK 5194 (1993) printed pp.22-23, Eq.(32): T_act = (T_m,d / 24 h)
* fact1 * fact2, fact2=1.75 daylight / 0.25 night. The printed
normalization only holds under a 12 h daylight/12 h night reference day.
R3 maps crop-specific T_m,d to the checked COMA Tables 9–12.

The activity operator below is an explicitly selected *isolated fixed-pool,
one-way first-order hypothetical test*. The manual's HTO->OBT transfer
rate does NOT by itself establish this as the historical complete kinetic
integrator. No respiration, source replenishment, radioactive decay,
exchangeable OBT, soil/leaf or food-chain fluxes are represented; no
production runtime imports this module. The source of both activity pools
must be identical Bq/m2 ground units.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan, KFK5194OBTFormationMode, KFK5194SolarPeriod,
    KFK5194PhotoOBTError, kfk5194_1993_obt_formation_rate,
)
from .kfk5194_1993_p2_crop_rate_source import (
    KFK5194P2CropSourceRate, audit_kfk5194_1993_p2_crop_source_rate,
)


class KFK5194R4Hypothesis(str, Enum):
    ISOLATED_ONE_WAY_FIXED_AREAL_POOLS = "ISOLATED_ONE_WAY_FIXED_AREAL_POOLS"


@dataclass(frozen=True, slots=True)
class KFK5194R4DayPart:
    period: KFK5194SolarPeriod
    duration_hours: float


@dataclass(frozen=True, slots=True)
class KFK5194R4BudgetStep:
    period: KFK5194SolarPeriod
    duration_hours: float
    start_hto_bq_m2: float
    end_hto_bq_m2: float
    start_obt_bq_m2: float
    end_obt_bq_m2: float
    effective_rate_per_h: float
    formation_transfer_bq_m2: float
    activity_closure_residual_bq_m2: float


@dataclass(frozen=True, slots=True)
class KFK5194R4DayBudget:
    source: KFK5194P2CropSourceRate
    segments: tuple[KFK5194R4BudgetStep, ...]
    daytime_hours: float
    nighttime_hours: float
    mean_coefficient_integral: float
    weighted_daily_factor: float
    initial_total_bq_m2: float
    final_hto_bq_m2: float
    final_obt_bq_m2: float
    cumulative_transfer_bq_m2: float
    full_day_activity_closure_residual_bq_m2: float
    historical_12_12_reference_matched: bool

    def provenance(self) -> dict[str, object]:
        return {
            "authority": "KFK5194_1993_PRINTED_P22_23_EQ32",
            "composite_source_rate": "KFK5194_COMA_TABLE9_12_DOCUMENTARY_MAPPING",
            "physical_integrator": "CONDITIONAL_ISOLATED_FIRST_ORDER_RESEARCH_OPERATOR",
            "source_activity_basis": "Bq_per_m2_ground_both_pools",
            "source_mass_normalization": "NO_TABLE1_G_TO_G_PER_M2_ASSUMED",
            "day_night_reference": "12_H_DAY_AND_12_H_NIGHT",
            "historical_reference_matched": self.historical_12_12_reference_matched,
            "daylight_branch": "EMPIRICAL_1_75",
            "night_branch": "SIMPLE_EQ32_EMPIRICAL_0_25_NOT_EQ33",
            "advanced_eq33_night_branch": "NOT_ESTABLISHED_NOT_EXECUTED",
            "atmospheric_exchange_soil_growth_decay": "NOT_INCLUDED",
            "original_fortran_parity": "NOT_ESTABLISHED",
            "scientific_acceptance": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def _nonnegative(name: str, value: float, *, strict: bool = False) -> float:
    if type(value) not in (float, int) or not math.isfinite(float(value)):
        raise KFK5194PhotoOBTError(f"{name} must be a finite numeric value")
    x = float(value)
    if x < 0.0 or (strict and x == 0.0):
        raise KFK5194PhotoOBTError(f"{name} must be nonnegative/positive")
    return x


def audit_kfk5194_1993_r4_eq32_diurnal_budget(
    *,
    profile: Historical1993SourceProfile,
    crop_organ: KFK5194CropOrgan,
    pinned_table_source: Path,
    segments: tuple[KFK5194R4DayPart, ...],
    externally_supplied_fig11_factor: float,
    initial_hto_bq_m2_ground: float,
    initial_obt_bq_m2_ground: float,
    hypothesis: KFK5194R4Hypothesis,
    require_historical_12_12_reference: bool = True,
) -> KFK5194R4DayBudget:
    """Mathematically exact nonnegative isolated-pool operator for Eq32.

    For rate k_j [h^-1], dt_j [h], F_j = H_j * (1-exp(-k_j*dt_j));
    H_(j+1)=H_j-F_j; B_(j+1)=B_j+F_j. Each step is closed,
    yet this only tests a CONDITIONAL model operator, not the real
    1993 physiological one or the COMA coupled source/sink graph.
    """
    if hypothesis is not KFK5194R4Hypothesis.ISOLATED_ONE_WAY_FIXED_AREAL_POOLS:
        raise KFK5194PhotoOBTError("explicit isolated-pool research hypothesis required")
    if type(require_historical_12_12_reference) is not bool:
        raise KFK5194PhotoOBTError("historical reference policy must be boolean")
    if not isinstance(segments, tuple) or not segments:
        raise KFK5194PhotoOBTError("complete 24h day partition tuple required")
    if len(segments) > 10000:
        raise KFK5194PhotoOBTError("excessively fragmented research partition")
    f11 = _nonnegative("explicit external Figure 11 factor",
                       externally_supplied_fig11_factor)
    h = _nonnegative("initial HTO activity Bq/m2 ground", initial_hto_bq_m2_ground)
    b = _nonnegative("initial OBT activity Bq/m2 ground", initial_obt_bq_m2_ground)
    origin = math.fsum((h, b))
    if not math.isfinite(origin):
        raise KFK5194PhotoOBTError("nonfinite initial activity total")
    src = audit_kfk5194_1993_p2_crop_source_rate(
        profile=profile, crop_organ=crop_organ, pinned_table_source=pinned_table_source
    )
    daytime = 0.0
    nighttime = 0.0
    for part in segments:
        if not isinstance(part, KFK5194R4DayPart) or not isinstance(
            part.period, KFK5194SolarPeriod
        ):
            raise KFK5194PhotoOBTError("explicit day/night enum segment required")
        duration = _nonnegative("segment duration in hours",
                                part.duration_hours, strict=True)
        if duration > 24:
            raise KFK5194PhotoOBTError("segment exceeds one day")
        if part.period is KFK5194SolarPeriod.DAY:
            daytime += duration
        else:
            nighttime += duration
    if not math.isclose(math.fsum((daytime, nighttime)), 24.,
                        rel_tol=0., abs_tol=1e-10):
        raise KFK5194PhotoOBTError("complete exactly 24h period required")
    reference = (
        math.isclose(daytime, 12.0, abs_tol=1e-10, rel_tol=0)
        and math.isclose(nighttime, 12.0, abs_tol=1e-10, rel_tol=0)
    )
    if require_historical_12_12_reference and not reference:
        raise KFK5194PhotoOBTError(
            "1993 1.75/0.25 daily normalization only source-grounded for 12/12; "
            "explicit diagnostic opt-out required for other photoperiods"
        )
    steps: list[KFK5194R4BudgetStep] = []
    total_formed = 0.0
    for part in segments:
        rate = kfk5194_1993_obt_formation_rate(
            profile=profile, crop_organ=crop_organ,
            mode=KFK5194OBTFormationMode.SIMPLE_EQ32,
            solar_period=part.period,
            mean_uniform_transfer_d_1=src.mean_hto_to_obt_d_1,
            external_fig11_phenology_factor=f11,
        ).actual_transfer_h_1
        if not math.isfinite(rate * part.duration_hours):
            raise KFK5194PhotoOBTError("nonfinite interval exponent")
        formed = h * (-math.expm1(-rate * part.duration_hours))
        h_new = h - formed
        b_new = b + formed
        if not all(map(math.isfinite, (formed, h_new, b_new))):
            raise KFK5194PhotoOBTError("nonfinite research ledger state")
        residual = math.fsum((h_new, b_new, -h, -b))
        scale = max(1., abs(h), abs(b), abs(h_new), abs(b_new))
        if h_new < -1e-13 * scale or b_new < 0 or abs(residual) > 5e-13 * scale:
            raise KFK5194PhotoOBTError("isolated-pool activity budget violation")
        steps.append(KFK5194R4BudgetStep(
            period=part.period, duration_hours=part.duration_hours,
            start_hto_bq_m2=h, end_hto_bq_m2=h_new,
            start_obt_bq_m2=b, end_obt_bq_m2=b_new,
            effective_rate_per_h=rate, formation_transfer_bq_m2=formed,
            activity_closure_residual_bq_m2=residual,
        ))
        total_formed += formed
        h, b = h_new, b_new
    final_residual = math.fsum((h, b, -origin))
    if (not math.isfinite(total_formed) or not math.isfinite(final_residual)
            or abs(final_residual) > 5e-13 * max(1., origin)):
        raise KFK5194PhotoOBTError("whole-day activity budget violation")
    coefficient_integral = src.mean_hto_to_obt_d_1 * f11 * (
        1.75*daytime + 0.25*nighttime
    ) / 24.
    factor = (1.75*daytime + 0.25*nighttime) / 24.
    return KFK5194R4DayBudget(
        source=src, segments=tuple(steps),
        daytime_hours=daytime, nighttime_hours=nighttime,
        mean_coefficient_integral=coefficient_integral,
        weighted_daily_factor=factor,
        initial_total_bq_m2=origin,
        final_hto_bq_m2=h, final_obt_bq_m2=b,
        cumulative_transfer_bq_m2=total_formed,
        full_day_activity_closure_residual_bq_m2=final_residual,
        historical_12_12_reference_matched=reference,
    )
