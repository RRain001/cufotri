"""Opt-in UFOTRI OBT semantic reconstruction.

This module records the narrow state/parameter roles recoverable from KfK 4605
without changing the frozen ``obt_v3`` solver.

The manual explicitly states that exchangeable organically bound tritium is in
equilibrium with free plant HTO and need not be distinguished from free HTO in
UFOTRI. Therefore this compatibility layer does *not* create an exchangeable
OBT inventory. ``TFWTState`` remains the model representation for free HTO and
the exchangeable-OBT role, while ``OBTState`` is interpreted narrowly as the
non-exchangeable organic-tritium compartment.

KfK 4605 provides two linked numerical descriptions of plant HTO/OBT transfer:

* Section 2.2.6, for the hourly atmospheric/dispersion calculation, states a
  daily-average non-exchangeable OBT incorporation rate of 0.06 % h^-1 of
  plant HTO and a mean organic-tritium loss rate of 0.3 % h^-1. It also states
  daytime uptake is increased and nighttime uptake reduced, but the recovered
  text does not provide an unambiguous normalized multiplier pair.
* Section 3.3.3, for the ingestion compartment system, gives Eq. (65)-(66): an
  organic-compartment loss half-time of about 10 d and a hydrogen-inventory-
  balanced HTO -> OBT coefficient of about 0.012 d^-1 for the stated 0.1 kg
  m^-2 organic and 0.4 kg m^-2 inorganic plant masses.

Section 2.2.6 explicitly says the ingestion transfer paths/rates are transmitted
to the dispersion submodule after adaptation to hourly time steps. Therefore
the first-order inventory transfer structure is recoverable: plant HTO drives
non-exchangeable OBT formation and the non-exchangeable OBT compartment has a
first-order loss. However, the two stated numerical forms are not identical:
Eq. (66)/24 is about 0.0004999 h^-1 rather than 0.0006 h^-1, while Eq. (65)/24
is about 0.002888 h^-1 rather than 0.003 h^-1. B1 preserves this internal manual
numerical tension instead of inventing an exact-original parameter choice.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from ..obt_v3 import (
    OBTParameters,
    OBTState,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    ufotri_obt_baseline_parameters,
)
from ..tfwt_v3 import TFWTState


EXCHANGEABLE_OBT_MODEL_REPRESENTATION = "TFWTState"
NONEXCHANGEABLE_OBT_MODEL_REPRESENTATION = "OBTState"
NO_SEPARATE_EXCHANGEABLE_POOL = True

SHORT_TERM_CONTEXT = "KFK4605_SECTION_2_2_6_ATMOSPHERIC_HOURLY"
LONG_TERM_CONTEXT = "KFK4605_SECTION_3_3_3_INGESTION_EQ65_66"

SHORT_TERM_FORMATION_PER_HOUR = 0.0006
SHORT_TERM_LOSS_PER_HOUR = 0.003
SHORT_TERM_FORMATION_S_1 = SHORT_TERM_FORMATION_PER_HOUR / 3600.0
SHORT_TERM_LOSS_S_1 = SHORT_TERM_LOSS_PER_HOUR / 3600.0

LONG_TERM_OBT_LOSS_HALF_TIME_D = 10.0
LONG_TERM_OBT_TO_HTO_D_1 = math.log(2.0) / LONG_TERM_OBT_LOSS_HALF_TIME_D
LONG_TERM_ORGANIC_PLANT_MASS_KG_M2 = 0.1
LONG_TERM_INORGANIC_PLANT_MASS_KG_M2 = 0.4
LONG_TERM_WATER_HYDROGEN_DIVISOR = 9.0
LONG_TERM_ORGANIC_HYDROGEN_DIVISOR = 13.0
LONG_TERM_MANUAL_ROUNDED_HTO_TO_OBT_D_1 = 0.012
HOURS_PER_DAY = 24.0


@dataclass(frozen=True)
class UFOTRIOBTRoleMap:
    """Recoverable UFOTRI state-role mapping for plant tritium."""

    exchangeable_obt_representation: str = EXCHANGEABLE_OBT_MODEL_REPRESENTATION
    nonexchangeable_obt_representation: str = NONEXCHANGEABLE_OBT_MODEL_REPRESENTATION
    separate_exchangeable_obt_pool: bool = False
    exchangeable_obt_extra_inventory_added: bool = False
    double_counting_prohibited: bool = True
    first_order_inventory_transfer_structure_recovered: bool = True
    manual_section: str = "KfK4605_2.2.6_and_3.3.3"


@dataclass(frozen=True)
class UFOTRIShortTermOBTProfile:
    """Section 2.2.6 short-term non-exchangeable OBT semantics."""

    formation_per_hour: float = SHORT_TERM_FORMATION_PER_HOUR
    loss_per_hour: float = SHORT_TERM_LOSS_PER_HOUR
    daylight_multiplier: float | None = None
    nighttime_multiplier: float | None = None
    day_night_split_recovered: bool = False
    inventory_transfer_structure_recovered: bool = True
    exact_original_parameterization_recovered: bool = False
    controlled_daily_average_binding_authorized: bool = True
    context: str = SHORT_TERM_CONTEXT
    source_section: str = "KfK4605_2.2.6"

    @property
    def formation_s_1(self) -> float:
        return self.formation_per_hour / 3600.0

    @property
    def loss_s_1(self) -> float:
        return self.loss_per_hour / 3600.0

    @property
    def source_ambiguities(self) -> tuple[str, ...]:
        return (
            "NORMALIZED_DAY_NIGHT_FORMATION_MULTIPLIERS_NOT_RECOVERED",
            "SECTION_2_2_6_AND_EQ66_FORWARD_RATE_NUMBERS_NOT_IDENTICAL",
            "SECTION_2_2_6_AND_EQ65_LOSS_RATE_NUMBERS_NOT_IDENTICAL",
            "ORIGINAL_EXECUTABLE_PARAMETER_SELECTION_UNAVAILABLE",
        )


@dataclass(frozen=True)
class UFOTRILongTermIngestionOBTProfile:
    """Section 3.3.3 vegetable HTO/OBT transfer context (Eq. 65-66)."""

    obt_to_hto_d_1: float
    hto_to_obt_d_1_exact_from_stated_masses: float
    hto_to_obt_d_1_manual_rounded: float
    organic_plant_mass_kg_m2: float
    inorganic_plant_mass_kg_m2: float
    water_hydrogen_divisor: float
    organic_hydrogen_divisor: float
    current_short_term_solver_binding_authorized: bool = False
    downstream_stage: str = "UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1"
    context: str = LONG_TERM_CONTEXT
    source_section: str = "KfK4605_3.3.3_Eq65_66"

    @property
    def obt_to_hto_h_1(self) -> float:
        return self.obt_to_hto_d_1 / HOURS_PER_DAY

    @property
    def hto_to_obt_h_1_exact_from_stated_masses(self) -> float:
        return self.hto_to_obt_d_1_exact_from_stated_masses / HOURS_PER_DAY


@dataclass(frozen=True)
class UFOTRIOBTRateReconciliation:
    """Quantify the manual's hourly-vs-ingestion numerical tension."""

    section_2_2_6_forward_h_1: float
    eq66_forward_h_1: float
    section_2_2_6_loss_h_1: float
    eq65_loss_h_1: float

    @property
    def forward_relative_difference_vs_eq66(self) -> float:
        return (
            self.section_2_2_6_forward_h_1 - self.eq66_forward_h_1
        ) / self.eq66_forward_h_1

    @property
    def loss_relative_difference_vs_eq65(self) -> float:
        return (
            self.section_2_2_6_loss_h_1 - self.eq65_loss_h_1
        ) / self.eq65_loss_h_1

    @property
    def numerically_identical(self) -> bool:
        return (
            self.section_2_2_6_forward_h_1 == self.eq66_forward_h_1
            and self.section_2_2_6_loss_h_1 == self.eq65_loss_h_1
        )


