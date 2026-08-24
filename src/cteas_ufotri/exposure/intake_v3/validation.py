"""Fail-closed validation for the isolated V3 P6.6A intake boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any


CONSUMPTION_RATE_UNIT = "kg/year"
FOOD_ACTIVITY_CONCENTRATION_UNIT = "Bq/kg"
FOOD_MASS_UNIT = "kg"
INTAKE_INVENTORY_UNIT = "Bq/year"
ANNUAL_TIME_PERIOD = "annual"


class IntakeValidationError(ValueError):
    """Base error for invalid P6.6A intake records."""


class IntakeStateError(IntakeValidationError):
    """An immutable human-intake state is malformed."""


class IntakeInputError(IntakeValidationError):
    """A food-product input violates the intake boundary."""


class IntakeParameterError(IntakeValidationError):
    """Consumption parameters are missing or invalid."""


class IntakeUnitError(IntakeValidationError):
    """A value is not expressed in the frozen P6.6A unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without accepting strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IntakeValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise IntakeValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise IntakeUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def validate_provenance(provenance: Any) -> None:
    """Validate immutable source metadata structurally."""

    for field in (
        "source_id",
        "source_version",
        "artifact_sha256",
        "spatial_reference",
    ):
        value = getattr(provenance, field, None)
        if not isinstance(value, str) or not value.strip():
            raise IntakeStateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise IntakeStateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise IntakeStateError(
            "provenance.temporal_resolution_s must be positive"
        )


def validate_identifier(
    value: Any,
    *,
    field: str,
    error_type: type[Exception],
) -> None:
    """Require a non-empty stable identifier."""

    if not isinstance(value, str) or not value.strip():
        raise error_type(f"{field} is required")


def validate_utc_timestamp(
    timestamp: Any,
    *,
    error_type: type[Exception],
) -> None:
    """Require a timezone-aware UTC timestamp."""

    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise error_type("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise error_type("timestamp must use UTC")


def validate_intake_state(state: Any) -> None:
    """Validate the immutable annual human-intake inventory state."""

    for field in (
        "consumer_identifier",
        "age_group_identifier",
        "food_product_identifier",
    ):
        validate_identifier(
            getattr(state, field, None),
            field=field,
            error_type=IntakeStateError,
        )
    require_unit(
        state.consumption_rate_unit,
        CONSUMPTION_RATE_UNIT,
        field="consumption_rate",
    )
    require_unit(
        state.inventory_unit,
        INTAKE_INVENTORY_UNIT,
        field="intake_inventory",
    )
    if state.time_period != ANNUAL_TIME_PERIOD:
        raise IntakeStateError(
            f"time_period must be {ANNUAL_TIME_PERIOD!r}"
        )
    consumption = require_finite(
        state.consumption_rate,
        field="consumption_rate",
    )
    inventory = require_finite(
        state.intake_inventory_bq,
        field="intake_inventory_bq",
    )
    if consumption < 0.0:
        raise IntakeStateError("consumption_rate must be non-negative")
    if inventory < 0.0:
        raise IntakeStateError("intake_inventory_bq must be non-negative")
    validate_utc_timestamp(state.timestamp, error_type=IntakeStateError)
    validate_provenance(state.provenance)


def validate_consumption_parameters(parameters: Any) -> None:
    """Validate explicit provisional annual food-consumption parameters."""

    for field in ("food_product_identifier", "age_group_identifier"):
        validate_identifier(
            getattr(parameters, field, None),
            field=field,
            error_type=IntakeParameterError,
        )
    require_unit(
        parameters.consumption_unit,
        CONSUMPTION_RATE_UNIT,
        field="annual_consumption_amount",
    )
    require_unit(
        parameters.food_product_mass_unit,
        FOOD_MASS_UNIT,
        field="food_product_mass",
    )
    consumption = require_finite(
        parameters.annual_consumption_amount,
        field="annual_consumption_amount",
    )
    food_mass = require_finite(
        parameters.food_product_mass_kg,
        field="food_product_mass_kg",
    )
    if consumption < 0.0:
        raise IntakeParameterError(
            "annual_consumption_amount must be non-negative"
        )
    if food_mass <= 0.0:
        raise IntakeParameterError(
            "food_product_mass_kg must be strictly positive"
        )
    if parameters.time_period != ANNUAL_TIME_PERIOD:
        raise IntakeParameterError(
            f"time_period must be {ANNUAL_TIME_PERIOD!r}"
        )
    if parameters.parameter_status != "provisional":
        raise IntakeParameterError(
            "P6.6A consumption parameters must remain provisional"
        )
    validate_provenance(parameters.provenance)


__all__ = [
    "ANNUAL_TIME_PERIOD",
    "CONSUMPTION_RATE_UNIT",
    "FOOD_ACTIVITY_CONCENTRATION_UNIT",
    "FOOD_MASS_UNIT",
    "INTAKE_INVENTORY_UNIT",
    "IntakeInputError",
    "IntakeParameterError",
    "IntakeStateError",
    "IntakeUnitError",
    "IntakeValidationError",
    "require_finite",
    "require_unit",
    "validate_consumption_parameters",
    "validate_intake_state",
    "validate_provenance",
]
