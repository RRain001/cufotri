"""Fail-closed validation for the V3 leaf-exchange resistance subsystem."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any


RESISTANCE_UNIT = "s m^-1"
EXCHANGE_VELOCITY_UNIT = "m s^-1"
CONCENTRATION_UNIT = "Bq m^-3"
FLUX_UNIT = "Bq m^-2 s^-1"


class ResistanceSubsystemError(ValueError):
    """Base error for invalid resistance-subsystem inputs."""


class UnitMismatchError(ResistanceSubsystemError):
    """A value was supplied with a unit outside the frozen SI contract."""


class InvalidResistanceError(ResistanceSubsystemError):
    """A resistance or derived exchange velocity is invalid."""


class InvalidForcingError(ResistanceSubsystemError):
    """Atmospheric forcing is incomplete or violates its contract."""


class ParameterUseNotAllowedError(ResistanceSubsystemError):
    """A parameter database entry is not allowed for this subsystem."""


class MissingParameterError(ResistanceSubsystemError):
    """A required parameter is absent, null, or otherwise unavailable."""


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no unit conversion is performed."""

    if actual != expected:
        raise UnitMismatchError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def require_finite(value: Any, *, field: str) -> float:
    """Return a real finite value, rejecting booleans and implicit strings."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidForcingError(f"{field} must be a numeric value")
    result = float(value)
    if not math.isfinite(result):
        raise InvalidForcingError(f"{field} must be finite")
    return result


def validate_resistance(
    value: Any,
    *,
    field: str,
    unit: str = RESISTANCE_UNIT,
) -> float:
    """Validate one strictly-positive resistance in the frozen SI unit."""

    require_unit(unit, RESISTANCE_UNIT, field=field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidResistanceError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise InvalidResistanceError(
            f"{field} must be finite and strictly positive in {RESISTANCE_UNIT}"
        )
    return result


def validate_exchange_velocity(value: Any, *, unit: str = EXCHANGE_VELOCITY_UNIT) -> float:
    """Validate the reciprocal resistance in the frozen SI unit."""

    require_unit(unit, EXCHANGE_VELOCITY_UNIT, field="exchange_velocity")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidResistanceError("exchange_velocity must be numeric")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise InvalidResistanceError(
            f"exchange_velocity must be finite and strictly positive in {EXCHANGE_VELOCITY_UNIT}"
        )
    return result


def validate_provenance(provenance: Any) -> None:
    """Validate the immutable forcing provenance fields."""

    required = (
        "source_id",
        "source_version",
        "artifact_sha256",
        "spatial_reference",
    )
    for field in required:
        value = getattr(provenance, field, None)
        if not isinstance(value, str) or not value.strip():
            raise InvalidForcingError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise InvalidForcingError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise InvalidForcingError("provenance.temporal_resolution_s must be positive")


def validate_forcing(forcing: Any) -> None:
    """Validate AtmosphericHTOForcing without deriving or repairing inputs."""

    timestamp = getattr(forcing, "time", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise InvalidForcingError("forcing.time must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise InvalidForcingError("forcing.time must use UTC")

    air = require_finite(
        forcing.air_hto_concentration_bq_m3,
        field="air_hto_concentration_bq_m3",
    )
    if air < 0.0:
        raise InvalidForcingError("air HTO concentration must be non-negative")
    temperature = require_finite(forcing.air_temperature_k, field="air_temperature_k")
    if temperature <= 0.0:
        raise InvalidForcingError("air temperature must be positive in K")
    humidity = require_finite(
        forcing.relative_humidity,
        field="relative_humidity",
    )
    if not 0.0 <= humidity <= 1.0:
        raise InvalidForcingError("relative_humidity must be in [0, 1]")

    optional_nonnegative = (
        "wind_speed_m_s",
        "shortwave_radiation_w_m2",
    )
    for field in optional_nonnegative:
        value = getattr(forcing, field, None)
        if value is not None and require_finite(value, field=field) < 0.0:
            raise InvalidForcingError(f"{field} must be non-negative")
    boundary_layer_height = getattr(forcing, "boundary_layer_height_m", None)
    if boundary_layer_height is not None and require_finite(
        boundary_layer_height,
        field="boundary_layer_height_m",
    ) <= 0.0:
        raise InvalidForcingError("boundary_layer_height_m must be positive")

    period = getattr(forcing, "day_night", None)
    if period is not None and period not in {"day", "night"}:
        raise InvalidForcingError("day_night must be 'day', 'night', or None")
    validate_provenance(forcing.provenance)
