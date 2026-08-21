"""Mass-balance ledger for one V3-P1 Leaf Exchange step."""

from __future__ import annotations

from dataclasses import dataclass
import math


class MassBalanceError(ValueError):
    """Raised when a leaf-exchange ledger is invalid or does not close."""


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise MassBalanceError(f"{name} must be a finite non-negative number")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise MassBalanceError(f"{name} must be a finite non-negative number")
    return numeric


@dataclass(frozen=True, slots=True)
class LeafExchangeMassBalance:
    """Integrated activity ledger for one interval, all quantities in Bq.

    ``leaf_exchange_flux`` is the positive activity leaving the modeled leaf
    domain back to the atmosphere.  TFWT-to-OBT transfer is internal and is
    therefore not counted as a boundary flux.
    """

    initial_inventory: float
    atmospheric_input: float
    leaf_exchange_flux: float
    decay_loss: float
    final_inventory: float

    def __post_init__(self) -> None:
        for name in (
            "initial_inventory",
            "atmospheric_input",
            "leaf_exchange_flux",
            "decay_loss",
            "final_inventory",
        ):
            _finite_nonnegative(getattr(self, name), name)

    @property
    def closure_error(self) -> float:
        """Return ``initial + input - output - decay - final`` in Bq."""

        return (
            self.initial_inventory
            + self.atmospheric_input
            - self.leaf_exchange_flux
            - self.decay_loss
            - self.final_inventory
        )

    @property
    def scale(self) -> float:
        return max(
            self.initial_inventory
            + self.atmospheric_input
            + self.leaf_exchange_flux
            + self.decay_loss,
            self.final_inventory,
            1.0,
        )

    def assert_closed(self, *, abs_tol: float = 1.0e-12, rel_tol: float = 1.0e-12) -> None:
        """Fail closed if the integrated ledger does not close."""

        tolerance = max(abs_tol, rel_tol * self.scale)
        if abs(self.closure_error) > tolerance:
            raise MassBalanceError(
                "Leaf Exchange mass balance did not close: "
                f"closure_error={self.closure_error!r} Bq, "
                f"scale={self.scale!r}, tolerance={tolerance!r}"
            )
