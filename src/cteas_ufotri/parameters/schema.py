"""Versioned schema and typed data model for parameter database entries."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .exceptions import ParameterBoundsError, ParameterSchemaError


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$")
_TRANSFORMS = {"IDENTITY", "LOG", "LOG10", "LOGIT"}
_CONFIDENCE = {
    "validated",
    "provisional",
    "internal_default",
    "placeholder_pending_validation",
}
_APPLICABILITY_STATUS = {"applicable", "conditional", "pending_validation"}


def default_schema_path() -> Path:
    """Return the repository schema path when running from a source checkout."""

    return Path(__file__).resolve().parents[3] / "schemas" / "parameter_database.schema.json"


def _reject_non_finite(value: Any, path: str = "") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ParameterSchemaError(
                f"Non-finite numeric value is not permitted at {path or 'document'}"
            )
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _reject_non_finite(child, f"{path}.{key}" if path else str(key))
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _reject_non_finite(child, f"{path}[{index}]")


def validate_parameter_document(
    document: Mapping[str, Any],
    *,
    schema_path: str | Path | None = None,
) -> None:
    """Validate document shape and reject non-finite YAML numeric values."""

    if not isinstance(document, Mapping):
        raise ParameterSchemaError("Parameter database must be a mapping")
    _reject_non_finite(document)
    path = Path(schema_path) if schema_path is not None else default_schema_path()
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParameterSchemaError(f"Unable to load parameter schema {path}: {exc}") from exc
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "document"
        raise ParameterSchemaError(f"Invalid parameter database at {location}: {error.message}")


@dataclass(frozen=True)
class ParameterBounds:
    """Optional numeric applicability bounds for a parameter value."""

    lower: float
    upper: float
    lower_inclusive: bool
    upper_inclusive: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterBounds":
        try:
            lower = float(value["lower"])
            upper = float(value["upper"])
            lower_inclusive = value["lower_inclusive"]
            upper_inclusive = value["upper_inclusive"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ParameterBoundsError("Bounds must contain numeric limits and inclusivity") from exc
        if not math.isfinite(lower) or not math.isfinite(upper):
            raise ParameterBoundsError("Bounds must be finite")
        if not isinstance(lower_inclusive, bool) or not isinstance(upper_inclusive, bool):
            raise ParameterBoundsError("Bound inclusivity flags must be boolean")
        if lower > upper:
            raise ParameterBoundsError("Lower bound must not exceed upper bound")
        if lower == upper and not (lower_inclusive and upper_inclusive):
            raise ParameterBoundsError("Equal bounds must both be inclusive")
        return cls(lower, upper, lower_inclusive, upper_inclusive)

    def contains(self, value: float) -> bool:
        lower_ok = value >= self.lower if self.lower_inclusive else value > self.lower
        upper_ok = value <= self.upper if self.upper_inclusive else value < self.upper
        return lower_ok and upper_ok

    def to_mapping(self) -> dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "lower_inclusive": self.lower_inclusive,
            "upper_inclusive": self.upper_inclusive,
        }


@dataclass(frozen=True)
class ParameterApplicability:
    """Scope and status describing where an entry may be interpreted."""

    status: str
    scope: str
    conditions: Mapping[str, Any] | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterApplicability":
        if not isinstance(value, Mapping):
            raise ParameterSchemaError("Applicability must be a mapping")
        status = value.get("status")
        scope = value.get("scope")
        if status not in _APPLICABILITY_STATUS:
            raise ParameterSchemaError(f"Unsupported applicability status: {status!r}")
        if not isinstance(scope, str) or not scope.strip():
            raise ParameterSchemaError("Applicability scope must be non-empty")
        conditions = value.get("conditions")
        if conditions is not None and not isinstance(conditions, Mapping):
            raise ParameterSchemaError("Applicability conditions must be a mapping")
        return cls(status, scope, dict(conditions) if conditions is not None else None)

    def to_mapping(self) -> dict[str, Any]:
        result: dict[str, Any] = {"status": self.status, "scope": self.scope}
        if self.conditions is not None:
            result["conditions"] = dict(self.conditions)
        return result


@dataclass(frozen=True)
class ParameterEntry:
    """A typed, provenance-bearing scalar parameter declaration."""

    name: str
    value: float | None
    unit: str
    category: str
    source: str
    reference: str
    confidence: str
    applicability: ParameterApplicability
    transform: str
    bounds: ParameterBounds | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterEntry":
        if not isinstance(value, Mapping):
            raise ParameterSchemaError("Parameter entry must be a mapping")
        validate_parameter_document({"schema_version": "1.0", "parameters": [dict(value)]})
        name = value["name"]
        raw_value = value["value"]
        if not isinstance(name, str) or not _NAME_PATTERN.fullmatch(name):
            raise ParameterSchemaError(f"Invalid parameter name: {name!r}")
        if raw_value is not None:
            if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
                raise ParameterSchemaError(f"Parameter {name!r} value must be numeric or null")
            raw_value = float(raw_value)
            if not math.isfinite(raw_value):
                raise ParameterSchemaError(f"Parameter {name!r} value must be finite")
        confidence = value["confidence"]
        bounds = (
            None
            if value["bounds"] is None
            else ParameterBounds.from_mapping(value["bounds"])
        )
        applicability = ParameterApplicability.from_mapping(value["applicability"])
        if confidence == "placeholder_pending_validation":
            if raw_value is not None or bounds is not None:
                raise ParameterSchemaError(
                    f"Placeholder parameter {name!r} must not carry a value or bounds"
                )
            if applicability.status != "pending_validation":
                raise ParameterSchemaError(
                    f"Placeholder parameter {name!r} must be pending_validation"
                )
        else:
            if raw_value is None or bounds is None:
                raise ParameterSchemaError(
                    f"Non-placeholder parameter {name!r} requires a value and bounds"
                )
            if not bounds.contains(raw_value):
                raise ParameterBoundsError(
                    f"Parameter {name!r} value {raw_value} is outside its bounds"
                )
        return cls(
            name=name,
            value=raw_value,
            unit=value["unit"],
            category=value["category"],
            source=value["source"],
            reference=value["reference"],
            confidence=confidence,
            applicability=applicability,
            transform=value["transform"],
            bounds=bounds,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "source": self.source,
            "reference": self.reference,
            "confidence": self.confidence,
            "applicability": self.applicability.to_mapping(),
            "transform": self.transform,
            "bounds": None if self.bounds is None else self.bounds.to_mapping(),
        }
