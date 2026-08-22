"""Fail-closed validation helpers for the V3 parameter evidence control plane."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
import math
import re
from typing import Any


class ParameterEvidenceError(ValueError):
    """Base error for malformed parameter evidence."""


class ParameterSchemaError(ParameterEvidenceError):
    """A record or manifest violates the frozen schema."""


class ParameterLifecycleError(ParameterEvidenceError):
    """A requested lifecycle transition is not permitted."""


class ParameterRegistryError(ParameterEvidenceError):
    """A registry violates uniqueness or stage-isolation rules."""


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")


def require_text(value: Any, *, field: str) -> str:
    """Require a non-empty text field without coercing other types."""

    if not isinstance(value, str) or not value.strip():
        raise ParameterSchemaError(f"{field} must be a non-empty string")
    return value


def require_identifier(value: Any, *, field: str) -> str:
    """Require a deterministic machine-readable identifier."""

    text = require_text(value, field=field)
    if _IDENTIFIER.fullmatch(text) is None:
        raise ParameterSchemaError(
            f"{field} must match {_IDENTIFIER.pattern!r}; received {text!r}"
        )
    return text


def require_unit(value: Any, *, field: str) -> str:
    """Require an explicit unit token; no conversion is performed here."""

    return require_text(value, field=field)


def validate_scalar(value: Any, *, field: str) -> None:
    """Validate a JSON-compatible scalar or scalar sequence without coercion."""

    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ParameterSchemaError(f"{field} must be finite")
        return
    if isinstance(value, str):
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            validate_scalar(item, field=f"{field}[{index}]")
        return
    raise ParameterSchemaError(
        f"{field} must be null, scalar text/number/bool, or a scalar sequence"
    )


def coerce_enum(value: Any, enum_type: type[Enum], *, field: str) -> Enum:
    """Parse an enum value without accepting unknown lifecycle tokens."""

    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(repr(item.value) for item in enum_type)
        raise ParameterSchemaError(
            f"{field} must be one of {allowed}; received {value!r}"
        ) from exc


_LIFECYCLE_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROVISIONAL": frozenset({"PROVISIONAL", "EVIDENCE_FOUND", "REJECTED"}),
    "EVIDENCE_FOUND": frozenset({"EVIDENCE_FOUND", "VALIDATED", "REJECTED"}),
    "VALIDATED": frozenset({"VALIDATED", "ACTIVE", "REJECTED"}),
    "ACTIVE": frozenset({"ACTIVE"}),
    "REJECTED": frozenset({"REJECTED"}),
}


def lifecycle_transition(current: Any, target: Any) -> tuple[str, str]:
    """Validate one adjacent lifecycle transition and return its tokens."""

    current_token = getattr(current, "value", current)
    target_token = getattr(target, "value", target)
    current_token = require_text(current_token, field="current_status").upper()
    target_token = require_text(target_token, field="target_status").upper()
    if current_token not in _LIFECYCLE_TRANSITIONS:
        raise ParameterLifecycleError(f"unknown current status {current_token!r}")
    if target_token not in _LIFECYCLE_TRANSITIONS[current_token]:
        raise ParameterLifecycleError(
            f"lifecycle transition {current_token} -> {target_token} is not allowed"
        )
    return current_token, target_token


transition_status = lifecycle_transition


def validate_stage_status(status: Any, *, field: str = "status") -> str:
    """Allow only statuses compatible with the P7.6A evidence freeze."""

    token = getattr(status, "value", status)
    token = require_text(token, field=field).upper()
    if token in {"VALIDATED", "ACTIVE"}:
        raise ParameterRegistryError(
            f"{field}={token} is forbidden during P7.6A; no activation or validation"
        )
    if token not in {"PROVISIONAL", "EVIDENCE_FOUND", "REJECTED"}:
        raise ParameterRegistryError(f"unsupported P7.6A status {token!r}")
    return token


def require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    """Require a mapping for manifest decoding."""

    if not isinstance(value, Mapping):
        raise ParameterSchemaError(f"{field} must be a mapping")
    return value


__all__ = [
    "ParameterEvidenceError",
    "ParameterLifecycleError",
    "ParameterRegistryError",
    "ParameterSchemaError",
    "coerce_enum",
    "lifecycle_transition",
    "require_identifier",
    "require_mapping",
    "require_text",
    "require_unit",
    "transition_status",
    "validate_scalar",
    "validate_stage_status",
]
