"""V3 P6.5 provisional plant-to-food inventory transfer solver."""

from __future__ import annotations

from dataclasses import dataclass

from ..leaf_exchange_resistance import ForcingProvenance
from ..obt_v3 import OBTState
from ..tfwt_v3 import TFWTState
from .harvest_state import FoodInventory, HarvestState
from .validation import (
    FOOD_INVENTORY_UNIT,
    FoodInputError,
    FoodParameterError,
    require_finite,
    require_unit,
    validate_harvest_parameters,
)


@dataclass(frozen=True)
class HarvestParameters:
    """Explicit provisional fractions and area for one harvest event."""

    plant_identifier: str
    crop_identifier: str
    growth_stage: str
    food_product_identifier: str
    harvest_fraction: float
    harvest_area_m2: float
    provenance: ForcingProvenance
    tfwt_harvest_fraction: float | None = None
    harvest_fraction_unit: str = "1"
    harvest_area_unit: str = "m^2"
    parameter_status: str = "provisional"

    def __post_init__(self) -> None:
        validate_harvest_parameters(self)


@dataclass(frozen=True)
class FoodTransferBalance:
    """Integrated plant-to-food inventory ledger in Bq."""

    obt_source_bq: float
    tfwt_source_bq: float
    obt_transfer_bq: float
    tfwt_transfer_bq: float
    harvest_transfer_bq: float
    remaining_plant_inventory_bq: float
    residual_bq: float
    unit: str = FOOD_INVENTORY_UNIT

    def __post_init__(self) -> None:
        require_unit(self.unit, FOOD_INVENTORY_UNIT, field="food_balance")
        for field in (
            "obt_source_bq",
            "tfwt_source_bq",
            "obt_transfer_bq",
            "tfwt_transfer_bq",
            "harvest_transfer_bq",
            "remaining_plant_inventory_bq",
            "residual_bq",
        ):
            value = require_finite(getattr(self, field), field=field)
            if field != "residual_bq" and value < 0.0:
                raise FoodInputError(f"{field} must be non-negative")

    @property
    def plant_inventory_bq(self) -> float:
        """Return the total source plant inventory on the harvest area."""

        return self.obt_source_bq + self.tfwt_source_bq


@dataclass(frozen=True)
class FoodTransferResult:
    """Harvest state, food inventory, and their auditable balance."""

    harvest_state: HarvestState
    food_inventory: FoodInventory
    balance: FoodTransferBalance

    @property
    def state(self) -> HarvestState:
        """Compatibility alias for the harvest transfer state."""

        return self.harvest_state

    @property
    def food(self) -> FoodInventory:
        """Compatibility alias for the food-product inventory."""

        return self.food_inventory

    def __iter__(self):
        """Allow explicit two-output unpacking: harvest, food."""

        yield self.harvest_state
        yield self.food_inventory


class FoodTransferSolver:
    """Transfer public OBT and TFWT inventories into one food product."""

    def __init__(self, parameters: HarvestParameters | None = None) -> None:
        self.parameters = parameters

    def _resolve_parameters(
        self,
        harvest_parameters: HarvestParameters | None,
    ) -> HarvestParameters:
        if self.parameters is not None and harvest_parameters is not None:
            raise FoodParameterError(
                "parameters cannot be supplied both at construction and advance"
            )
        parameters = (
            self.parameters
            if self.parameters is not None
            else harvest_parameters
        )
        if parameters is None:
            raise FoodParameterError(
                "explicit HarvestParameters are required"
            )
        validate_harvest_parameters(parameters)
        return parameters

    def _source_inventories(
        self,
        obt_state: OBTState,
        tfwt_state: TFWTState,
    ) -> tuple[float, float]:
        """Read source activity through only the public inventory methods."""

        if not isinstance(obt_state, OBTState):
            raise FoodInputError("obt_state must be a V3 OBTState")
        if not isinstance(tfwt_state, TFWTState):
            raise FoodInputError("tfwt_state must be a V3 TFWTState")
        obt_inventory = require_finite(
            obt_state.inventory(),
            field="obt_state.inventory()",
        )
        tfwt_inventory = require_finite(
            tfwt_state.inventory(),
            field="tfwt_state.inventory()",
        )
        if obt_inventory < 0.0 or tfwt_inventory < 0.0:
            raise FoodInputError(
                "OBT and TFWT inventories must be non-negative"
            )
        if obt_state.timestamp != tfwt_state.time:
            raise FoodInputError(
                "OBT and TFWT states must share the harvest timestamp"
            )
        return obt_inventory, tfwt_inventory

    def advance(
        self,
        obt_state: OBTState,
        tfwt_state: TFWTState,
        harvest_parameters: HarvestParameters | None = None,
    ) -> FoodTransferResult:
        """Advance one explicit plant-to-food transfer event."""

        parameters = self._resolve_parameters(harvest_parameters)
        obt_inventory, tfwt_inventory = self._source_inventories(
            obt_state,
            tfwt_state,
        )
        area = parameters.harvest_area_m2
        obt_source = obt_inventory * area
        tfwt_source = tfwt_inventory * area
        obt_transfer = obt_source * parameters.harvest_fraction
        tfwt_fraction = parameters.tfwt_harvest_fraction
        tfwt_transfer = (
            0.0
            if tfwt_fraction is None
            else tfwt_source * tfwt_fraction
        )
        harvest_transfer = obt_transfer + tfwt_transfer
        remaining = obt_source + tfwt_source - harvest_transfer
        if remaining < -1.0e-12:
            raise FoodInputError("harvest transfer exceeds plant inventory")
        remaining = max(remaining, 0.0)
        timestamp = obt_state.timestamp
        food_inventory = FoodInventory.from_components(
            food_product_identifier=parameters.food_product_identifier,
            obt_inventory_bq=obt_transfer,
            tfwt_inventory_bq=tfwt_transfer,
            timestamp=timestamp,
            provenance=parameters.provenance,
        )
        harvest_state = HarvestState.from_inventory(
            plant_identifier=parameters.plant_identifier,
            crop_identifier=parameters.crop_identifier,
            growth_stage=parameters.growth_stage,
            harvest_fraction=parameters.harvest_fraction,
            harvest_inventory_bq=harvest_transfer,
            food_product_identifier=parameters.food_product_identifier,
            timestamp=timestamp,
            provenance=parameters.provenance,
        )
        balance = FoodTransferBalance(
            obt_source_bq=obt_source,
            tfwt_source_bq=tfwt_source,
            obt_transfer_bq=obt_transfer,
            tfwt_transfer_bq=tfwt_transfer,
            harvest_transfer_bq=harvest_transfer,
            remaining_plant_inventory_bq=remaining,
            residual_bq=(
                obt_source
                + tfwt_source
                - harvest_transfer
                - remaining
            ),
        )
        return FoodTransferResult(
            harvest_state=harvest_state,
            food_inventory=food_inventory,
            balance=balance,
        )

    def step(
        self,
        obt_state: OBTState,
        tfwt_state: TFWTState,
        harvest_parameters: HarvestParameters | None = None,
    ) -> FoodTransferResult:
        """Alias for the public one-event transfer operation."""

        return self.advance(obt_state, tfwt_state, harvest_parameters)


__all__ = [
    "FoodTransferBalance",
    "FoodTransferResult",
    "FoodTransferSolver",
    "HarvestParameters",
]