@dataclass(frozen=True)
class UFOTRIOBTPlantStateView:
    """Validated UFOTRI semantic view over existing TFWT and OBT states.

    No activity is copied into a new exchangeable-OBT inventory. The view only
    labels which existing state carries each manual role.
    """

    tfwt_state: TFWTState
    nonexchangeable_obt_state: OBTState
    role_map: UFOTRIOBTRoleMap = UFOTRIOBTRoleMap()

    def __post_init__(self) -> None:
        tfwt = self.tfwt_state
        obt = self.nonexchangeable_obt_state
        if tfwt.plant_identifier != obt.plant_identifier:
            raise ValueError("TFWT and non-exchangeable OBT plant identifiers must match")
        if tfwt.crop != obt.crop:
            raise ValueError("TFWT and non-exchangeable OBT crop identifiers must match")
        if tfwt.growth_stage != obt.growth_stage:
            raise ValueError("TFWT and non-exchangeable OBT growth stages must match")
        if tfwt.time != obt.timestamp:
            raise ValueError("TFWT and non-exchangeable OBT timestamps must match")
        if tfwt.area_basis != obt.area_basis:
            raise ValueError("TFWT and non-exchangeable OBT area bases must match")

    @property
    def tfwt_inventory_bq_m2(self) -> float:
        """Existing TFWT inventory; no separate exchangeable OBT is added."""

        return self.tfwt_state.inventory()

    @property
    def nonexchangeable_obt_inventory_bq_m2(self) -> float:
        return self.nonexchangeable_obt_state.inventory()

    @property
    def represented_food_components_bq_m2(self) -> tuple[float, float]:
        """Return the two existing downstream food-transfer components.

        The tuple is ``(nonexchangeable OBT, TFWT)``. Exchangeable OBT is not
        a third activity component because the manual explicitly co-represents
        it with free HTO in the plant-water pathway.
        """

        return (
            self.nonexchangeable_obt_inventory_bq_m2,
            self.tfwt_inventory_bq_m2,
        )


