"""Fail-closed validation for the isolated V3 P6.4 root-transfer boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any


ROOT_INVENTORY_UNIT = "Bq m^-2"
ROOT_FLUX_UNIT = "Bq m^-2 s^-1"
ROOT_COEFFICIENT_UNIT = "m s^-1"
INTEGRATED_ACTIVITY_UNIT = "Bq m^-2"


class RootValidationError(ValueError):
    """Base error for invalid P6.4 root state, forcing, or parameters."""


class RootStateError(RootValidationError):
    """A root transfer state is malformed or inconsistent."""


class RootInputError(RootValidationError):
    """A soil interface or root forcing input is invalid."""


class RootParameterError(RootValidationError):
    """A root uptake coefficient is missing or invalid."""


class RootUnitError(RootValidationError):
    """A value is not expressed in the frozen P6.4 unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without accepting strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RootValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise RootValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise RootUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def validate_provenance(provenance: Any) -> None:
    """Validate the immutable source metadata structurally."""

    for field in (
        "source_id",
        "source_version",
        "artifact_sha256",
        "spatial_reference",
    ):
        value = getattr(provenance, field, None)
        if not isinstance(value, str) or not value.strip():
            raise RootStateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise RootStateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise RootStateError("provenance.temporal_resolution_s must be positive")


def validate_state(state: Any) -> None:
    """Validate the immutable root transfer state."""

    for field in ("plant_identifier", "root_zone_identifier"):
        value = getattr(state, field, None)
        if not isinstance(value, str) or not value.strip():
            raise RootStateError(f"{field} is required")

    require_unit(
        state.inventory_unit,
        ROOT_INVENTORY_UNIT,
        field="uptake_inventory",
    )
    require_unit(state.flux_unit, ROOT_FLUX_UNIT, field="uptake_flux")

    timestamp = getattr(state, "timestamp", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise RootStateError("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise RootStateError("timestamp must use UTC")

    inventory = require_finite(
        state.uptake_inventory_bq_m2,
        field="uptake_inventory_bq_m2",
    )
    flux = require_finite(
        state.uptake_flux_bq_m2_s,
        field="uptake_flux_bq_m2_s",
    )
    if inventory < 0.0 or flux < 0.0:
        raise RootStateError(
            "root uptake inventory and flux must be non-negative"
        )
    validate_provenance(state.provenance)


def validate_forcing(forcing: Any) -> None:
    """Validate the interval and identity metadata for one root step."""

    for field in ("plant_identifier", "root_zone_identifier"):
        value = getattr(forcing, field, None)
        if not isinstance(value, str) or not value.strip():
            raise RootInputError(f"{field} is required")
    interval = require_finite(
        forcing.interval_seconds,
        field="interval_seconds",
    )
    if interval <= 0.0:
        raise RootInputError("interval_seconds must be strictly positive")
    validate_provenance(forcing.provenance)


def validate_parameters(parameters: Any) -> None:
    """Validate the explicit provisional root coefficient."""

    require_unit(
        parameters.coefficient_unit,
        ROOT_COEFFICIENT_UNIT,
        field="k_root",
    )
    coefficient = require_finite(
        parameters.k_root_m_s,
        field="k_root_m_s",
    )
    if coefficient < 0.0:
        raise RootParameterError("k_root_m_s must be non-negative")
    if parameters.parameter_status != "provisional":
        raise RootParameterError(
            "P6.4 root uptake coefficients must remain provisional"
        )


def validate_interval(interval_seconds: Any) -> float:
    """Validate a positive interval in seconds."""

    interval = require_finite(interval_seconds, field="interval_seconds")
    if interval <= 0.0:
        raise RootInputError("interval_seconds must be strictly positive")
    return interval


def validate_nonnegative(value: Any, *, field: str) -> float:
    """Validate one non-negative activity amount."""

    result = require_finite(value, field=field)
    if result < 0.0:
        raise RootInputError(f"{field} must be non-negative")
    return result
