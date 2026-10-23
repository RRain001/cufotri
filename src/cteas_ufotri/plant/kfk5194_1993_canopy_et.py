"""KfK 5194 (1993) P3 R1: opt-in daylight/dry canopy and Monteith physics.

Only printed equations (4)-(11) and the radiation partition following (11)
are implemented. Inputs with unavailable crop-specific historical defaults are
required explicitly. Neither legacy config nor the active 1990 path imports
this module. Night, rain and non-physical parameter regimes fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID,
    Historical1993SourceProfile,
)


KFK5194_SOURCE_URL = "https://publikationen.bibliothek.kit.edu/270034158/3813483"
KFK5194_LAI_RADIATION_EXPONENT = 0.398


class KFK5194P3InputError(ValueError):
    """Unsafe or unresolved 1993 canopy/ET input."""


def _real(value: float, label: str, *, positive: bool = False,
          nonnegative: bool = False) -> float:
    if type(value) not in (float, int) or not math.isfinite(float(value)):
        raise KFK5194P3InputError(f"{label} must be a finite SI number")
    number = float(value)
    if positive and number <= 0:
        raise KFK5194P3InputError(f"{label} must be positive")
    if nonnegative and number < 0:
        raise KFK5194P3InputError(f"{label} must be nonnegative")
    return number


def _profile(profile: Historical1993SourceProfile) -> None:
    if not isinstance(profile, Historical1993SourceProfile):
        raise KFK5194P3InputError("explicit typed KfK5194 P1 profile required")
    if (profile.profile_id != PROFILE_ID or profile.source_url != KFK5194_SOURCE_URL
            or dict(profile.flag_defaults).get("IMODEL") != 1
            or dict(profile.flag_defaults).get("IMONT") != 1
            or dict(profile.flag_printed_pages).get("IMODEL") != 54
            or dict(profile.flag_printed_pages).get("IMONT") != 54):
        raise KFK5194P3InputError(
            "KfK5194 IMODEL=1 and IMONT=1 source-backed defaults required"
        )


@dataclass(frozen=True, slots=True)
class KFK5194P3Canopy:
    """Eq.(4)-(10) canopy-state resistances in s/m, except dimensionless factors."""

    profile_id: str
    leaf_area_index: float
    vapour_pressure_deficit_hpa: float
    humidity_factor: float
    soil_water_factor: float
    temperature_factor: float
    temperature_exponent: float
    stomatal_resistance_s_m: float
    aerodynamic_resistance_s_m: float
    boundary_resistance_s_m: float
    canopy_resistance_s_m: float
    leaf_total_resistance_s_m: float
    canopy_total_resistance_s_m: float

    @property
    def atmosphere_resistance_s_m(self) -> float:
        """Printed Eq.(11): r_AV = r_av + r_bv."""
        return self.aerodynamic_resistance_s_m + self.boundary_resistance_s_m

    def provenance(self) -> dict[str, object]:
        return {
            "manual": "KfK 5194 (1993) printed pp. 4-5, equations 4-10",
            "profile_id": self.profile_id,
            "regime": "DAYLIGHT_DRY_ONLY",
            "soil_water_factor": "EXPLICIT_RESEARCH_INPUT_SOURCE_LIMITED",
            "crop_specific_parameter_defaults": "NOT_ASSUMED",
            "original_executable_equivalence": "NOT_ESTABLISHED",
            "whole_1993_runtime_activated": False,
        }


@dataclass(frozen=True, slots=True)
class KFK5194P3Monteith:
    """Eq.(11) latent-energy (W/m²) and evaporated mass flux (kg/m²/s)."""

    profile_id: str
    input_net_radiation_w_m2: float
    plant_radiation_w_m2: float
    soil_radiation_w_m2: float
    plant_latent_heat_flux_w_m2: float
    soil_latent_heat_flux_w_m2: float
    plant_water_flux_kg_m2_s: float
    soil_water_flux_kg_m2_s: float
    latent_heat_vaporization_j_kg: float

    @property
    def net_radiation_partition_residual_w_m2(self) -> float:
        return (self.input_net_radiation_w_m2
                - self.plant_radiation_w_m2 - self.soil_radiation_w_m2)

    @property
    def total_water_flux_kg_m2_s(self) -> float:
        return self.plant_water_flux_kg_m2_s + self.soil_water_flux_kg_m2_s

    def provenance(self) -> dict[str, object]:
        return {
            "manual": "KfK 5194 (1993) printed p. 7, Eq. 11 and radiation partition",
            "profile_id": self.profile_id,
            "radiation_partition_exponent": KFK5194_LAI_RADIATION_EXPONENT,
            "regime": "DAYLIGHT_DRY_ONLY",
            "shared_atmospheric_resistance": "EXPLICIT_RECONSTRUCTION_ASSUMPTION",
            "crop_specific_soil_resistance": "CALLER_REQUIRED",
            "original_executable_equivalence": "NOT_ESTABLISHED",
            "whole_1993_runtime_activated": False,
        }


def kfk5194_1993_daylight_canopy(
    *,
    profile: Historical1993SourceProfile,
    regime: str,
    minimum_stomatal_resistance_s_m: float,
    radiation_balance_w_m2: float,
    half_response_radiation_w_m2: float,
    vapour_pressure_deficit_hpa: float,
    humidity_sensitivity_per_hpa: float,
    soil_water_factor: float,
    temperature_c: float,
    minimum_temperature_c: float,
    optimal_temperature_c: float,
    maximum_temperature_c: float,
    leaf_area_index: float,
    wind_speed_at_reference_m_s: float,
    friction_velocity_m_s: float,
    stanton_number: float,
) -> KFK5194P3Canopy:
    """Compute printed 1993 Eq.(4)-(10), crop parameters explicitly supplied.

    f_l = 1 - b_v Delta_e, f_t = [(T-Te)/(T0-Te)] *
    [(Th-T)/(Th-T0)]**B_t, B_t=(Th-T0)/(T0-Te).
    The KfK5194 f_w response is only described as roughly step-like, so its
    quantitative value is an explicit caller input, never inferred.
    """
    _profile(profile)
    if regime != "DAYLIGHT_DRY":
        raise KFK5194P3InputError(
            "1993 night/rain stomata branches require separate source review"
        )
    minimum = _real(minimum_stomatal_resistance_s_m, "minimum_stomatal_resistance_s_m", positive=True)
    radiation = _real(radiation_balance_w_m2, "radiation_balance_w_m2", positive=True)
    half = _real(half_response_radiation_w_m2, "half_response_radiation_w_m2", nonnegative=True)
    vpd = _real(vapour_pressure_deficit_hpa, "vapour_pressure_deficit_hpa", nonnegative=True)
    humidity_slope = _real(humidity_sensitivity_per_hpa, "humidity_sensitivity_per_hpa", nonnegative=True)
    soil = _real(soil_water_factor, "soil_water_factor", positive=True)
    lai = _real(leaf_area_index, "leaf_area_index", positive=True)
    wind = _real(wind_speed_at_reference_m_s, "wind_speed_at_reference_m_s", positive=True)
    ustar = _real(friction_velocity_m_s, "friction_velocity_m_s", positive=True)
    stanton = _real(stanton_number, "stanton_number", positive=True)
    te = _real(minimum_temperature_c, "minimum_temperature_c")
    t0 = _real(optimal_temperature_c, "optimal_temperature_c")
    th = _real(maximum_temperature_c, "maximum_temperature_c")
    temp = _real(temperature_c, "temperature_c")
    if not te < t0 < th or not te < temp < th:
        raise KFK5194P3InputError("required Te < T0 < Th and Te < T < Th; no temperature clipping")
    if soil > 1.0:
        raise KFK5194P3InputError("explicit soil-water response must be in (0,1]")
    humidity = 1.0 - humidity_slope * vpd
    if humidity <= 0.0:
        raise KFK5194P3InputError("f_l must be positive; no implicit humidity floor")
    bt = (th - t0) / (t0 - te)
    temperature = ((temp - te) / (t0 - te)) * ((th - temp) / (th - t0)) ** bt
    if temperature <= 0.0 or not math.isfinite(temperature):
        raise KFK5194P3InputError("invalid Eq.(8)-(9) temperature factor")
    stomatal = minimum * (1.0 + half / radiation) / (humidity * soil * temperature)
    aerodynamic = wind / ustar**2
    boundary = 1.0 / (ustar * stanton)
    canopy = stomatal / lai
    values = (stomatal, aerodynamic, boundary, canopy)
    if not all(math.isfinite(v) and v > 0.0 for v in values):
        raise KFK5194P3InputError("resistance calculation overflow/underflow")
    return KFK5194P3Canopy(
        profile_id=profile.profile_id, leaf_area_index=lai,
        vapour_pressure_deficit_hpa=vpd,
        humidity_factor=humidity, soil_water_factor=soil,
        temperature_factor=temperature, temperature_exponent=bt,
        stomatal_resistance_s_m=stomatal,
        aerodynamic_resistance_s_m=aerodynamic,
        boundary_resistance_s_m=boundary,
        canopy_resistance_s_m=canopy,
        leaf_total_resistance_s_m=stomatal + aerodynamic + boundary,
        canopy_total_resistance_s_m=canopy + aerodynamic + boundary,
    )


def _monteith_latent_w_m2(
    radiation_w_m2: float,
    atmospheric_resistance_s_m: float,
    surface_resistance_s_m: float,
    vapour_pressure_deficit_pa: float,
    vapour_pressure_slope_pa_k: float,
    psychrometric_constant_pa_k: float,
    air_volumetric_heat_capacity_j_m3_k: float,
) -> float:
    """Dimensionally explicit Eq.(11), using Pa = J/m³ and s/m resistances."""
    numerator = (
        vapour_pressure_slope_pa_k * radiation_w_m2
        + air_volumetric_heat_capacity_j_m3_k
        * vapour_pressure_deficit_pa / atmospheric_resistance_s_m
    )
    denominator = (
        vapour_pressure_slope_pa_k
        + psychrometric_constant_pa_k
        * (1.0 + surface_resistance_s_m / atmospheric_resistance_s_m)
    )
    result = numerator / denominator
    if not math.isfinite(result) or result < 0.0:
        raise KFK5194P3InputError("invalid Monteith latent-heat flux")
    return result


def kfk5194_1993_monteith_et(
    *,
    profile: Historical1993SourceProfile,
    canopy: KFK5194P3Canopy,
    net_radiation_w_m2: float,
    soil_surface_resistance_s_m: float,
    vapour_pressure_slope_pa_k: float,
    psychrometric_constant_pa_k: float,
    air_volumetric_heat_capacity_j_m3_k: float,
    latent_heat_vaporization_j_kg: float,
) -> KFK5194P3Monteith:
    """1993 Eq.(11) separately for plant and soil, with printed LAI splitting.

    Consumes the SAME observed vapour deficit as canopy Eq.(7): hPa * 100 = Pa.
    Soil surface resistance and atmospheric thermodynamic inputs must be given.
    Uses a shared (r_av + r_bv) for soil/leaf as an explicit bounded
    reconstruction assumption, not a proven original FORTRAN implementation.
    """
    _profile(profile)
    if not isinstance(canopy, KFK5194P3Canopy) or canopy.profile_id != PROFILE_ID:
        raise KFK5194P3InputError("must supply validated 1993 daylight canopy state")
    net = _real(net_radiation_w_m2, "net_radiation_w_m2", nonnegative=True)
    soil_res = _real(soil_surface_resistance_s_m, "soil_surface_resistance_s_m", positive=True)
    slope = _real(vapour_pressure_slope_pa_k, "vapour_pressure_slope_pa_k", positive=True)
    gamma = _real(psychrometric_constant_pa_k, "psychrometric_constant_pa_k", positive=True)
    rho_cp = _real(air_volumetric_heat_capacity_j_m3_k,
                   "air_volumetric_heat_capacity_j_m3_k", positive=True)
    latent = _real(latent_heat_vaporization_j_kg,
                   "latent_heat_vaporization_j_kg", positive=True)
    attenuation = math.exp(-KFK5194_LAI_RADIATION_EXPONENT * canopy.leaf_area_index)
    soil_radiation = net * attenuation
    leaf_radiation = net * (1.0 - attenuation)
    air_res = canopy.atmosphere_resistance_s_m
    vpd_pa = canopy.vapour_pressure_deficit_hpa * 100.0
    leaf_flux = _monteith_latent_w_m2(
        leaf_radiation, air_res, canopy.canopy_resistance_s_m,
        vpd_pa, slope, gamma, rho_cp,
    )
    soil_flux = _monteith_latent_w_m2(
        soil_radiation, air_res, soil_res, vpd_pa, slope, gamma, rho_cp,
    )
    return KFK5194P3Monteith(
        profile_id=PROFILE_ID, input_net_radiation_w_m2=net,
        plant_radiation_w_m2=leaf_radiation,
        soil_radiation_w_m2=soil_radiation,
        plant_latent_heat_flux_w_m2=leaf_flux,
        soil_latent_heat_flux_w_m2=soil_flux,
        plant_water_flux_kg_m2_s=leaf_flux / latent,
        soil_water_flux_kg_m2_s=soil_flux / latent,
        latent_heat_vaporization_j_kg=latent,
    )