def ufotri_obt_role_map() -> UFOTRIOBTRoleMap:
    """Return the narrow manual-supported exchangeable/non-exchangeable map."""

    return UFOTRIOBTRoleMap()


def ufotri_short_term_obt_profile() -> UFOTRIShortTermOBTProfile:
    """Return Section 2.2.6 daily-average values and explicit ambiguities."""

    return UFOTRIShortTermOBTProfile()


def ufotri_long_term_ingestion_obt_profile() -> UFOTRILongTermIngestionOBTProfile:
    """Reconstruct Eq. (65)-(66) from the masses/divisors stated by the manual."""

    reverse = LONG_TERM_OBT_TO_HTO_D_1
    forward = (
        reverse
        * LONG_TERM_ORGANIC_PLANT_MASS_KG_M2
        * LONG_TERM_WATER_HYDROGEN_DIVISOR
        / (
            LONG_TERM_INORGANIC_PLANT_MASS_KG_M2
            * LONG_TERM_ORGANIC_HYDROGEN_DIVISOR
        )
    )
    return UFOTRILongTermIngestionOBTProfile(
        obt_to_hto_d_1=reverse,
        hto_to_obt_d_1_exact_from_stated_masses=forward,
        hto_to_obt_d_1_manual_rounded=LONG_TERM_MANUAL_ROUNDED_HTO_TO_OBT_D_1,
        organic_plant_mass_kg_m2=LONG_TERM_ORGANIC_PLANT_MASS_KG_M2,
        inorganic_plant_mass_kg_m2=LONG_TERM_INORGANIC_PLANT_MASS_KG_M2,
        water_hydrogen_divisor=LONG_TERM_WATER_HYDROGEN_DIVISOR,
        organic_hydrogen_divisor=LONG_TERM_ORGANIC_HYDROGEN_DIVISOR,
    )


