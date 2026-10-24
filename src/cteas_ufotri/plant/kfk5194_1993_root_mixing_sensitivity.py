"""Source-limited analytic HTO sensitivity for 1993 P3 R6 research mixing.

This is a diagnostic tangent to the EXPLICIT opt-in, R=E fixed-leaf-water
Belot/root model. It does not create a time-lagged root transport model,
predict actual mixing times, or reproduce original UFOTRI 4.0 FORTRAN.
Fractions: KfK5194 (1993) printed p.15; Belot Eq.(1)-(3), printed p.3.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile, PROFILE_ID
from .kfk5194_1993_canopy_et import KFK5194P3Canopy
from .kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup, KFK5194RootMixingHypothesis,
    KFK5194RootCoupledStep,
    advance_kfk5194_1993_soil_weighted_root_boundary,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194WaterActivityError, KFK5194LeafWaterHypothesis,
    KFK5194WaterActivityForcing,
)
from .tfwt_v3 import TFWTState


@dataclass(frozen=True, slots=True)
class KFK5194RootMixingSensitivity:
    """Local partial derivatives at fixed water pool and forcing, SI units.

    Each tuple element is the first-order response to 1 Bq/kg change in
    that horizon's externally specified soil liquid-water HTO concentration.
    """

    profile_id: str
    plant_group: KFK5194RootPlantGroup
    baseline: KFK5194RootCoupledStep
    initial_hto_memory_fraction: float
    root_layer_final_activity_sensitivity_kg_m2_ground: tuple[float, float, float]
    root_layer_final_concentration_sensitivity: tuple[float, float, float]
    air_hto_final_activity_sensitivity_m: float

    def provenance(self) -> dict[str, object]:
        return {
            "source_fractions": "KFK5194_1993_PRINTED_P15",
            "source_exchange": "KFK5194_1993_PRINTED_EQ1_TO3",
            "response_type": "EXACT_LINEAR_LOCAL_SENSITIVITY_FIXED_WATER",
            "root_leaf_mixing": "SOURCE_LIMITED_INSTANT_HOMOGENEOUS_RESEARCH_OPT_IN",
            "root_transit_time": "NOT_ESTABLISHED",
            "actual_mixing_timescale": "NOT_ESTABLISHED",
            "original_fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def diagnose_kfk5194_1993_root_mixing_sensitivity(
    *,
    profile: Historical1993SourceProfile,
    plant_group: KFK5194RootPlantGroup,
    soil_layer_water_hto_bq_kg: tuple[float, float, float],
    mixing_hypothesis: KFK5194RootMixingHypothesis,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194RootMixingSensitivity:
    """Exact tangent from a verified run; not a physical validation.

    For fixed W, a and R=E:
      dI/dt = a(C_eq - I/W) + R * sum(f_i C_soil,i)
      dI_final/dC_soil,i = W*(R*f_i/a)*(1-exp(-a*dt/W))
      dC_final/dC_soil,i = (R*f_i/a)*(1-exp(-a*dt/W))
      dI_final/dC_air = W*alpha/rho*(1-exp(-a*dt/W))
      dI_final/dI_initial = exp(-a*dt/W)

    Source-defined fractions f_i are fixed for each historical plant group.
    They do NOT constrain any root transport delay, fractionation, or mixing.
    """
    coupled = advance_kfk5194_1993_soil_weighted_root_boundary(
        profile=profile, plant_group=plant_group,
        soil_layer_water_hto_bq_kg=soil_layer_water_hto_bq_kg,
        mixing_hypothesis=mixing_hypothesis,
        canopy=canopy, state=state, forcing=forcing,
        leaf_hypothesis=leaf_hypothesis,
    )
    leaf = coupled.leaf_water_hto_step
    W = leaf.initial_leaf_water_kg_m2_ground
    a = leaf.belot_exchange_water_equivalent_kg_m2_ground_s
    rho = forcing.saturated_vapour_density_kg_m3
    alpha = forcing.isotope_fractionation_liquid_to_vapour
    R = forcing.root_water_delivery_kg_m2_ground_s
    dt = forcing.interval_seconds
    rate = a / W
    decay = math.exp(-rate * dt)
    uptake_factor = -math.expm1(-rate * dt)
    concentration_sensitivity = tuple(
        R * f * uptake_factor / a
        for f in coupled.boundary.root_water_fractions
    )
    activity_sensitivity = tuple(
        W * x for x in concentration_sensitivity
    )
    air_sensitivity = W * alpha / rho * uptake_factor
    if not all(math.isfinite(x) and x >= 0. for x in (
        decay, uptake_factor, air_sensitivity,
        *activity_sensitivity, *concentration_sensitivity,
    )):
        raise KFK5194WaterActivityError(
            "nonfinite or negative fixed-water root/air HTO tangent"
        )
    return KFK5194RootMixingSensitivity(
        profile_id=PROFILE_ID,
        plant_group=plant_group,
        baseline=coupled,
        initial_hto_memory_fraction=decay,
        root_layer_final_activity_sensitivity_kg_m2_ground=activity_sensitivity,
        root_layer_final_concentration_sensitivity=concentration_sensitivity,
        air_hto_final_activity_sensitivity_m=air_sensitivity,
    )
