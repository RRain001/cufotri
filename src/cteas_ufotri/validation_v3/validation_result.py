"""Immutable, provenance-complete validation result records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
import re
from typing import Any

from .validation_case import ParameterSnapshot, ValidationCaseError


class ValidationResultError(ValueError):
    """A validation result violates the result contract."""


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationResultError(f"{field} must be a non-empty string")
    return value


def _finite(value: Any, *, field: str, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationResultError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationResultError(f"{field} must be finite")
    if non_negative and result < 0.0:
        raise ValidationResultError(f"{field} must be non-negative")
    return result


def _hash(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if _SHA256.fullmatch(text) is None:
        raise ValidationResultError(f"{field} must be lowercase hexadecimal SHA-256")
    return text


def _identifier(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if _IDENTIFIER.fullmatch(text) is None:
        raise ValidationResultError(f"{field} must be a stable lower-case identifier")
    return text


def _coerce_snapshot(value: Any) -> ParameterSnapshot:
    if isinstance(value, ParameterSnapshot):
        return value
    if not isinstance(value, Mapping):
        raise ValidationResultError("parameter_snapshot entries must be mappings")
    try:
        return ParameterSnapshot.from_mapping(value)
    except ValidationCaseError as exc:
        raise ValidationResultError(str(exc)) from exc


def _passes(value: float, threshold: float, comparison: str) -> bool:
    if comparison == "ABSOLUTE_LTE":
        return abs(value) <= threshold
    if comparison == "LTE":
        return value <= threshold
    if comparison == "GTE":
        return value >= threshold
    if comparison == "EXACT":
        return value == threshold
    raise ValidationResultError(
        "comparison must be ABSOLUTE_LTE, LTE, GTE, or EXACT"
    )


@dataclass(frozen=True)
class ValidationResult:
    """One metric outcome with execution and parameter provenance."""

    case_id: str
    metric_name: str
    value: float
    threshold: float
    pass_fail: bool
    uncertainty: float | None
    execution_hash: str
    solver_version: str
    parameter_snapshot: tuple[ParameterSnapshot, ...] | Sequence[ParameterSnapshot]
    unit: str = "1"
    comparison: str = "ABSOLUTE_LTE"

    def __post_init__(self) -> None:
        _identifier(self.case_id, field="case_id")
        _text(self.metric_name, field="metric_name")
        value = _finite(self.value, field="value")
        threshold = _finite(
            self.threshold,
            field="threshold",
            non_negative=True,
        )
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "threshold", threshold)
        if not isinstance(self.pass_fail, bool):
            raise ValidationResultError("pass_fail must be a boolean")
        if self.uncertainty is not None:
            uncertainty = _finite(
                self.uncertainty,
                field="uncertainty",
                non_negative=True,
            )
            object.__setattr__(self, "uncertainty", uncertainty)
        _hash(self.execution_hash, field="execution_hash")
        _text(self.solver_version, field="solver_version")
        _text(self.unit, field="unit")
        if self.comparison not in {"ABSOLUTE_LTE", "LTE", "GTE", "EXACT"}:
            raise ValidationResultError(
                "comparison must be ABSOLUTE_LTE, LTE, GTE, or EXACT"
            )
        snapshots = tuple(_coerce_snapshot(item) for item in self.parameter_snapshot)
        identifiers = [item.parameter_id for item in snapshots]
        if len(identifiers) != len(set(identifiers)):
            raise ValidationResultError("parameter_snapshot parameter_id values must be unique")
        object.__setattr__(self, "parameter_snapshot", snapshots)
        expected = _passes(value, threshold, self.comparison)
        if expected is not self.pass_fail:
            raise ValidationResultError(
                "pass_fail does not match value, threshold, and comparison"
            )

    @classmethod
    def from_metric(
        cls,
        *,
        case_id: str,
        metric_name: str,
        value: float,
        threshold: float,
        uncertainty: float | None,
        execution_hash: str,
        solver_version: str,
        parameter_snapshot: Sequence[ParameterSnapshot],
        unit: str = "1",
        comparison: str = "ABSOLUTE_LTE",
    ) -> "ValidationResult":
        numeric_value = _finite(value, field="value")
        numeric_threshold = _finite(
            threshold,
            field="threshold",
            non_negative=True,
        )
        return cls(
            case_id=case_id,
            metric_name=metric_name,
            value=numeric_value,
            threshold=numeric_threshold,
            pass_fail=_passes(numeric_value, numeric_threshold, comparison),
            uncertainty=uncertainty,
            execution_hash=execution_hash,
            solver_version=solver_version,
            parameter_snapshot=tuple(parameter_snapshot),
            unit=unit,
            comparison=comparison,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationResult":
        if not isinstance(value, Mapping):
            raise ValidationResultError("validation result must be a mapping")
        payload = dict(value)
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ValidationResultError(f"invalid validation result: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "metric_name": self.metric_name,
            "value": self.value,
            "threshold": self.threshold,
            "pass_fail": self.pass_fail,
            "uncertainty": self.uncertainty,
            "execution_hash": self.execution_hash,
            "solver_version": self.solver_version,
            "parameter_snapshot": [
                item.to_mapping() for item in self.parameter_snapshot
            ],
            "unit": self.unit,
            "comparison": self.comparison,
        }


__all__ = ["ValidationResult", "ValidationResultError"]
