"""Coordinator for the isolated V3-P4 dose-interface framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ..parameters import ParameterDatabase
from .balance import DoseLedger
from .parameters import DEFAULT_PARAMETER_NAMES, DoseParameters
from .physics import (
    FrameworkOnlyPhysics,
    DosePhysics,
    DosePhysicsResult,
    _select_coefficient,
)
from .state import (
    ConsumptionPathway,
    DoseCoefficient,
    DoseState,
    DoseStateError,
)


class DoseModelError(ValueError):
    """Raised when a P4 dose-interface calculation cannot be completed."""


DEFAULT_TIME = datetime(1970, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class DoseModel:
    """Immutable coordinator with an injected calculation kernel."""

    parameters: DoseParameters
    physics: DosePhysics = field(default_factory=FrameworkOnlyPhysics)
    module_id: str = "v3_dose_interface"
    module_version: str = "0.1.0"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] | None = None,
        physics: DosePhysics | None = None,
    ) -> "DoseModel":
        parameters = DoseParameters.from_database(
            parameter_db,
            parameter_names=(
                DEFAULT_PARAMETER_NAMES if parameter_names is None else parameter_names
            ),
        )
        return cls(
            parameters=parameters,
            physics=FrameworkOnlyPhysics() if physics is None else physics,
        )

    def calculate(
        self,
        pathway: ConsumptionPathway,
        coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
        *,
        time: datetime = DEFAULT_TIME,
    ) -> tuple[DoseState, DoseLedger]:
        """Calculate one interface result and return its auditable ledger."""

        if not isinstance(pathway, ConsumptionPathway):
            raise DoseModelError("pathway must be a ConsumptionPathway")
        try:
            coefficient = _select_coefficient(coefficients)
        except DoseStateError as exc:
            raise DoseModelError(str(exc)) from exc
        result = self.physics.calculate(pathway, coefficients, self.parameters)
        if not isinstance(result, DosePhysicsResult):
            raise DoseModelError("dose kernel must return DosePhysicsResult")
        try:
            result.validate()
            ledger = DoseLedger(
                input_activity=pathway.intake_activity,
                consumption_transfer=result.consumption_transfer,
                dose_coefficient=coefficient.coefficient,
                calculated_dose=result.calculated_dose,
                uncertainty=result.uncertainty,
                closure=pathway.intake_activity - result.consumption_transfer,
                status=result.status,
            )
            ledger.assert_closed()
            state = DoseState(
                radionuclide=coefficient.radionuclide,
                pathway=pathway,
                age_group=pathway.age_group,
                intake_activity=pathway.intake_activity,
                dose_coefficient=coefficient,
                committed_dose=result.calculated_dose,
                time=time,
            )
        except DoseStateError as exc:
            raise DoseModelError(str(exc)) from exc
        return state, ledger

    def provenance(
        self,
        coefficient: DoseCoefficient | None = None,
    ) -> dict[str, Any]:
        """Return deterministic module, parameter, and coefficient provenance."""

        result: dict[str, Any] = {
            "module_id": self.module_id,
            "module_version": self.module_version,
            "implementation_status": "FRAMEWORK_COMPLETE",
            "physics_status": self.physics.status,
            "physics_equivalence": "NOT_CLAIMED",
            "regulatory_assessment": "NOT_IMPLEMENTED",
            "parameter_provenance": self.parameters.provenance_mapping(),
        }
        if coefficient is not None:
            result["coefficient_provenance"] = coefficient.provenance_mapping()
        return result


DoseInterfaceModel = DoseModel


def calculate(
    pathway: ConsumptionPathway,
    coefficients: DoseCoefficient | Mapping[str, DoseCoefficient],
    parameters: DoseParameters,
    *,
    kernel: DosePhysics | None = None,
    time: datetime = DEFAULT_TIME,
) -> tuple[DoseState, DoseLedger]:
    """Functional ``calculate(pathway, coefficients, parameters)`` adapter."""

    return DoseModel(
        parameters=parameters,
        physics=FrameworkOnlyPhysics() if kernel is None else kernel,
    ).calculate(pathway, coefficients, time=time)
