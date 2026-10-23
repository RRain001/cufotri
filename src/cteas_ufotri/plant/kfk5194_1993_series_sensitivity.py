"""Conditional multi-interval tangent of P3 R6 extraction-only research.

KfK5194 (1993) printed p.15 supplies *only* root water uptake fractions.
Printed pp.3/7 provide Belot composite exchange, including transpiration-related
HTO loss. This module derives an exact mathematical tangent of the explicitly
opted-in fixed-W, R=E, no-recharge and instantaneous-mixing RESEARCH model.
It provides no evidence for physical instantaneous mixing, root lag, soil
hydrology, field validity or original 1993 FORTRAN numerical equivalence.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_canopy_et import KFK5194P3Canopy
from .kfk5194_1993_root_soil_boundary import KFK5194RootMixingHypothesis
from .kfk5194_1993_soil_root_transfer import (
    KFK5194SoilEvolutionHypothesis,
    KFK5194SoilLayerInventoryState,
    KFK5194SoilRootLeafSeries,
    advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis,
    KFK5194WaterActivityError,
    KFK5194WaterActivityForcing,
)
from .tfwt_v3 import TFWTState


@dataclass(frozen=True, slots=True)
class KFK5194SeriesSensitivity:
    """Final-activity derivatives, conditional on unchanged water/forcing.

    Soil-input basis: independently vary each initial *liquid-water HTO
    concentration* [Bq/kg], equivalently varying initial soil HTO stock by
    W_soil_initial[i] * dC[i] while holding soil water fixed.
    Air-input basis: independently vary each interval's C_air [Bq/m3].
    All sensitivities are of final leaf HTO inventory [Bq/m2 ground].
    """

    baseline: KFK5194SoilRootLeafSeries
    initial_leaf_activity_memory_fraction: float  # (Bq/m2)/(Bq/m2)
    initial_soil_concentration_to_final_leaf_activity_kg_m2_ground: tuple[float, float, float]
    interval_air_concentration_to_final_leaf_activity_m: tuple[float, ...]
    initial_soil_concentration_to_final_soil_activity_kg_m2_ground: tuple[float, float, float]
    initial_soil_concentration_to_cumulative_belot_activity_kg_m2_ground: tuple[float, float, float]

    def provenance(self) -> dict[str, object]:
        return {
            "source_root_fractions": "KFK5194_1993_PRINTED_P15",
            "source_exchange": "KFK5194_1993_PRINTED_EQ1_TO3_P7_COMPOSITE",
            "sensitivity_basis": "FIXED_INITIAL_SOIL_WATER_AND_EXPLICIT_INTERVAL_FORCING",
            "model": "EXTRACTION_ONLY_FIXED_LEAF_WATER_RESEARCH",
            "root_leaf_mixing": "SOURCE_LIMITED_INSTANT_MIXING_RESEARCH_OPT_IN",
            "soil_transport_recharge": "NOT_IMPLEMENTED",
            "root_transit_time": "NOT_ESTABLISHED",
            "original_fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "independent_scientific_validation": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def diagnose_kfk5194_1993_series_sensitivity(
    *,
    profile: Historical1993SourceProfile,
    initial_soil: KFK5194SoilLayerInventoryState,
    initial_leaf: TFWTState,
    canopy: KFK5194P3Canopy,
    intervals: tuple[KFK5194WaterActivityForcing, ...],
    evolution_hypothesis: KFK5194SoilEvolutionHypothesis,
    root_mixing_hypothesis: KFK5194RootMixingHypothesis,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194SeriesSensitivity:
    """Compute exact *conditional* tangent across all supplied intervals.

    During extraction alone each active well-mixed layer retains its initial
    C_i=A_i/W_i. This statement ceases to be differentiable at soil-water
    exhaustion; all contributing layers must remain strictly wet after each
    interval. It does not apply to infiltration, mixing delays or any other
    soil process.

    For j-th interval, with W fixed and a_j>0:
      g_j = exp(-a_j dt_j/W)
      b_ij = W*R_j*f_i*(1-g_j)/a_j  [kg/m2]
      h_j = W*(alpha_j/rho_j)*(1-g_j)  [m]
      dI_j/dC_i = g_j*dI_(j-1)/dC_i + b_ij
      dI_j/dC_air,k = g_j*dI_(j-1)/dC_air,k (k<j), or h_j (k=j)
    Initial-leaf memory is product(g_j). The flux is Belot composite;
    an extra -E*C term MUST NOT be introduced.
    """
    baseline = advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals(
        profile=profile, initial_soil=initial_soil, initial_leaf=initial_leaf,
        canopy=canopy, intervals=intervals,
        evolution_hypothesis=evolution_hypothesis,
        root_mixing_hypothesis=root_mixing_hypothesis,
        leaf_hypothesis=leaf_hypothesis,
    )
    soil_slope = [0.0, 0.0, 0.0]
    air_slopes: list[float] = []
    initial_memory = 1.0
    for forcing, step in zip(intervals, baseline.steps, strict=True):
        leaf_step = step.root_leaf.leaf_water_hto_step
        W = leaf_step.initial_leaf_water_kg_m2_ground
        a = leaf_step.belot_exchange_water_equivalent_kg_m2_ground_s
        rate_seconds = a * forcing.interval_seconds / W
        g = math.exp(-rate_seconds)
        gain = -math.expm1(-rate_seconds)
        weights = step.root_leaf.boundary.root_water_fractions
        # At an exhausted active soil layer the one-sided feasibility boundary
        # makes the derivative non-regular. Refuse to present a smooth tangent.
        for i, f in enumerate(weights):
            if f > 0.0 and step.next_soil.water_kg_m2_ground[i] <= 0.0:
                raise KFK5194WaterActivityError(
                    "conditional soil sensitivity undefined at active-layer exhaustion"
                )
            soil_slope[i] = (
                g * soil_slope[i] + W * gain * forcing.root_water_delivery_kg_m2_ground_s * f / a
            )
        air_slopes = [g * x for x in air_slopes]
        air_slopes.append(
            W * forcing.isotope_fractionation_liquid_to_vapour
            / forcing.saturated_vapour_density_kg_m3 * gain
        )
        initial_memory *= g
    # For proportional extraction, dA_soil,final/dC_soil,initial is
    # exactly the remaining liquid-water mass. The HTO cross-budget gives
    # dBelot/dC_i = dI_leaf/dC_i + W_soil,final_i - W_soil,initial_i.
    final_soil = baseline.final_soil.water_kg_m2_ground
    belot_slopes = tuple(
        soil_slope[i] + final_soil[i] - initial_soil.water_kg_m2_ground[i]
        for i in range(3)
    )
    if not all(
        math.isfinite(x)
        for x in (*soil_slope, *air_slopes, initial_memory, *belot_slopes)
    ) or not all(x >= 0 for x in (*soil_slope, *air_slopes, initial_memory)):
        raise KFK5194WaterActivityError("nonfinite or negative research tangent")
    return KFK5194SeriesSensitivity(
        baseline=baseline,
        initial_leaf_activity_memory_fraction=initial_memory,
        initial_soil_concentration_to_final_leaf_activity_kg_m2_ground=tuple(soil_slope),
        interval_air_concentration_to_final_leaf_activity_m=tuple(air_slopes),
        initial_soil_concentration_to_final_soil_activity_kg_m2_ground=final_soil,
        initial_soil_concentration_to_cumulative_belot_activity_kg_m2_ground=belot_slopes,
    )
