"""Opt-in UFOTRI Eq. (7)-(31) leaf compatibility path.

This module implements only the manual-fidelity mechanisms authorized by
``UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1``.  It deliberately does not replace
historical V2 leaf exchange or the frozen V4 RC1 resistance/TFWT defaults.

The available manual does not recover the original UFOTRI Monin-Obukhov-length
estimator.  Consequently this module requires either an explicitly sourced
Monin-Obukhov length or an explicitly named literature estimator.  The latter
is never represented as exact original UFOTRI source logic.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from ...meteorology.derived_variables import saturation_vapour_pressure_pa
from ..leaf_exchange import golder_monin_obukhov_length_m
from ..leaf_exchange_resistance import LeafExchangeFlux, ResistanceChain
from ..tfwt_v3 import TFWTState, TFWTStepResult, TFWTStorageSolver
from ..root_v3 import RootFlux


GOLDER_ESTIMATOR_ID = "GOLDER_1972_APPROXIMATION"
EXPLICIT_MONIN_OBUKHOV_METHOD = "EXPLICIT_MONIN_OBUKHOV_LENGTH"
UFOTRI_EQ21_FORMULA_ID = "UFOTRI_EQ21_RB_2_OVER_K_USTAR"
UFOTRI_EQ27_30_FORMULA_ID = "UFOTRI_EQ27_30_ANALYTIC_INTERVAL"
UFOTRI_EQ31_DIAGNOSTIC_ID = "UFOTRI_EQ31_ZERO_AIR_REEMISSION_FRACTION"


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


@dataclass(frozen=True)
class UFOTRILeafGeometry:
    """Recoverable UFOTRI vegetation geometry used by the fidelity path."""

    canopy_height_m: float
    roughness_length_m: float
    displacement_height_m: float
    area_source_emission_height_m: float


@dataclass(frozen=True)
class MoninObukhovProvenance:
    """Source identity for the Monin-Obukhov length used by Eq. (22)-(25)."""

    length_m: float
    method: str
    source_id: str
    source_version: str
    exact_original_ufotri_logic: bool = False

    def __post_init__(self) -> None:
        length = float(self.length_m)
        if math.isnan(length) or length == 0.0:
            raise ValueError("Monin-Obukhov length must be non-zero or +/-inf")
        if not self.method.strip() or not self.source_id.strip() or not self.source_version.strip():
            raise ValueError("Monin-Obukhov provenance fields must be non-empty")
        if self.exact_original_ufotri_logic:
            raise ValueError(
                "Original UFOTRI Monin-Obukhov estimator is not recovered; "
                "exact-original provenance is forbidden"
            )


@dataclass(frozen=True)
class UFOTRIWindProfileResult:
    """Eq. (18), (22)-(25) wind-profile compatibility result."""

    station_wind_speed_m_s: float
    wind_100m_m_s: float
    vegetation_wind_speed_m_s: float
    friction_velocity_m_s: float
    aerodynamic_resistance_s_m: float
    station_to_100m_power_exponent: float
    geometry: UFOTRILeafGeometry
    monin_obukhov: MoninObukhovProvenance


@dataclass(frozen=True)
class UFOTRILeafResistanceResult:
    """Manual-compatible resistance components projected onto the RC1 contract."""

    chain: ResistanceChain
    wind: UFOTRIWindProfileResult
    canopy_resistance_s_m: float
    boundary_layer_resistance_s_m: float


@dataclass(frozen=True)
class UFOTRIAnalyticLeafTransfer:
    """Exact Eq. (27)-(30) interval transfer for interval-constant inputs."""

    initial_tfwt_concentration_bq_kg_water: float
    target_tfwt_concentration_bq_kg_water: float
    next_tfwt_concentration_bq_kg_water: float
    equilibrium_air_concentration_initial_bq_m3: float
    saturated_vapour_density_kg_m3: float
    exchange_rate_constant_s_1: float
    attenuation: float
    leaf_transfer_bq_m2: float
    mean_leaf_exchange_flux_bq_m2_s: float
    eq31_zero_air_reemission_fraction: float
    eq31_zero_air_reemission_percent: float
    formula_id: str = UFOTRI_EQ27_30_FORMULA_ID
    eq31_diagnostic_id: str = UFOTRI_EQ31_DIAGNOSTIC_ID

    def as_leaf_exchange_flux(self) -> LeafExchangeFlux:
        """Project the exact integrated transfer onto the frozen signed flux API."""

        return LeafExchangeFlux(
            air_to_leaf_flux_bq_m2_s=self.mean_leaf_exchange_flux_bq_m2_s
        )


@dataclass(frozen=True)
class UFOTRITFWTCompatibilityStep:
    """Exact leaf operator plus the existing auditable TFWT storage result."""

    analytic_leaf_transfer: UFOTRIAnalyticLeafTransfer
    tfwt_step: TFWTStepResult

    @property
    def state(self) -> TFWTState:
        return self.tfwt_step.state


def ufotri_manual_leaf_geometry(canopy_height_m: float) -> UFOTRILeafGeometry:
    """Return the recovered UFOTRI geometry: z0=0.1H, d=0.6H, FLQH=0.8H.

    The area-source emission height is subject to the manual compatibility
    minimum of 1 m.  It is exposed for later area-source/re-emission coupling;
    aerodynamic leaf resistance itself uses vegetation height ``H``.
    """

    height = _positive(canopy_height_m, field="canopy_height_m")
    return UFOTRILeafGeometry(
        canopy_height_m=height,
        roughness_length_m=0.1 * height,
        displacement_height_m=0.6 * height,
        area_source_emission_height_m=max(0.8 * height, 1.0),
    )


def manual_canopy_resistance_s_m(
    *,
    lai: float,
    is_day: bool,
    soil_available_water_exhausted: bool,
    precipitation_m_s: float,
    stomatal_resistance_day_s_m: float,
    stomatal_resistance_night_s_m: float,
) -> float:
    """Recoverable UFOTRI canopy rule associated with Eq. (14).

    Daytime rain opens the canopy resistance to zero.  Otherwise daytime uses
    the daytime stomatal resistance unless available soil water is exhausted,
    in which case it switches to the nighttime resistance.  Nighttime always
    retains the nighttime/epidermal resistance, including during rain.

    No VPD multiplier is applied in this compatibility path.
    """

    leaf_area_index = _positive(lai, field="lai")
    precipitation = _nonnegative(precipitation_m_s, field="precipitation_m_s")
    day_resistance = _positive(
        stomatal_resistance_day_s_m,
        field="stomatal_resistance_day_s_m",
    )
    night_resistance = _positive(
        stomatal_resistance_night_s_m,
        field="stomatal_resistance_night_s_m",
    )
    if is_day and precipitation > 0.0:
        return 0.0
    stomatal = (
        day_resistance
        if is_day and not soil_available_water_exhausted
        else night_resistance
    )
    return stomatal / leaf_area_index


def resolve_monin_obukhov_provenance(
    *,
    roughness_length_m: float,
    explicit_length_m: float | None = None,
    explicit_source_id: str | None = None,
    explicit_source_version: str | None = None,
    estimator_id: str | None = None,
    stability_class: str | None = None,
) -> MoninObukhovProvenance:
    """Resolve one explicit, auditable Monin-Obukhov source.

    Exactly one route is permitted:

    * explicit length + explicit source identity; or
    * named ``GOLDER_1972_APPROXIMATION`` with a Pasquill class.
    """

    roughness = _positive(roughness_length_m, field="roughness_length_m")
    explicit_selected = explicit_length_m is not None
    estimator_selected = estimator_id is not None
    if explicit_selected == estimator_selected:
        raise ValueError(
            "Select exactly one Monin-Obukhov route: explicit length or named estimator"
        )
    if explicit_selected:
        if not explicit_source_id or not explicit_source_version:
            raise ValueError(
                "Explicit Monin-Obukhov length requires source_id and source_version"
            )
        length = float(explicit_length_m)
        if math.isnan(length) or length == 0.0:
            raise ValueError("explicit_length_m must be non-zero or +/-inf")
        return MoninObukhovProvenance(
            length_m=length,
            method=EXPLICIT_MONIN_OBUKHOV_METHOD,
            source_id=explicit_source_id,
            source_version=explicit_source_version,
        )
    if estimator_id != GOLDER_ESTIMATOR_ID:
        raise ValueError(f"Unsupported Monin-Obukhov estimator: {estimator_id}")
    if not stability_class:
        raise ValueError("Golder estimator requires a Pasquill stability class")
    length = golder_monin_obukhov_length_m(stability_class, roughness)
    return MoninObukhovProvenance(
        length_m=length,
        method=GOLDER_ESTIMATOR_ID,
        source_id="GOLDER_1972_LITERATURE_APPROXIMATION",
        source_version="historical-v2-compatibility",
    )


def _stability_profile_term(
    height_m: float,
    displacement_height_m: float,
    roughness_length_m: float,
    monin_obukhov_length_m: float,
) -> float:
    """Return the literal UFOTRI Eq. (22)-(24) wind-profile bracket.

    The manual uses ``ln((z-d)/z0)`` for the roughness/displacement term, while
    the stable correction ``4.7 z/L`` and the unstable Dyer-Businger ``Phi_m``
    use the actual height ``z``.  Do not replace those latter ``z`` terms by
    ``z-d``: doing so changes the recoverable manual semantics.
    """

    height = _positive(height_m, field="height_m")
    displacement = _nonnegative(
        displacement_height_m,
        field="displacement_height_m",
    )
    roughness = _positive(roughness_length_m, field="roughness_length_m")
    if displacement >= height:
        raise ValueError("height must exceed displacement height")
    effective = height - displacement
    if effective <= roughness:
        raise ValueError("height minus displacement must exceed roughness length")
    length = float(monin_obukhov_length_m)
    if math.isnan(length) or length == 0.0:
        raise ValueError("Monin-Obukhov length must be non-zero or +/-inf")
    log_term = math.log(effective / roughness)
    if math.isinf(length):
        result = log_term
    elif length > 0.0:
        result = log_term + 4.7 * height / length
    else:
        phi_m = (1.0 - 15.0 * height / length) ** -0.25
        inverse_phi = 1.0 / phi_m
        result = (
            log_term
            - 2.0 * math.log(0.5 * (1.0 + inverse_phi))
            + 2.0 * math.atan(inverse_phi)
            - math.log(0.5 * (1.0 + inverse_phi**2))
            - math.pi / 2.0
        )
    if result <= 0.0 or not math.isfinite(result):
        raise ValueError("stability-corrected wind-profile term must be finite and positive")
    return result


def ufotri_eq25_wind_profile(
    *,
    station_wind_speed_m_s: float,
    station_height_m: float,
    station_to_100m_power_exponent: float,
    canopy_height_m: float,
    explicit_monin_obukhov_length_m: float | None = None,
    monin_obukhov_source_id: str | None = None,
    monin_obukhov_source_version: str | None = None,
    monin_obukhov_estimator_id: str | None = None,
    stability_class: str | None = None,
    von_karman_constant: float = 0.4,
) -> UFOTRIWindProfileResult:
    """Apply Eq. (25): station wind -> 100 m -> vegetation height.

    The first mapping is an explicit caller-supplied power law.  The second is
    the Eq. (22)-(24) stability-dependent logarithmic profile.  No hidden calm
    wind clamp or unstated power exponent is applied.
    """

    station_wind = _positive(station_wind_speed_m_s, field="station_wind_speed_m_s")
    station_height = _positive(station_height_m, field="station_height_m")
    exponent = _nonnegative(
        station_to_100m_power_exponent,
        field="station_to_100m_power_exponent",
    )
    von_karman = _positive(von_karman_constant, field="von_karman_constant")
    geometry = ufotri_manual_leaf_geometry(canopy_height_m)
    monin = resolve_monin_obukhov_provenance(
        roughness_length_m=geometry.roughness_length_m,
        explicit_length_m=explicit_monin_obukhov_length_m,
        explicit_source_id=monin_obukhov_source_id,
        explicit_source_version=monin_obukhov_source_version,
        estimator_id=monin_obukhov_estimator_id,
        stability_class=stability_class,
    )
    wind_100m = station_wind * (100.0 / station_height) ** exponent
    reference_term = _stability_profile_term(
        100.0,
        geometry.displacement_height_m,
        geometry.roughness_length_m,
        monin.length_m,
    )
    vegetation_term = _stability_profile_term(
        geometry.canopy_height_m,
        geometry.displacement_height_m,
        geometry.roughness_length_m,
        monin.length_m,
    )
    friction_velocity = von_karman * wind_100m / reference_term
    vegetation_wind = friction_velocity / von_karman * vegetation_term
    aerodynamic_resistance = vegetation_wind / friction_velocity**2
    return UFOTRIWindProfileResult(
        station_wind_speed_m_s=station_wind,
        wind_100m_m_s=wind_100m,
        vegetation_wind_speed_m_s=vegetation_wind,
        friction_velocity_m_s=friction_velocity,
        aerodynamic_resistance_s_m=aerodynamic_resistance,
        station_to_100m_power_exponent=exponent,
        geometry=geometry,
        monin_obukhov=monin,
    )


def ufotri_eq21_boundary_resistance_s_m(
    friction_velocity_m_s: float,
    *,
    von_karman_constant: float = 0.4,
) -> float:
    """UFOTRI Eq. (21): ``r_b = 2 / (k u_*)``."""

    friction_velocity = _positive(
        friction_velocity_m_s,
        field="friction_velocity_m_s",
    )
    von_karman = _positive(von_karman_constant, field="von_karman_constant")
    return 2.0 / (von_karman * friction_velocity)


def build_ufotri_eq7_25_resistance_chain(
    *,
    lai: float,
    is_day: bool,
    soil_available_water_exhausted: bool,
    precipitation_m_s: float,
    stomatal_resistance_day_s_m: float,
    stomatal_resistance_night_s_m: float,
    station_wind_speed_m_s: float,
    station_height_m: float,
    station_to_100m_power_exponent: float,
    canopy_height_m: float,
    explicit_monin_obukhov_length_m: float | None = None,
    monin_obukhov_source_id: str | None = None,
    monin_obukhov_source_version: str | None = None,
    monin_obukhov_estimator_id: str | None = None,
    stability_class: str | None = None,
    von_karman_constant: float = 0.4,
) -> UFOTRILeafResistanceResult:
    """Build the A2 manual-fidelity resistance chain without changing RC1."""

    canopy = manual_canopy_resistance_s_m(
        lai=lai,
        is_day=is_day,
        soil_available_water_exhausted=soil_available_water_exhausted,
        precipitation_m_s=precipitation_m_s,
        stomatal_resistance_day_s_m=stomatal_resistance_day_s_m,
        stomatal_resistance_night_s_m=stomatal_resistance_night_s_m,
    )
    wind = ufotri_eq25_wind_profile(
        station_wind_speed_m_s=station_wind_speed_m_s,
        station_height_m=station_height_m,
        station_to_100m_power_exponent=station_to_100m_power_exponent,
        canopy_height_m=canopy_height_m,
        explicit_monin_obukhov_length_m=explicit_monin_obukhov_length_m,
        monin_obukhov_source_id=monin_obukhov_source_id,
        monin_obukhov_source_version=monin_obukhov_source_version,
        monin_obukhov_estimator_id=monin_obukhov_estimator_id,
        stability_class=stability_class,
        von_karman_constant=von_karman_constant,
    )
    boundary = ufotri_eq21_boundary_resistance_s_m(
        wind.friction_velocity_m_s,
        von_karman_constant=von_karman_constant,
    )
    chain = ResistanceChain.from_components(
        wind.aerodynamic_resistance_s_m,
        boundary,
        canopy,
    )
    return UFOTRILeafResistanceResult(
        chain=chain,
        wind=wind,
        canopy_resistance_s_m=canopy,
        boundary_layer_resistance_s_m=boundary,
    )


def saturated_vapour_density_kg_m3(
    temperature_k: float,
    *,
    water_vapour_gas_constant_j_kg_k: float = 461.5,
) -> float:
    """Saturated water-vapour density used by UFOTRI Eq. (27)."""

    temperature = _positive(temperature_k, field="temperature_k")
    gas_constant = _positive(
        water_vapour_gas_constant_j_kg_k,
        field="water_vapour_gas_constant_j_kg_k",
    )
    return float(saturation_vapour_pressure_pa(temperature)) / (
        gas_constant * temperature
    )


def ufotri_eq27_equilibrium_air_concentration_bq_m3(
    *,
    tfwt_concentration_bq_kg_water: float,
    temperature_k: float,
    isotope_fractionation_liquid_to_vapour: float,
) -> float:
    """Atmospheric-equivalent concentration of plant TFWT for Eq. (27).

    ``TFWTState`` uses Bq per kg of plant water, so the historical volumetric
    ``rho_water`` factor cancels and the compatible form is
    ``C_air,eq = C_TFWT * rho_v,sat / alpha``.
    """

    concentration = _nonnegative(
        tfwt_concentration_bq_kg_water,
        field="tfwt_concentration_bq_kg_water",
    )
    alpha = _positive(
        isotope_fractionation_liquid_to_vapour,
        field="isotope_fractionation_liquid_to_vapour",
    )
    rho_v = saturated_vapour_density_kg_m3(temperature_k)
    return concentration * rho_v / alpha


def ufotri_eq27_30_analytic_interval_transfer(
    *,
    air_concentration_bq_m3: float,
    initial_tfwt_concentration_bq_kg_water: float,
    plant_water_content_kg_m2: float,
    temperature_k: float,
    total_resistance_s_m: float,
    isotope_fractionation_liquid_to_vapour: float,
    interval_seconds: float,
) -> UFOTRIAnalyticLeafTransfer:
    """Integrate the recoverable Eq. (27)-(30) exchange exactly for one interval.

    With interval-constant air concentration ``chi``, plant-water mass per area
    ``mu``, saturated vapour density ``rho``, fractionation ``alpha`` and total
    resistance ``r``:

    ``k = rho / (alpha * mu * r)``

    ``C_target = alpha * chi / rho``

    ``C(t+dt) = C_target + (C(t)-C_target) exp(-k dt)``.

    The returned signed mean flux is exactly the integrated leaf transfer
    divided by ``dt`` and can therefore pass through the frozen RC1 signed flux
    boundary without changing that boundary's semantics.
    """

    air = _nonnegative(air_concentration_bq_m3, field="air_concentration_bq_m3")
    initial = _nonnegative(
        initial_tfwt_concentration_bq_kg_water,
        field="initial_tfwt_concentration_bq_kg_water",
    )
    water_content = _positive(
        plant_water_content_kg_m2,
        field="plant_water_content_kg_m2",
    )
    resistance = _positive(total_resistance_s_m, field="total_resistance_s_m")
    alpha = _positive(
        isotope_fractionation_liquid_to_vapour,
        field="isotope_fractionation_liquid_to_vapour",
    )
    interval = _positive(interval_seconds, field="interval_seconds")
    rho_v = saturated_vapour_density_kg_m3(temperature_k)
    rate_constant = rho_v / (alpha * water_content * resistance)
    target = alpha * air / rho_v
    attenuation = math.exp(-rate_constant * interval)
    next_concentration = target + (initial - target) * attenuation
    leaf_transfer = water_content * (next_concentration - initial)
    mean_flux = leaf_transfer / interval
    equilibrium_air_initial = initial * rho_v / alpha
    eq31_fraction = 1.0 - attenuation
    return UFOTRIAnalyticLeafTransfer(
        initial_tfwt_concentration_bq_kg_water=initial,
        target_tfwt_concentration_bq_kg_water=target,
        next_tfwt_concentration_bq_kg_water=next_concentration,
        equilibrium_air_concentration_initial_bq_m3=equilibrium_air_initial,
        saturated_vapour_density_kg_m3=rho_v,
        exchange_rate_constant_s_1=rate_constant,
        attenuation=attenuation,
        leaf_transfer_bq_m2=leaf_transfer,
        mean_leaf_exchange_flux_bq_m2_s=mean_flux,
        eq31_zero_air_reemission_fraction=eq31_fraction,
        eq31_zero_air_reemission_percent=100.0 * eq31_fraction,
    )


def advance_tfwt_with_ufotri_analytic_leaf_exchange(
    state: TFWTState,
    *,
    air_concentration_bq_m3: float,
    temperature_k: float,
    total_resistance_s_m: float,
    isotope_fractionation_liquid_to_vapour: float,
    interval_seconds: float,
    root_uptake_flux: RootFlux | None = None,
    water_loss_flux_bq_m2_s: float = 0.0,
    transformation_flux_bq_m2_s: float = 0.0,
) -> UFOTRITFWTCompatibilityStep:
    """Project the exact leaf operator through the frozen TFWT storage boundary.

    Eq. (27)-(30) is integrated exactly for the leaf-exchange operator.  Root,
    water-loss and transformation terms retain the existing explicit TFWT
    operator semantics; this function does not claim a new coupled analytic
    solution for those independent terms.
    """

    transfer = ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=air_concentration_bq_m3,
        initial_tfwt_concentration_bq_kg_water=(
            state.tfwt_concentration_bq_kg_water
        ),
        plant_water_content_kg_m2=state.water_content_kg_m2,
        temperature_k=temperature_k,
        total_resistance_s_m=total_resistance_s_m,
        isotope_fractionation_liquid_to_vapour=(
            isotope_fractionation_liquid_to_vapour
        ),
        interval_seconds=interval_seconds,
    )
    step = TFWTStorageSolver().advance(
        state,
        transfer.as_leaf_exchange_flux(),
        interval_seconds,
        root_uptake_flux=root_uptake_flux,
        water_loss_flux_bq_m2_s=water_loss_flux_bq_m2_s,
        transformation_flux_bq_m2_s=transformation_flux_bq_m2_s,
    )
    return UFOTRITFWTCompatibilityStep(
        analytic_leaf_transfer=transfer,
        tfwt_step=step,
    )


__all__ = [
    "EXPLICIT_MONIN_OBUKHOV_METHOD",
    "GOLDER_ESTIMATOR_ID",
    "MoninObukhovProvenance",
    "UFOTRIAnalyticLeafTransfer",
    "UFOTRILeafGeometry",
    "UFOTRILeafResistanceResult",
    "UFOTRITFWTCompatibilityStep",
    "UFOTRIWindProfileResult",
    "UFOTRI_EQ21_FORMULA_ID",
    "UFOTRI_EQ27_30_FORMULA_ID",
    "UFOTRI_EQ31_DIAGNOSTIC_ID",
    "advance_tfwt_with_ufotri_analytic_leaf_exchange",
    "build_ufotri_eq7_25_resistance_chain",
    "manual_canopy_resistance_s_m",
    "resolve_monin_obukhov_provenance",
    "saturated_vapour_density_kg_m3",
    "ufotri_eq21_boundary_resistance_s_m",
    "ufotri_eq25_wind_profile",
    "ufotri_eq27_30_analytic_interval_transfer",
    "ufotri_eq27_equilibrium_air_concentration_bq_m3",
    "ufotri_manual_leaf_geometry",
]
