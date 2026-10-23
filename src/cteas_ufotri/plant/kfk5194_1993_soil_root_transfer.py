"""Opt-in, extraction-only three-layer soil/root/leaf conservative time step.

Scientific scope: KfK5194 (1993) printed p.15 source uptake fractions, and
P3 R6 Belot composite HTO + fixed-water R=E experimental leaf state.
The soil evolution below is an explicitly chosen finite-volume *arithmetic*
extraction-only model: NO infiltration, rain, vertical flow, evaporation,
diffusion, decay, sorption, plant hydraulics or original 1993 FORTRAN parity.
No default 1990/1993 runtime path imports this module.

A root-to-leaf instantaneous mixing hypothesis remains mandatory and
unvalidated, even though water and HTO inventories close across compartments.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import (
    Historical1993SourceProfile, PROFILE_ID,
)
from .kfk5194_1993_canopy_et import KFK5194P3Canopy
from .kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup, KFK5194RootMixingHypothesis,
    KFK5194RootCoupledStep,
    advance_kfk5194_1993_soil_weighted_root_boundary,
)
from .kfk5194_1993_root_soil_capacity import (
    KFK5194RootSoilCapacityAudit,
    audit_kfk5194_1993_root_soil_capacity,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194WaterActivityError, KFK5194LeafWaterHypothesis,
    KFK5194WaterActivityForcing,
)
from .tfwt_v3 import TFWTState


DEPTHS_CM = ((0, 5), (5, 15), (15, 30))


class KFK5194SoilEvolutionHypothesis(str, Enum):
    """Never silently declare water transport or 1993 FORTRAN soil physics."""

    EXTRACTION_ONLY_NO_RECHARGE_RESEARCH = "EXTRACTION_ONLY_NO_RECHARGE_RESEARCH"


@dataclass(frozen=True, slots=True)
class KFK5194SoilLayerInventoryState:
    """Externally prescribed, well-mixed liquid-water source buckets."""

    time: datetime
    plant_group: KFK5194RootPlantGroup
    water_kg_m2_ground: tuple[float, float, float]
    hto_bq_m2_ground: tuple[float, float, float]
    source_profile_id: str = PROFILE_ID
    layer_depths_cm: tuple[tuple[int, int], ...] = DEPTHS_CM

    def __post_init__(self) -> None:
        if not isinstance(self.time, datetime) or (
            self.time.tzinfo is None or self.time.utcoffset() != timedelta(0)
        ):
            raise KFK5194WaterActivityError("soil state time must be timezone-aware UTC")
        if self.source_profile_id != PROFILE_ID or (
            self.layer_depths_cm != DEPTHS_CM
        ) or not isinstance(self.plant_group, KFK5194RootPlantGroup):
            raise KFK5194WaterActivityError(
                "1993 source profile, plant group and soil depth basis required"
            )
        for name, values in (
            ("soil-water inventory", self.water_kg_m2_ground),
            ("soil-HTO inventory", self.hto_bq_m2_ground),
        ):
            if not isinstance(values, tuple) or len(values) != 3 or any(
                type(v) not in (int, float)
                or not math.isfinite(float(v)) or v < 0.0
                for v in values
            ):
                raise KFK5194WaterActivityError(
                    f"{name} requires three finite nonnegative ground-area stocks"
                )
        if any(
            w == 0 and a != 0
            for w, a in zip(self.water_kg_m2_ground, self.hto_bq_m2_ground)
        ):
            raise KFK5194WaterActivityError(
                "zero soil liquid water cannot contain positive dissolved HTO"
            )

    def concentrations_bq_kg_water(self) -> tuple[float, float, float]:
        """Derive exact state concentrations; 0/0 dry bucket maps to zero."""
        concentrations = tuple(
            a/w if w > 0 else 0.0
            for w, a in zip(self.water_kg_m2_ground, self.hto_bq_m2_ground)
        )
        if any(not math.isfinite(v) or v < 0 for v in concentrations):
            raise KFK5194WaterActivityError("nonfinite soil pore-water concentration")
        return concentrations


@dataclass(frozen=True, slots=True)
class KFK5194SoilRootLeafTransfer:
    """All inventories per m² ground; full cross-control-volume residuals."""

    original_soil: KFK5194SoilLayerInventoryState
    next_soil: KFK5194SoilLayerInventoryState
    root_leaf: KFK5194RootCoupledStep
    capacity: KFK5194RootSoilCapacityAudit
    cross_water_residual_kg_m2_ground: float
    cross_hto_residual_bq_m2_ground: float

    @property
    def next_leaf(self) -> TFWTState:
        return self.root_leaf.leaf_water_hto_step.state

    def provenance(self) -> dict[str, object]:
        return {
            "soil_uptake_depth_fractions": "KFK5194_1993_PRINTED_P15",
            "leaf_HTO": "KFK5194_1993_PRINTED_EQ1_TO3_WITH_SOURCE_LIMITED_ROOT_MIXING",
            "soil_evolution": "EXTRACTION_ONLY_NO_RECHARGE_RESEARCH",
            "soil_state_updated": "IMMUTABLE_EXPLICIT_ACCOUNTING_ONLY",
            "soil_infiltration_vertical_flux_ET": "NOT_IMPLEMENTED",
            "root_transit_delay": "NOT_ESTABLISHED",
            "original_fortran_soil_root_parity": "NOT_ESTABLISHED",
            "whole_1993_solver_activated": False,
        }


def advance_kfk5194_1993_extraction_only_soil_root_leaf(
    *, profile: Historical1993SourceProfile,
    soil: KFK5194SoilLayerInventoryState,
    leaf: TFWTState,
    canopy: KFK5194P3Canopy,
    forcing: KFK5194WaterActivityForcing,
    evolution_hypothesis: KFK5194SoilEvolutionHypothesis,
    root_mixing_hypothesis: KFK5194RootMixingHypothesis,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194SoilRootLeafTransfer:
    """Advance only root extraction and a stationary R=E leaf exchange step.

    Boundary fluxes are evaluated from PRE-step soil concentrations.
    The root boundary and source fractions are validated independently by
    their own KfK5194 modules. Soil availability must be sufficient for the
    full timestep. The next soil state is returned without mutating input.
    Cross-water budget includes plant transpiration to atmosphere; the HTO
    budget includes the complete signed Belot composite exchange ONCE.
    """
    if evolution_hypothesis is not (
        KFK5194SoilEvolutionHypothesis.EXTRACTION_ONLY_NO_RECHARGE_RESEARCH
    ):
        raise KFK5194WaterActivityError(
            "explicit extraction-only soil evolution research hypothesis required"
        )
    if not isinstance(soil, KFK5194SoilLayerInventoryState) or not (
        isinstance(leaf, TFWTState)
    ) or not isinstance(forcing, KFK5194WaterActivityForcing):
        raise KFK5194WaterActivityError(
            "typed soil, leaf and interval forcing required"
        )
    if soil.time != leaf.time:
        raise KFK5194WaterActivityError(
            "soil/leaf times must match exactly; root lag is not modelled"
        )
    concentrations = soil.concentrations_bq_kg_water()
    # The root adapter enforces the source, mixing and R=E leaf contract.
    coupled = advance_kfk5194_1993_soil_weighted_root_boundary(
        profile=profile,
        plant_group=soil.plant_group,
        soil_layer_water_hto_bq_kg=concentrations,
        mixing_hypothesis=root_mixing_hypothesis,
        canopy=canopy,
        state=leaf,
        forcing=forcing,
        leaf_hypothesis=leaf_hypothesis,
    )
    cap = audit_kfk5194_1993_root_soil_capacity(
        boundary=coupled.boundary, withdrawals=coupled.layer_withdrawal,
        soil_water_available_kg_m2_ground=soil.water_kg_m2_ground,
        soil_hto_available_bq_m2_ground=soil.hto_bq_m2_ground,
    )
    next_soil = replace(
        soil,
        time=coupled.leaf_water_hto_step.state.time,
        water_kg_m2_ground=cap.water_after_kg_m2_ground,
        hto_bq_m2_ground=cap.hto_after_bq_m2_ground,
    )
    leaf_budget = coupled.leaf_water_hto_step
    water_delta = (
        math.fsum(next_soil.water_kg_m2_ground)
        - math.fsum(soil.water_kg_m2_ground)
        + leaf_budget.final_leaf_water_kg_m2_ground
        - leaf_budget.initial_leaf_water_kg_m2_ground
        + leaf_budget.monteith_plant_water_loss_kg_m2_ground
    )
    hto_delta = (
        math.fsum(next_soil.hto_bq_m2_ground)
        - math.fsum(soil.hto_bq_m2_ground)
        + leaf_budget.final_hto_activity_bq_m2_ground
        - leaf_budget.initial_hto_activity_bq_m2_ground
        - leaf_budget.belot_composite_hto_exchange_bq_m2_ground
    )
    w_scale = max(
        1.0, math.fsum(soil.water_kg_m2_ground),
        leaf_budget.initial_leaf_water_kg_m2_ground,
        leaf_budget.root_water_input_kg_m2_ground,
    )
    a_scale = max(
        1.0, math.fsum(soil.hto_bq_m2_ground),
        leaf_budget.initial_hto_activity_bq_m2_ground,
        abs(leaf_budget.belot_composite_hto_exchange_bq_m2_ground),
    )
    if not all(math.isfinite(v) for v in (water_delta, hto_delta)) or (
        abs(water_delta) > 2e-11 * w_scale
        or abs(hto_delta) > 2e-11 * a_scale
    ):
        raise KFK5194WaterActivityError(
            "soil + leaf + transpired water / Belot HTO control-volume mismatch"
        )
    return KFK5194SoilRootLeafTransfer(
        original_soil=soil, next_soil=next_soil,
        root_leaf=coupled, capacity=cap,
        cross_water_residual_kg_m2_ground=water_delta,
        cross_hto_residual_bq_m2_ground=hto_delta,
    )
