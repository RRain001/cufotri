"""Coordinator for the isolated V3-P3 plant/food-chain framework."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping

from ..parameters import ParameterDatabase
from .balance import FoodChainMassBalance
from .parameters import DEFAULT_PARAMETER_NAMES, FoodChainParameters
from .physics import (
    FrameworkOnlyPhysics,
    PlantPhysics,
    PlantPhysicsResult,
)
from .state import (
    CropCompartment,
    FoodChainStateError,
    HarvestProduct,
    PlantInputs,
    PlantState,
    receive_leaf_activity,
    receive_root_zone_activity,
)


class FoodChainModelError(ValueError):
    """Raised when a V3-P3 advance cannot be completed safely."""


def _validate_dt(dt: Any) -> float:
    if isinstance(dt, bool):
        raise FoodChainModelError("dt must be a finite positive number of seconds")
    try:
        numeric = float(dt)
    except (TypeError, ValueError) as exc:
        raise FoodChainModelError(
            "dt must be a finite positive number of seconds"
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise FoodChainModelError("dt must be a finite positive number of seconds")
    return numeric


def _coerce_inputs(inputs: PlantInputs | Mapping[str, Any] | None) -> PlantInputs:
    if inputs is None:
        return PlantInputs()
    if isinstance(inputs, PlantInputs):
        return inputs
    if not isinstance(inputs, Mapping):
        raise FoodChainModelError("inputs must be a PlantInputs record or mapping")

    def value(*names: str) -> Any:
        for name in names:
            if name in inputs:
                return inputs[name]
        return 0.0

    try:
        return PlantInputs(
            leaf_tfwt_activity=value("leaf_tfwt_activity", "tfwt_activity"),
            leaf_obt_activity=value("leaf_obt_activity", "obt_activity"),
            plant_exposure_time_s=value(
                "plant_exposure_time_s", "exposure_time_s", "plant_exposure_time"
            ),
            root_zone_activity=value("root_zone_activity"),
            soil_water_activity=value("soil_water_activity"),
        )
    except FoodChainStateError as exc:
        raise FoodChainModelError(str(exc)) from exc


def _apply_leaf_inputs(state: PlantState, inputs: PlantInputs) -> PlantState:
    """Apply only leaf inputs; root-zone values remain a no-uptake seam."""

    return state.copy(
        tfwt_activity=state.tfwt_activity + inputs.leaf_tfwt_activity,
        obt_activity=state.obt_activity + inputs.leaf_obt_activity,
        total_activity=state.total_activity + inputs.leaf_input,
    )


@dataclass(frozen=True, slots=True)
class FoodChainModel:
    """Immutable coordinator with an injected plant-transfer kernel."""

    parameters: FoodChainParameters
    physics: PlantPhysics = field(default_factory=FrameworkOnlyPhysics)
    module_id: str = "v3_food_chain"
    module_version: str = "0.1.0"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] | None = None,
        physics: PlantPhysics | None = None,
    ) -> "FoodChainModel":
        parameters = FoodChainParameters.from_database(
            parameter_db,
            parameter_names=(
                DEFAULT_PARAMETER_NAMES if parameter_names is None else parameter_names
            ),
        )
        return cls(
            parameters=parameters,
            physics=FrameworkOnlyPhysics() if physics is None else physics,
        )

    def advance(
        self,
        plant_state: PlantState,
        inputs: PlantInputs | Mapping[str, Any] | None,
        dt: float,
    ) -> tuple[PlantState, FoodChainMassBalance]:
        """Advance one interval and return the new state plus closed ledger."""

        interval = _validate_dt(dt)
        if not isinstance(plant_state, PlantState):
            raise FoodChainModelError("plant_state must be a PlantState")
        normalized_inputs = _coerce_inputs(inputs)
        with_leaf_input = _apply_leaf_inputs(plant_state, normalized_inputs)
        result = self.physics.step(
            with_leaf_input,
            normalized_inputs,
            interval,
            self.parameters,
        )
        if not isinstance(result, PlantPhysicsResult):
            raise FoodChainModelError(
                "physics kernel must return PlantPhysicsResult"
            )
        try:
            result.validate()
            final_state = with_leaf_input.copy(
                tfwt_activity=result.tfwt_activity,
                obt_activity=result.obt_activity,
                total_activity=result.tfwt_activity + result.obt_activity,
            )
        except FoodChainStateError as exc:
            raise FoodChainModelError(str(exc)) from exc
        balance = FoodChainMassBalance(
            initial_inventory=plant_state.total_activity,
            leaf_input=normalized_inputs.leaf_input,
            # Root-zone input is a seam record only.  No uptake is performed.
            soil_input=0.0,
            internal_transfer=result.internal_transfer,
            harvest_output=result.harvest_output,
            decay_loss=result.decay_loss,
            final_inventory=final_state.total_activity,
        )
        balance.assert_closed()
        return final_state, balance

    @staticmethod
    def harvest(
        crop: CropCompartment,
        harvest_time: Any,
    ) -> HarvestProduct:
        """Create a product record without connecting human intake or dose."""

        return crop.harvest(harvest_time)

    def provenance(self) -> dict[str, object]:
        """Return module, coupling, physics, and parameter provenance."""

        return {
            "module_id": self.module_id,
            "module_version": self.module_version,
            "implementation_status": "FRAMEWORK_COMPLETE",
            "physics_status": self.physics.status,
            "root_uptake_status": "NOT_IMPLEMENTED",
            "harvest_status": "INTERFACE_ONLY_NO_HUMAN_INTAKE",
            "physics_equivalence": "NOT_CLAIMED",
            "parameter_provenance": self.parameters.provenance_mapping(),
        }


PlantModel = FoodChainModel


def advance(
    plant_state: PlantState,
    inputs: PlantInputs | Mapping[str, Any] | None,
    dt: float,
    parameters: FoodChainParameters,
    *,
    kernel: PlantPhysics | None = None,
) -> tuple[PlantState, FoodChainMassBalance]:
    """Functional ``advance(plant_state, inputs, dt, parameters)`` adapter."""

    return FoodChainModel(
        parameters=parameters,
        physics=FrameworkOnlyPhysics() if kernel is None else kernel,
    ).advance(plant_state, inputs, dt)


def harvest_product(crop: CropCompartment, harvest_time: Any) -> HarvestProduct:
    """Functional adapter for the edible-product boundary interface."""

    return FoodChainModel.harvest(crop, harvest_time)
