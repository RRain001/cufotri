"""Auditable activity ledger for the V3-P4 dose interface."""

from __future__ import annotations

from dataclasses import dataclass
import math


class DoseLedgerError(ValueError):
    """Raised when a dose ledger is invalid or fails its activity audit."""


def _finite_nonnegative(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise DoseLedgerError(f"{name} must be finite and non-negative")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DoseLedgerError(f"{name} must be finite and non-negative") from exc
    if not math.isfinite(numeric) or numeric < 0.0:
        raise DoseLedgerError(f"{name} must be finite and non-negative")
    return numeric


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise DoseLedgerError(f"{name} must be finite")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DoseLedgerError(f"{name} must be finite") from exc
    if not math.isfinite(numeric):
        raise DoseLedgerError(f"{name} must be finite")
    return numeric


@dataclass(frozen=True, slots=True)
class DoseLedger:
    """One pathway's activity-to-dose audit record.

    ``input_activity`` and ``consumption_transfer`` are Bq, the coefficient is
    Sv Bq-1, dose and uncertainty are Sv, and ``closure`` is an activity
    residual in Bq. A zero kernel may deliberately skip dose arithmetic while
    still closing the activity transfer.
    """

    input_activity: float
    consumption_transfer: float
    dose_coefficient: float
    calculated_dose: float
    uncertainty: float = 0.0
    closure: float | None = None
    status: str = "CLOSED"

    def __post_init__(self) -> None:
        for name in (
            "input_activity",
            "consumption_transfer",
            "dose_coefficient",
            "calculated_dose",
            "uncertainty",
        ):
            _finite_nonnegative(getattr(self, name), name)
        residual = (
            self.input_activity - self.consumption_transfer
            if self.closure is None
            else _finite(self.closure, "closure")
        )
        object.__setattr__(self, "closure", residual)
        if not isinstance(self.status, str) or not self.status.strip():
            raise DoseLedgerError("status must be a non-empty string")

    @property
    def dose_identity_error(self) -> float:
        """Return the synthetic dose identity residual in Sv."""

        return self.calculated_dose - (
            self.consumption_transfer * self.dose_coefficient
        )

    @property
    def scale(self) -> float:
        return max(
            self.input_activity,
            self.consumption_transfer,
            self.dose_coefficient,
            self.calculated_dose,
            self.uncertainty,
            1.0,
        )

    def assert_closed(
        self,
        *,
        abs_tol: float = 1.0e-12,
        rel_tol: float = 1.0e-12,
    ) -> None:
        """Fail closed when food activity is not reconciled to intake."""

        tolerance = max(abs_tol, rel_tol * self.scale)
        if abs(float(self.closure)) > tolerance:
            raise DoseLedgerError(
                "Dose activity ledger did not close: "
                f"closure={self.closure!r} Bq, "
                f"scale={self.scale!r}, tolerance={tolerance!r}"
            )


DoseMassBalance = DoseLedger