def ufotri_obt_rate_reconciliation() -> UFOTRIOBTRateReconciliation:
    """Compare Section 2.2.6 hourly rates with Eq. (65)-(66) / 24."""

    long_term = ufotri_long_term_ingestion_obt_profile()
    return UFOTRIOBTRateReconciliation(
        section_2_2_6_forward_h_1=SHORT_TERM_FORMATION_PER_HOUR,
        eq66_forward_h_1=long_term.hto_to_obt_h_1_exact_from_stated_masses,
        section_2_2_6_loss_h_1=SHORT_TERM_LOSS_PER_HOUR,
        eq65_loss_h_1=long_term.obt_to_hto_h_1,
    )


def current_short_term_inventory_baseline() -> OBTParameters:
    """Expose the frozen controlled Section 2.2.6 daily-average baseline.

    The existing V4 profile uses 1/1 day/night multipliers solely to preserve
    the recovered daily-average Section 2.2.6 formation rate. This helper does
    not claim those multipliers reproduce the missing original diurnal split,
    nor that Section 2.2.6 and Eq. (65)-(66) select numerically identical rates.
    """

    parameters = ufotri_obt_baseline_parameters()
    if not math.isclose(parameters.kf_s, UFOTRI_OBT_KF_S, rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError("Frozen UFOTRI OBT formation baseline drifted")
    if not math.isclose(parameters.kr_s, UFOTRI_OBT_KR_S, rel_tol=0.0, abs_tol=0.0):
        raise RuntimeError("Frozen UFOTRI OBT loss baseline drifted")
    return parameters


def make_ufotri_obt_state_view(
    tfwt_state: TFWTState,
    nonexchangeable_obt_state: OBTState,
) -> UFOTRIOBTPlantStateView:
    """Validate and label existing states without creating a new OBT pool."""

    if not isinstance(tfwt_state, TFWTState):
        raise TypeError("tfwt_state must be TFWTState")
    if not isinstance(nonexchangeable_obt_state, OBTState):
        raise TypeError("nonexchangeable_obt_state must be OBTState")
    return UFOTRIOBTPlantStateView(
        tfwt_state=tfwt_state,
        nonexchangeable_obt_state=nonexchangeable_obt_state,
    )


__all__ = [
    "EXCHANGEABLE_OBT_MODEL_REPRESENTATION",
    "HOURS_PER_DAY",
    "LONG_TERM_CONTEXT",
    "LONG_TERM_INORGANIC_PLANT_MASS_KG_M2",
    "LONG_TERM_MANUAL_ROUNDED_HTO_TO_OBT_D_1",
    "LONG_TERM_OBT_LOSS_HALF_TIME_D",
    "LONG_TERM_OBT_TO_HTO_D_1",
    "LONG_TERM_ORGANIC_HYDROGEN_DIVISOR",
    "LONG_TERM_ORGANIC_PLANT_MASS_KG_M2",
    "LONG_TERM_WATER_HYDROGEN_DIVISOR",
    "NONEXCHANGEABLE_OBT_MODEL_REPRESENTATION",
    "NO_SEPARATE_EXCHANGEABLE_POOL",
    "SHORT_TERM_CONTEXT",
    "SHORT_TERM_FORMATION_PER_HOUR",
    "SHORT_TERM_FORMATION_S_1",
    "SHORT_TERM_LOSS_PER_HOUR",
    "SHORT_TERM_LOSS_S_1",
    "UFOTRILongTermIngestionOBTProfile",
    "UFOTRIOBTPlantStateView",
    "UFOTRIOBTRateReconciliation",
    "UFOTRIOBTRoleMap",
    "UFOTRIShortTermOBTProfile",
    "current_short_term_inventory_baseline",
    "make_ufotri_obt_state_view",
    "ufotri_long_term_ingestion_obt_profile",
    "ufotri_obt_rate_reconciliation",
    "ufotri_obt_role_map",
    "ufotri_short_term_obt_profile",
]
