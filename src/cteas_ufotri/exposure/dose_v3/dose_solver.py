"""V3 P6.6B intake-to-dose conversion solver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..intake_v3 import IntakeState
from .dose_state import DoseState
from .validation import (
    DoseInputError,
    DoseParameterError,
    require_finite,
    validate_dose_parameters,
)


@dataclass(frozen=True)
class DoseParameters:
    """Explicit provisional dose-coefficient parameters."""

    age_group_identifier: str
    radionuclide_identifier: str
    pathway_identifier: str
    dose_coefficient: float
    dose_coefficient_unit: str
    provenance: Any
    parameter_status: str = "provisional"

    def __post_init__(self) -> None:
        validate_dose_parameters(self)


class DoseSolver:
    """Convert one public IntakeState into one DoseState."""

    def advance(
        self,
        intake_state: IntakeState,
        dose_parameters: DoseParameters,
    ) -> DoseState:
        """Advance one explicit intake-to-dose conversion.

        The annual IntakeState inventory is the period-integrated activity
        used by this stage under the explicit annual-period contract:

            D [Sv] = I [Bq] * e [Sv/Bq]
        """

        if not isinstance(intake_state, IntakeState):
            raise DoseInputError("intake_state must be a V3 IntakeState")
        if not isinstance(dose_parameters, DoseParameters):
            raise DoseParameterError(
                "dose_parameters must be DoseParameters"
            )
        validate_dose_parameters(dose_parameters)
        if intake_state.age_group() != dose_parameters.age_group_identifier:
            raise DoseInputError(
                "intake and dose-parameter age groups do not match"
            )
        intake_inventory_bq = require_finite(
            intake_state.inventory(),
            field="intake_state.inventory()",
        )
        if intake_inventory_bq < 0.0:
            raise DoseInputError(
                "intake inventory must be non-negative"
            )
        coefficient = require_finite(
            dose_parameters.dose_coefficient,
            field="dose_coefficient",
        )
        committed_dose_sv = require_finite(
            intake_inventory_bq * coefficient,
            field="committed_dose_sv",
        )
        return DoseState.from_calculation(
            consumer_identifier=intake_state.consumer(),
            age_group_identifier=intake_state.age_group(),
            pathway_identifier=dose_parameters.pathway_identifier,
            intake_inventory_bq=intake_inventory_bq,
            dose_coefficient=coefficient,
            committed_dose_sv=committed_dose_sv,
            time_period=intake_state.period(),
            timestamp=intake_state.time(),
            provenance=dose_parameters.provenance,
        )

    def step(
        self,
        intake_state: IntakeState,
        dose_parameters: DoseParameters,
    ) -> DoseState:
        """Alias for the public one-event dose operation."""

        return self.advance(intake_state, dose_parameters)


__all__ = ["DoseParameters", "DoseSolver"]
