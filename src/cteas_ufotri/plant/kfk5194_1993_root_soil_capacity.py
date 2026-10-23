"""Explicit soil inventory capacity preflight for KfK5194 (1993) root uptake.

The 1993 manual supplies the agricultural/grass three-layer uptake fractions.
This routine supplies an additional USER-PROVIDED *static inventory* feasibility
check. It is NOT a historical UFOTRI soil transport / depletion algorithm and
does not update any soil state, recharge, capillary flux or transpiration rate.

Units of water and HTO inventories: kg/m² ground and Bq/m² ground.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .kfk5194_1993_root_soil_boundary import (
    KFK5194RootPlantGroup, KFK5194RootSoilBoundary,
    KFK5194RootLayerWithdrawal,
)
from .kfk5194_1993_water_hto_joint import KFK5194WaterActivityError
from cteas_ufotri.versioned_inputs_1993 import PROFILE_ID


@dataclass(frozen=True, slots=True)
class KFK5194RootSoilCapacityAudit:
    """Non-mutating finite soil-water and HTO extraction feasibility result."""

    water_before_kg_m2_ground: tuple[float, float, float]
    hto_before_bq_m2_ground: tuple[float, float, float]
    water_after_kg_m2_ground: tuple[float, float, float]
    hto_after_bq_m2_ground: tuple[float, float, float]
    extracted_water_kg_m2_ground: tuple[float, float, float]
    extracted_hto_bq_m2_ground: tuple[float, float, float]
    total_water_balance_residual_kg_m2_ground: float
    total_hto_balance_residual_bq_m2_ground: float

    def provenance(self) -> dict[str, object]:
        return {
            "root_fractions": "KFK5194_1993_PRINTED_P15",
            "external_layer_inventories": "USER_SUPPLIED_NOT_SOURCE_DEFAULT",
            "stock_model": "STATIC_WELL_MIXED_SOIL_WATER_CAPACITY_PREFLIGHT",
            "soil_inventory_mutated": False,
            "soil_water_transport": "NOT_IMPLEMENTED",
            "root_transport_lag": "NOT_ESTABLISHED",
            "1993_fortran_soil_code_equivalence": "NOT_ESTABLISHED",
            "whole_1993_runtime_activated": False,
        }


def _layer_triplet(values: tuple[float, float, float], name: str) -> tuple[float, float, float]:
    if not isinstance(values, tuple) or len(values) != 3:
        raise KFK5194WaterActivityError(f"{name} requires three explicit layers")
    if any(
        type(x) not in (int, float) or not math.isfinite(float(x)) or x < 0
        for x in values
    ):
        raise KFK5194WaterActivityError(
            f"{name} must contain only finite nonnegative numbers"
        )
    return tuple(float(x) for x in values)


def audit_kfk5194_1993_root_soil_capacity(
    *,
    boundary: KFK5194RootSoilBoundary,
    withdrawals: KFK5194RootLayerWithdrawal,
    soil_water_available_kg_m2_ground: tuple[float, float, float],
    soil_hto_available_bq_m2_ground: tuple[float, float, float],
) -> KFK5194RootSoilCapacityAudit:
    """Preflight supply without advancing the original or modern soil model.

    Requires I_soil,i = W_soil,i * C_soil,i in each explicitly homogeneous
    liquid-water compartment; rejects insufficient water or HTO stock
    rather than permitting negative soil inventories. Independently checks
    the published 1993 fractions and the supplied withdrawal ledger.
    """
    if not isinstance(boundary, KFK5194RootSoilBoundary) or (
        boundary.profile_id != PROFILE_ID
    ) or not isinstance(withdrawals, KFK5194RootLayerWithdrawal) or (
        withdrawals.profile_id != PROFILE_ID
    ):
        raise KFK5194WaterActivityError("source-verified root boundary and ledger required")
    fractions = (
        (0.20, 0.40, 0.40)
        if boundary.plant_group is KFK5194RootPlantGroup.AGRICULTURAL_PLANT
        else (0.40, 0.60, 0.00)
        if boundary.plant_group is KFK5194RootPlantGroup.PASTURE_GRASS
        else None
    )
    if fractions is None or boundary.root_water_fractions != fractions or (
        boundary.soil_layer_intervals_cm != ((0, 5), (5, 15), (15, 30))
    ):
        raise KFK5194WaterActivityError("unverified root uptake fractions or depth intervals")
    concentrations = _layer_triplet(
        boundary.soil_water_hto_bq_kg, "soil water concentration [Bq/kg]"
    )
    source_concentration = math.fsum(f * c for f, c in zip(fractions, concentrations))
    if not math.isclose(
        source_concentration, boundary.effective_root_water_hto_bq_kg,
        rel_tol=1e-12, abs_tol=1e-12,
    ):
        raise KFK5194WaterActivityError("root concentration is inconsistent with layers")
    water = _layer_triplet(
        soil_water_available_kg_m2_ground, "soil water inventory [kg/m² ground]"
    )
    hto = _layer_triplet(
        soil_hto_available_bq_m2_ground, "soil HTO inventory [Bq/m² ground]"
    )
    taken_water = _layer_triplet(
        withdrawals.layer_water_kg_m2_ground, "withdrawn water"
    )
    taken_hto = _layer_triplet(
        withdrawals.layer_hto_bq_m2_ground, "withdrawn HTO"
    )
    total_water = withdrawals.total_water_kg_m2_ground
    total_hto = withdrawals.total_hto_bq_m2_ground
    if any(
        type(x) not in (float, int) or not math.isfinite(float(x)) or x < 0
        for x in (total_water, total_hto)
    ):
        raise KFK5194WaterActivityError("invalid total root withdrawals")
    for i in range(3):
        if not math.isclose(
            taken_water[i], total_water * fractions[i],
            rel_tol=1e-12, abs_tol=1e-13,
        ) or not math.isclose(
            taken_hto[i], taken_water[i] * concentrations[i],
            rel_tol=1e-12, abs_tol=1e-13,
        ):
            raise KFK5194WaterActivityError("forged or mismatched layer withdrawals")
        if water[i] < taken_water[i] or hto[i] < taken_hto[i]:
            raise KFK5194WaterActivityError(
                "insufficient soil-layer water or HTO to support root withdrawal"
            )
        if not math.isclose(
            hto[i], water[i] * concentrations[i],
            rel_tol=1e-10, abs_tol=1e-12,
        ):
            raise KFK5194WaterActivityError(
                "soil-layer HTO inventory inconsistent with liquid-water concentration"
            )
    if not math.isclose(
        math.fsum(taken_water), total_water, rel_tol=1e-12, abs_tol=1e-13,
    ) or not math.isclose(
        math.fsum(taken_hto), total_hto, rel_tol=1e-12, abs_tol=1e-13,
    ):
        raise KFK5194WaterActivityError("soil-to-root total withdrawals do not close")
    water_after = tuple(w - take for w, take in zip(water, taken_water))
    hto_after = tuple(a - take for a, take in zip(hto, taken_hto))
    water_balance = math.fsum(water) - math.fsum(water_after) - total_water
    hto_balance = math.fsum(hto) - math.fsum(hto_after) - total_hto
    if abs(water_balance) > 2e-12 * max(1., math.fsum(water)) or abs(
        hto_balance
    ) > 2e-12 * max(1., math.fsum(hto)):
        raise KFK5194WaterActivityError("static soil layer capacity budget does not close")
    return KFK5194RootSoilCapacityAudit(
        water_before_kg_m2_ground=water,
        hto_before_bq_m2_ground=hto,
        water_after_kg_m2_ground=water_after,
        hto_after_bq_m2_ground=hto_after,
        extracted_water_kg_m2_ground=taken_water,
        extracted_hto_bq_m2_ground=taken_hto,
        total_water_balance_residual_kg_m2_ground=water_balance,
        total_hto_balance_residual_bq_m2_ground=hto_balance,
    )
