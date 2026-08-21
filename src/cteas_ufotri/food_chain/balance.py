"""Explicit activity ledger for one V3-P3 plant-framework interval."""

from __future__ import annotations

from dataclasses import dataclass
import math


class FoodChainMassBalanceError(ValueError):
    """Raised when a food-chain ledger is invalid or does not close."""


MassBalanceError = FoodChainMassBalanceError


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise FoodChainMassBalanceError(
            f"{name} must be finite and non-negative"
        )
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise FoodChainMassBalanceError(
            f"{name} must be finite and non-negative"
        ) from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise FoodChainMassBalanceError(
            f"{name} must be finite and non-negative"
        )
    return numeric


@dataclass(frozen=True, slots=True)
class FoodChainMassBalance:
    """Integrated plant activity ledger, with all terms in Bq.

    ``internal_transfer`` is a non-negative magnitude of a balanced internal
    movement and therefore does not appear in the global closure identity.
    ``soil_input`` is zero for the current framework because the root-zone
    seam is explicitly no-uptake.
    """

    initial_inventory: float
    leaf_input: float
    soil_input: float
    internal_transfer: float
    harvest_output: float
    decay_loss: float
    final_inventory: float

    def __post_init__(self) -> None:
        for name in (
            "initial_inventory",
            "leaf_input",
            "soil_input",
            "internal_transfer",
            "harvest_output",
            "decay_loss",
            "final_inventory",
        ):
            _finite_nonnegative(getattr(self, name), name)

    @property
    def closure_error(self) -> float:
        """Return ``initial + inputs - outputs - decay - final`` in Bq."""

        return (
            self.initial_inventory
            + self.leaf_input
            + self.soil_input
            - self.harvest_output
            - self.decay_loss
            - self.final_inventory
        )

    @property
    def scale(self) -> float:
        return max(
            self.initial_inventory
            + self.leaf_input
            + self.soil_input
            + self.internal_transfer
            + self.harvest_output
            + self.decay_loss,
            self.final_inventory,
            1.0,
        )

    def assert_closed(
        self,
        *,
        abs_tol: float = 1.0e-12,
        rel_tol: float = 1.0e-12,
    ) -> None:
        """Fail closed when the integrated ledger does not reconcile."""

        tolerance = max(abs_tol, rel_tol * self.scale)
        if abs(self.closure_error) > tolerance:
            raise FoodChainMassBalanceError(
                "Food-chain mass balance did not close: "
                f"closure_error={self.closure_error!r} Bq, "
                f"scale={self.scale!r}, tolerance={tolerance!r}"
            )
