"""Opt-in LAI-conservative projection of KfK5194 (1993) leaf HTO onto ground.

Assumptions: homogeneous leaf water, constant known LAI, leaf-water-only pool.
This does NOT solve LAI growth, root replenishment, or Monteith water loss.
Original FORTRAN ground/leaf projection is not established.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile, PROFILE_ID
from .kfk5194_1993_leaf_eq1_3 import (
    KFK5194LeafInterval, KFK5194Eq1To3Step,
    advance_kfk5194_1993_leaf_eq1_to3,
)
from .tfwt_v3 import TFWTState


class KFK5194ProjectionError(ValueError):
    """Invalid area basis or nonconservative source projection."""


class KFK5194GroundWaterPool(str, Enum):
    LEAF_WATER_ONLY = "LEAF_WATER_ONLY"


@dataclass(frozen=True)
class KFK5194GroundStep:
    """Conservative signed HTO inventory ledger on m² ground."""

    profile_id: str
    lai: float
    leaf_water_kg_m2_leaf: float
    ground_water_kg_m2_ground: float
    initial_ground_activity_bq_m2: float
    ground_transfer_bq_m2: float
    ground_residual_bq_m2: float
    leaf_result: KFK5194Eq1To3Step
    state: TFWTState

    def provenance(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "source": "KFK5194_1993_LEAF_EQ1_TO3",
            "geometric_projection": "CONSTANT_LAI_HOMOGENEOUS_CANOPY_ASSUMPTION",
            "area_basis": "LEAF_WATER_ONLY_PER_GROUND_AREA",
            "original_fortran_projection": "NOT_ESTABLISHED",
            "dynamic_lai": "NOT_IMPLEMENTED",
            "root_or_monteith_water_mass_coupling": "NOT_IMPLEMENTED",
            "whole_1993_runtime_activated": False,
        }


def _lai(value: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)) or value <= 0:
        raise KFK5194ProjectionError("fixed LAI must be finite and strictly positive")
    return float(value)


def advance_kfk5194_ground_leaf_budget(
    *, profile: Historical1993SourceProfile,
    state: TFWTState,
    exposure: KFK5194LeafInterval,
    fixed_lai: float,
    water_pool: KFK5194GroundWaterPool,
) -> KFK5194GroundStep:
    """Transform water and HTO inventories by LAI without scaling concentration."""
    if not isinstance(state, TFWTState) or state.area_basis != "ground_area":
        raise KFK5194ProjectionError("ground-area TFWT state required")
    if water_pool is not KFK5194GroundWaterPool.LEAF_WATER_ONLY:
        raise KFK5194ProjectionError("explicit leaf-water-only pool selection required")
    if not isinstance(exposure, KFK5194LeafInterval):
        raise KFK5194ProjectionError("typed KfK5194 leaf interval required")
    lai = _lai(fixed_lai)
    canopy_lai = _lai(exposure.canopy.leaf_area_index)
    if not math.isclose(lai, canopy_lai, rel_tol=1e-12, abs_tol=0):
        raise KFK5194ProjectionError("LAI mismatch/change requires explicit growth ledger")
    water_leaf = state.water_content_kg_m2 / lai
    activity_leaf = state.tfwt_inventory_bq_m2 / lai
    if not all(math.isfinite(x) for x in (water_leaf, activity_leaf)) or water_leaf <= 0:
        raise KFK5194ProjectionError("leaf-area mass/activity overflow or underflow")
    leaf_state = TFWTState.from_inventory(
        plant_identifier=state.plant_identifier,
        crop=state.crop,
        growth_stage=state.growth_stage,
        tfwt_inventory_bq_m2=activity_leaf,
        water_content_kg_m2=water_leaf,
        time=state.time,
        provenance=state.provenance,
        area_basis="leaf_area",
    )
    leaf = advance_kfk5194_1993_leaf_eq1_to3(
        profile=profile, state=leaf_state, exposure=exposure,
    )
    ground_transfer = lai * leaf.signed_leaf_transfer_bq_m2_leaf
    next_inventory = lai * leaf.state.tfwt_inventory_bq_m2
    if not all(math.isfinite(x) for x in (ground_transfer, next_inventory)):
        raise KFK5194ProjectionError("ground HTO budget overflow")
    next_state = state.with_inventory(
        tfwt_inventory_bq_m2=next_inventory, time=leaf.state.time,
    )
    residual = next_inventory - state.tfwt_inventory_bq_m2 - ground_transfer
    scale = max(1, abs(next_inventory), abs(ground_transfer), abs(state.tfwt_inventory_bq_m2))
    if not math.isfinite(residual) or abs(residual) > 2e-11 * scale:
        raise KFK5194ProjectionError("ground-area activity closure failure")
    if not math.isclose(
        next_state.tfwt_concentration_bq_kg_water,
        leaf.state.tfwt_concentration_bq_kg_water,
        rel_tol=2e-12, abs_tol=2e-12 * scale,
    ):
        raise KFK5194ProjectionError("leaf-to-ground concentration drift")
    return KFK5194GroundStep(
        profile_id=PROFILE_ID, lai=lai,
        leaf_water_kg_m2_leaf=water_leaf,
        ground_water_kg_m2_ground=state.water_content_kg_m2,
        initial_ground_activity_bq_m2=state.tfwt_inventory_bq_m2,
        ground_transfer_bq_m2=ground_transfer,
        ground_residual_bq_m2=residual,
        leaf_result=leaf, state=next_state,
    )


def advance_kfk5194_ground_leaf_intervals(
    *, profile: Historical1993SourceProfile,
    initial_state: TFWTState,
    exposures: Sequence[KFK5194LeafInterval],
    fixed_lai: float,
    water_pool: KFK5194GroundWaterPool,
) -> tuple[KFK5194GroundStep, ...]:
    """Propagate interval-constant forcing, refusing a change in LAI."""
    if not isinstance(exposures, (tuple, list)) or not exposures:
        raise KFK5194ProjectionError("at least one interval is required")
    results = []
    current = initial_state
    for exposure in exposures:
        result = advance_kfk5194_ground_leaf_budget(
            profile=profile, state=current, exposure=exposure,
            fixed_lai=fixed_lai, water_pool=water_pool,
        )
        results.append(result)
        current = result.state
    return tuple(results)
