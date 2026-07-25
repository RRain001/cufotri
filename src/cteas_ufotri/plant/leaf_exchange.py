from __future__ import annotations

from dataclasses import dataclass
import math

from ..meteorology.derived_variables import (
    relative_humidity,
    saturation_vapour_pressure_pa,
    vapour_pressure_deficit_pa,
)


LEAF_EQUILIBRIUM_FORMULA_ID = (
    "UFOTRI_EQ27_SATURATED_WATER_VAPOUR_DENSITY"
)
LEAF_EQUILIBRIUM_FORMULA_DESCRIPTION = (
    "Ca_eq = Cplant * rho_v_sat / (alpha * rho_water)"
)
LEAF_EQUILIBRIUM_VAPOUR_DENSITY_BASIS = "SATURATED"


@dataclass(frozen=True)
class LeafExchange:
    net_to_plant_bq_m2_s: float
    conductance_m_s: float
    equilibrium_air_concentration_bq_m3: float
    relative_humidity: float
    vapour_pressure_deficit_pa: float
    aerodynamic_resistance_s_m: float = 0.0
    boundary_resistance_s_m: float = 0.0
    canopy_resistance_s_m: float = 0.0
    friction_velocity_m_s: float = 0.0
    leaf_wind_speed_m_s: float = 0.0
    monin_obukhov_length_m: float = math.inf


_GOLDER_COEFFICIENTS = {
    "A": (-0.096, 0.029),
    "B": (-0.037, 0.029),
    "C": (-0.002, 0.018),
    "D": (0.0, 0.0),
    "E": (0.004, -0.018),
    "F": (0.035, -0.036),
}


def golder_monin_obukhov_length_m(
    stability_class: str,
    roughness_length_m: float,
) -> float:
    """Estimate Monin-Obukhov length from Golder's 1972 approximation.

    ``1/L = a + b log10(z0)`` with ``z0`` and ``L`` in metres.
    """

    stability = stability_class.upper()
    if stability not in _GOLDER_COEFFICIENTS:
        raise ValueError(f"Unsupported Pasquill stability class: {stability_class}")
    if roughness_length_m <= 0:
        raise ValueError("Surface roughness length must be positive")
    a, b = _GOLDER_COEFFICIENTS[stability]
    inverse_length = a + b * math.log10(roughness_length_m)
    return math.inf if inverse_length == 0.0 else 1.0 / inverse_length


def canopy_aerodynamic_resistance_s_m(
    wind_speed_m_s: float,
    wind_measurement_height_m: float,
    roughness_length_m: float,
    canopy_height_m: float,
    stability_class: str,
    *,
    von_karman_constant: float = 0.4,
    minimum_wind_speed_m_s: float = 0.05,
) -> tuple[float, float, float, float]:
    """Return ``r_a``, friction velocity, leaf wind, and Monin length.

    UFOTRI manual Eqs. (18), (22)-(24) are used with the Golder (1972)
    Pasquill-class estimate of Monin-Obukhov length.
    """

    if min(
        wind_measurement_height_m,
        roughness_length_m,
        canopy_height_m,
        von_karman_constant,
        minimum_wind_speed_m_s,
    ) <= 0:
        raise ValueError("Aerodynamic-resistance geometry must be positive")
    displacement_m = 0.6 * canopy_height_m
    effective_height_m = wind_measurement_height_m - displacement_m
    if effective_height_m <= roughness_length_m:
        raise ValueError(
            "Wind measurement height must exceed displacement plus roughness"
        )
    wind = max(float(wind_speed_m_s), minimum_wind_speed_m_s)
    monin_length = golder_monin_obukhov_length_m(
        stability_class,
        roughness_length_m,
    )
    log_term = math.log(effective_height_m / roughness_length_m)
    if math.isinf(monin_length):
        profile_term = log_term
    elif monin_length > 0.0:
        profile_term = log_term + 4.7 * effective_height_m / monin_length
    else:
        phi_m = (1.0 - 15.0 * effective_height_m / monin_length) ** -0.25
        inverse_phi = 1.0 / phi_m
        profile_term = (
            log_term
            - 2.0 * math.log(0.5 * (1.0 + inverse_phi))
            + 2.0 * math.atan(inverse_phi)
            - math.log(0.5 * (1.0 + inverse_phi**2))
            - math.pi / 2.0
        )
    if profile_term <= 0.0:
        raise ValueError("Stability-corrected wind-profile term must be positive")
    friction_velocity = von_karman_constant * wind / profile_term
    aerodynamic = wind / friction_velocity**2
    leaf_height_m = max(
        canopy_height_m + roughness_length_m,
        displacement_m + 1.01 * roughness_length_m,
    )
    leaf_wind = (
        friction_velocity
        / von_karman_constant
        * math.log((leaf_height_m - displacement_m) / roughness_length_m)
    )
    return (
        aerodynamic,
        friction_velocity,
        max(leaf_wind, minimum_wind_speed_m_s),
        monin_length,
    )


