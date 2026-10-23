"""1993 KfK5194 printed p.15 source-anchored root uptake HTO boundary.

Direct historical assumptions: agricultural plant soil-water uptake fractions
(0-5/5-15/15-30 cm) = (0.20,0.40,0.40); pasture grass = (0.40,0.60,0).
Inputs are soil-WATER HTO concentrations Bq/kg water. This computes an
effective root-water inflow boundary only. Root transport delay, instant
mixing into all leaf water and actual 1993 FORTRAN algorithm remain unknown.
No default solver or hydrological soil state is activated.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math

from cteas_ufotri.versioned_inputs_1993 import (
    Historical1993SourceProfile, PROFILE_ID,
)
from .kfk5194_1993_canopy_et import (
    KFK5194P3Canopy, KFK5194_SOURCE_URL,
)
from .kfk5194_1993_water_hto_joint import (
    KFK5194LeafWaterHypothesis, KFK5194WaterActivityError,
    KFK5194WaterActivityForcing, KFK5194WaterActivityStep,
    advance_kfk5194_water_hto_joint,
)
from .tfwt_v3 import TFWTState


class KFK5194RootPlantGroup(str, Enum):
    AGRICULTURAL_PLANT = "AGRICULTURAL_PLANT"
    PASTURE_GRASS = "PASTURE_GRASS"


class KFK5194RootMixingHypothesis(str, Enum):
    """Required on coupling: NOT directly established by printed p.15."""

    INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH = (
        "INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH"
    )


@dataclass(frozen=True, slots=True)
class KFK5194RootSoilBoundary:
    profile_id: str
    plant_group: KFK5194RootPlantGroup
    soil_layer_intervals_cm: tuple[tuple[int, int], ...]
    soil_water_hto_bq_kg: tuple[float, float, float]
    root_water_fractions: tuple[float, float, float]
    effective_root_water_hto_bq_kg: float

    def provenance(self) -> dict[str, object]:
        return {
            "source": "KfK 5194 (1993) printed p.15; PDF zero-based p.24",
            "source_basis": "SOIL_WATER_SPECIFIC_HTO_CONCENTRATIONS",
            "root_water_layer_fractions": "DIRECT_SOURCE_DOCUMENTED",
            "soil_root_flux": "NOT_SOLVED_EXTERNAL_INPUT",
            "root_to_leaf_mixing_rate": "NOT_ESTABLISHED",
            "original_fortran_algorithm": "NOT_ESTABLISHED",
            "whole_1993_solver_activated": False,
        }


@dataclass(frozen=True, slots=True)
class KFK5194RootLayerWithdrawal:
    """Layer-resolved withdrawals PER m² GROUND, without soil state mutation."""

    profile_id: str
    layer_water_kg_m2_ground: tuple[float, float, float]
    layer_hto_bq_m2_ground: tuple[float, float, float]
    total_water_kg_m2_ground: float
    total_hto_bq_m2_ground: float
    water_residual_kg_m2_ground: float
    hto_residual_bq_m2_ground: float

    def provenance(self) -> dict[str, object]:
        return {
            "root_layer_fractions": "KFK5194_1993_PRINTED_PAGE15",
            "control_volume": "SOIL_TO_ROOT_ONE_INTERVAL_WITHDRAWALS",
            "external_root_flow_prescribed": True,
            "soil_inventory_updated": False,
            "soil_water_availability_validated": False,
            "root_to_leaf_transit_time": "NOT_ESTABLISHED",
            "original_fortran_algorithm": "NOT_ESTABLISHED",
        }


@dataclass(frozen=True, slots=True)
class KFK5194RootCoupledStep:
    boundary: KFK5194RootSoilBoundary
    layer_withdrawal: KFK5194RootLayerWithdrawal
    leaf_water_hto_step: KFK5194WaterActivityStep
    mixing_hypothesis: KFK5194RootMixingHypothesis

    def provenance(self) -> dict[str, object]:
        return {
            **self.boundary.provenance(),
            "root_to_leaf_mixing_hypothesis": self.mixing_hypothesis.value,
            "soil_layer_withdrawal_budget": "CONSERVATIVE_NOT_SOIL_STATE_SOLVER",
            "assumption": "SOURCE_LIMITED_INSTANT_MIXING",
            "1993_fortran_numeric_parity": "NOT_ESTABLISHED",
        }


def kfk5194_1993_root_soil_boundary(
    *, profile: Historical1993SourceProfile,
    plant_group: KFK5194RootPlantGroup,
    soil_layer_water_hto_bq_kg: tuple[float, float, float],
) -> KFK5194RootSoilBoundary:
    """Source-based three-soil-layer mixture, no soil transport simulation.

    Each C_i is the HTO concentration in soil liquid water of a depth
    interval. Their water-flux-weighted sum gives entering root-water HTO.
    """
    if not isinstance(profile, Historical1993SourceProfile) or (
        profile.profile_id != PROFILE_ID
        or profile.source_url != KFK5194_SOURCE_URL
        or dict(profile.flag_defaults).get("IMODEL") != 1
    ):
        raise KFK5194WaterActivityError("explicit verified 1993 P1 profile required")
    if not isinstance(plant_group, KFK5194RootPlantGroup):
        raise KFK5194WaterActivityError(
            "agricultural vs pasture-grass uptake must be explicitly selected"
        )
    if not isinstance(soil_layer_water_hto_bq_kg, tuple) or len(
        soil_layer_water_hto_bq_kg
    ) != 3:
        raise KFK5194WaterActivityError(
            "three soil-water HTO concentrations (0-5,5-15,15-30 cm) required"
        )
    if any(
        type(c) not in (float, int)
        or not math.isfinite(float(c))
        or c < 0
        for c in soil_layer_water_hto_bq_kg
    ):
        raise KFK5194WaterActivityError(
            "each soil layer must have finite nonnegative Bq/kg water"
        )
    if plant_group is KFK5194RootPlantGroup.AGRICULTURAL_PLANT:
        fractions = (0.20, 0.40, 0.40)
    else:
        fractions = (0.40, 0.60, 0.00)
    concentrations = tuple(float(c) for c in soil_layer_water_hto_bq_kg)
    effective = math.fsum(f*c for f,c in zip(fractions, concentrations))
    if not math.isfinite(effective) or effective < 0:
        raise KFK5194WaterActivityError("weighted root HTO concentration overflow")
    return KFK5194RootSoilBoundary(
        profile_id=PROFILE_ID,
        plant_group=plant_group,
        soil_layer_intervals_cm=((0,5),(5,15),(15,30)),
        soil_water_hto_bq_kg=concentrations,
        root_water_fractions=fractions,
        effective_root_water_hto_bq_kg=effective,
    )


def kfk5194_1993_root_layer_withdrawals(
    *,
    boundary: KFK5194RootSoilBoundary,
    root_water_delivery_kg_m2_ground_s: float,
    interval_seconds: float,
) -> KFK5194RootLayerWithdrawal:
    """Audit water and HTO removed from each source layer, without soil mutation.

    Water_i = f_i * R * dt [kg/m² ground];
    HTO_i = Water_i * Csoil,i [Bq/m² ground].
    This does NOT prove that source-layer inventories can sustain withdrawal.
    """
    if not isinstance(boundary, KFK5194RootSoilBoundary) or (
        boundary.profile_id != PROFILE_ID
    ):
        raise KFK5194WaterActivityError("source-verified 1993 root boundary required")
    if type(root_water_delivery_kg_m2_ground_s) not in (float, int) or (
        not math.isfinite(float(root_water_delivery_kg_m2_ground_s))
    ) or root_water_delivery_kg_m2_ground_s < 0:
        raise KFK5194WaterActivityError("root water rate must be finite nonnegative SI")
    if type(interval_seconds) not in (float, int) or (
        not math.isfinite(float(interval_seconds))
    ) or interval_seconds <= 0:
        raise KFK5194WaterActivityError("interval must be finite positive seconds")
    expected_fractions = (
        (0.20, 0.40, 0.40)
        if boundary.plant_group is KFK5194RootPlantGroup.AGRICULTURAL_PLANT
        else (0.40, 0.60, 0.00)
        if boundary.plant_group is KFK5194RootPlantGroup.PASTURE_GRASS
        else None
    )
    if boundary.root_water_fractions != expected_fractions or (
        boundary.soil_layer_intervals_cm != ((0, 5), (5, 15), (15, 30))
    ) or len(boundary.soil_water_hto_bq_kg) != 3:
        raise KFK5194WaterActivityError("unverified root layer fractions or depths")
    if any(
        type(x) not in (float, int) or not math.isfinite(float(x)) or x < 0
        for x in boundary.soil_water_hto_bq_kg
    ):
        raise KFK5194WaterActivityError("invalid layer-specific soil-water activity")
    flow = float(root_water_delivery_kg_m2_ground_s)
    dt = float(interval_seconds)
    total_water = flow * dt
    layer_water = tuple(total_water * f for f in expected_fractions)
    layer_hto = tuple(
        w * float(c) for w, c in zip(layer_water, boundary.soil_water_hto_bq_kg)
    )
    root_total_hto = total_water * boundary.effective_root_water_hto_bq_kg
    if not all(
        math.isfinite(x) and x >= 0
        for x in (total_water, root_total_hto, *layer_water, *layer_hto)
    ):
        raise KFK5194WaterActivityError("nonfinite layer withdrawal budget")
    water_residual = math.fsum(layer_water) - total_water
    hto_residual = math.fsum(layer_hto) - root_total_hto
    water_tol = 2e-12 * max(1., total_water)
    hto_tol = 2e-12 * max(1., root_total_hto)
    if abs(water_residual) > water_tol or abs(hto_residual) > hto_tol:
        raise KFK5194WaterActivityError("root layer water/HTO budget does not close")
    return KFK5194RootLayerWithdrawal(
        profile_id=PROFILE_ID,
        layer_water_kg_m2_ground=layer_water,
        layer_hto_bq_m2_ground=layer_hto,
        total_water_kg_m2_ground=total_water,
        total_hto_bq_m2_ground=root_total_hto,
        water_residual_kg_m2_ground=water_residual,
        hto_residual_bq_m2_ground=hto_residual,
    )


def advance_kfk5194_1993_soil_weighted_root_boundary(
    *, profile: Historical1993SourceProfile,
    plant_group: KFK5194RootPlantGroup,
    soil_layer_water_hto_bq_kg: tuple[float, float, float],
    mixing_hypothesis: KFK5194RootMixingHypothesis,
    canopy: KFK5194P3Canopy,
    state: TFWTState,
    forcing: KFK5194WaterActivityForcing,
    leaf_hypothesis: KFK5194LeafWaterHypothesis,
) -> KFK5194RootCoupledStep:
    """Explicit opt-in research bridge; do not claim original code parity.

    Preserves the caller-supplied Monteith ET/root water rate and every
    atmospheric/plant forcing value, replacing ONLY C_root with published
    three-layer water-flux-weighted concentration.
    """
    if mixing_hypothesis is not (
        KFK5194RootMixingHypothesis.INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH
    ):
        raise KFK5194WaterActivityError(
            "root-to-leaf instantaneous mixing requires explicit research opt-in"
        )
    if not isinstance(forcing, KFK5194WaterActivityForcing):
        raise KFK5194WaterActivityError("typed 1993 joint forcing required")
    boundary = kfk5194_1993_root_soil_boundary(
        profile=profile,
        plant_group=plant_group,
        soil_layer_water_hto_bq_kg=soil_layer_water_hto_bq_kg,
    )
    joint = advance_kfk5194_water_hto_joint(
        profile=profile,
        canopy=canopy,
        state=state,
        forcing=replace(
            forcing,
            root_water_hto_concentration_bq_kg=(
                boundary.effective_root_water_hto_bq_kg
            ),
        ),
        hypothesis=leaf_hypothesis,
    )
    withdrawals = kfk5194_1993_root_layer_withdrawals(
        boundary=boundary,
        root_water_delivery_kg_m2_ground_s=forcing.root_water_delivery_kg_m2_ground_s,
        interval_seconds=forcing.interval_seconds,
    )
    water_scale = max(1., joint.root_water_input_kg_m2_ground)
    hto_scale = max(1., joint.root_hto_input_bq_m2_ground)
    if not (
        math.isclose(
            withdrawals.total_water_kg_m2_ground, joint.root_water_input_kg_m2_ground,
            rel_tol=0, abs_tol=2e-12 * water_scale,
        )
        and math.isclose(
            withdrawals.total_hto_bq_m2_ground, joint.root_hto_input_bq_m2_ground,
            rel_tol=0, abs_tol=2e-12 * hto_scale,
        )
    ):
        raise KFK5194WaterActivityError(
            "soil-layer root HTO withdrawal does not match leaf input"
        )
    return KFK5194RootCoupledStep(
        boundary=boundary,
        layer_withdrawal=withdrawals,
        leaf_water_hto_step=joint,
        mixing_hypothesis=mixing_hypothesis,
    )
