"""Time-resolved, conditional isotope-source budgets for 1993 P3 R6.

Only for the explicitly opted-in fixed-W, R=E, extraction-only,
instantaneous-homogeneous-mixing research hypothesis. KfK 5194 (1993)
printed p.3 Eq.(1)-(3), p.7 composite Belot exchange and p.15 root
uptake fractions. This is a linear model attribution, not a recovered
1993 FORTRAN tracer-origin algorithm or empirical source attribution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_canopy_et import KFK5194P3Canopy
from .kfk5194_1993_root_soil_boundary import KFK5194RootMixingHypothesis
from .kfk5194_1993_soil_root_transfer import (
    KFK5194SoilEvolutionHypothesis, KFK5194SoilLayerInventoryState,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis, KFK5194WaterActivityError,
    KFK5194WaterActivityForcing,
)
from .kfk5194_1993_series_attribution import (
    KFK5194SeriesAttribution, attribute_kfk5194_1993_series_final_hto,
)
from .tfwt_v3 import TFWTState


@dataclass(frozen=True, slots=True)
class KFK5194IntervalSourceBudget:
    """All activities are Bq/m² ground; signed Belot terms can be negative."""

    end_time: datetime
    retained_initial_leaf_hto: float
    retained_initial_soil_hto_by_layer: tuple[float, float, float]
    retained_air_hto_by_interval: tuple[float, ...]
    reconstructed_leaf_hto: float
    observed_leaf_hto: float
    leaf_residual: float
    signed_belot_from_initial_leaf: float
    signed_belot_from_initial_soil_by_layer: tuple[float, float, float]
    signed_belot_from_air_by_interval: tuple[float, ...]
    reconstructed_signed_belot: float
    observed_signed_belot: float
    belot_residual: float


@dataclass(frozen=True, slots=True)
class KFK5194SeriesSourceBudget:
    """Chronological source-retention and signed exchange decompositions."""

    endpoint: KFK5194SeriesAttribution
    intervals: tuple[KFK5194IntervalSourceBudget, ...]

    def provenance(self) -> dict[str, object]:
        return {
            "authority": "KFK5194_1993_PRINTED_P3_P7_P15",
            "source_tracking": "CONDITIONAL_LINEAR_RESEARCH_MODEL_ONLY",
            "belot_budget": "SIGNED_COMPOSITE_ONCE_NOT_INDEPENDENT_TRANSPIRATION_SINK",
            "root_leaf_mixing": "SOURCE_LIMITED_INSTANT_RESEARCH_OPT_IN",
            "soil_physics": "EXTRACTION_ONLY_NO_RECHARGE_RESEARCH",
            "original_fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "independent_scientific_validation": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def audit_kfk5194_1993_series_source_budget(
    *,
    profile: Historical1993SourceProfile,
    initial_soil: KFK5194SoilLayerInventoryState,
    initial_leaf: TFWTState,
    canopy: KFK5194P3Canopy,
    intervals: tuple[KFK5194WaterActivityForcing, ...],
    evolution_hypothesis: KFK5194SoilEvolutionHypothesis,
    root_mixing_hypothesis: KFK5194RootMixingHypothesis,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194SeriesSourceBudget:
    """Account for each source after every interval; fail on budget drift.

    For j, g=exp(-a_j*dt_j/W), q=1-g, and initial soil C_i fixed
    under proportional extraction, retained inventories obey:
       L_j = g L_(j-1)
       S_ij = g S_i,j-1 + W*(R_j*f_i/a_j)*q*C_i
       A_kj = g A_k,j-1 (k<j)
       A_jj = W*(alpha_j/rho_j)*q*C_air,j
    The source-specific signed Belot contributions are changes in these
    retained inventories, less the *same interval* root HTO withdrawal
    for each soil source. Their sum is the composite Belot flux, with
    no extra -E*C sink. Not a physical isotope-origin certification.
    """
    endpoint = attribute_kfk5194_1993_series_final_hto(
        profile=profile, initial_soil=initial_soil, initial_leaf=initial_leaf,
        canopy=canopy, intervals=intervals,
        evolution_hypothesis=evolution_hypothesis,
        root_mixing_hypothesis=root_mixing_hypothesis,
        leaf_hypothesis=leaf_hypothesis,
    )
    soil_conc = initial_soil.concentrations_bq_kg_water()
    kept_leaf = initial_leaf.tfwt_inventory_bq_m2
    kept_soil = (0.0, 0.0, 0.0)
    kept_air: tuple[float, ...] = ()
    results: list[KFK5194IntervalSourceBudget] = []

    for forcing, step in zip(intervals, endpoint.tangent.baseline.steps, strict=True):
        leaf_step = step.root_leaf.leaf_water_hto_step
        w = leaf_step.initial_leaf_water_kg_m2_ground
        a = leaf_step.belot_exchange_water_equivalent_kg_m2_ground_s
        g = math.exp(-a * forcing.interval_seconds / w)
        q = -math.expm1(-a * forcing.interval_seconds / w)
        f = step.root_leaf.boundary.root_water_fractions
        previous_leaf, previous_soil, previous_air = kept_leaf, kept_soil, kept_air
        kept_leaf = g * previous_leaf
        kept_soil = tuple(
            g * old + w * (forcing.root_water_delivery_kg_m2_ground_s * fraction / a)
            * q * soil_conc[i]
            for i, (old, fraction) in enumerate(zip(previous_soil, f, strict=True))
        )
        kept_air = (
            *(g * x for x in previous_air),
            w * forcing.isotope_fractionation_liquid_to_vapour
            / forcing.saturated_vapour_density_kg_m3 * q
            * forcing.air_hto_concentration_bq_m3,
        )
        reconstructed = math.fsum((kept_leaf, *kept_soil, *kept_air))
        observed = step.next_leaf.tfwt_inventory_bq_m2
        leaf_residual = reconstructed - observed
        root_withdrawn = tuple(
            old - new for old, new in zip(
                step.original_soil.hto_bq_m2_ground,
                step.next_soil.hto_bq_m2_ground, strict=True,
            )
        )
        belot_leaf = kept_leaf - previous_leaf
        belot_soil = tuple(
            new - old - root_withdrawn[i]
            for i, (new, old) in enumerate(zip(kept_soil, previous_soil, strict=True))
        )
        belot_air = tuple(
            new - (previous_air[i] if i < len(previous_air) else 0.0)
            for i, new in enumerate(kept_air)
        )
        reconstructed_belot = math.fsum((belot_leaf, *belot_soil, *belot_air))
        observed_belot = leaf_step.belot_composite_hto_exchange_bq_m2_ground
        belot_residual = reconstructed_belot - observed_belot
        terms = (
            kept_leaf, *kept_soil, *kept_air, reconstructed, observed, leaf_residual,
            belot_leaf, *belot_soil, *belot_air, reconstructed_belot,
            observed_belot, belot_residual,
        )
        scale = max(
            1.0, abs(reconstructed), abs(observed),
            abs(reconstructed_belot), abs(observed_belot),
            *(abs(x) for x in root_withdrawn),
        )
        if not all(math.isfinite(x) for x in terms) or (
            abs(leaf_residual) > 2e-11 * scale
            or abs(belot_residual) > 2e-11 * scale
        ):
            raise KFK5194WaterActivityError(
                "conditional interval source attribution or signed Belot mismatch"
            )
        results.append(KFK5194IntervalSourceBudget(
            end_time=step.next_leaf.time,
            retained_initial_leaf_hto=kept_leaf,
            retained_initial_soil_hto_by_layer=kept_soil,
            retained_air_hto_by_interval=kept_air,
            reconstructed_leaf_hto=reconstructed, observed_leaf_hto=observed,
            leaf_residual=leaf_residual,
            signed_belot_from_initial_leaf=belot_leaf,
            signed_belot_from_initial_soil_by_layer=belot_soil,
            signed_belot_from_air_by_interval=belot_air,
            reconstructed_signed_belot=reconstructed_belot,
            observed_signed_belot=observed_belot,
            belot_residual=belot_residual,
        ))

    last = results[-1]
    if not all(math.isclose(x, y, rel_tol=2e-11, abs_tol=2e-11)
               for x, y in [
                   (last.retained_initial_leaf_hto, endpoint.retained_initial_leaf_hto_bq_m2_ground),
                   *zip(last.retained_initial_soil_hto_by_layer,
                        endpoint.retained_initial_soil_hto_by_layer_bq_m2_ground, strict=True),
                   *zip(last.retained_air_hto_by_interval,
                        endpoint.retained_air_hto_by_interval_bq_m2_ground, strict=True),
               ]):
        raise KFK5194WaterActivityError("per-interval and endpoint attribution drift")
    return KFK5194SeriesSourceBudget(endpoint=endpoint, intervals=tuple(results))
