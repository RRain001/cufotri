"""Mass-balance ledger for one V3-P2 soil interval."""

from __future__ import annotations

from dataclasses import dataclass
import math


class SoilMassBalanceError(ValueError):
    """Raised when a soil ledger is invalid or does not close."""


MassBalanceError = SoilMassBalanceError


def _finite_nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool):
        raise SoilMassBalanceError(f"{name} must be finite and non-negative")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise SoilMassBalanceError(
            f"{name} must be finite and non-negative"
        ) from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise SoilMassBalanceError(f"{name} must be finite and non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class SoilMassBalance:
    """Integrated soil activity ledger, with all quantities in Bq m-2.

    ``internal_transfer`` is the non-negative magnitude of balanced transfer
    between soil layers. It is audited separately and has zero net contribution
    to the global inventory identity.
    """

    initial_inventory: float
    atmospheric_input: float
    internal_transfer: float
    decay_loss: float
    output_to_plants: float
    final_inventory: float

    def __post_init__(self) -> None:
        for name in (
            "initial_inventory",
            "atmospheric_input",
            "internal_transfer",
            "decay_loss",
            "output_to_plants",
            "final_inventory",
        ):
            _finite_nonnegative(getattr(self, name), name)

    @property
    def closure_error(self) -> float:
        """Return ``initial + input - output - decay - final`` in Bq m-2."""

        return (
            self.initial_inventory
            + self.atmospheric_input
            - self.output_to_plants
            - self.decay_loss
            - self.final_inventory
        )

    @property
    def scale(self) -> float:
        return max(
            self.initial_inventory
            + self.atmospheric_input
            + self.internal_transfer
            + self.decay_loss
            + self.output_to_plants,
            self.final_inventory,
            1.0,
        )

    def assert_closed(
        self,
        *,
        abs_tol: float = 1.0e-12,
        rel_tol: float = 1.0e-12,
    ) -> None:
        """Fail closed when total activity does not reconcile."""

        tolerance = max(abs_tol, rel_tol * self.scale)
        if abs(self.closure_error) > tolerance:
            raise SoilMassBalanceError(
                "Soil mass balance did not close: "
                f"closure_error={self.closure_error!r} Bq m-2, "
                f"scale={self.scale!r}, tolerance={tolerance!r}"
            )
