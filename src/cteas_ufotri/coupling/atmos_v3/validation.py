"""Fail-closed validation for the V3 P7 atmospheric forcing boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any


AIR_CONCENTRATION_UNIT = "Bq m^-3"
DEPOSITION_FLUX_UNIT = "Bq m^-2 s^-1"
TEMPERATURE_UNIT = "K"
HUMIDITY_UNIT = "1"
WIND_SPEED_UNIT = "m s^-1"
PRECIPITATION_UNIT = "m s^-1"
TIME_RESOLUTION_UNIT = "s"


class AtmosV3ValidationError(ValueError):
    """Base error for invalid P7 atmospheric interface data."""


class AtmosphericForcingError(AtmosV3ValidationError):
    """A forcing record is incomplete or outside the frozen contract."""


class AtmosphericMetadataError(AtmosV3ValidationError):
    """Atmospheric forcing metadata is incomplete or invalid."""


class AtmosphericUnitError(AtmosV3ValidationError):
    """A value uses a unit outside the explicit SI interface contract."""


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no conversion is performed."""

    if actual != expected:
        raise AtmosphericUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite numeric value, rejecting booleans and strings."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AtmosphericForcingError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise AtmosphericForcingError(f"{field} must be finite")
    return result


def require_text(value: Any, *, field: str, error_type: type[ValueError]) -> str:
    """Require a non-empty textual identifier."""

    if not isinstance(value, str) or not value.strip():
        raise error_type(f"{field} is required")
    return value


def validate_utc(timestamp: Any, *, field: str, error_type: type[ValueError]) -> None:
    """Require a timezone-aware UTC timestamp."""

    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise error_type(f"{field} must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise error_type(f"{field} must use UTC")


def validate_metadata(metadata: Any) -> None:
    """Validate metadata without choosing a model, dataset, or quality policy."""

    for field in (
        "model_name",
        "version",
        "grid_definition",
        "source_dataset",
        "quality_flag",
    ):
        require_text(
            getattr(metadata, field, None),
            field=field,
            error_type=AtmosphericMetadataError,
        )
    time_resolution = require_finite(
        getattr(metadata, "time_resolution", None),
        field="time_resolution",
    )
    if time_resolution <= 0.0:
        raise AtmosphericMetadataError("time_resolution must be positive")
    require_unit(
        getattr(metadata, "time_resolution_unit", None),
        TIME_RESOLUTION_UNIT,
        field="time_resolution",
    )
    validate_utc(
        getattr(metadata, "creation_time", None),
        field="creation_time",
        error_type=AtmosphericMetadataError,
    )


def validate_location(location: Any) -> str | tuple[float, float]:
    """Validate a stable location label or a latitude/longitude pair."""

    if isinstance(location, str):
        if not location.strip():
            raise AtmosphericForcingError("location is required")
        return location
    if isinstance(location, (tuple, list)) and len(location) == 2:
        latitude = require_finite(location[0], field="location.latitude")
        longitude = require_finite(location[1], field="location.longitude")
        if not -90.0 <= latitude <= 90.0:
            raise AtmosphericForcingError("location.latitude must be in [-90, 90]")
        if not -180.0 <= longitude <= 180.0:
            raise AtmosphericForcingError(
                "location.longitude must be in [-180, 180]"
            )
        return (latitude, longitude)
    raise AtmosphericForcingError(
        "location must be a non-empty label or (latitude, longitude)"
    )


def validate_forcing(forcing: Any) -> None:
    """Validate an atmospheric forcing record without repairing inputs."""

    validate_utc(
        getattr(forcing, "timestamp", None),
        field="timestamp",
        error_type=AtmosphericForcingError,
    )
    validate_location(getattr(forcing, "location", None))
    require_text(
        getattr(forcing, "source", None),
        field="source",
        error_type=AtmosphericForcingError,
    )

    require_unit(
        getattr(forcing, "air_hto_concentration_unit", None),
        AIR_CONCENTRATION_UNIT,
        field="air_hto_concentration",
    )
    require_unit(
        getattr(forcing, "air_ht0_concentration_unit", None),
        AIR_CONCENTRATION_UNIT,
        field="air_ht0_concentration",
    )
    require_unit(
        getattr(forcing, "deposition_flux_unit", None),
        DEPOSITION_FLUX_UNIT,
        field="deposition_flux",
    )
    require_unit(
        getattr(forcing, "temperature_unit", None),
        TEMPERATURE_UNIT,
        field="temperature",
    )
    require_unit(
        getattr(forcing, "humidity_unit", None),
        HUMIDITY_UNIT,
        field="humidity",
    )
    require_unit(
        getattr(forcing, "wind_speed_unit", None),
        WIND_SPEED_UNIT,
        field="wind_speed",
    )
    require_unit(
        getattr(forcing, "precipitation_unit", None),
        PRECIPITATION_UNIT,
        field="precipitation",
    )

    air_hto = require_finite(
        getattr(forcing, "air_hto_concentration", None),
        field="air_hto_concentration",
    )
    air_ht0 = require_finite(
        getattr(forcing, "air_ht0_concentration", None),
        field="air_ht0_concentration",
    )
    if air_hto < 0.0 or air_ht0 < 0.0:
        raise AtmosphericForcingError(
            "air HTO concentration must be non-negative"
        )
    if air_hto != air_ht0:
        raise AtmosphericForcingError(
            "air_hto_concentration and air_ht0_concentration must agree"
        )

    temperature = require_finite(
        getattr(forcing, "temperature", None),
        field="temperature",
    )
    if temperature <= 0.0:
        raise AtmosphericForcingError("temperature must be positive in K")
    humidity = require_finite(
        getattr(forcing, "humidity", None),
        field="humidity",
    )
    if not 0.0 <= humidity <= 1.0:
        raise AtmosphericForcingError("humidity must be in [0, 1]")
    for field in ("deposition_flux", "wind_speed", "precipitation"):
        if require_finite(getattr(forcing, field, None), field=field) < 0.0:
            raise AtmosphericForcingError(f"{field} must be non-negative")

    provenance = getattr(forcing, "provenance", None)
    for field in (
        "source_id",
        "source_version",
        "artifact_sha256",
        "spatial_reference",
    ):
        require_text(
            getattr(provenance, field, None),
            field=f"provenance.{field}",
            error_type=AtmosphericForcingError,
        )
    artifact_sha256 = provenance.artifact_sha256
    if len(artifact_sha256) != 64 or any(
        character not in "0123456789abcdefABCDEF"
        for character in artifact_sha256
    ):
        raise AtmosphericForcingError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise AtmosphericForcingError(
            "provenance.temporal_resolution_s must be positive"
        )

    metadata = getattr(forcing, "metadata", None)
    if metadata is not None:
        validate_metadata(metadata)


__all__ = [
    "AIR_CONCENTRATION_UNIT",
    "AtmosV3ValidationError",
    "AtmosphericForcingError",
    "AtmosphericMetadataError",
    "AtmosphericUnitError",
    "DEPOSITION_FLUX_UNIT",
    "HUMIDITY_UNIT",
    "PRECIPITATION_UNIT",
    "TEMPERATURE_UNIT",
    "TIME_RESOLUTION_UNIT",
    "WIND_SPEED_UNIT",
    "require_finite",
    "require_text",
    "require_unit",
    "validate_forcing",
    "validate_location",
    "validate_metadata",
    "validate_utc",
]
