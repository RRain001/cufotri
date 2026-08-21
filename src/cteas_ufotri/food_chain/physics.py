"""Replaceable physics seam for the V3-P3 food-chain framework.

The supplied kernels are software test harnesses.  They are not UFOTRI
food-chain equations and do not constitute parameter or physical validation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

from .parameters import FoodChainParameters
from .state import FoodChainStateError, PlantInputs, PlantState


@dataclass(frozen=True, slots=True)
class PlantPhysicsResult:
    """Final TFWT/OBT activities and integrated interval terms in Bq."""

    tfwt_activity: float
    obt_activity: float
    internal_transfer: float
    harvest_output: float
    decay_loss: float

    def validate(self) -> None:
        for name in (
            "tfwt_activity",
            "obt_activity",
            "internal_transfer",
            "harvest_output",
            "decay_loss",
        ):
            value = getattr(self, name)
            if isinstance(value, bool):
                raise FoodChainStateError(
                    f"physics result {name} must be finite and non-negative"
                )
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise FoodChainStateError(
                    f"physics result {name} must be finite and non-negative"
                ) from exc
            if not math.isfinite(numeric) or numeric < 0.0:
                raise FoodChainStateError(
                    f"physics result {name} must be finite and non-negative"
                )


class PlantPhysics(Protocol):
    """Protocol for a future reviewed UFOTRI plant/food-chain kernel."""

    status: str

    def step(
        self,
        plant_state: PlantState,
        inputs: PlantInputs,
        dt: float,
        parameters: FoodChainParameters,
    ) -> PlantPhysicsResult:
        ...


@dataclass(frozen=True, slots=True)
class FrameworkOnlyPhysics:
    """Default fail-closed implementation before physics migration."""

    status: str = "PHYSICS_PENDING_UFOTRI_MIGRATION"

    def step(
        self,
        plant_state: PlantState,
        inputs: PlantInputs,
        dt: float,
        parameters: FoodChainParameters,
    ) -> PlantPhysicsResult:
        del plant_state, inputs, dt, parameters
        raise RuntimeError(
            "No food-chain physics kernel is configured; "
            "UFOTRI food-chain equation migration is pending"
        )


@dataclass(frozen=True, slots=True)
class ZeroTransferKernel:
    """TEST_ONLY kernel preserving plant activity during an advance."""

    status: str = "TEST_ONLY"

    def step(
        self,
        plant_state: PlantState,
        inputs: PlantInputs,
        dt: float,
        parameters: FoodChainParameters,
    ) -> PlantPhysicsResult:
        del inputs, dt, parameters
        return PlantPhysicsResult(
            tfwt_activity=plant_state.tfwt_activity,
            obt_activity=plant_state.obt_activity,
            internal_transfer=0.0,
            harvest_output=0.0,
            decay_loss=0.0,
        )


@dataclass(frozen=True, slots=True)
class SyntheticTransferKernel:
    """TEST_ONLY first-order TFWT-to-OBT transfer and decay harness.

    The explicit-Euler update is intentionally simple and dimensionally
    transparent.  It exists only to test the transfer seam, positivity, and
    conservation; it is not a UFOTRI model.
    """

    status: str = "TEST_ONLY"

    def step(
        self,
        plant_state: PlantState,
        inputs: PlantInputs,
        dt: float,
        parameters: FoodChainParameters,
    ) -> PlantPhysicsResult:
        del inputs
        if isinstance(dt, bool):
            raise FoodChainStateError("dt must be a finite positive number of seconds")
        try:
            interval = float(dt)
        except (TypeError, ValueError) as exc:
            raise FoodChainStateError(
                "dt must be a finite positive number of seconds"
            ) from exc
        if not math.isfinite(interval) or interval <= 0.0:
            raise FoodChainStateError(
                "dt must be a finite positive number of seconds"
            )

        transfer = parameters.transfer_rate_s * plant_state.tfwt_activity * interval
        if transfer > plant_state.tfwt_activity:
            raise FoodChainStateError(
                "Synthetic food-chain transfer would create negative TFWT "
                "inventory; reduce dt or use a reviewed positivity-preserving kernel"
            )
        tfwt = plant_state.tfwt_activity - transfer
        obt_before_decay = plant_state.obt_activity + transfer
        decay = parameters.decay_rate_s * obt_before_decay * interval
        if decay > obt_before_decay:
            raise FoodChainStateError(
                "Synthetic food-chain decay would create negative OBT inventory; "
                "reduce dt or use a reviewed positivity-preserving kernel"
            )
        return PlantPhysicsResult(
            tfwt_activity=tfwt,
            obt_activity=obt_before_decay - decay,
            internal_transfer=transfer,
            harvest_output=0.0,
            decay_loss=decay,
        )


def advance(
    plant_state: PlantState,
    inputs: PlantInputs,
    dt: float,
    parameters: FoodChainParameters,
    *,
    kernel: PlantPhysics | None = None,
) -> PlantPhysicsResult:
    """Call an explicit kernel; the default remains fail-closed."""

    selected = FrameworkOnlyPhysics() if kernel is None else kernel
    return selected.step(plant_state, inputs, dt, parameters)
