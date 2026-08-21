"""Semantic, fail-closed validation for the V3-P5.1 parameter contract."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .exceptions import ParameterValidationError
from .registry import SourceRegistry
from .schema import ParameterEntry, ParameterStatus


MODULE_PARAMETER_PATHS: dict[str, str] = {
    "leaf_exchange": "leaf_exchange.*",
    "soil": "soil.*",
    "food_chain": "food_chain.*",
    "dose": "dose.*",
}


def _check_finite(value: Any, path: str) -> None:
    if isinstance(value, bool):
        raise ParameterValidationError(f"{path} must not be boolean")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ParameterValidationError(f"{path} must be finite")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _check_finite(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _check_finite(child, f"{path}[{index}]")


def validate_parameter(
    parameter: ParameterEntry,
    *,
    source_registry: SourceRegistry | None = None,
    expected_unit: str | None = None,
    expected_module: str | None = None,
) -> None:
    """Validate one P5.1 entry and raise on the first semantic defect.

    The function intentionally returns ``None`` on success.  It never repairs
    missing values, substitutes defaults, or changes lifecycle status.
    """

    if not isinstance(parameter, ParameterEntry):
        raise ParameterValidationError("validate_parameter requires a ParameterEntry")
    if parameter._format != "migration":
        raise ParameterValidationError(
            f"Parameter {parameter.name!r} is a legacy P0 entry; use the migration schema"
        )

    parameter_id = parameter.parameter_id
    module = expected_module or parameter.module
    if module not in MODULE_PARAMETER_PATHS:
        raise ParameterValidationError(f"Unsupported parameter module: {module!r}")
    if not parameter_id.startswith(f"{module}."):
        raise ParameterValidationError(
            f"Parameter {parameter_id!r} is outside module namespace {module!r}"
        )
    if expected_unit is not None and parameter.unit != expected_unit:
        raise ParameterValidationError(
            f"Parameter {parameter_id!r} has unit {parameter.unit!r}; expected {expected_unit!r}"
        )
    if not parameter.unit.strip():
        raise ParameterValidationError(f"Parameter {parameter_id!r} requires a unit")
    if not parameter.source.strip() or not parameter.source_type.strip():
        raise ParameterValidationError(
            f"Parameter {parameter_id!r} requires source and source_type provenance"
        )
    if not parameter.reference.strip():
        raise ParameterValidationError(f"Parameter {parameter_id!r} requires a reference")
    if source_registry is not None:
        source_registry.get(parameter.source)

    status = parameter.status
    if status not in {item.value for item in ParameterStatus}:
        raise ParameterValidationError(f"Unsupported parameter status: {status!r}")
    _check_finite(parameter.value, f"{parameter_id}.value") if parameter.value is not None else None
    if parameter.uncertainty is not None:
        _check_finite(parameter.uncertainty, f"{parameter_id}.uncertainty")
        if isinstance(parameter.uncertainty, (int, float)) and parameter.uncertainty < 0:
            raise ParameterValidationError(f"{parameter_id}.uncertainty must be non-negative")

    if status == ParameterStatus.PLACEHOLDER.value:
        if parameter.value is not None or parameter.valid_range is not None:
            raise ParameterValidationError(
                f"Placeholder parameter {parameter_id!r} must not carry value or valid_range"
            )
    else:
        if parameter.value is None or parameter.valid_range is None:
            raise ParameterValidationError(
                f"Non-placeholder parameter {parameter_id!r} requires value and valid_range"
            )
        if not parameter.valid_range.contains(float(parameter.value)):
            raise ParameterValidationError(
                f"Parameter {parameter_id!r} value is outside valid_range"
            )


def validate_parameter_module_path(parameter_id: str, module: str) -> None:
    """Validate a registered module path without loading a parameter value."""

    if module not in MODULE_PARAMETER_PATHS or not parameter_id.startswith(f"{module}."):
        raise ParameterValidationError(
            f"Parameter path {parameter_id!r} is not registered for module {module!r}"
        )
