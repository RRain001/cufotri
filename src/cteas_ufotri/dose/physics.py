"""Replaceable calculation seam for the V3-P4 dose interface.

The included kernels are deterministic software fixtures. They are not UFOTRI
equations, ICRP coefficients, GB/T 18871 calculations, or regulatory results.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Protocol

from .parameters import DoseParameters
from .state import (
    ConsumptionPathway,
    DoseCoefficient,
    DoseStateError,
)


@dataclass(frozen=True, slots=True)
class DosePhysicsResult:
    """Calculated interface terms with dose in Sv and activity in Bq."""

    consumption_transfer: float
    calculated_dose: float
    uncertainty: float
    status: str

    def validate(self) -> None:
        for name in (
            "consumption_transfer",
            "calculated_dose",
            "uncertainty",
        ):
            value = getattr(self, name)
            if isinstance(value, bool):
                raise DoseStateError(
                    f"physics result {name} must be finite and non-negative"
                )
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise DoseStateError(
                    f"physics result {name} must be finite and non-negative"
                ) from exc
            if not math.isfinite(numeric) or numeric < 0.0:
                raise DoseStateError(
                    f"physics result {name} must be finite and non-negative"
                )
        if not isinstance(self.status, str) or not self.status.strip():
            raise DoseStateError("physics result status must be non-empty")


class DosePhysics(Protocol):
    """Protocol for a future reviewed dose-physics implementation."""

    status: str

    def calculate(
        self,
        pathway: ConsumptionPathway,
        coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
        parameters: DoseParameters,
    ) -> DosePhysicsResult:
        ...


def _select_coefficient(
    coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
) -> DoseCoefficient:
    if isinstance(coefficients, DoseCoefficient):
        return coefficients
    if not isinstance(coefficients, Mapping) or not coefficients:
        raise DoseStateError("coefficients must contain a DoseCoefficient")
    values = list(coefficients.values())
    if not all(isinstance(value, DoseCoefficient) for value in values):
        raise DoseStateError("coefficients must contain DoseCoefficient records")
    if len(values) == 1:
        return values[0]
    raise DoseStateError(
        "a pathway calculation requires one explicit DoseCoefficient"
    )


@dataclass(frozen=True, slots=True)
class FrameworkOnlyPhysics:
    """Default fail-closed implementation before dose migration."""

    status: str = "PHYSICS_PENDING_UFOTRI_MIGRATION"

    def calculate(
        self,
        pathway: ConsumptionPathway,
        coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
        parameters: DoseParameters,
    ) -> DosePhysicsResult:
        del pathway, coefficients, parameters
        raise RuntimeError(
            "No dose physics kernel is configured; "
            "UFOTRI dose-equation migration is pending"
        )


@dataclass(frozen=True, slots=True)
class ZeroDoseKernel:
    """TEST_ONLY flow kernel that returns zero dose without discarding intake."""

    status: str = "TEST_ONLY_ZERO_DOSE"

    def calculate(
        self,
        pathway: ConsumptionPathway,
        coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
        parameters: DoseParameters,
    ) -> DosePhysicsResult:
        del parameters
        _select_coefficient(coefficients)
        return DosePhysicsResult(
            consumption_transfer=pathway.intake_activity,
            calculated_dose=0.0,
            uncertainty=0.0,
            status=self.status,
        )


@dataclass(frozen=True, slots=True)
class SyntheticDoseKernel:
    """TEST_ONLY arithmetic kernel: intake activity times supplied coefficient."""

    status: str = "TEST_ONLY_SYNTHETIC"

    def calculate(
        self,
        pathway: ConsumptionPathway,
        coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
        parameters: DoseParameters,
    ) -> DosePhysicsResult:
        del parameters
        coefficient = _select_coefficient(coefficients)
        transfer = pathway.intake_activity
        dose = transfer * coefficient.coefficient
        if not math.isfinite(dose) or dose < 0.0:
            raise DoseStateError(
                "Synthetic dose calculation would create invalid dose"
            )
        return DosePhysicsResult(
            consumption_transfer=transfer,
            calculated_dose=dose,
            uncertainty=0.0,
            status=self.status,
        )


def calculate(
    pathway: ConsumptionPathway,
    coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
    parameters: DoseParameters,
    *,
    kernel: DosePhysics | None = None,
) -> DosePhysicsResult:
    """Call the explicit dose seam; the default remains fail-closed."""

    selected = FrameworkOnlyPhysics() if kernel is None else kernel
    return selected.calculate(pathway, coefficients, parameters)
