"""Fail-closed validation for the opt-in V4 three-layer soil core."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any, Iterable

SOIL_INVENTORY_UNIT = "Bq m^-2"
SOIL_CONCENTRATION_UNIT = "Bq m^-3 water"
WATER_INVENTORY_UNIT = "m water"
DEPTH_UNIT = "m"
WATER_FLUX_UNIT = "m s^-1"
HTO_FLUX_UNIT = "Bq m^-2 s^-1"
HALF_LIFE_UNIT = "s"
RATE_UNIT = "s^-1"

CANONICAL_LAYER_GEOMETRY = (
    ("L1", 0.00, 0.05),
    ("L2", 0.05, 0.15),
    ("L3", 0.15, 0.30),
)


class SoilV4ValidationError(ValueError):
    """Base error for malformed V4 three-layer soil inputs."""


class SoilV4StateError(SoilV4ValidationError):
    pass


class SoilV4InputError(SoilV4ValidationError):
    pass


class SoilV4ParameterError(SoilV4ValidationError):
    pass


class SoilV4UnitError(SoilV4ValidationError):
    pass


def require_finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SoilV4ValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise SoilV4ValidationError(f"{field} must be finite")
    return result


def require_nonnegative(value: Any, *, field: str) -> float:
    result = require_finite(value, field=field)
    if result < 0.0:
        raise SoilV4InputError(f"{field} must be non-negative")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    if actual != expected:
        raise SoilV4UnitError(f"{field} requires unit {expected!r}; received {actual!r}")


def validate_utc_timestamp(value: Any, *, field: str = "timestamp") -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SoilV4StateError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise SoilV4StateError(f"{field} must use UTC")
    return value


def validate_provenance(provenance: Any) -> None:
    for field in ("source_id", "source_version", "artifact_sha256", "spatial_reference"):
        value = getattr(provenance, field, None)
        if not isinstance(value, str) or not value.strip():
            raise SoilV4StateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise SoilV4StateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise SoilV4StateError("provenance.temporal_resolution_s must be positive")


def validate_layer_geometry(layer_id: str, top_m: Any, bottom_m: Any) -> tuple[float, float]:
    if not isinstance(layer_id, str) or not layer_id.strip():
        raise SoilV4StateError("layer_id is required")
    top = require_finite(top_m, field=f"{layer_id}.depth_top_m")
    bottom = require_finite(bottom_m, field=f"{layer_id}.depth_bottom_m")
    if bottom <= top:
        raise SoilV4StateError(f"{layer_id} bottom depth must exceed top depth")
    expected = {item[0]: item[1:] for item in CANONICAL_LAYER_GEOMETRY}.get(layer_id)
    if expected is None:
        raise SoilV4StateError(f"unsupported layer_id {layer_id!r}")
    if not (
        math.isclose(top, expected[0], rel_tol=0.0, abs_tol=1.0e-12)
        and math.isclose(bottom, expected[1], rel_tol=0.0, abs_tol=1.0e-12)
    ):
        raise SoilV4StateError(
            f"{layer_id} geometry must be {expected[0]}-{expected[1]} m"
        )
    return top, bottom


def validate_triplet(values: Iterable[Any], *, field: str, nonnegative: bool) -> tuple[float, float, float]:
    items = tuple(values)
    if len(items) != 3:
        raise SoilV4InputError(f"{field} must contain exactly three values")
    checked = tuple(require_finite(value, field=f"{field}[{i}]") for i, value in enumerate(items))
    if nonnegative and any(value < 0.0 for value in checked):
        raise SoilV4InputError(f"{field} values must be non-negative")
    return checked  # type: ignore[return-value]


def validate_interval(value: Any) -> float:
    interval = require_finite(value, field="interval_seconds")
    if interval <= 0.0:
        raise SoilV4InputError("interval_seconds must be strictly positive")
    return interval


def validate_half_life(value: Any) -> float:
    half_life = require_finite(value, field="tritium_half_life_s")
    if half_life <= 0.0:
        raise SoilV4ParameterError("tritium_half_life_s must be strictly positive")
    return half_life


__all__ = [
    "CANONICAL_LAYER_GEOMETRY",
    "DEPTH_UNIT",
    "HALF_LIFE_UNIT",
    "HTO_FLUX_UNIT",
    "RATE_UNIT",
    "SOIL_CONCENTRATION_UNIT",
    "SOIL_INVENTORY_UNIT",
    "WATER_FLUX_UNIT",
    "WATER_INVENTORY_UNIT",
    "SoilV4InputError",
    "SoilV4ParameterError",
    "SoilV4StateError",
    "SoilV4UnitError",
    "SoilV4ValidationError",
    "require_finite",
    "require_nonnegative",
    "require_unit",
    "validate_half_life",
    "validate_interval",
    "validate_layer_geometry",
    "validate_provenance",
    "validate_triplet",
    "validate_utc_timestamp",
]
