"""KfK 5194 (1993) printed Eqs.(1)-(3): opt-in leaf-normalised HTO kinetics.

Normative evidence: Raskob, KfK 5194, §5.2, printed p.3, PDF0 p.12.
The printed leaf water content is per unit LEAF area, not ground area.
This module therefore does not silently exchange leaf/ground area or reuse
the 1990 analytical implementation. Original FORTRAN parity is unverified.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, Historical1993SourceProfile,
)
from .kfk5194_1993_canopy_et import (
    KFK5194P3Canopy, KFK5194_SOURCE_URL,
)
from .kfk5194_1993_canopy_regimes import KFK5194P3RegimeResistance
from .leaf_exchange_resistance import LeafExchangeFlux
from .tfwt_v3 import TFWTState, TFWTStepResult, TFWTStorageSolver


class KFK5194Eq1To3Error(ValueError):
    """Invalid SI inputs or unsupported leaf/ground basis."""


CanopyState = KFK5194P3Canopy | KFK5194P3RegimeResistance


@dataclass(frozen=True, slots=True)
class KFK5194LeafInterval:
    """Stationary leaf-atmosphere boundary for one time step."""

    canopy: CanopyState
    air_hto_concentration_bq_m3: float
    saturated_vapour_density_kg_m3: float
    isotope_fractionation_liquid_to_vapour: float
    interval_seconds: float


@dataclass(frozen=True, slots=True)
class KFK5194Eq1To3Step:
    """Exact published transient leaf solution and V3 inventory projection."""

    profile_id: str
    branch: str
    total_leaf_resistance_s_m: float
    equilibration_rate_s_1: float
    equilibrium_tfwt_concentration_bq_kg_water: float
    original_tfwt_concentration_bq_kg_water: float
    analytic_tfwt_concentration_bq_kg_water: float
    eq1_zero_initial_uptake_bq_kg_water: float
    eq3_zero_air_retained_fraction: float
    signed_leaf_transfer_bq_m2_leaf: float
    tfwt_step: TFWTStepResult

    @property
    def state(self) -> TFWTState:
        return self.tfwt_step.state

    @property
    def activity_balance_residual_bq_m2_leaf(self) -> float:
        return self.tfwt_step.balance.residual_bq_m2

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KfK5194_1993_SECTION5_2_PRINTED_P3_PDF0_12",
            "equations": ["1", "2", "3", "4", "5", "6"],
            "profile_id": self.profile_id,
            "normalization": "PER_LEAF_AREA_NOT_GROUND_AREA",
            "leaf_resistance_branch": self.branch,
            "physics_kernel": "DIRECT_1993_PRINTED_BEL0T_EQUATIONS_1_TO_3",
            "water_content": "EXPLICIT_USER_LEAF_AREA_MASS",
            "rho_v_saturated": "EXPLICIT_USER_METEOROLOGICAL_INPUT",
            "assumption": "INTERVAL_STATIONARY_METEOROLOGY_AND_RESISTANCE",
            "original_1993_fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "whole_1993_solver_activation": False,
        }


def _positive(x: float, field: str) -> float:
    if type(x) not in (int, float) or not math.isfinite(float(x)):
        raise KFK5194Eq1To3Error(f"{field} must be finite SI numeric")
    x = float(x)
    if x <= 0.0:
        raise KFK5194Eq1To3Error(f"{field} must be strictly positive")
    return x


def _nonnegative(x: float, field: str) -> float:
    if type(x) not in (int, float) or not math.isfinite(float(x)):
        raise KFK5194Eq1To3Error(f"{field} must be finite SI numeric")
    x = float(x)
    if x < 0.0:
        raise KFK5194Eq1To3Error(f"{field} must be nonnegative")
    return x


def _guard_profile(profile: Historical1993SourceProfile) -> None:
    if not isinstance(profile, Historical1993SourceProfile):
        raise KFK5194Eq1To3Error("explicit 1993 historical typed profile required")
    if (profile.profile_id != PROFILE_ID
            or profile.source_url != KFK5194_SOURCE_URL
            or dict(profile.flag_defaults).get("IMODEL") != 1
            or dict(profile.flag_printed_pages).get("IMODEL") != 54):
        raise KFK5194Eq1To3Error("KfK5194 1993 source identity mismatch")


def _leaf_resistance(canopy: CanopyState) -> tuple[str, float]:
    if isinstance(canopy, KFK5194P3Canopy):
        branch = "DAYLIGHT_DRY"
        stomata = canopy.stomatal_resistance_s_m
        ra = canopy.aerodynamic_resistance_s_m
        rb = canopy.boundary_resistance_s_m
    elif isinstance(canopy, KFK5194P3RegimeResistance):
        branch = canopy.regime.value
        stomata = canopy.leaf_or_epidermal_resistance_s_m
        ra = canopy.aerodynamic_resistance_s_m
        rb = canopy.boundary_layer_resistance_s_m
    else:
        raise KFK5194Eq1To3Error("validated 1993 P3 R1/R2 canopy state required")
    if canopy.profile_id != PROFILE_ID:
        raise KFK5194Eq1To3Error("canopy version mismatch")
    ra = _positive(ra, "aerodynamic_resistance_s_m")
    rb = _positive(rb, "boundary_resistance_s_m")
    stomata = _nonnegative(stomata, "leaf_stomatal_or_epidermal_resistance_s_m")
    if stomata == 0.0 and branch != "DAY_RAIN_ATMOSPHERIC_ONLY_LIMIT":
        raise KFK5194Eq1To3Error("zero leaf resistance allowed only for explicit rain limit")
    leaf_total = _positive(canopy.leaf_total_resistance_s_m, "leaf_total_resistance_s_m")
    if not math.isclose(leaf_total, ra + rb + stomata, rel_tol=1e-12, abs_tol=1e-12):
        raise KFK5194Eq1To3Error("printed Eq.(4) leaf resistance does not close")
    return branch, leaf_total


def advance_kfk5194_1993_leaf_eq1_to3(
    *,
    profile: Historical1993SourceProfile,
    state: TFWTState,
    exposure: KFK5194LeafInterval,
) -> KFK5194Eq1To3Step:
    """Integrate Eq.(1)-(3) in exact SI units, per m² of total leaf area.

    Printed units: mu [g/cm² leaf], rho [g/ml], chi [Bq/ml],
    C [Bq/g water], r_g [s/cm]. The consistent SI transformation is
    mu [kg/m² leaf], rho [kg/m³], chi [Bq/m³], C [Bq/kg], r_g [s/m].

    l = rho/(alpha * mu * r_g) [s^-1];
    C_eq = alpha * chi/rho [Bq/kg];
    C_new = C_old*exp(-l*dt) + C_eq*(1-exp(-l*dt)).
    The 1993 printed Eq.(1) is C_old=0 and Eq.(3) is chi=0.
    """
    _guard_profile(profile)
    if not isinstance(state, TFWTState) or state.area_basis != "leaf_area":
        raise KFK5194Eq1To3Error(
            "1993 printed Eqs.(1)-(3) require TFWT area_basis='leaf_area'"
        )
    if not isinstance(exposure, KFK5194LeafInterval):
        raise KFK5194Eq1To3Error("typed leaf interval exposure required")
    branch, r_leaf = _leaf_resistance(exposure.canopy)
    air = _nonnegative(
        exposure.air_hto_concentration_bq_m3, "air_hto_concentration_bq_m3"
    )
    rho = _positive(
        exposure.saturated_vapour_density_kg_m3, "saturated_vapour_density_kg_m3"
    )
    alpha = _positive(
        exposure.isotope_fractionation_liquid_to_vapour,
        "isotope_fractionation_liquid_to_vapour"
    )
    dt = _positive(exposure.interval_seconds, "interval_seconds")
    mu = _positive(state.water_content_kg_m2, "water_content_kg_m2_leaf")
    initial = _nonnegative(
        state.tfwt_concentration_bq_kg_water, "initial_tfwt_concentration_bq_kg_water"
    )
    rate = rho / (alpha * mu * r_leaf)
    if not math.isfinite(rate) or rate <= 0.0:
        raise KFK5194Eq1To3Error("Eq.(2) rate is invalid")
    equilibrium = alpha * air / rho
    if not math.isfinite(equilibrium):
        raise KFK5194Eq1To3Error("Eq.(1) equilibrium concentration overflows")
    # expm1 avoids subtractive cancellation when dt is short compared to 1/rate.
    fraction = -math.expm1(-rate * dt)
    next_conc = (1.0 - fraction) * initial + fraction * equilibrium
    # Compute signed integrated transfer independently of rounded C_new.
    signed_transfer = mu * (equilibrium - initial) * fraction
    if not all(math.isfinite(x) for x in (next_conc, signed_transfer)):
        raise KFK5194Eq1To3Error("Eq.(1)-(3) integrated exchange overflow")
    mean_flux = signed_transfer / dt
    if not math.isfinite(mean_flux):
        raise KFK5194Eq1To3Error("integrated exchange rate overflow")
    step = TFWTStorageSolver().advance(
        state, LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=mean_flux), dt
    )
    predicted_activity = mu * next_conc
    activity_scale = max(
        1.0, abs(predicted_activity), abs(step.state.tfwt_inventory_bq_m2)
    )
    if not math.isclose(
        step.state.tfwt_inventory_bq_m2, predicted_activity,
        rel_tol=2e-12, abs_tol=2e-12 * activity_scale
    ):
        raise KFK5194Eq1To3Error("1993 analytic TFWT state mismatch")
    return KFK5194Eq1To3Step(
        profile_id=PROFILE_ID, branch=branch, total_leaf_resistance_s_m=r_leaf,
        equilibration_rate_s_1=rate,
        equilibrium_tfwt_concentration_bq_kg_water=equilibrium,
        original_tfwt_concentration_bq_kg_water=initial,
        analytic_tfwt_concentration_bq_kg_water=next_conc,
        eq1_zero_initial_uptake_bq_kg_water=equilibrium * fraction,
        eq3_zero_air_retained_fraction=1.0 - fraction,
        signed_leaf_transfer_bq_m2_leaf=signed_transfer,
        tfwt_step=step,
    )


def advance_kfk5194_1993_leaf_intervals(
    *,
    profile: Historical1993SourceProfile,
    initial_state: TFWTState,
    exposures: Sequence[KFK5194LeafInterval],
) -> tuple[KFK5194Eq1To3Step, ...]:
    """Sequential interval-constant Eq.(1)-(3) state progression."""
    if not isinstance(exposures, (list, tuple)) or not exposures:
        raise KFK5194Eq1To3Error("nonempty sequence of explicit intervals required")
    state = initial_state
    history = []
    for exposure in exposures:
        result = advance_kfk5194_1993_leaf_eq1_to3(
            profile=profile, state=state, exposure=exposure
        )
        history.append(result)
        state = result.state
    return tuple(history)
