"""Source-visible, opt-in KfK 5194 §5.5.1 Eq.(28)-(30) audit.

This module intentionally does NOT select a canopy assimilation formula for
production: the literal printed Eq.(28) and the integral of printed Eq.(26)
and Eq.(27) disagree. Both are computed and labelled; neither is coupled to
Eq.(31) or the OBT inventory. KfK 5194 (1993), printed p.20 (PDF0 p.29).
No original 1993 executable, coefficients or physical calibration available.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from cteas_ufotri.versioned_inputs_1993 import (
    Historical1993SourceProfile, PROFILE_ID,
)
from .kfk5194_1993_photo_obt_rates import PAR_EXTINCTION_K, KFK5194PhotoOBTError


def _require_profile(profile: Historical1993SourceProfile) -> None:
    if not isinstance(profile, Historical1993SourceProfile) or profile.profile_id != PROFILE_ID:
        raise KFK5194PhotoOBTError("explicit KFK5194_1993_V4 source profile required")
    if dict(profile.flag_defaults).get("IPHOTO") != 1:
        raise KFK5194PhotoOBTError("historical IPHOTO=1 source profile required")


def _real(name: str, value: float, *, strictly_positive: bool = False) -> float:
    if type(value) not in (float, int) or not math.isfinite(float(value)):
        raise KFK5194PhotoOBTError(f"{name} must be a finite number (not bool)")
    n = float(value)
    if n < 0.0 or (strictly_positive and n == 0.0):
        raise KFK5194PhotoOBTError(f"{name} must be nonnegative or positive as required")
    return n


def _signed(name: str, value: float) -> float:
    if type(value) not in (float, int) or not math.isfinite(float(value)):
        raise KFK5194PhotoOBTError(f"{name} must be a finite numeric quantity")
    return float(value)


@dataclass(frozen=True, slots=True)
class KFK5194Eq28PrintedVsIntegrated:
    """Both results in g CO2/m² ground/h on the stated R2 area convention.

    This area assignment is a research interpretation of Eq.(26)-(28) and
    remains pending original source/executable units review.
    """

    incident_par_w_m2_ground: float
    lai_m2_leaf_per_m2_ground: float
    bottom_absorbed_par_w_m2_leaf: float
    printed_eq28_pc_g_co2_m2_ground_h: float
    integrated_eq26_27_pc_g_co2_m2_ground_h: float
    printed_minus_integrated_g_co2_m2_ground_h: float

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KFK5194_1993_PRINTED_P20_EQ26_27_28",
            "printed_denominator": "P_M_PLUS_EPSILON_TIMES_K_TIMES_I_ABS",
            "eq27_i_abs": "INCIDENT_PAR_TIMES_K_TIMES_EXP_MINUS_K_L",
            "printed_respiration_term": "MINUS_RD_ONCE",
            "mathematical_integral_respiration": "MINUS_RD_TIMES_LAI",
            "disposition": "FORMULAE_NOT_EQUIVALENT_DO_NOT_AUTO_SELECT",
            "exact_1993_fortran_or_empirical_equivalence": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def audit_kfk5194_1993_eq28_canopy(
    *,
    profile: Historical1993SourceProfile,
    incident_par_w_m2_ground: float,
    lai_m2_leaf_per_m2_ground: float,
    maximum_co2_g_m2_leaf_h: float,
    initial_light_efficiency_g_co2_per_w_h: float,
    respiration_g_co2_m2_leaf_h: float,
) -> KFK5194Eq28PrintedVsIntegrated:
    """Compare *literal* Eq.(28) with independent integration of Eq.(26)-(27).

    Literal printed numerator Pm + epsilon*k*I_in and denominator
    Pm + epsilon*k*I_abs(LAI), where Eq.(27) defines
    I_abs(LAI)=I_in*k*exp(-k*LAI). Eq.(28) subtracts Rd only once.
    By calculus the integral instead uses denominator Pm + epsilon*I_abs(LAI)
    and subtracts LAI*Rd. This is a scientific discrepancy, not a choice of
    production algorithm.
    """
    _require_profile(profile)
    incident = _real("incident PAR", incident_par_w_m2_ground)
    lai = _real("LAI", lai_m2_leaf_per_m2_ground)
    pm = _real("Eq26 maximum CO2", maximum_co2_g_m2_leaf_h, strictly_positive=True)
    epsilon = _real("light use efficiency", initial_light_efficiency_g_co2_per_w_h)
    respiration = _real("respiration", respiration_g_co2_m2_leaf_h)
    k = PAR_EXTINCTION_K
    bottom_par = incident * k * math.exp(-k * lai)
    common_top = epsilon * k * incident / pm
    # log1p helps in the weak-light limit, and never forms a ratio of
    # potentially overflowing intermediates.
    log_numerator = math.log1p(common_top)
    literal = pm/k * (
        log_numerator - math.log1p(epsilon * k * bottom_par / pm)
    ) - respiration
    integrated = pm/k * (
        log_numerator - math.log1p(epsilon * bottom_par / pm)
    ) - respiration * lai
    residual = literal - integrated
    if not all(math.isfinite(x) for x in (bottom_par, literal, integrated, residual)):
        raise KFK5194PhotoOBTError("Eq28 overflow/nonfinite source audit")
    return KFK5194Eq28PrintedVsIntegrated(
        incident_par_w_m2_ground=incident,
        lai_m2_leaf_per_m2_ground=lai,
        bottom_absorbed_par_w_m2_leaf=bottom_par,
        printed_eq28_pc_g_co2_m2_ground_h=literal,
        integrated_eq26_27_pc_g_co2_m2_ground_h=integrated,
        printed_minus_integrated_g_co2_m2_ground_h=residual,
    )


@dataclass(frozen=True, slots=True)
class KFK5194Eq29TemperatureAudit:
    """Unconverted printed Eq.(29) Pm expression; output units UNRESOLVED."""

    temperature_kelvin: float
    co_source_mg_co2_m2_h: float
    printed_pm_raw: float

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KFK5194_1993_PRINTED_P20_EQ29",
            "printed_numerator": "0_158_TIMES_CO_TIMES_10_POWER_9_TIMES_T_EXP_MINUS_DH1_OVER_RT",
            "printed_denominator": "1_PLUS_EXP_MINUS_DH2_OVER_RT_TIMES_EXP_MINUS_DS_OVER_R",
            "co_unit_printed": "MG_CO2_M2_H",
            "eq26_pm_unit_printed": "G_CO2_M2_H",
            "conversion_to_eq26": "NOT_ESTABLISHED",
            "use_as_eq26_pm": "PROHIBITED_WITHOUT_INDEPENDENT_UNIT_AUDIT",
            "temperature_basis": "KELVIN",
            "production_runtime_activated": False,
        }


def audit_kfk5194_1993_eq29_temperature(
    *,
    profile: Historical1993SourceProfile,
    temperature_kelvin: float,
    co_source_mg_co2_m2_h: float,
    activation_energy_dh1_cal_mol: float,
    denaturation_energy_dh2_cal_mol: float,
    entropy_change_ds_cal_mol_kelvin: float,
    gas_constant_r_cal_mol_kelvin: float,
) -> KFK5194Eq29TemperatureAudit:
    """Evaluate literal Eq29 robustly, WITHOUT inventing CO mg->Pm g scaling.

    All plant-specific values are explicit inputs. Source printed Pm in g
    (Eq26) but CO as mg in Eq29: the internal 10^9 scaling is preserved.
    Caller may not pass this raw result straight into Eq26 as a verified Pm.
    """
    _require_profile(profile)
    t = _real("temperature_kelvin", temperature_kelvin, strictly_positive=True)
    co = _real("Eq29 CO", co_source_mg_co2_m2_h)
    dh1 = _real("activation energy", activation_energy_dh1_cal_mol)
    dh2 = _real("denaturation energy", denaturation_energy_dh2_cal_mol)
    ds = _signed("denaturation entropy change", entropy_change_ds_cal_mol_kelvin)
    r = _real("gas constant", gas_constant_r_cal_mol_kelvin, strictly_positive=True)
    # log(exp(x)+1) with overflow-safe softplus.
    x = -dh2/(r*t) - ds/r
    if not math.isfinite(x):
        raise KFK5194PhotoOBTError("nonfinite Eq29 exponent")
    softplus = math.log1p(math.exp(x)) if x <= 0 else x + math.log1p(math.exp(-x))
    if co == 0:
        pm = 0.0
    else:
        log_pm = (math.log(0.158) + math.log(co) + math.log(1e9)
                  + math.log(t) - dh1/(r*t) - softplus)
        if not math.isfinite(log_pm):
            raise KFK5194PhotoOBTError("nonfinite Eq29 logarithm")
        try:
            pm = math.exp(log_pm)
        except OverflowError as exc:
            raise KFK5194PhotoOBTError("Eq29 raw Pm overflow") from exc
    if not math.isfinite(pm):
        raise KFK5194PhotoOBTError("nonfinite Eq29 raw Pm")
    return KFK5194Eq29TemperatureAudit(
        temperature_kelvin=t, co_source_mg_co2_m2_h=co, printed_pm_raw=pm,
    )


@dataclass(frozen=True, slots=True)
class KFK5194Eq30RespirationAudit:
    """Signed input basis is explicitly CO2 equivalents per ground area."""

    canopy_pc_g_co2_m2_ground_h: float
    accumulated_biomass_g_co2_equiv_m2_ground: float
    total_respiration_g_co2_m2_ground_h: float

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KFK5194_1993_PRINTED_P20_EQ30",
            "c1_rd": 0.36,
            "c2_rd": 1.67e-4,
            "c2_units": "G_CO2_PER_H_PER_G_CO2_EQUIVALENT",
            "biomass_basis": "CO2_EQUIVALENTS_NOT_RAW_DRY_MATTER",
            "implicit_eq28_coupling": "NOT_RECONSTRUCTED",
            "production_runtime_activated": False,
        }


def audit_kfk5194_1993_eq30_respiration(
    *,
    profile: Historical1993SourceProfile,
    canopy_pc_g_co2_m2_ground_h: float,
    accumulated_biomass_g_co2_equiv_m2_ground: float,
) -> KFK5194Eq30RespirationAudit:
    """Printed Eq.(30): Rd=0.36*Pc + 1.67e-4*W, not an extra sink."""
    _require_profile(profile)
    pc = _real("nonnegative canopy CO2 assimilation", canopy_pc_g_co2_m2_ground_h)
    biomass = _real("biomass CO2 equivalents", accumulated_biomass_g_co2_equiv_m2_ground)
    respiration = math.fsum((0.36 * pc, 1.67e-4 * biomass))
    if not math.isfinite(respiration):
        raise KFK5194PhotoOBTError("nonfinite Eq30 respiration")
    return KFK5194Eq30RespirationAudit(
        canopy_pc_g_co2_m2_ground_h=pc,
        accumulated_biomass_g_co2_equiv_m2_ground=biomass,
        total_respiration_g_co2_m2_ground_h=respiration,
    )
