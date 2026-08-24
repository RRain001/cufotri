"""Fail-closed validation for the isolated V3 P6.2C OBT solver."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any

from ..leaf_exchange_resistance.validation import (
    validate_provenance as validate_forcing_provenance,
)


OBT_CONCENTRATION_UNIT = "Bq kg^-1 fresh"
OBT_INVENTORY_UNIT = "Bq m^-2"
PLANT_MASS_UNIT = "kg fresh m^-2"
RATE_UNIT = "s^-1"
INTEGRATED_ACTIVITY_UNIT = "Bq m^-2"


class OBTValidationError(ValueError):
    """Base error for invalid P6.2C state, forcing, or rate terms."""


class OBTStateError(OBTValidationError):
    """An OBT state is malformed or internally inconsistent."""


class OBTInputError(OBTValidationError):
    """A TFWT or biological forcing input violates the public boundary."""


class OBTParameterError(OBTValidationError):
    """A formation or turnover parameter is invalid."""


class OBTUnitError(OBTValidationError):
    """A value is not expressed in the frozen P6.2C unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without coercing strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OBTValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise OBTValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise OBTUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def validate_state(state: Any) -> None:
    """Validate the OBT inventory, concentration, time, and provenance."""

    for field in ("plant_identifier", "crop", "growth_stage", "area_basis"):
        value = getattr(state, field, None)
        if not isinstance(value, str) or not value.strip():
            raise OBTStateError(f"{field} is required")

    require_unit(
        state.inventory_unit,
        OBT_INVENTORY_UNIT,
        field="obt_inventory",
    )
    require_unit(
        state.concentration_unit,
        OBT_CONCENTRATION_UNIT,
        field="obt_concentration",
    )
    require_unit(
        state.plant_mass_unit,
        PLANT_MASS_UNIT,
        field="plant_mass",
    )

    timestamp = getattr(state, "timestamp", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise OBTStateError("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise OBTStateError("timestamp must use UTC")

    inventory = require_finite(
        state.obt_inventory_bq_m2,
        field="obt_inventory_bq_m2",
    )
    concentration = require_finite(
        state.obt_concentration,
        field="obt_concentration",
    )
    plant_mass = require_finite(
        state.plant_mass_kg_m2,
        field="plant_mass_kg_m2",
    )
    if inventory < 0.0 or concentration < 0.0:
        raise OBTStateError("OBT inventory and concentration must be non-negative")
    if plant_mass <= 0.0:
        raise OBTStateError("plant_mass_kg_m2 must be strictly positive")

    expected_concentration = inventory / plant_mass
    if not math.isclose(
        concentration,
        expected_concentration,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise OBTStateError(
            "obt_concentration must equal inventory divided by plant mass"
        )

    try:
        validate_forcing_provenance(state.provenance)
    except ValueError as exc:
        raise OBTStateError(str(exc)) from exc


def validate_interval(interval_seconds: Any) -> float:
    """Validate a strictly positive integration interval in seconds."""

    interval = require_finite(interval_seconds, field="interval_seconds")
    if interval <= 0.0:
        raise OBTInputError("interval_seconds must be strictly positive")
    return interval


def validate_rate(value: Any, *, field: str) -> float:
    """Validate a non-negative first-order rate in ``s^-1``."""

    rate = require_finite(value, field=field)
    if rate < 0.0:
        raise OBTParameterError(f"{field} must be non-negative")
    return rate


def validate_multiplier(value: Any, *, field: str) -> float:
    """Validate a non-negative dimensionless biological multiplier."""

    multiplier = require_finite(value, field=field)
    if multiplier < 0.0:
        raise OBTParameterError(f"{field} must be non-negative")
    return multiplier


def validate_biological_forcing(forcing: Any) -> None:
    """Validate the first-version forcing boundary.

    Only ``is_daylight`` participates in P6.2C arithmetic. The optional
    temperature, photosynthetic-activity, and growth-stage fields reserve the
    extension seam without silently affecting the current solver.
    """

    if not isinstance(getattr(forcing, "is_daylight", None), bool):
        raise OBTInputError("is_daylight must be a boolean")

    temperature = getattr(forcing, "temperature_k", None)
    if temperature is not None and require_finite(
        temperature,
        field="temperature_k",
    ) <= 0.0:
        raise OBTInputError("temperature_k must be positive in K")

    photosynthetic_activity = getattr(forcing, "photosynthetic_activity", None)
    if photosynthetic_activity is not None and require_finite(
        photosynthetic_activity,
        field="photosynthetic_activity",
    ) < 0.0:
        raise OBTInputError("photosynthetic_activity must be non-negative")

    growth_stage = getattr(forcing, "growth_stage", None)
    if growth_stage is not None and (
        not isinstance(growth_stage, str) or not growth_stage.strip()
    ):
        raise OBTInputError("growth_stage must be a non-empty string when supplied")


__all__ = [
    "INTEGRATED_ACTIVITY_UNIT",
    "OBT_CONCENTRATION_UNIT",
    "OBT_INVENTORY_UNIT",
    "OBTInputError",
    "OBTParameterError",
    "OBTStateError",
    "OBTUnitError",
    "OBTValidationError",
    "PLANT_MASS_UNIT",
    "RATE_UNIT",
    "require_finite",
    "require_unit",
    "validate_biological_forcing",
    "validate_interval",
    "validate_multiplier",
    "validate_rate",
    "validate_state",
]
