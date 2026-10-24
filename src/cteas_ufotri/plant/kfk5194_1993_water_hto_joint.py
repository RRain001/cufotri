"""KfK 5194 (1993) P3 R6: source-limited fixed-water Belot/root ledger.

Primary evidence: §5.2 printed p.3 Eq.(1)-(3), §5.3 printed p.6,
§5.3.1 printed p.7 (PDF zero-based pp.12,15,16).
The manual explicitly says Belot HTO re-emission ALREADY includes diffusion
AND transpiration-related tritium loss. The Monteith E is therefore used
only in the water-loss/root-replacement balance, NOT as an extra -E*C HTO
sink. Root-to-leaf instantaneous mixing remains a research assumption.

This deliberately supports R=E and fixed leaf water only. Dynamic water
mass, isotope partition/fractionation, soil hydraulics, OBT and complete
1993 FORTRAN numerical behavior are not established or activated.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import timedelta
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile, PROFILE_ID
from .kfk5194_1993_canopy_et import (
    KFK5194P3Canopy, KFK5194P3Monteith, KFK5194_SOURCE_URL,
    KFK5194_LAI_RADIATION_EXPONENT,
)
from .tfwt_v3 import TFWTState


class KFK5194WaterActivityError(ValueError):
    """Unsafe source identity, unsupported control volume, or invalid SI forcing."""


class KFK5194LeafWaterHypothesis(str, Enum):
    """Explicit scientific scope: fixed water, composite Belot HTO loss."""

    BELOT_COMPOSITE_FIXED_LEAF_WATER = "BELOT_COMPOSITE_FIXED_LEAF_WATER"


@dataclass(frozen=True, slots=True)
class KFK5194WaterActivityForcing:
    """Prescribed dry-day interval, SI units, with external root-water boundary."""

    monteith: KFK5194P3Monteith
    air_hto_concentration_bq_m3: float
    saturated_vapour_density_kg_m3: float
    isotope_fractionation_liquid_to_vapour: float
    root_water_delivery_kg_m2_ground_s: float
    root_water_hto_concentration_bq_kg: float
    interval_seconds: float


@dataclass(frozen=True, slots=True)
class KFK5194WaterActivityStep:
    """Water mass and independently closed composite Belot/root HTO budget."""

    profile_id: str
    leaf_area_index: float
    initial_leaf_water_kg_m2_ground: float
    final_leaf_water_kg_m2_ground: float
    root_water_input_kg_m2_ground: float
    monteith_plant_water_loss_kg_m2_ground: float
    water_balance_residual_kg_m2_ground: float
    initial_hto_activity_bq_m2_ground: float
    final_hto_activity_bq_m2_ground: float
    belot_composite_hto_exchange_bq_m2_ground: float
    root_hto_input_bq_m2_ground: float
    additional_et_hto_sink_bq_m2_ground: float
    hto_balance_residual_bq_m2_ground: float
    belot_exchange_water_equivalent_kg_m2_ground_s: float
    equilibrium_atmospheric_leaf_hto_bq_kg_water: float
    integrated_leaf_concentration_bq_s_kg_water: float
    state: TFWTState

    def provenance(self) -> dict[str, object]:
        return {
            "source_leaf_exchange": "KFK5194_1993_PRINTED_EQ1_TO4",
            "source_plant_et": "KFK5194_1993_PRINTED_EQ11",
            "source_flux_partition": "KFK5194_1993_PRINTED_P7_BELOT_COMPOSITE_DIFFUSION_AND_TRANSPIRATION_LOSS",
            "profile_id": self.profile_id,
            "water_pool": "FIXED_LEAF_WATER_ONLY_PER_GROUND_AREA",
            "area_assumption": "HOMOGENEOUS_CONSTANT_LAI",
            "water_control_volume": "ROOT_REPLACES_ALL_PLANT_ET_R_EQUALS_E",
            "root_activity_delivery": "EXPLICIT_INSTANT_LEAF_MIXING_ASSUMPTION",
            "belot_hto_loss_already_includes_transpiration": True,
            "extra_transpiration_hto_sink": "PROHIBITED_TO_PREVENT_DOUBLE_COUNT",
            "original_fortran_water_mass_coupling": "NOT_ESTABLISHED",
            "dynamic_water_mass": "REJECTED_NOT_SOURCE_QUALIFIED",
            "soil_root_dynamics_obt_growth": "NOT_IMPLEMENTED",
            "whole_1993_solver_runtime_activated": False,
        }


def _finite(x: float, name: str, *, positive: bool = False) -> float:
    if type(x) not in (int, float) or not math.isfinite(float(x)):
        raise KFK5194WaterActivityError(f"{name} must be a finite SI number")
    x = float(x)
    if (positive and x <= 0.0) or (not positive and x < 0.0):
        raise KFK5194WaterActivityError(f"{name} is outside its allowed physical domain")
    return x


def _validated(
    *, profile: Historical1993SourceProfile,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    hypothesis: KFK5194LeafWaterHypothesis,
) -> tuple[float, float, float, float, float, float, float, float, float]:
    if not isinstance(profile, Historical1993SourceProfile) or (
        profile.profile_id != PROFILE_ID
        or profile.source_url != KFK5194_SOURCE_URL
        or dict(profile.flag_defaults).get("IMODEL") != 1
        or dict(profile.flag_defaults).get("IMONT") != 1
    ):
        raise KFK5194WaterActivityError("explicit 1993 historical P1 profile required")
    if not isinstance(canopy, KFK5194P3Canopy) or canopy.profile_id != PROFILE_ID:
        raise KFK5194WaterActivityError("1993 dry-day P3 canopy is required")
    if not isinstance(state, TFWTState) or state.area_basis != "ground_area":
        raise KFK5194WaterActivityError("explicit ground_area leaf-water-only state required")
    if not isinstance(forcing, KFK5194WaterActivityForcing):
        raise KFK5194WaterActivityError("typed interval forcing required")
    if hypothesis is not KFK5194LeafWaterHypothesis.BELOT_COMPOSITE_FIXED_LEAF_WATER:
        raise KFK5194WaterActivityError("explicit non-double-counting Belot hypothesis required")
    et_result = forcing.monteith
    if not isinstance(et_result, KFK5194P3Monteith) or et_result.profile_id != PROFILE_ID:
        raise KFK5194WaterActivityError("1993 Monteith result is required")
    lai = _finite(canopy.leaf_area_index, "LAI", positive=True)
    ra = _finite(canopy.aerodynamic_resistance_s_m, "r_av", positive=True)
    rb = _finite(canopy.boundary_resistance_s_m, "r_bv", positive=True)
    rs = _finite(canopy.stomatal_resistance_s_m, "r_st", positive=True)
    rg = _finite(canopy.leaf_total_resistance_s_m, "r_g", positive=True)
    if not math.isclose(rg, ra + rb + rs, rel_tol=1e-12, abs_tol=1e-12):
        raise KFK5194WaterActivityError("1993 Eq.(4) leaf resistance does not close")
    radiation = _finite(et_result.input_net_radiation_w_m2, "net radiation")
    plant_rad = _finite(et_result.plant_radiation_w_m2, "plant radiation")
    soil_rad = _finite(et_result.soil_radiation_w_m2, "soil radiation")
    scale = max(1.0, radiation)
    if not (
        math.isclose(plant_rad + soil_rad, radiation, rel_tol=0, abs_tol=1e-10 * scale)
        and math.isclose(
            soil_rad, radiation * math.exp(-KFK5194_LAI_RADIATION_EXPONENT * lai),
            rel_tol=0, abs_tol=1e-10 * scale,
        )
    ):
        raise KFK5194WaterActivityError("Monteith canopy LAI/radiation mismatch")
    latent = _finite(et_result.latent_heat_vaporization_j_kg, "latent heat", positive=True)
    plant_latent = _finite(et_result.plant_latent_heat_flux_w_m2, "plant latent heat")
    et = _finite(et_result.plant_water_flux_kg_m2_s, "plant ET")
    if not math.isclose(et, plant_latent / latent, rel_tol=1e-12, abs_tol=1e-15):
        raise KFK5194WaterActivityError("Monteith plant-only ET units invalid")
    rho = _finite(forcing.saturated_vapour_density_kg_m3, "saturated vapour", positive=True)
    alpha = _finite(forcing.isotope_fractionation_liquid_to_vapour, "fractionation", positive=True)
    air = _finite(forcing.air_hto_concentration_bq_m3, "air HTO")
    root = _finite(forcing.root_water_delivery_kg_m2_ground_s, "root delivery")
    root_c = _finite(forcing.root_water_hto_concentration_bq_kg, "root-water HTO")
    dt = _finite(forcing.interval_seconds, "interval duration", positive=True)
    _finite(state.water_content_kg_m2, "initial leaf water", positive=True)
    _finite(state.tfwt_inventory_bq_m2, "initial HTO activity")
    # Only the printed p.6 transpiration-driven root replenishment is within
    # scope. Even a small R-E discrepancy would imply an unverified isotope
    # equation for changing W, therefore this branch fails closed.
    if not math.isclose(root, et, rel_tol=1e-12, abs_tol=1e-15):
        raise KFK5194WaterActivityError(
            "fixed leaf-water control volume requires root delivery R=Monteith E"
        )
    return lai, rg, et, rho, alpha, air, root, root_c, dt


def advance_kfk5194_water_hto_joint(
    *, profile: Historical1993SourceProfile,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194WaterActivityStep:
    """Exact interval solution of a non-overlapping fixed-water source budget.

    Wdot=R-E=0  [kg/m² ground/s] (explicit R=E).
    Idot=a*(Ceq-C)+R*Croot [Bq/m² ground/s] ; C=I/W.
    a=LAI*rho/(alpha*r_g) [kg/m² ground/s], Ceq=alpha*Cair/rho.

    The negative part of a*(Ceq-C) is the COMPLETE Belot composite leaf
    HTO loss (diffusion plus transpiration); no extra -E*C is ever added.
    Root HTO delivery is external and added once; instantaneous root
    mixing remains an unverified reconstruction assumption. No inference
    about original binary execution or changing leaf water is made.
    """
    lai, rg, et, rho, alpha, air, root, root_c, dt = _validated(
        profile=profile, canopy=canopy, state=state,
        forcing=forcing, hypothesis=hypothesis,
    )
    W0 = state.water_content_kg_m2
    C0 = state.tfwt_concentration_bq_kg_water
    I0 = state.tfwt_inventory_bq_m2
    a = lai * rho / (alpha * rg)
    Ceq = alpha * air / rho
    rate = a / W0
    root_activity_rate = root * root_c
    if not all(math.isfinite(x) for x in (a, Ceq, rate, root_activity_rate)) or a <= 0:
        raise KFK5194WaterActivityError("Belot parameters overflow or underflow")
    Cstar = Ceq + root_activity_rate / a
    if not math.isfinite(Cstar):
        raise KFK5194WaterActivityError("fixed-water equilibrium HTO overflow")
    fraction = -math.expm1(-rate * dt)
    C1 = C0 + (Cstar - C0) * fraction
    # Exact time integral of C for a constant leaf water reservoir.
    integrated_C = Cstar * dt + (C0 - Cstar) * fraction / rate
    I1 = W0 * C1
    belot = a * (Ceq * dt - integrated_C)
    root_in = root_activity_rate * dt
    if not all(math.isfinite(x) for x in (C1, integrated_C, I1, belot, root_in)):
        raise KFK5194WaterActivityError("non-finite fixed-water HTO ledger")
    if C1 < 0 or integrated_C < 0 or I1 < 0:
        raise KFK5194WaterActivityError("negative HTO activity outside physical domain")
    water_in = root * dt
    water_out = et * dt
    water_residual = water_in - water_out
    hto_residual = I1 - I0 - belot - root_in
    water_scale = max(1.0, W0, water_in, water_out)
    hto_scale = max(1.0, abs(I0), abs(I1), abs(belot), root_in)
    if (abs(water_residual) > 2e-11 * water_scale
            or abs(hto_residual) > 2e-11 * hto_scale):
        raise KFK5194WaterActivityError("water or HTO isotope budget does not close")
    updated = replace(
        state,
        tfwt_inventory_bq_m2=I1,
        tfwt_concentration_bq_kg_water=C1,
        time=state.time + timedelta(seconds=dt),
    )
    return KFK5194WaterActivityStep(
        profile_id=PROFILE_ID, leaf_area_index=lai,
        initial_leaf_water_kg_m2_ground=W0, final_leaf_water_kg_m2_ground=W0,
        root_water_input_kg_m2_ground=water_in,
        monteith_plant_water_loss_kg_m2_ground=water_out,
        water_balance_residual_kg_m2_ground=water_residual,
        initial_hto_activity_bq_m2_ground=I0,
        final_hto_activity_bq_m2_ground=I1,
        belot_composite_hto_exchange_bq_m2_ground=belot,
        root_hto_input_bq_m2_ground=root_in,
        additional_et_hto_sink_bq_m2_ground=0.0,
        hto_balance_residual_bq_m2_ground=hto_residual,
        belot_exchange_water_equivalent_kg_m2_ground_s=a,
        equilibrium_atmospheric_leaf_hto_bq_kg_water=Ceq,
        integrated_leaf_concentration_bq_s_kg_water=integrated_C,
        state=updated,
    )
