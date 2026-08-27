"""Validation helpers for the opt-in V4 three-layer root flux core."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import string
from typing import Iterable


WATER_FLUX_UNIT = "m s^-1"
HTO_CONCENTRATION_UNIT = "Bq m^-3 water"
HTO_FLUX_UNIT = "Bq m^-2 s^-1"
WATER_TRANSFER_UNIT = "m"
HTO_TRANSFER_UNIT = "Bq m^-2"
INTERVAL_UNIT = "s"


class RootV4ValidationError(ValueError):
    """Base class for fail-closed V4 root validation errors."""


class RootV4InputError(RootV4ValidationError):
    """Invalid forcing, state compatibility, or interval input."""


class RootV4UnitError(RootV4ValidationError):
    """Unit identity does not match the frozen V4 contract."""


class RootV4ProvenanceError(RootV4ValidationError):
    """Required forcing provenance is missing or malformed."""


def require_text(value: object, *, field: str, error_type: type[RootV4ValidationError] = RootV4InputError) -> str:
    if not isinstance(value, str) or not value.strip():
        raise error_type(f"{field} is required")
    return value.strip()


def require_finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RootV4InputError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise RootV4InputError(f"{field} must be finite")
    return numeric


def require_unit(value: object, expected: str, *, field: str) -> None:
    if value != expected:
        raise RootV4UnitError(f"{field} unit must be {expected!r}")


def validate_utc_timestamp(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise RootV4InputError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise RootV4InputError(f"{field} must use UTC")
    return value


def validate_interval(value: object) -> float:
    interval = require_finite(value, field="interval_seconds")
    if interval <= 0.0:
        raise RootV4InputError("interval_seconds must be strictly positive")
    return interval


def validate_nonnegative_triplet(value: object, *, field: str) -> tuple[float, float, float]:
    if not isinstance(value, tuple) or len(value) != 3:
        raise RootV4InputError(f"{field} must be a three-element tuple for L1, L2, L3")
    result = tuple(require_finite(item, field=f"{field}[{index}]") for index, item in enumerate(value))
    if any(item < 0.0 for item in result):
        raise RootV4InputError(f"{field} values must be non-negative")
    return result  # type: ignore[return-value]


def validate_sha256(value: object, *, field: str = "artifact_sha256") -> str:
    text = require_text(value, field=field, error_type=RootV4ProvenanceError).lower()
    if len(text) != 64 or any(char not in string.hexdigits.lower() for char in text):
        raise RootV4ProvenanceError(f"{field} must be a 64-character hexadecimal SHA-256")
    return text


def validate_provenance(value: object) -> None:
    for field in ("source_id", "source_locator", "revision", "profile_context"):
        require_text(getattr(value, field, None), field=f"provenance.{field}", error_type=RootV4ProvenanceError)
    validate_sha256(getattr(value, "artifact_sha256", None), field="provenance.artifact_sha256")


def require_layer_ids(values: Iterable[object]) -> None:
    ids = tuple(values)
    if ids != ("L1", "L2", "L3"):
        raise RootV4InputError("root layer transfers must be ordered L1, L2, L3")


__all__ = [
    "HTO_CONCENTRATION_UNIT",
    "HTO_FLUX_UNIT",
    "HTO_TRANSFER_UNIT",
    "INTERVAL_UNIT",
    "RootV4InputError",
    "RootV4ProvenanceError",
    "RootV4UnitError",
    "RootV4ValidationError",
    "WATER_FLUX_UNIT",
    "WATER_TRANSFER_UNIT",
    "require_finite",
    "require_layer_ids",
    "require_text",
    "require_unit",
    "validate_interval",
    "validate_nonnegative_triplet",
    "validate_provenance",
    "validate_sha256",
    "validate_utc_timestamp",
]
