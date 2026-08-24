"""Immutable schemas for the V3 P7.7A validation control plane.

The classes in this module describe validation inputs and expected evidence.
They do not call a solver, resolve a parameter, or turn a case into a
production run.  Numeric case values therefore remain in YAML configuration;
this module only validates and freezes the decoded representation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType
import re
from typing import Any


class ValidationCaseError(ValueError):
    """A validation case or nested record violates the P7.7A schema."""


class ScenarioType(str, Enum):
    """Case classes kept separate by the validation gate."""

    SYNTHETIC_BENCHMARK = "SYNTHETIC_BENCHMARK"
    SOFTWARE_REGRESSION = "SOFTWARE_REGRESSION"
    ANALYTICAL_SEMANTIC = "ANALYTICAL_SEMANTIC"
    EVALUATED_PHYSICAL_CONSTANT = "EVALUATED_PHYSICAL_CONSTANT"
    EMPIRICAL_OBSERVATION = "EMPIRICAL_OBSERVATION"


class ParameterStatus(str, Enum):
    """Status recorded in a case snapshot, never a runtime lookup result."""

    TEST_ONLY = "TEST_ONLY"
    PROVISIONAL = "PROVISIONAL"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationCaseError(f"{field} must be a non-empty string")
    return value


def _require_identifier(value: Any, *, field: str) -> str:
    text = _require_text(value, field=field)
    if _IDENTIFIER.fullmatch(text) is None:
        raise ValidationCaseError(
            f"{field} must match {_IDENTIFIER.pattern!r}; received {text!r}"
        )
    return text


def _require_finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationCaseError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationCaseError(f"{field} must be finite")
    return number


def _require_sha256(value: Any, *, field: str) -> str:
    text = _require_text(value, field=field)
    if _SHA256.fullmatch(text) is None:
        raise ValidationCaseError(f"{field} must be lowercase hexadecimal SHA-256")
    return text


def _freeze_value(value: Any, *, field: str) -> Any:
    """Freeze JSON-like case payloads and reject anonymous/non-serializable data."""

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValidationCaseError(f"{field} must contain finite numbers")
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ValidationCaseError(
                    f"{field} mapping keys must be non-empty strings"
                )
            frozen[key] = _freeze_value(item, field=f"{field}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(
            _freeze_value(item, field=f"{field}[{index}]")
            for index, item in enumerate(value)
        )
    raise ValidationCaseError(
        f"{field} must contain only JSON-compatible mappings, sequences, or scalars"
    )


def _thaw_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_value(item) for item in value]
    return value


def _coerce_enum(value: Any, enum_type: type[Enum], *, field: str) -> Enum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(repr(item.value) for item in enum_type)
        raise ValidationCaseError(
            f"{field} must be one of {allowed}; received {value!r}"
        ) from exc


@dataclass(frozen=True)
class Provenance:
    """Traceability required for a case, parameter, or reference record."""

    source_kind: str
    source_identifier: str
    artifact_sha256: str
    license_or_access_basis: str
    locator: str

    def __post_init__(self) -> None:
        for field in (
            "source_kind",
            "source_identifier",
            "license_or_access_basis",
            "locator",
        ):
            _require_text(getattr(self, field), field=f"provenance.{field}")
        _require_sha256(
            self.artifact_sha256,
            field="provenance.artifact_sha256",
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Provenance":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("provenance must be a mapping")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(f"invalid provenance: {exc}") from exc

    def to_mapping(self) -> dict[str, str]:
        return {
            "source_kind": self.source_kind,
            "source_identifier": self.source_identifier,
            "artifact_sha256": self.artifact_sha256,
            "license_or_access_basis": self.license_or_access_basis,
            "locator": self.locator,
        }


@dataclass(frozen=True)
class ParameterSnapshot:
    """One explicit parameter/test input carried with a validation case."""

    parameter_id: str
    value: Any
    unit: str
    status: ParameterStatus | str
    provenance: Provenance | Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_identifier(self.parameter_id, field="parameter_id")
        if self.value is None or isinstance(self.value, Mapping):
            raise ValidationCaseError(
                "parameter value must be an explicit scalar, not a hidden mapping"
            )
        if isinstance(self.value, Sequence) and not isinstance(
            self.value,
            (str, bytes, bytearray),
        ):
            raise ValidationCaseError(
                "parameter value must be an explicit scalar, not a hidden sequence"
            )
        frozen_value = _freeze_value(
            self.value,
            field=f"parameter[{self.parameter_id}].value",
        )
        object.__setattr__(self, "value", frozen_value)
        _require_text(self.unit, field=f"parameter[{self.parameter_id}].unit")
        status = _coerce_enum(
            self.status,
            ParameterStatus,
            field=f"parameter[{self.parameter_id}].status",
        )
        object.__setattr__(self, "status", status)
        provenance = self.provenance
        if not isinstance(provenance, Provenance):
            provenance = Provenance.from_mapping(provenance)
        object.__setattr__(self, "provenance", provenance)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterSnapshot":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("parameter_context entries must be mappings")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(f"invalid parameter snapshot: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "value": _thaw_value(self.value),
            "unit": self.unit,
            "status": self.status.value,
            "provenance": self.provenance.to_mapping(),
        }


@dataclass(frozen=True)
class ObservableSpec:
    """Named model output with an explicit unit and time basis."""

    observable_id: str
    quantity: str
    unit: str
    time_basis: str
    output_reference: str

    def __post_init__(self) -> None:
        _require_identifier(self.observable_id, field="observable_id")
        for field in ("quantity", "unit", "time_basis", "output_reference"):
            _require_text(getattr(self, field), field=f"observable.{field}")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ObservableSpec":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("model_outputs entries must be mappings")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(f"invalid observable specification: {exc}") from exc

    def to_mapping(self) -> dict[str, str]:
        return {
            "observable_id": self.observable_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "time_basis": self.time_basis,
            "output_reference": self.output_reference,
        }


@dataclass(frozen=True)
class ReferenceDataSpec:
    """Reference definition kept distinct from production model output."""

    observable_id: str
    quantity: str
    unit: str
    time_basis: str
    reference_method: str
    independent: bool
    provenance: Provenance | Mapping[str, Any]
    reference_expression: str | None = None
    values: tuple[float, ...] | Sequence[float] | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.observable_id, field="reference.observable_id")
        for field in (
            "quantity",
            "unit",
            "time_basis",
            "reference_method",
        ):
            _require_text(getattr(self, field), field=f"reference.{field}")
        if not isinstance(self.independent, bool):
            raise ValidationCaseError("reference.independent must be a boolean")
        if self.reference_expression is not None:
            _require_text(
                self.reference_expression,
                field="reference.reference_expression",
            )
        values: tuple[float, ...] | None
        if self.values is None:
            values = None
        else:
            if isinstance(self.values, (str, bytes, Mapping)):
                raise ValidationCaseError("reference.values must be a numeric sequence")
            try:
                values = tuple(
                    _require_finite(item, field=f"reference.values[{index}]")
                    for index, item in enumerate(self.values)
                )
            except TypeError as exc:
                raise ValidationCaseError("reference.values must be a sequence") from exc
            if not values:
                raise ValidationCaseError("reference.values must not be empty")
        if values is None and self.reference_expression is None:
            raise ValidationCaseError(
                "reference data requires values or an independent reference expression"
            )
        object.__setattr__(self, "values", values)
        provenance = self.provenance
        if not isinstance(provenance, Provenance):
            provenance = Provenance.from_mapping(provenance)
        object.__setattr__(self, "provenance", provenance)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReferenceDataSpec":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("reference_data entries must be mappings")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(f"invalid reference data: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "observable_id": self.observable_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "time_basis": self.time_basis,
            "reference_method": self.reference_method,
            "independent": self.independent,
            "provenance": self.provenance.to_mapping(),
        }
        if self.reference_expression is not None:
            result["reference_expression"] = self.reference_expression
        if self.values is not None:
            result["values"] = list(self.values)
        return result


@dataclass(frozen=True)
class ExpectedMetric:
    """Metric identity used to compare one named observable."""

    metric_name: str
    observable_id: str
    unit: str
    reference_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.metric_name, field="expected_metric.metric_name")
        _require_identifier(
            self.observable_id,
            field="expected_metric.observable_id",
        )
        _require_text(self.unit, field="expected_metric.unit")
        if self.reference_id is not None:
            _require_identifier(
                self.reference_id,
                field="expected_metric.reference_id",
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExpectedMetric":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("expected_metric must be a mapping")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(f"invalid expected metric: {exc}") from exc

    def to_mapping(self) -> dict[str, str]:
        result = {
            "metric_name": self.metric_name,
            "observable_id": self.observable_id,
            "unit": self.unit,
        }
        if self.reference_id is not None:
            result["reference_id"] = self.reference_id
        return result


@dataclass(frozen=True)
class AcceptanceCriterion:
    """Explicit threshold and comparison rule for one metric."""

    metric_name: str
    observable_id: str
    threshold: float
    comparison: str
    unit: str
    rationale: str

    def __post_init__(self) -> None:
        _require_text(self.metric_name, field="acceptance_criteria.metric_name")
        _require_identifier(
            self.observable_id,
            field="acceptance_criteria.observable_id",
        )
        threshold = _require_finite(
            self.threshold,
            field="acceptance_criteria.threshold",
        )
        if threshold < 0.0:
            raise ValidationCaseError("acceptance threshold must be non-negative")
        object.__setattr__(self, "threshold", threshold)
        if self.comparison not in {"ABSOLUTE_LTE", "LTE", "GTE", "EXACT"}:
            raise ValidationCaseError(
                "acceptance comparison must be ABSOLUTE_LTE, LTE, GTE, or EXACT"
            )
        _require_text(self.unit, field="acceptance_criteria.unit")
        _require_text(self.rationale, field="acceptance_criteria.rationale")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AcceptanceCriterion":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("acceptance_criteria entries must be mappings")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ValidationCaseError(
                f"invalid acceptance criterion: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "observable_id": self.observable_id,
            "threshold": self.threshold,
            "comparison": self.comparison,
            "unit": self.unit,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ValidationCase:
    """Complete immutable P7.7A case contract."""

    case_id: str
    description: str
    scenario_type: ScenarioType | str
    forcing_definition: Mapping[str, Any]
    initial_state: Mapping[str, Any]
    parameter_context: tuple[ParameterSnapshot, ...] | Sequence[ParameterSnapshot]
    model_outputs: tuple[ObservableSpec, ...] | Sequence[ObservableSpec]
    reference_data: tuple[ReferenceDataSpec, ...] | Sequence[ReferenceDataSpec]
    expected_metric: ExpectedMetric | Mapping[str, Any]
    acceptance_criteria: tuple[AcceptanceCriterion, ...] | Sequence[AcceptanceCriterion]
    provenance: Provenance | Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_identifier(self.case_id, field="case_id")
        _require_text(self.description, field="description")
        scenario = _coerce_enum(
            self.scenario_type,
            ScenarioType,
            field="scenario_type",
        )
        object.__setattr__(self, "scenario_type", scenario)

        forcing = _freeze_value(self.forcing_definition, field="forcing_definition")
        initial = _freeze_value(self.initial_state, field="initial_state")
        if not isinstance(forcing, Mapping) or "forcing_id" not in forcing:
            raise ValidationCaseError(
                "forcing_definition must contain a named forcing_id"
            )
        if not isinstance(initial, Mapping) or "state_id" not in initial:
            raise ValidationCaseError("initial_state must contain a named state_id")
        _require_identifier(forcing["forcing_id"], field="forcing_definition.forcing_id")
        _require_identifier(initial["state_id"], field="initial_state.state_id")
        object.__setattr__(self, "forcing_definition", forcing)
        object.__setattr__(self, "initial_state", initial)

        parameters = tuple(self.parameter_context)
        converted_parameters = tuple(
            item
            if isinstance(item, ParameterSnapshot)
            else ParameterSnapshot.from_mapping(item)
            for item in parameters
        )
        parameter_ids = [item.parameter_id for item in converted_parameters]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValidationCaseError("parameter_context parameter_id values must be unique")
        object.__setattr__(self, "parameter_context", converted_parameters)

        outputs = tuple(self.model_outputs)
        converted_outputs = tuple(
            item if isinstance(item, ObservableSpec) else ObservableSpec.from_mapping(item)
            for item in outputs
        )
        if not converted_outputs:
            raise ValidationCaseError("model_outputs must not be empty")
        output_ids = [item.observable_id for item in converted_outputs]
        if len(output_ids) != len(set(output_ids)):
            raise ValidationCaseError("model_outputs observable_id values must be unique")
        object.__setattr__(self, "model_outputs", converted_outputs)

        references = tuple(self.reference_data)
        converted_references = tuple(
            item
            if isinstance(item, ReferenceDataSpec)
            else ReferenceDataSpec.from_mapping(item)
            for item in references
        )
        if not converted_references:
            raise ValidationCaseError("reference_data must not be empty")
        reference_ids = [item.observable_id for item in converted_references]
        if len(reference_ids) != len(set(reference_ids)):
            raise ValidationCaseError("reference_data observable_id values must be unique")
        output_by_id = {item.observable_id: item for item in converted_outputs}
        for reference in converted_references:
            output = output_by_id.get(reference.observable_id)
            if output is None:
                raise ValidationCaseError(
                    "reference_data observable_id must name a model output"
                )
            if reference.unit != output.unit:
                raise ValidationCaseError(
                    f"reference {reference.observable_id} unit must match model output"
                )
            if reference.time_basis != output.time_basis:
                raise ValidationCaseError(
                    f"reference {reference.observable_id} time_basis must match model output"
                )
        object.__setattr__(self, "reference_data", converted_references)

        expected = self.expected_metric
        if not isinstance(expected, ExpectedMetric):
            expected = ExpectedMetric.from_mapping(expected)
        if expected.observable_id not in output_ids:
            raise ValidationCaseError(
                "expected_metric.observable_id must name a model output"
            )
        if expected.observable_id not in reference_ids:
            raise ValidationCaseError(
                "expected_metric.observable_id must name reference data"
            )
        if expected.reference_id is not None and expected.reference_id not in reference_ids:
            raise ValidationCaseError(
                "expected_metric.reference_id must name reference data"
            )
        object.__setattr__(self, "expected_metric", expected)

        criteria = tuple(self.acceptance_criteria)
        converted_criteria = tuple(
            item
            if isinstance(item, AcceptanceCriterion)
            else AcceptanceCriterion.from_mapping(item)
            for item in criteria
        )
        if not converted_criteria:
            raise ValidationCaseError("acceptance_criteria must not be empty")
        for criterion in converted_criteria:
            if criterion.observable_id not in output_ids:
                raise ValidationCaseError(
                    "acceptance criterion must name a model output"
                )
        object.__setattr__(self, "acceptance_criteria", converted_criteria)

        provenance = self.provenance
        if not isinstance(provenance, Provenance):
            provenance = Provenance.from_mapping(provenance)
        object.__setattr__(self, "provenance", provenance)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationCase":
        if not isinstance(value, Mapping):
            raise ValidationCaseError("validation case must be a mapping")
        payload = dict(value)
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ValidationCaseError(f"invalid validation case: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "scenario_type": self.scenario_type.value,
            "forcing_definition": _thaw_value(self.forcing_definition),
            "initial_state": _thaw_value(self.initial_state),
            "parameter_context": [item.to_mapping() for item in self.parameter_context],
            "model_outputs": [item.to_mapping() for item in self.model_outputs],
            "reference_data": [item.to_mapping() for item in self.reference_data],
            "expected_metric": self.expected_metric.to_mapping(),
            "acceptance_criteria": [
                item.to_mapping() for item in self.acceptance_criteria
            ],
            "provenance": self.provenance.to_mapping(),
        }


__all__ = [
    "AcceptanceCriterion",
    "ExpectedMetric",
    "ObservableSpec",
    "ParameterSnapshot",
    "ParameterStatus",
    "Provenance",
    "ReferenceDataSpec",
    "ScenarioType",
    "ValidationCase",
    "ValidationCaseError",
]
