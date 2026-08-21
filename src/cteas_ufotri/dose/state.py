"""State and boundary records for the isolated V3-P4 dose interface."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
import math
from typing import Any, Mapping

from ..parameters.provenance import ParameterProvenance


class DoseStateError(ValueError):
    """Raised when a V3-P4 state, pathway, or coefficient is invalid."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise DoseStateError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DoseStateError(f"{name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise DoseStateError(f"{name} must be finite")
    return numeric


def _nonnegative(value: Any, name: str) -> float:
    numeric = _finite(value, name)
    if numeric < 0.0:
        raise DoseStateError(f"{name} must be non-negative")
    return numeric


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DoseStateError(f"{name} must be a non-empty string")
    return value


class AgeGroup(str, Enum):
    """Interface-only age-group vocabulary with no embedded rates or factors."""

    INFANT = "infant"
    CHILD = "child"
    ADULT = "adult"

    @classmethod
    def coerce(cls, value: "AgeGroup | str") -> "AgeGroup":
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except (TypeError, ValueError) as exc:
            raise DoseStateError(
                "age_group must be one of: infant, child, adult"
            ) from exc


def _provenance_mapping(
    value: ParameterProvenance | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(value, ParameterProvenance):
        mapping = value.to_mapping()
    elif isinstance(value, Mapping):
        mapping = dict(value)
    else:
        raise DoseStateError("source_provenance must be a non-empty mapping")
    if not mapping:
        raise DoseStateError("source_provenance must not be empty")
    return mapping


@dataclass(frozen=True, slots=True)
class ConsumptionPathway:
    """A generic food-to-intake pathway with no crop or survey assumptions.

    ``food_activity`` is a product activity concentration in ``Bq kg-1
    food``. ``consumption_rate`` is ``kg s-1`` and ``exposure_duration`` is
    ``s``. Their product is the interface intake activity in Bq. No age-group
    consumption rate or local-food fraction is stored here.
    """

    food_id: str
    food_activity: float
    consumption_rate: float
    exposure_duration: float
    age_group: AgeGroup

    def __post_init__(self) -> None:
        _identifier(self.food_id, "food_id")
        _nonnegative(self.food_activity, "food_activity")
        _nonnegative(self.consumption_rate, "consumption_rate")
        _nonnegative(self.exposure_duration, "exposure_duration")
        object.__setattr__(self, "age_group", AgeGroup.coerce(self.age_group))
        _finite(self.intake_activity, "intake_activity")

    @property
    def intake_activity(self) -> float:
        """Return interface intake activity in Bq."""

        value = (
            float(self.food_activity)
            * float(self.consumption_rate)
            * float(self.exposure_duration)
        )
        if not math.isfinite(value) or value < 0.0:
            raise DoseStateError("intake_activity must be finite and non-negative")
        return value

    @classmethod
    def from_product(
        cls,
        product: Any,
        *,
        consumption_rate: float,
        exposure_duration: float,
        age_group: AgeGroup,
    ) -> "ConsumptionPathway":
        """Build a pathway from a V3-P3 ``HarvestProduct`` boundary record."""

        from ..food_chain.state import HarvestProduct

        if not isinstance(product, HarvestProduct):
            raise DoseStateError("product must be a V3-P3 HarvestProduct")
        return cls(
            food_id=product.crop_id,
            food_activity=product.activity_concentration,
            consumption_rate=consumption_rate,
            exposure_duration=exposure_duration,
            age_group=age_group,
        )

    def copy(self, **changes: Any) -> "ConsumptionPathway":
        """Return a validated immutable pathway copy."""

        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class DoseCoefficient:
    """A provenance-bearing dose-coefficient interface record.

    The coefficient is in ``Sv Bq-1``. The current framework accepts only
    values resolved from ``ParameterDatabase``; direct construction is useful
    for validating the record and therefore still requires provenance.
    """

    radionuclide: str
    coefficient: float
    unit: str
    source_provenance: ParameterProvenance | Mapping[str, Any]
    parameter_name: str = ""
    status: str = "PLACEHOLDER"

    def __post_init__(self) -> None:
        _identifier(self.radionuclide, "radionuclide")
        _nonnegative(self.coefficient, "coefficient")
        if self.unit not in {"Sv Bq-1", "Sv Bq^-1", "Sv/Bq"}:
            raise DoseStateError(
                "dose coefficient unit must be an explicit Sv per Bq unit"
            )
        _provenance_mapping(self.source_provenance)
        if self.parameter_name and not isinstance(self.parameter_name, str):
            raise DoseStateError("parameter_name must be a string")
        _identifier(self.status, "status")

    @classmethod
    def from_database(
        cls,
        parameter_db: Any,
        *,
        radionuclide: str,
        parameter_name: str = "dose.coefficient",
    ) -> "DoseCoefficient":
        """Resolve a coefficient and provenance through ``ParameterDatabase``."""

        from .parameters import DoseParameters

        parameters = DoseParameters.from_database(
            parameter_db,
            parameter_names={"dose_coefficient": parameter_name},
        )
        return cls(
            radionuclide=radionuclide,
            coefficient=parameters.coefficient,
            unit=parameters.coefficient_unit,
            source_provenance=parameters.provenance["dose_coefficient"],
            parameter_name=parameter_name,
            status=parameters.status,
        )

    def provenance_mapping(self) -> dict[str, Any]:
        """Return serializable coefficient provenance."""

        return {
            "radionuclide": self.radionuclide,
            "parameter_name": self.parameter_name,
            "status": self.status,
            "source_provenance": _provenance_mapping(self.source_provenance),
        }


@dataclass(frozen=True, slots=True)
class DoseState:
    """One calculated dose-interface result on an explicit time stamp.

    ``intake_activity`` is Bq, ``dose_coefficient`` is a resolved
    :class:`DoseCoefficient`, ``committed_dose`` is Sv, and ``time`` is a
    caller-supplied ``datetime``. The state is an interface result, not a
    regulatory dose assessment.
    """

    radionuclide: str
    pathway: ConsumptionPathway
    age_group: AgeGroup
    intake_activity: float
    dose_coefficient: DoseCoefficient
    committed_dose: float
    time: datetime

    def __post_init__(self) -> None:
        _identifier(self.radionuclide, "radionuclide")
        if not isinstance(self.pathway, ConsumptionPathway):
            raise DoseStateError("pathway must be a ConsumptionPathway")
        object.__setattr__(self, "age_group", AgeGroup.coerce(self.age_group))
        if self.age_group is not self.pathway.age_group:
            raise DoseStateError("DoseState age_group must match pathway age_group")
        intake = _nonnegative(self.intake_activity, "intake_activity")
        expected_intake = self.pathway.intake_activity
        tolerance = max(1.0e-12, 1.0e-12 * max(intake, expected_intake, 1.0))
        if abs(intake - expected_intake) > tolerance:
            raise DoseStateError(
                "intake_activity must equal pathway.intake_activity"
            )
        if not isinstance(self.dose_coefficient, DoseCoefficient):
            raise DoseStateError("dose_coefficient must be a DoseCoefficient")
        if self.dose_coefficient.radionuclide != self.radionuclide:
            raise DoseStateError(
                "DoseState radionuclide must match dose_coefficient radionuclide"
            )
        _nonnegative(self.committed_dose, "committed_dose")
        if not isinstance(self.time, datetime):
            raise DoseStateError("time must be a datetime")

    @property
    def coefficient_value(self) -> float:
        """Return the resolved numeric coefficient in Sv Bq-1."""

        return float(self.dose_coefficient.coefficient)

    def copy(self, **changes: Any) -> "DoseState":
        """Return a validated immutable result copy."""

        return replace(self, **changes)


DoseResult = DoseState
