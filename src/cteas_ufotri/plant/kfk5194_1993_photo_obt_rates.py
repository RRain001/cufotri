"""Opt-in, source-scoped 1993 photosynthesis and HTO->OBT rate primitives.

Authority: Raskob, KfK 5194 (1993), printed pp.19-23 (PDF0 28-32),
Eq.(26), (27), (31), (32), (33). Eq.(28)-(30), original Eq.(33)
nighttime routing, historical Figure 11 time interpolation and tissue
inventory integration are NOT reconstructed by this module.

The 1990 KfK 4605 baseline, current TFWT/OBT integrators and CLI are
intentionally untouched. Synthetic inputs do not establish 1993 FORTRAN
numeric equivalence, photosynthetic validity or physical calibration.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import (
    Historical1993SourceProfile, PROFILE_ID,
)


class KFK5194PhotoOBTError(ValueError):
    """A required historical branch, unit or research boundary was violated."""


class KFK5194CropOrgan(str, Enum):
    GRASS_WHOLE = "GRASS_WHOLE"
    LEAFY_VEGETABLE_WHOLE = "LEAFY_VEGETABLE_WHOLE"
    POTATO_TUBER = "POTATO_TUBER"
    WHEAT_SEEDLINGS_PRINTED = "WHEAT_SEEDLINGS_PRINTED"


class KFK5194OBTFormationMode(str, Enum):
    SIMPLE_EQ32 = "SIMPLE_EQ32"
    ADVANCED_EQ33_DAYLIGHT_ONLY = "ADVANCED_EQ33_DAYLIGHT_ONLY"


class KFK5194SolarPeriod(str, Enum):
    DAY = "DAY"
    NIGHT = "NIGHT"


# KfK 5194 Eq.(27), printed p.19, and Eq.(31), printed p.21.
PAR_EXTINCTION_K = 0.6
CO2_TO_DRY_MATTER_FACTOR = 1.5
# KfK 5194 printed p.22-23: historically modelled factors, NOT
# mechanistic proof of photosynthesis or HTO incorporation at night.
DAY_FACTOR = 1.75
NIGHT_FACTOR = 0.25


def _finite(name: str, value: float, *, minimum: float = 0.0,
            strictly: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise KFK5194PhotoOBTError(f"{name} requires a finite numeric input")
    x = float(value)
    if x < minimum or (strictly and x <= minimum):
        raise KFK5194PhotoOBTError(f"{name} outside documented domain")
    return x


def _source_profile(profile: Historical1993SourceProfile) -> None:
    if not isinstance(profile, Historical1993SourceProfile) or profile.profile_id != PROFILE_ID:
        raise KFK5194PhotoOBTError("explicit KFK5194_1993_V4 source profile required")
    if dict(profile.flag_defaults).get("IPHOTO") != 1:
        raise KFK5194PhotoOBTError("KfK 5194 documented IPHOTO=1 default required")


@dataclass(frozen=True, slots=True)
class KFK5194PhotosynthesisRates:
    """Eq.(26)/(27)/(31) outputs with noninterchangeable area bases.

    Potential assimilation (Eq.26): g CO2 / m² leaf / h.
    Canopy assimilated CO2 (Eq.31 input): g CO2 / m² ground / h.
    Actual biomass production (Eq.31): g dry matter / m² ground / h.
    The canopy integration Eq.(28) is NOT supplied or inferred here.
    """

    absorbed_par_w_m2_leaf: float
    potential_co2_g_m2_leaf_h: float
    canopy_co2_g_m2_ground_h: float
    stomatal_stress_fraction: float
    actual_dry_matter_g_m2_ground_h: float

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KFK5194_1993_EQ26_EQ27_EQ31",
            "canopy_integral_eq28": "EXTERNAL_INPUT_NOT_RECONSTRUCTED",
            "temperature_response_eq29": "NOT_RECONSTRUCTED",
            "respiration_eq30": "EXPLICIT_INPUT_NOT_RECONSTRUCTED",
            "stomatal_stress": "EXPLICIT_INPUT_NOT_CALIBRATED",
            "fortran_parity": "NOT_ESTABLISHED",
            "runtime_activated": False,
        }


def kfk5194_1993_photo_rates(
    *,
    profile: Historical1993SourceProfile,
    incident_par_w_m2_ground: float,
    leaf_depth_lai: float,
    total_leaf_area_index: float,
    maximum_co2_g_m2_leaf_h: float,
    initial_light_efficiency_g_co2_per_w_h: float,
    respiration_g_co2_m2_leaf_h: float,
    externally_integrated_canopy_co2_g_m2_ground_h: float,
    externally_determined_stomatal_stress_fraction: float,
) -> KFK5194PhotosynthesisRates:
    """Literal leaf Eq.(26)/(27) + *externally supplied* canopy Eq.(31).

    The potential CO2 value may be negative in darkness due to respiration;
    it is NEVER directly re-labelled as a nonnegative OBT formation flux.
    """
    _source_profile(profile)
    incident = _finite("PAR", incident_par_w_m2_ground)
    depth = _finite("leaf-area depth", leaf_depth_lai)
    lai = _finite("LAI", total_leaf_area_index)
    if depth > lai:
        raise KFK5194PhotoOBTError("leaf depth exceeds LAI")
    pm = _finite("Eq26 maximum CO2 assimilation", maximum_co2_g_m2_leaf_h,
                 strictly=True)
    efficiency = _finite("light use efficiency", initial_light_efficiency_g_co2_per_w_h,
                         strictly=True)
    respiration = _finite("respiration", respiration_g_co2_m2_leaf_h)
    canopy = _finite("Eq31 canopy CO2 assimilation",
                     externally_integrated_canopy_co2_g_m2_ground_h)
    stress = _finite("Eq31 stomatal stress fraction",
                     externally_determined_stomatal_stress_fraction)
    if stress > 1.0:
        raise KFK5194PhotoOBTError("stomatal stress must be within [0,1]")
    par = incident * PAR_EXTINCTION_K * math.exp(-PAR_EXTINCTION_K * depth)
    absorbed = efficiency * par
    potential = pm * absorbed / (pm + absorbed) - respiration
    actual = canopy * CO2_TO_DRY_MATTER_FACTOR * stress
    if not all(math.isfinite(v) for v in (par, potential, actual)):
        raise KFK5194PhotoOBTError("nonfinite photosynthesis quantity")
    return KFK5194PhotosynthesisRates(
        absorbed_par_w_m2_leaf=par,
        potential_co2_g_m2_leaf_h=potential,
        canopy_co2_g_m2_ground_h=canopy,
        stomatal_stress_fraction=stress,
        actual_dry_matter_g_m2_ground_h=actual,
    )


@dataclass(frozen=True, slots=True)
class KFK5194OBTFormationRate:
    """Formation coefficient [h^-1]; does not move any TFWT/OBT activity."""

    crop_organ: KFK5194CropOrgan
    mode: KFK5194OBTFormationMode
    solar_period: KFK5194SolarPeriod
    mean_transfer_d_1: float
    actual_transfer_h_1: float
    factor_day_night: float
    factor_phenology: float | None
    distribution_factor: float | None
    declared_actual_dry_matter_g_m2_ground_h: float | None
    declared_mean_dry_matter_g_m2_ground_h: float | None

    @property
    def actual_transfer_s_1(self) -> float:
        return self.actual_transfer_h_1 / 3600.0

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KFK5194_1993_PRINTED_P22_23_EQ32_33",
            "source_profile": PROFILE_ID,
            "day_night_factors": "HISTORICAL_EMPIRICAL_1_75_0_25",
            "iphoto_documented_default": "ADVANCED_1",
            "mean_transfer_rate": "CALLER_SUPPLIED_DAILY_CROP_SPECIFIC_NOT_1990_DEFAULT",
            "figure_11_growth_factor": "CALLER_SUPPLIED_NOT_RECONSTRUCTED"
            if self.mode is KFK5194OBTFormationMode.SIMPLE_EQ32 else "NOT_APPLICABLE",
            "eq33_night_branch": "NOT_ESTABLISHED",
            "obs_or_fortran_validation": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def kfk5194_1993_obt_formation_rate(
    *,
    profile: Historical1993SourceProfile,
    crop_organ: KFK5194CropOrgan,
    mode: KFK5194OBTFormationMode,
    solar_period: KFK5194SolarPeriod,
    mean_uniform_transfer_d_1: float,
    external_fig11_phenology_factor: float | None = None,
    photosynthesis: KFK5194PhotosynthesisRates | None = None,
    external_mean_dry_matter_g_m2_ground_h: float | None = None,
    external_nonuniform_distribution_fraction: float | None = None,
) -> KFK5194OBTFormationRate:
    """Reconstruct printed Eq.(32) or daylight-only Eq.(33), opt-in.

    Eq32: T_act,h = T_m,d / 24 * fact1 * fact2.
    Eq33: T_act,h = (P_act / P_m,mean) * T_m,d /24 * fact2 * dis.
    Eq33's P_m is the MEAN HOURLY DRY MATTER production [g/m2/h],
    not Eq26's maximum instantaneous CO2 assimilation [g CO2/m2/h].
    The original nighttime continuation of Eq33 is source-limited:
    reject rather than silently equating zero PAR to 25% night transfer.
    """
    _source_profile(profile)
    if not isinstance(crop_organ, KFK5194CropOrgan):
        raise KFK5194PhotoOBTError("supported KfK5194 crop/organ enum required")
    if not isinstance(mode, KFK5194OBTFormationMode) or not isinstance(
        solar_period, KFK5194SolarPeriod
    ):
        raise KFK5194PhotoOBTError("explicit historical OBT mode and solar period required")
    rate_d = _finite("source-specific mean transfer (per day)",
                     mean_uniform_transfer_d_1)
    factor = DAY_FACTOR if solar_period is KFK5194SolarPeriod.DAY else NIGHT_FACTOR
    if mode is KFK5194OBTFormationMode.SIMPLE_EQ32:
        if photosynthesis is not None or external_mean_dry_matter_g_m2_ground_h is not None or (
            external_nonuniform_distribution_fraction is not None
        ):
            raise KFK5194PhotoOBTError("Eq32 may not use advanced model parameters")
        fact1 = _finite("externally derived Figure 11 phenology factor",
                        external_fig11_phenology_factor)
        formed_h = rate_d / 24.0 * fact1 * factor
        distribution = None
        actual = mean = None
    else:
        if solar_period is KFK5194SolarPeriod.NIGHT:
            raise KFK5194PhotoOBTError(
                "Eq33 historical night flux ambiguous; only daylight branch reconstructed"
            )
        if external_fig11_phenology_factor is not None:
            raise KFK5194PhotoOBTError("advanced Eq33 does not multiply Figure 11 fact1")
        if not isinstance(photosynthesis, KFK5194PhotosynthesisRates):
            raise KFK5194PhotoOBTError("typed Eq31 dry matter input required")
        mean = _finite("Eq33 mean hourly dry matter", external_mean_dry_matter_g_m2_ground_h,
                       strictly=True)
        distribution = _finite("Eq33 HTO distribution factor",
                               external_nonuniform_distribution_fraction)
        if distribution > 1.0:
            raise KFK5194PhotoOBTError("distribution fraction outside [0,1]")
        actual = _finite("Eq31 actual dry matter",
                         photosynthesis.actual_dry_matter_g_m2_ground_h)
        formed_h = actual / mean * (rate_d / 24.0) * factor * distribution
        fact1 = None
    if not math.isfinite(formed_h) or formed_h < 0.0:
        raise KFK5194PhotoOBTError("nonfinite or negative OBT formation coefficient")
    return KFK5194OBTFormationRate(
        crop_organ=crop_organ, mode=mode, solar_period=solar_period,
        mean_transfer_d_1=rate_d, actual_transfer_h_1=formed_h,
        factor_day_night=factor, factor_phenology=fact1,
        distribution_factor=distribution,
        declared_actual_dry_matter_g_m2_ground_h=actual,
        declared_mean_dry_matter_g_m2_ground_h=mean,
    )