def leaf_boundary_resistance_s_m(
    leaf_wind_speed_m_s: float,
    leaf_characteristic_length_m: float,
    air_kinematic_viscosity_m2_s: float,
    water_vapour_diffusivity_m2_s: float,
) -> float:
    """Laminar flat-plate water-vapour resistance from a Sherwood correlation."""

    if min(
        leaf_wind_speed_m_s,
        leaf_characteristic_length_m,
        air_kinematic_viscosity_m2_s,
        water_vapour_diffusivity_m2_s,
    ) <= 0:
        raise ValueError("Leaf boundary-layer inputs must be positive")
    reynolds = (
        leaf_wind_speed_m_s
        * leaf_characteristic_length_m
        / air_kinematic_viscosity_m2_s
    )
    if reynolds > 5.0e5:
        raise ValueError("Laminar flat-plate leaf correlation requires Re <= 5e5")
    schmidt = air_kinematic_viscosity_m2_s / water_vapour_diffusivity_m2_s
    sherwood = 0.664 * math.sqrt(reynolds) * schmidt ** (1.0 / 3.0)
    mass_transfer_m_s = (
        sherwood
        * water_vapour_diffusivity_m2_s
        / leaf_characteristic_length_m
    )
    return 1.0 / mass_transfer_m_s


def bidirectional_leaf_exchange(
    air_concentration_bq_m3: float,
    plant_water_concentration_bq_m3: float,
    temperature_k: float,
    dewpoint_k: float,
    lai: float,
    is_day: bool,
    *,
    wind_speed_m_s: float,
    stability_class: str,
    roughness_length_m: float,
    canopy_height_m: float,
    wind_measurement_height_m: float,
    leaf_characteristic_length_m: float,
    air_kinematic_viscosity_m2_s: float,
    water_vapour_diffusivity_m2_s: float,
    stomatal_resistance_day_s_m: float,
    stomatal_resistance_night_s_m: float,
    vpd_sensitivity_per_kpa: float,
    isotope_fractionation_liquid_to_vapour: float,
    water_density_kg_m3: float,
    precipitation_m_s: float = 0.0,
    von_karman_constant: float = 0.4,
    minimum_wind_speed_m_s: float = 0.05,
) -> LeafExchange:
    """Meteorology-responsive net HTO exchange through canopy resistance.

    Plant-water activity is converted to equilibrium air activity using the
    saturated water-vapour density required by UFOTRI Eq. (27) and the
    configured liquid/vapour isotope fractionation.  Relative humidity still
    affects stomatal resistance through vapour-pressure deficit, but it does
    not enter the Eq. (27) equilibrium concentration.  Aerodynamic resistance
    follows the manual resistance model with a literature Pasquill-to-Monin
    mapping; boundary resistance uses a laminar flat-plate mass-transfer
    correlation. Positive flux is air to plant; negative flux is re-release.
    """
    if lai <= 0:
        return LeafExchange(0.0, 0.0, 0.0, 0.0, 0.0)
    if min(
        stomatal_resistance_day_s_m,
        stomatal_resistance_night_s_m,
        isotope_fractionation_liquid_to_vapour,
        water_density_kg_m3,
    ) <= 0:
        raise ValueError("Leaf-exchange resistances and conversion factors must be positive")
    if vpd_sensitivity_per_kpa < 0:
        raise ValueError("VPD sensitivity must be non-negative")
    rh = float(relative_humidity(temperature_k, dewpoint_k))
    vpd = float(vapour_pressure_deficit_pa(temperature_k, dewpoint_k))
    stomatal = (
        stomatal_resistance_day_s_m
        if is_day
        else stomatal_resistance_night_s_m
    )
    canopy = (
        0.0
        if is_day and precipitation_m_s > 0.0
        else stomatal * (1.0 + vpd_sensitivity_per_kpa * vpd / 1000.0) / lai
    )
    aerodynamic, friction_velocity, leaf_wind, monin_length = (
        canopy_aerodynamic_resistance_s_m(
            wind_speed_m_s,
            wind_measurement_height_m,
            roughness_length_m,
            canopy_height_m,
            stability_class,
            von_karman_constant=von_karman_constant,
            minimum_wind_speed_m_s=minimum_wind_speed_m_s,
        )
    )
    boundary = leaf_boundary_resistance_s_m(
        leaf_wind,
        leaf_characteristic_length_m,
        air_kinematic_viscosity_m2_s,
        water_vapour_diffusivity_m2_s,
    )
    total_resistance = aerodynamic + boundary + canopy
    conductance = 1.0 / total_resistance
    rho_v_sat = float(saturation_vapour_pressure_pa(temperature_k)) / (
        461.5 * temperature_k
    )
    equilibrium_air = (
        max(plant_water_concentration_bq_m3, 0.0)
        * rho_v_sat
        / (
            isotope_fractionation_liquid_to_vapour
            * water_density_kg_m3
        )
    )
    net = conductance * (
        max(air_concentration_bq_m3, 0.0) - equilibrium_air
    )
    return LeafExchange(
        net,
        conductance,
        equilibrium_air,
        rh,
        vpd,
        aerodynamic,
        boundary,
        canopy,
        friction_velocity,
        leaf_wind,
        monin_length,
    )
