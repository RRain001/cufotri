"""Opt-in UFOTRI vegetable/grass long-term food-chain compatibility roles.

This module closes only the recoverable KfK 4605 vegetable/grass compartment
semantics needed by D3.  It does not replace the frozen V4 RC1 path, the
short-term OBT solver, the three-layer soil/hydrology solvers, or the pasture
root allocator.

For vegetables, KfK 4605 Eq. (65)-(66) defines a genuinely reversible
plant-HTO <-> plant-OBT pair.  The existing short-term ``OBTSolver`` reports its
``kr`` term as an external OBT loss, which is appropriate for the already
qualified short-term numerical boundary but is not a literal implementation of
Eq. (65), where plant OBT returns to plant HTO.  D3 therefore provides a
separate, explicitly opt-in two-compartment analytic solver for the long-term
ingestion context.

For grass, Eq. (67)-(81) is recorded as a role/reference map rather than a
second transport solver.  Leaf exchange is already owned by the opt-in UFOTRI
leaf path, three-layer soil transport by the Phase-C soil/hydrology path, and
40/60/0 pasture root allocation by D2.  The Eq. (67)-(81) equilibrium-derived
rate constants are retained as manual evidence only and are not activated as
production parameters.  Grass OBT Eq. (105-1)-(105-2) remains owned by D4,
because its reverse rate explicitly subtracts cow/milk loss pathways.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math

from cteas_ufotri.plant.obt_ufotri_v4.model import (
    LONG_TERM_MANUAL_ROUNDED_HTO_TO_OBT_D_1,
    ufotri_long_term_ingestion_obt_profile,
)
from cteas_ufotri.plant.obt_v3 import OBTState
from cteas_ufotri.plant.root_v4.pasture_profile import (
    UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState

SECONDS_PER_DAY = 86400.0
EQ66_EXACT_FROM_STATED_MASSES = "EQ66_EXACT_FROM_STATED_MASSES"
EQ66_MANUAL_ROUNDED_0_012_D_1 = "EQ66_MANUAL_ROUNDED_0_012_D_1"


class UFOTRIFoodchainInputError(ValueError):
    """Fail-closed error for the isolated UFOTRI food-chain compatibility path."""


def _require_finite(value: float, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UFOTRIFoodchainInputError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise UFOTRIFoodchainInputError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class UFOTRIVegetableExchangeParameters:
    """Explicit long-term Eq. (65)-(66) plant HTO/OBT rate selection."""

    forward_s_1: float
    reverse_s_1: float
    profile_id: str
    source_section: str = "KfK4605_3.3.3_Eq65_66"
    exact_original_parameterization_recovered: bool = False
    production_binding_authorized: bool = False

    def __post_init__(self) -> None:
        forward = _require_finite(self.forward_s_1, field="forward_s_1")
        reverse = _require_finite(self.reverse_s_1, field="reverse_s_1")
        if forward < 0.0 or reverse < 0.0:
            raise UFOTRIFoodchainInputError("vegetable exchange rates must be non-negative")
        if not isinstance(self.profile_id, str) or not self.profile_id.strip():
            raise UFOTRIFoodchainInputError("profile_id is required")
        if not isinstance(self.source_section, str) or not self.source_section.strip():
            raise UFOTRIFoodchainInputError("source_section is required")

    @property
    def forward_d_1(self) -> float:
        return self.forward_s_1 * SECONDS_PER_DAY

    @property
    def reverse_d_1(self) -> float:
        return self.reverse_s_1 * SECONDS_PER_DAY


@dataclass(frozen=True)
class UFOTRIVegetableExchangeBalance:
    """Integrated conservative balance for the reversible vegetable pair."""

    initial_tfwt_bq_m2: float
    initial_obt_bq_m2: float
    final_tfwt_bq_m2: float
    final_obt_bq_m2: float
    net_hto_to_obt_bq_m2: float
    total_residual_bq_m2: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _require_finite(getattr(self, field), field=field)


@dataclass(frozen=True)
class UFOTRIVegetableExchangeResult:
    tfwt_state: TFWTState
    obt_state: OBTState
    balance: UFOTRIVegetableExchangeBalance


@dataclass(frozen=True)
class UFOTRIGrassEq67To81RoleMap:
    """Manual reference map for Eq. (67)-(81), with ownership boundaries."""

    layer_depths_m: tuple[float, float, float] = (0.05, 0.10, 0.15)
    root_fractions: tuple[float, float, float] = UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS
    soil3_external_loss_d_1: float = 8.2e-3  # Eq. 67
    grass_to_atmosphere_d_1: float = 5.4  # Eq. 68 representative example
    atmosphere_to_grass_d_1: float = 0.2  # Eq. 69 representative example
    atmosphere_to_soil1_d_1: float = 0.68  # Eq. 70
    soil1_to_atmosphere_d_1: float = 0.27  # Eq. 72
    soil2_to_soil1_d_1: float = 1.2e-2  # Eq. 73
    soil3_to_soil2_d_1: float = 8.2e-3  # Eq. 74
    soil1_to_grass_d_1: float = 5.2e-2  # Eq. 76, manual rounded
    soil2_to_grass_d_1: float = 3.9e-2  # Eq. 77
    soil1_to_soil2_d_1: float = 0.13  # Eq. 79
    soil2_to_soil3_d_1: float = 2.45e-2  # Eq. 81
    leaf_exchange_owner: str = "plant.leaf_ufotri_v4"
    soil_hydrology_owner: str = "plant.soil_ufotri_v4+plant.soil_v4"
    root_uptake_owner: str = "plant.root_v4.pasture_profile"
    grass_obt_owner: str = "D4_EQ99_105_2"
    reference_rates_activated: bool = False
    duplicate_soil_solver_added: bool = False
    production_binding_authorized: bool = False

    def __post_init__(self) -> None:
        if self.layer_depths_m != (0.05, 0.10, 0.15):
            raise UFOTRIFoodchainInputError("UFOTRI grass soil layers must remain 0-5/5-15/15-30 cm")
        if self.root_fractions != (0.4, 0.6, 0.0):
            raise UFOTRIFoodchainInputError("UFOTRI grass root fractions must remain 40/60/0")
        rate_fields = (
            "soil3_external_loss_d_1",
            "grass_to_atmosphere_d_1",
            "atmosphere_to_grass_d_1",
            "atmosphere_to_soil1_d_1",
            "soil1_to_atmosphere_d_1",
            "soil2_to_soil1_d_1",
            "soil3_to_soil2_d_1",
            "soil1_to_grass_d_1",
            "soil2_to_grass_d_1",
            "soil1_to_soil2_d_1",
            "soil2_to_soil3_d_1",
        )
        for field in rate_fields:
            value = _require_finite(getattr(self, field), field=field)
            if value < 0.0:
                raise UFOTRIFoodchainInputError(f"{field} must be non-negative")
        if self.reference_rates_activated:
            raise UFOTRIFoodchainInputError("Eq.67-81 reference rates are evidence only in D3")
        if self.duplicate_soil_solver_added:
            raise UFOTRIFoodchainInputError("D3 must not add a duplicate soil solver")
        if self.production_binding_authorized:
            raise UFOTRIFoodchainInputError("D3 does not authorize production parameter binding")


class UFOTRIVegetableExchangeSolver:
    """Analytic conservative two-compartment Eq. (65)-(66) solver."""

    def __init__(self, parameters: UFOTRIVegetableExchangeParameters) -> None:
        if not isinstance(parameters, UFOTRIVegetableExchangeParameters):
            raise UFOTRIFoodchainInputError(
                "explicit UFOTRIVegetableExchangeParameters are required"
            )
        self.parameters = parameters

    @staticmethod
    def _validate_states(tfwt_state: TFWTState, obt_state: OBTState) -> None:
        if not isinstance(tfwt_state, TFWTState):
            raise UFOTRIFoodchainInputError("tfwt_state must be TFWTState")
        if not isinstance(obt_state, OBTState):
            raise UFOTRIFoodchainInputError("obt_state must be OBTState")
        if tfwt_state.plant_identifier != obt_state.plant_identifier:
            raise UFOTRIFoodchainInputError("TFWT and OBT plant identifiers must match")
        if tfwt_state.crop != obt_state.crop:
            raise UFOTRIFoodchainInputError("TFWT and OBT crop identifiers must match")
        if tfwt_state.growth_stage != obt_state.growth_stage:
            raise UFOTRIFoodchainInputError("TFWT and OBT growth stages must match")
        if tfwt_state.time != obt_state.timestamp:
            raise UFOTRIFoodchainInputError("TFWT and OBT timestamps must match")
        if tfwt_state.area_basis != obt_state.area_basis:
            raise UFOTRIFoodchainInputError("TFWT and OBT area bases must match")

    def advance(
        self,
        tfwt_state: TFWTState,
        obt_state: OBTState,
        interval_seconds: float,
    ) -> UFOTRIVegetableExchangeResult:
        """Advance the closed HTO/OBT pair with exact constant-rate dynamics."""

        self._validate_states(tfwt_state, obt_state)
        interval = _require_finite(interval_seconds, field="interval_seconds")
        if interval <= 0.0:
            raise UFOTRIFoodchainInputError("interval_seconds must be strictly positive")

        h0 = _require_finite(tfwt_state.inventory(), field="tfwt_inventory_bq_m2")
        o0 = _require_finite(obt_state.inventory(), field="obt_inventory_bq_m2")
        if h0 < 0.0 or o0 < 0.0:
            raise UFOTRIFoodchainInputError("TFWT and OBT inventories must be non-negative")

        kf = self.parameters.forward_s_1
        kr = self.parameters.reverse_s_1
        total = h0 + o0
        rate_sum = kf + kr
        if total == 0.0 or rate_sum == 0.0:
            o1 = o0
        else:
            o_eq = (kf / rate_sum) * total
            o1 = o_eq + (o0 - o_eq) * math.exp(-rate_sum * interval)
        h1 = total - o1

        tolerance = 1.0e-12 * max(1.0, total)
        if h1 < -tolerance or o1 < -tolerance:
            raise UFOTRIFoodchainInputError("vegetable exchange produced a negative inventory")
        h1 = max(h1, 0.0)
        o1 = max(o1, 0.0)
        next_time = tfwt_state.time + timedelta(seconds=interval)
        next_tfwt = tfwt_state.with_inventory(
            tfwt_inventory_bq_m2=h1,
            time=next_time,
        )
        next_obt = obt_state.with_inventory(
            obt_inventory_bq_m2=o1,
            timestamp=next_time,
        )
        residual = total - (h1 + o1)
        if abs(residual) > tolerance:
            raise UFOTRIFoodchainInputError(
                f"vegetable exchange conservation failed: {residual}"
            )
        return UFOTRIVegetableExchangeResult(
            tfwt_state=next_tfwt,
            obt_state=next_obt,
            balance=UFOTRIVegetableExchangeBalance(
                initial_tfwt_bq_m2=h0,
                initial_obt_bq_m2=o0,
                final_tfwt_bq_m2=h1,
                final_obt_bq_m2=o1,
                net_hto_to_obt_bq_m2=o1 - o0,
                total_residual_bq_m2=residual,
            ),
        )


def ufotri_vegetable_eq65_66_parameters(
    *,
    forward_rate_basis: str,
) -> UFOTRIVegetableExchangeParameters:
    """Build explicit Eq. (65)-(66) rates; no hidden forward-rate default."""

    profile = ufotri_long_term_ingestion_obt_profile()
    if forward_rate_basis == EQ66_EXACT_FROM_STATED_MASSES:
        forward_d_1 = profile.hto_to_obt_d_1_exact_from_stated_masses
    elif forward_rate_basis == EQ66_MANUAL_ROUNDED_0_012_D_1:
        forward_d_1 = LONG_TERM_MANUAL_ROUNDED_HTO_TO_OBT_D_1
    else:
        raise UFOTRIFoodchainInputError(
            "forward_rate_basis must explicitly select exact Eq.66 reconstruction or manual-rounded 0.012 d^-1"
        )
    return UFOTRIVegetableExchangeParameters(
        forward_s_1=forward_d_1 / SECONDS_PER_DAY,
        reverse_s_1=profile.obt_to_hto_d_1 / SECONDS_PER_DAY,
        profile_id=forward_rate_basis,
    )


def ufotri_vegetable_equilibrium_specific_activity_ratio(
    parameters: UFOTRIVegetableExchangeParameters,
) -> float:
    """Return organic/inorganic specific-activity ratio implied at equilibrium."""

    if not isinstance(parameters, UFOTRIVegetableExchangeParameters):
        raise UFOTRIFoodchainInputError("explicit vegetable exchange parameters are required")
    if parameters.reverse_s_1 == 0.0:
        raise UFOTRIFoodchainInputError("reverse_s_1 must be positive for an equilibrium ratio")
    profile = ufotri_long_term_ingestion_obt_profile()
    inventory_ratio = parameters.forward_s_1 / parameters.reverse_s_1
    inorganic_hydrogen = profile.inorganic_plant_mass_kg_m2 / profile.water_hydrogen_divisor
    organic_hydrogen = profile.organic_plant_mass_kg_m2 / profile.organic_hydrogen_divisor
    return inventory_ratio * inorganic_hydrogen / organic_hydrogen


def ufotri_grass_eq67_81_role_map() -> UFOTRIGrassEq67To81RoleMap:
    """Return the D3 ownership/reference map without activating old rate constants."""

    return UFOTRIGrassEq67To81RoleMap()


__all__ = [
    "EQ66_EXACT_FROM_STATED_MASSES",
    "EQ66_MANUAL_ROUNDED_0_012_D_1",
    "SECONDS_PER_DAY",
    "UFOTRIFoodchainInputError",
    "UFOTRIGrassEq67To81RoleMap",
    "UFOTRIVegetableExchangeBalance",
    "UFOTRIVegetableExchangeParameters",
    "UFOTRIVegetableExchangeResult",
    "UFOTRIVegetableExchangeSolver",
    "ufotri_grass_eq67_81_role_map",
    "ufotri_vegetable_eq65_66_parameters",
    "ufotri_vegetable_equilibrium_specific_activity_ratio",
]
