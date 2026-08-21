"""Fail-closed validation for the isolated V3 P6.3 soil HTO pathway."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any


SOIL_INVENTORY_UNIT = "Bq m^-2"
SOIL_CONCENTRATION_UNIT = "Bq m^-3 water"
SOIL_WATER_CONTENT_UNIT = "m water"
LAYER_DEPTH_UNIT = "m"
FLUX_UNIT = "Bq m^-2 s^-1"
INTEGRATED_ACTIVITY_UNIT = "Bq m^-2"
RATE_UNIT = "s^-1"
HALF_LIFE_UNIT = "s"


class SoilValidationError(ValueError):
    """Base error for invalid P6.3 soil state, forcing, or parameters."""


class SoilStateError(SoilValidationError):
    """A soil state is malformed or internally inconsistent."""


class SoilInputError(SoilValidationError):
    """A deposition, transport, or time-step input is invalid."""


class SoilParameterError(SoilValidationError):
    """A half-life or derived decay parameter is invalid."""


class SoilUnitError(SoilValidationError):
    """A value is not expressed in the frozen P6.3 unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without coercing strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SoilValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise SoilValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise SoilUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def validate_provenance(provenance: Any) -> None:
    """Validate immutable source metadata without coupling to plant modules."""

    for field in (
        "source_id",
        "source_version",
        "artifact_sha256",
        "spatial_reference",
    ):
        value = getattr(provenance, field, None)
        if not isinstance(value, str) or not value.strip():
            raise SoilStateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise SoilStateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise SoilStateError("provenance.temporal_resolution_s must be positive")


def validate_state(state: Any) -> None:
    """Validate the soil inventory, water basis, layer geometry, and time."""

    for field in ("soil_identifier", "layer_id", "area_basis"):
        value = getattr(state, field, None)
        if not isinstance(value, str) or not value.strip():
            raise SoilStateError(f"{field} is required")

    require_unit(state.inventory_unit, SOIL_INVENTORY_UNIT, field="soil_inventory")
    require_unit(
        state.concentration_unit,
        SOIL_CONCENTRATION_UNIT,
        field="soil_water_concentration",
    )
    require_unit(
        state.water_content_unit,
        SOIL_WATER_CONTENT_UNIT,
        field="soil_water_content",
    )
    require_unit(state.layer_depth_unit, LAYER_DEPTH_UNIT, field="layer_depth")

    timestamp = getattr(state, "timestamp", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise SoilStateError("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise SoilStateError("timestamp must use UTC")

    layer_depth = require_finite(state.layer_depth_m, field="layer_depth_m")
    water_content = require_finite(
        state.soil_water_content,
        field="soil_water_content",
    )
    inventory = require_finite(
        state.soil_water_inventory_bq_m2,
        field="soil_water_inventory_bq_m2",
    )
    concentration = require_finite(
        state.soil_water_concentration,
        field="soil_water_concentration",
    )
    if layer_depth <= 0.0:
        raise SoilStateError("layer_depth_m must be strictly positive")
    if water_content <= 0.0:
        raise SoilStateError("soil_water_content must be strictly positive")
    if inventory < 0.0 or concentration < 0.0:
        raise SoilStateError(
            "soil water inventory and concentration must be non-negative"
        )
    expected_concentration = inventory / water_content
    if not math.isclose(
        concentration,
        expected_concentration,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise SoilStateError(
            "soil_water_concentration must equal inventory divided by water content"
        )
    validate_provenance(state.provenance)


def validate_interval(interval_seconds: Any) -> float:
    """Validate a strictly positive integration interval in seconds."""

    interval = require_finite(interval_seconds, field="interval_seconds")
    if interval <= 0.0:
        raise SoilInputError("interval_seconds must be strictly positive")
    return interval


def validate_deposition_flux(value: Any) -> float:
    """Validate a non-negative atmospheric deposition flux."""

    flux = require_finite(value, field="deposition_flux_bq_m2_s")
    if flux < 0.0:
        raise SoilInputError("deposition_flux_bq_m2_s must be non-negative")
    return flux


def validate_transport_flux(value: Any) -> float:
    """Validate a signed layer transport flux.

    Positive values enter the current layer; negative values leave it. The
    solver does not derive this flux from a hydrological model.
    """

    return require_finite(value, field="transport_flux_bq_m2_s")


def validate_half_life(value: Any) -> float:
    """Validate a finite, strictly positive tritium half-life in seconds."""

    half_life = require_finite(value, field="tritium_half_life_s")
    if half_life <= 0.0:
        raise SoilParameterError("tritium_half_life_s must be strictly positive")
    return half_life


__all__ = [
    "FLUX_UNIT",
    "HALF_LIFE_UNIT",
    "INTEGRATED_ACTIVITY_UNIT",
    "LAYER_DEPTH_UNIT",
    "RATE_UNIT",
    "SOIL_CONCENTRATION_UNIT",
    "SOIL_INVENTORY_UNIT",
    "SOIL_WATER_CONTENT_UNIT",
    "SoilInputError",
    "SoilParameterError",
    "SoilStateError",
    "SoilUnitError",
    "SoilValidationError",
    "require_finite",
    "require_unit",
    "validate_deposition_flux",
    "validate_half_life",
    "validate_interval",
    "validate_provenance",
    "validate_state",
    "validate_transport_flux",
]
