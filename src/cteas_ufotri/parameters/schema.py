"""Versioned schema and typed data model for parameter database entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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


class ParameterStatus(str, Enum):
    """Auditable lifecycle states for migrated parameters."""

    PLACEHOLDER = "PLACEHOLDER"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"


_PARAMETER_STATUSES = {item.value for item in ParameterStatus}


def _status_from_confidence(confidence: str | None) -> str:
    return {
        "placeholder_pending_validation": ParameterStatus.PLACEHOLDER.value,
        "internal_default": ParameterStatus.CANDIDATE.value,
        "provisional": ParameterStatus.CANDIDATE.value,
        "validated": ParameterStatus.VALIDATED.value,
    }.get(confidence or "", ParameterStatus.PLACEHOLDER.value)


def _confidence_from_status(status: str) -> str:
    return {
        ParameterStatus.PLACEHOLDER.value: "placeholder_pending_validation",
        ParameterStatus.CANDIDATE.value: "provisional",
        ParameterStatus.REVIEWED.value: "provisional",
        ParameterStatus.VALIDATED.value: "validated",
        ParameterStatus.ACTIVE.value: "validated",
    }[status]


def default_schema_path() -> Path:
    """Return the repository schema path when running from a source checkout."""

    return Path(__file__).resolve().parents[3] / "schemas" / "parameter_database.schema.json"


def migration_schema_path() -> Path:
    """Return the P5.1 migration-document schema path."""

    return Path(__file__).resolve().parents[3] / "schemas" / "parameter_migration.schema.json"


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
    version = document.get("schema_version")
    if schema_path is not None:
        path = Path(schema_path)
    elif version == "2.0":
        path = migration_schema_path()
    else:
        path = default_schema_path()
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
    """A typed parameter declaration with a backwards-compatible P0 view.

    P0 entries use ``name/category/confidence/applicability/transform/bounds``.
    P5.1 entries use ``parameter_id/description/module/status/source_type`` and
    ``uncertainty/valid_range/notes``.  Both representations resolve to the
    same object so existing V3 interface modules remain untouched.
    """

    # The defaults allow callers to construct either the P0 or P5.1 form with
    # keyword arguments.  __post_init__ enforces the required common fields.
    name: str | None = None
    value: float | None = None
    unit: str | None = None
    category: str | None = None
    source: str | None = None
    reference: str | None = None
    confidence: str | None = None
    applicability: ParameterApplicability | None = None
    transform: str = "IDENTITY"
    bounds: ParameterBounds | None = None
    parameter_id: str | None = None
    description: str | None = None
    module: str | None = None
    status: str | ParameterStatus | None = None
    source_type: str | None = None
    uncertainty: Any = None
    valid_range: ParameterBounds | Mapping[str, Any] | None = None
    notes: str | None = None
    _format: str = field(default="legacy", init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        migration = (
            self.parameter_id is not None
            or self.status is not None
            or self.module is not None
            or self.description is not None
            or self.source_type is not None
            or self.valid_range is not None
            or self.uncertainty is not None
            or self.notes is not None
        )
        parameter_id = self.parameter_id or self.name
        if not isinstance(parameter_id, str) or not _NAME_PATTERN.fullmatch(parameter_id):
            raise ParameterSchemaError(f"Invalid parameter id: {parameter_id!r}")
        if self.name is not None and self.name != parameter_id:
            raise ParameterSchemaError("Parameter name and parameter_id must match")
        unit = self.unit
        source = self.source
        reference = self.reference
        if not isinstance(unit, str) or not unit.strip():
            raise ParameterSchemaError(f"Parameter {parameter_id!r} requires a unit")
        if not isinstance(source, str) or not source.strip():
            raise ParameterSchemaError(f"Parameter {parameter_id!r} requires a source")
        if not isinstance(reference, str) or not reference.strip():
            raise ParameterSchemaError(f"Parameter {parameter_id!r} requires a reference")

        raw_status = self.status.value if isinstance(self.status, ParameterStatus) else self.status
        status = raw_status or _status_from_confidence(self.confidence)
        if status not in _PARAMETER_STATUSES:
            raise ParameterSchemaError(f"Unsupported parameter status: {status!r}")
        confidence = self.confidence or _confidence_from_status(status)
        if confidence not in _CONFIDENCE:
            raise ParameterSchemaError(f"Unsupported parameter confidence: {confidence!r}")

        module = self.module or self.category or parameter_id.split(".", 1)[0]
        if not isinstance(module, str) or not module.strip():
            raise ParameterSchemaError(f"Parameter {parameter_id!r} requires a module")
        category = self.category or module
        description = self.description or reference
        source_type = self.source_type or "legacy_registry"
        if not isinstance(source_type, str) or not source_type.strip():
            raise ParameterSchemaError(f"Parameter {parameter_id!r} requires source_type")

        bounds = self.bounds
        valid_range = self.valid_range
        if valid_range is not None and not isinstance(valid_range, ParameterBounds):
            valid_range = ParameterBounds.from_mapping(valid_range)
        if bounds is None:
            bounds = valid_range
        if valid_range is None:
            valid_range = bounds
        applicability = self.applicability
        if applicability is None:
            applicability = ParameterApplicability(
                status=(
                    "pending_validation"
                    if status == ParameterStatus.PLACEHOLDER.value
                    else "applicable"
                ),
                scope=f"module:{module}",
            )
        if self.value is not None:
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ParameterSchemaError(f"Parameter {parameter_id!r} value must be numeric or null")
            if not math.isfinite(float(self.value)):
                raise ParameterSchemaError(f"Parameter {parameter_id!r} value must be finite")
        if status == ParameterStatus.PLACEHOLDER.value and self.value is not None:
            raise ParameterSchemaError(f"Placeholder parameter {parameter_id!r} must not carry a value")
        if self.value is not None and valid_range is not None and not valid_range.contains(float(self.value)):
            raise ParameterBoundsError(
                f"Parameter {parameter_id!r} value {self.value} is outside its bounds"
            )
        if self.uncertainty is not None:
            _reject_non_finite(self.uncertainty, f"{parameter_id}.uncertainty")
        if self.notes is not None and not isinstance(self.notes, str):
            raise ParameterSchemaError(f"Parameter {parameter_id!r}.notes must be text")

        object.__setattr__(self, "name", parameter_id)
        object.__setattr__(self, "parameter_id", parameter_id)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "reference", reference)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "module", module)
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "source_type", source_type)
        object.__setattr__(self, "applicability", applicability)
        object.__setattr__(self, "bounds", bounds)
        object.__setattr__(self, "valid_range", valid_range)
        object.__setattr__(self, "notes", self.notes or "")
        object.__setattr__(self, "_format", "migration" if migration else "legacy")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterEntry":
        if not isinstance(value, Mapping):
            raise ParameterSchemaError("Parameter entry must be a mapping")
        if "parameter_id" in value or "status" in value:
            validate_parameter_document({"schema_version": "2.0", "parameters": [dict(value)]})
            valid_range = (
                None
                if value["valid_range"] is None
                else ParameterBounds.from_mapping(value["valid_range"])
            )
            return cls(
                parameter_id=value["parameter_id"],
                value=value["value"],
                unit=value["unit"],
                description=value["description"],
                module=value["module"],
                status=value["status"],
                source=value["source"],
                source_type=value["source_type"],
                reference=value["reference"],
                uncertainty=value["uncertainty"],
                valid_range=valid_range,
                notes=value["notes"],
            )
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
        if self._format == "migration":
            return {
                "parameter_id": self.parameter_id,
                "value": self.value,
                "unit": self.unit,
                "description": self.description,
                "module": self.module,
                "status": self.status,
                "source": self.source,
                "source_type": self.source_type,
                "reference": self.reference,
                "uncertainty": self.uncertainty,
                "valid_range": (
                    None if self.valid_range is None else self.valid_range.to_mapping()
                ),
                "notes": self.notes,
            }
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
