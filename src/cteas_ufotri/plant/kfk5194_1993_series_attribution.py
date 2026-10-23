"""Conditional final-HTO source attribution for 1993 P3 R6 option-A research.

KfK 5194 (1993) printed p.15 provides root uptake depth fractions;
printed p.3 Eq.(1)-(3) and printed p.7 support the *composite* Belot
exchange used by this already opted-in R=E fixed-W research model.
Attribution is a mathematical decomposition, NOT a physical source
apportionment certified against original UFOTRI 4.0 or measurements.
In particular the air term below is retained atmospheric-origin leaf
inventory, NOT cumulative signed or gross air-leaf exchange.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile
from .kfk5194_1993_canopy_et import KFK5194P3Canopy
from .kfk5194_1993_root_soil_boundary import KFK5194RootMixingHypothesis
from .kfk5194_1993_series_sensitivity import (
    KFK5194SeriesSensitivity, diagnose_kfk5194_1993_series_sensitivity,
)
from .kfk5194_1993_soil_root_transfer import (
    KFK5194SoilEvolutionHypothesis, KFK5194SoilLayerInventoryState,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis, KFK5194WaterActivityError,
    KFK5194WaterActivityForcing,
)
from .tfwt_v3 import TFWTState


@dataclass(frozen=True, slots=True)
class KFK5194SeriesAttribution:
    """Contributions to final leaf HTO activity [Bq/m2 ground], not fluxes."""

    tangent: KFK5194SeriesSensitivity
    retained_initial_leaf_hto_bq_m2_ground: float
    retained_initial_soil_hto_by_layer_bq_m2_ground: tuple[float, float, float]
    retained_air_hto_by_interval_bq_m2_ground: tuple[float, ...]
    reconstructed_final_leaf_hto_bq_m2_ground: float
    actual_final_leaf_hto_bq_m2_ground: float
    attribution_residual_bq_m2_ground: float

    def provenance(self) -> dict[str, object]:
        return {
            "source_root_fractions": "KFK5194_1993_PRINTED_P15",
            "source_leaf_exchange": "KFK5194_1993_PRINTED_EQ1_TO3_P7_COMPOSITE",
            "attribution": "EXACT_CONDITIONAL_AFFINE_ENDPOINT_DECOMPOSITION",
            "air_contributions": "RETAINED_AIR_ORIGIN_NOT_SIGNED_NET_BELOT_FLUX",
            "initial_soil_contributions": "RETAINED_ROOT_WATER_ORIGIN_NOT_TOTAL_ROOT_WITHDRAWAL",
            "root_leaf_mixing": "SOURCE_LIMITED_INSTANT_MIXING_RESEARCH_OPT_IN",
            "soil_physics": "EXTRACTION_ONLY_NO_RECHARGE_RESEARCH",
            "independent_physics_approval": "NOT_ESTABLISHED",
            "original_fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "production_runtime_activated": False,
        }


def attribute_kfk5194_1993_series_final_hto(
    *,
    profile: Historical1993SourceProfile,
    initial_soil: KFK5194SoilLayerInventoryState,
    initial_leaf: TFWTState,
    canopy: KFK5194P3Canopy,
    intervals: tuple[KFK5194WaterActivityForcing, ...],
    evolution_hypothesis: KFK5194SoilEvolutionHypothesis,
    root_mixing_hypothesis: KFK5194RootMixingHypothesis,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194SeriesAttribution:
    """Reconstruct I_final = M*I_initial + sum_i S_i*C_soil,i
    + sum_j T_j*C_air,j from the exact conditional research tangent.

    Units: S_i [kg/m2 ground], C_soil,i [Bq/kg];
    T_j [m], C_air,j [Bq/m3]. This superposition is exact for the
    fixed-coefficient homogeneous, extraction-only *mathematical* model.
    It makes no inference about physical residence times or 1993 code.
    """
    diag = diagnose_kfk5194_1993_series_sensitivity(
        profile=profile, initial_soil=initial_soil, initial_leaf=initial_leaf,
        canopy=canopy, intervals=intervals,
        evolution_hypothesis=evolution_hypothesis,
        root_mixing_hypothesis=root_mixing_hypothesis,
        leaf_hypothesis=leaf_hypothesis,
    )
    soil_conc = initial_soil.concentrations_bq_kg_water()
    initial = diag.initial_leaf_activity_memory_fraction * initial_leaf.tfwt_inventory_bq_m2
    from_soil = tuple(
        slope * conc
        for slope, conc in zip(
            diag.initial_soil_concentration_to_final_leaf_activity_kg_m2_ground,
            soil_conc, strict=True,
        )
    )
    from_air = tuple(
        slope * forcing.air_hto_concentration_bq_m3
        for slope, forcing in zip(
            diag.interval_air_concentration_to_final_leaf_activity_m,
            intervals, strict=True,
        )
    )
    final = diag.baseline.final_leaf.tfwt_inventory_bq_m2
    reconstructed = math.fsum((initial, *from_soil, *from_air))
    residual = reconstructed - final
    terms = (initial, *from_soil, *from_air, reconstructed, residual, final)
    if not all(math.isfinite(x) for x in terms):
        raise KFK5194WaterActivityError("nonfinite conditional source attribution")
    # Reject unphysical negative contributions rather than masking sign errors.
    if any(x < 0. for x in (initial, *from_soil, *from_air)):
        raise KFK5194WaterActivityError("negative retained isotope-source contribution")
    scale = max(1., abs(final), abs(reconstructed))
    if abs(residual) > 2e-11 * scale:
        raise KFK5194WaterActivityError("conditional final-activity attribution mismatch")
    return KFK5194SeriesAttribution(
        tangent=diag, retained_initial_leaf_hto_bq_m2_ground=initial,
        retained_initial_soil_hto_by_layer_bq_m2_ground=from_soil,
        retained_air_hto_by_interval_bq_m2_ground=from_air,
        reconstructed_final_leaf_hto_bq_m2_ground=reconstructed,
        actual_final_leaf_hto_bq_m2_ground=final,
        attribution_residual_bq_m2_ground=residual,
    )
