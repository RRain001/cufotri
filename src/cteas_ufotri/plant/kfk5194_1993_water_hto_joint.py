"""P3 R6 opt-in joint leaf-water and HTO ledger under explicit assumptions.

KfK5194 (1993) supplies Eqs.(1)-(4) leaf exchange, Eq.(10) LAI and
Eq.(11) daytime Monteith plant transpiration. The water-mass and root
mixing operators here are RESEARCH CLOSURE ASSUMPTIONS, not verified
original UFOTRI 1993 FORTRAN or a complete root/soil/OBT transport model.

Homogeneous constant-LAI ground-area LEAF-water pool only.
Transpired water is assumed nonfractionating and leaves with instantaneous
TFWT concentration; supplied root water mixes instantly into the leaf pool.
These additional terms might double-count parts of true plant-vapour
exchange if coupled to a different atmospheric mass formulation; this
module stays opt-in and explicitly marks this source limitation.
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
    """Invalid provenance, SI forcing, dry-water state or ledger closure."""


class KFK5194LeafWaterHypothesis(str, Enum):
    """Never silently interpret root-water delivery or transpiration isotopes."""

    WELL_MIXED_NO_ET_FRACTIONATION = "WELL_MIXED_NO_ET_FRACTIONATION"


@dataclass(frozen=True, slots=True)
class KFK5194WaterActivityForcing:
    """Daylight dry interval, concentrations and rates in explicit SI units."""

    monteith: KFK5194P3Monteith
    air_hto_concentration_bq_m3: float
    saturated_vapour_density_kg_m3: float
    isotope_fractionation_liquid_to_vapour: float
    root_water_delivery_kg_m2_ground_s: float
    root_water_hto_concentration_bq_kg: float
    interval_seconds: float


@dataclass(frozen=True, slots=True)
class KFK5194WaterActivityStep:
    """Exact fixed-forcing solution and signed extensive water/HTO ledger."""

    profile_id: str
    leaf_area_index: float
    initial_leaf_water_kg_m2_ground: float
    final_leaf_water_kg_m2_ground: float
    root_water_input_kg_m2_ground: float
    monteith_plant_water_loss_kg_m2_ground: float
    water_balance_residual_kg_m2_ground: float
    initial_hto_activity_bq_m2_ground: float
    final_hto_activity_bq_m2_ground: float
    air_leaf_hto_transfer_bq_m2_ground: float
    root_hto_input_bq_m2_ground: float
    transpired_hto_loss_bq_m2_ground: float
    hto_balance_residual_bq_m2_ground: float
    leaf_air_exchange_water_equivalent_kg_m2_ground_s: float
    equilibrium_leaf_hto_bq_kg_water: float
    mean_leaf_hto_bq_kg_water: float
    state: TFWTState

    def provenance(self) -> dict[str, object]:
        return {
            "source_leaf_exchange": "KFK5194_1993_EQ1_TO4",
            "source_leaf_area_index": "KFK5194_1993_EQ10",
            "source_plant_transpiration": "KFK5194_1993_EQ11",
            "profile_id": self.profile_id,
            "water_pool": "LEAF_WATER_ONLY_PER_GROUND_AREA",
            "area_assumption": "HOMOGENEOUS_CONSTANT_LAI",
            "root_water_transport": "INSTANT_EXPLICIT_DELIVERY_ASSUMPTION",
            "transpired_hto": "NO_FRACTIONATION_WELL_MIXED_ASSUMPTION",
            "potential_overlap_of_vapour_exchange_and_transpiration": "SCIENTIFIC_REVIEW_REQUIRED",
            "original_fortran_water_mass_coupling": "NOT_ESTABLISHED",
            "soil_root_dynamics_obt_growth": "NOT_IMPLEMENTED",
            "whole_1993_solver_runtime_activated": False,
        }


def _finite(x: float, label: str, *, strictly_positive: bool = False) -> float:
    if type(x) not in (int, float) or not math.isfinite(float(x)):
        raise KFK5194WaterActivityError(f"{label} must be finite numeric SI")
    x = float(x)
    if (strictly_positive and x <= 0.0) or (not strictly_positive and x < 0.0):
        raise KFK5194WaterActivityError(f"{label} outside positive SI domain")
    return x


def _validate(
    *, profile: Historical1993SourceProfile,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    hypothesis: KFK5194LeafWaterHypothesis,
) -> tuple[float, float, float, float, float, float, float, float]:
    if not isinstance(profile, Historical1993SourceProfile) or (
        profile.profile_id != PROFILE_ID
        or profile.source_url != KFK5194_SOURCE_URL
        or dict(profile.flag_defaults).get("IMODEL") != 1
        or dict(profile.flag_defaults).get("IMONT") != 1
    ):
        raise KFK5194WaterActivityError("explicit KfK5194 1993 source profile required")
    if not isinstance(canopy, KFK5194P3Canopy) or canopy.profile_id != PROFILE_ID:
        raise KFK5194WaterActivityError("P3 R1 DAYLIGHT_DRY canopy required")
    if not isinstance(state, TFWTState) or state.area_basis != "ground_area":
        raise KFK5194WaterActivityError("ground-area LEAF-water-only TFWT state required")
    if not isinstance(forcing, KFK5194WaterActivityForcing):
        raise KFK5194WaterActivityError("typed KfK5194 water/activity forcing required")
    if hypothesis is not KFK5194LeafWaterHypothesis.WELL_MIXED_NO_ET_FRACTIONATION:
        raise KFK5194WaterActivityError("explicit well-mixed isotope assumption required")
    monteith = forcing.monteith
    if not isinstance(monteith, KFK5194P3Monteith) or monteith.profile_id != PROFILE_ID:
        raise KFK5194WaterActivityError("1993 P3 R1 Monteith result required")
    lai = _finite(canopy.leaf_area_index, "LAI", strictly_positive=True)
    ra = _finite(canopy.aerodynamic_resistance_s_m, "ra", strictly_positive=True)
    rb = _finite(canopy.boundary_resistance_s_m, "rb", strictly_positive=True)
    rs = _finite(canopy.stomatal_resistance_s_m, "rs", strictly_positive=True)
    rg = _finite(canopy.leaf_total_resistance_s_m, "rg", strictly_positive=True)
    if not math.isclose(rg, ra + rb + rs, rel_tol=1e-12, abs_tol=1e-12):
        raise KFK5194WaterActivityError("leaf resistance does not close Eq.(4)")
    radiation = _finite(monteith.input_net_radiation_w_m2, "net radiation")
    plant_rad = _finite(monteith.plant_radiation_w_m2, "plant radiation")
    soil_rad = _finite(monteith.soil_radiation_w_m2, "soil radiation")
    scale = max(1.0, radiation)
    if (not math.isclose(plant_rad + soil_rad, radiation, abs_tol=1e-10*scale)
        or not math.isclose(soil_rad, radiation * math.exp(
            -KFK5194_LAI_RADIATION_EXPONENT*lai), abs_tol=1e-10*scale)):
        raise KFK5194WaterActivityError("Monteith LAI/radiation basis mismatch")
    latent = _finite(monteith.latent_heat_vaporization_j_kg,
                     "latent heat", strictly_positive=True)
    plant_heat = _finite(monteith.plant_latent_heat_flux_w_m2, "plant latent heat")
    et = _finite(monteith.plant_water_flux_kg_m2_s, "plant ET")
    if not math.isclose(et, plant_heat / latent, rel_tol=1e-12, abs_tol=1e-15):
        raise KFK5194WaterActivityError("Monteith plant water/latent heat units mismatch")
    rho = _finite(forcing.saturated_vapour_density_kg_m3, "vapour density", strictly_positive=True)
    alpha = _finite(forcing.isotope_fractionation_liquid_to_vapour,
                    "fractionation", strictly_positive=True)
    air = _finite(forcing.air_hto_concentration_bq_m3, "air HTO")
    root = _finite(forcing.root_water_delivery_kg_m2_ground_s, "root water")
    root_c = _finite(forcing.root_water_hto_concentration_bq_kg, "root TFWT")
    dt = _finite(forcing.interval_seconds, "interval", strictly_positive=True)
    _finite(state.water_content_kg_m2, "leaf pool water", strictly_positive=True)
    _finite(state.tfwt_inventory_bq_m2, "leaf pool HTO inventory")
    return lai, rg, et, rho, alpha, air, root, root_c, dt


def advance_kfk5194_water_hto_joint(
    *, profile: Historical1993SourceProfile,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194WaterActivityStep:
    """Exact homogeneous daytime water/HTO ODE under interval-fixed fluxes.

    Wdot=R-E [kg/m2 ground/s].
    I_dot=a*(Ceq-C)+R*Croot-E*C [Bq/m2 ground/s].
    a=LAI*rho/(alpha*r_g) [kg/m2 ground/s], C=I/W [Bq/kg],
    Ceq=alpha*Cair/rho. Root delivery R and plant (not soil) Monteith
    ET E are explicit external rates. The no-fractionation ET sink and
    instantaneous root-water mixing are assumed, not original FORTRAN.

    With W linear, concentration satisfies
    Cdot=(a*(Ceq-C)+R*(Croot-C))/W(t),
    which is integrated analytically. Also integrate the concentration
    over the interval to give independent air/root/ET HTO flux ledgers.
    """
    lai, rg, et, rho, alpha, air, root, root_c, dt = _validate(
        profile=profile, canopy=canopy, state=state,
        forcing=forcing, hypothesis=hypothesis,
    )
    W0 = state.water_content_kg_m2
    C0 = state.tfwt_concentration_bq_kg_water
    I0 = state.tfwt_inventory_bq_m2
    water_delta = (root-et)*dt
    W1 = W0 + water_delta
    if not math.isfinite(W1) or W1 <= 0.0:
        raise KFK5194WaterActivityError(
            "Monteith transpiration exhausts leaf water: explicit replenishment required"
        )
    a = lai*rho/(alpha*rg)
    Ceq = alpha*air/rho
    if not math.isfinite(a) or a <= 0 or not math.isfinite(Ceq):
        raise KFK5194WaterActivityError("leaf-air HTO transfer parameter overflow")
    total_supply = a+root
    total_removal = a+et
    Cstar = (a*Ceq+root*root_c)/total_supply
    if not math.isfinite(Cstar):
        raise KFK5194WaterActivityError("equilibrium leaf HTO overflow")
    x = water_delta/W0
    # L = integral_0^dt 1/W(t) dt, stable also when root water = plant ET.
    exposure = dt/W0 if x == 0.0 else (dt/W0)*(math.log1p(x)/x)
    uptake_fraction = -math.expm1(-total_supply*exposure)
    C1 = C0+(Cstar-C0)*uptake_fraction
    integrated_C = (
        Cstar*dt
        + (C0-Cstar)*(W0/total_removal)*(
            -math.expm1(-total_removal*exposure)
        )
    )
    air_exchange = a*(Ceq*dt-integrated_C)
    root_in = root*root_c*dt
    et_out = et*integrated_C
    I1 = W1*C1
    if not all(math.isfinite(v) for v in
               (exposure, C1, integrated_C, I1, air_exchange, root_in, et_out)):
        raise KFK5194WaterActivityError("joint water-HTO solution overflow")
    if C1 < -1e-12 or integrated_C < -1e-12 or I1 < -1e-12:
        raise KFK5194WaterActivityError("negative HTO concentration or inventory")
    new = replace(
        state,
        water_content_kg_m2=W1,
        tfwt_inventory_bq_m2=I1,
        tfwt_concentration_bq_kg_water=C1,
        time=state.time+timedelta(seconds=dt),
    )
    water_residual = W1-W0-root*dt+et*dt
    hto_residual = I1-I0-air_exchange-root_in+et_out
    water_scale = max(1.0, abs(W0), abs(W1), root*dt, et*dt)
    hto_scale = max(1.0, abs(I0), abs(I1), abs(air_exchange), root_in, et_out)
    if (abs(water_residual)>2e-10*water_scale
            or abs(hto_residual)>2e-10*hto_scale):
        raise KFK5194WaterActivityError("joint mass/activity conservation failed")
    return KFK5194WaterActivityStep(
        profile_id=PROFILE_ID, leaf_area_index=lai,
        initial_leaf_water_kg_m2_ground=W0, final_leaf_water_kg_m2_ground=W1,
        root_water_input_kg_m2_ground=root*dt,
        monteith_plant_water_loss_kg_m2_ground=et*dt,
        water_balance_residual_kg_m2_ground=water_residual,
        initial_hto_activity_bq_m2_ground=I0,
        final_hto_activity_bq_m2_ground=I1,
        air_leaf_hto_transfer_bq_m2_ground=air_exchange,
        root_hto_input_bq_m2_ground=root_in,
        transpired_hto_loss_bq_m2_ground=et_out,
        hto_balance_residual_bq_m2_ground=hto_residual,
        leaf_air_exchange_water_equivalent_kg_m2_ground_s=a,
        equilibrium_leaf_hto_bq_kg_water=Ceq,
        mean_leaf_hto_bq_kg_water=integrated_C/dt,
        state=new,
    )
