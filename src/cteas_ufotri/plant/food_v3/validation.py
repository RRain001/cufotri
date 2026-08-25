"""Fail-closed validation for the isolated V3 P6.5 food-transfer boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
import re
from typing import Any


FOOD_INVENTORY_UNIT = "Bq"
HARVEST_FRACTION_UNIT = "1"
HARVEST_AREA_UNIT = "m^2"
INTEGRATED_ACTIVITY_UNIT = "Bq"


class FoodValidationError(ValueError):
    """Base error for invalid P6.5 food-transfer records."""


class FoodStateError(FoodValidationError):
    """A harvest or food inventory state is malformed."""


class FoodInputError(FoodValidationError):
    """A plant-state input violates the public food boundary."""


class FoodParameterError(FoodValidationError):
    """A harvest parameter is missing or invalid."""


class FoodUnitError(FoodValidationError):
    """A value is not expressed in the frozen P6.5 unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without accepting strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FoodValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise FoodValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise FoodUnitError(
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
            raise FoodStateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise FoodStateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise FoodStateError("provenance.temporal_resolution_s must be positive")


def validate_fraction(value: Any, *, field: str, error_type: type[Exception]) -> float:
    """Validate a dimensionless transfer fraction in [0, 1]."""

    fraction = require_finite(value, field=field)
    if not 0.0 <= fraction <= 1.0:
        raise error_type(f"{field} must be within [0, 1]")
    return fraction


def validate_harvest_state(state: Any) -> None:
    """Validate the immutable harvest transfer state."""

    for field in (
        "plant_identifier",
        "crop_identifier",
        "growth_stage",
        "food_product_identifier",
    ):
        value = getattr(state, field, None)
        if not isinstance(value, str) or not value.strip():
            raise FoodStateError(f"{field} is required")

    require_unit(
        state.inventory_unit,
        FOOD_INVENTORY_UNIT,
        field="harvest_inventory",
    )
    require_unit(
        state.harvest_fraction_unit,
        HARVEST_FRACTION_UNIT,
        field="harvest_fraction",
    )
    timestamp = getattr(state, "timestamp", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise FoodStateError("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise FoodStateError("timestamp must use UTC")

    inventory = require_finite(
        state.harvest_inventory_bq,
        field="harvest_inventory_bq",
    )
    if inventory < 0.0:
        raise FoodStateError("harvest_inventory_bq must be non-negative")
    validate_fraction(
        state.harvest_fraction,
        field="harvest_fraction",
        error_type=FoodStateError,
    )
    validate_provenance(state.provenance)


def validate_food_inventory(state: Any) -> None:
    """Validate total and component food-product activity inventories."""

    value = getattr(state, "food_product_identifier", None)
    if not isinstance(value, str) or not value.strip():
        raise FoodStateError("food_product_identifier is required")
    require_unit(state.inventory_unit, FOOD_INVENTORY_UNIT, field="food_inventory")
    timestamp = getattr(state, "timestamp", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise FoodStateError("timestamp must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise FoodStateError("timestamp must use UTC")
    total = require_finite(state.food_inventory_bq, field="food_inventory_bq")
    obt = require_finite(state.obt_inventory_bq, field="obt_inventory_bq")
    tfwt = require_finite(state.tfwt_inventory_bq, field="tfwt_inventory_bq")
    if total < 0.0 or obt < 0.0 or tfwt < 0.0:
        raise FoodStateError("food inventories must be non-negative")
    if not math.isclose(total, obt + tfwt, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise FoodStateError(
            "food_inventory_bq must equal OBT plus TFWT food inventories"
        )
    validate_provenance(state.provenance)


def validate_harvest_parameters(parameters: Any) -> None:
    """Validate explicit provisional harvest-transfer parameters."""

    for field in (
        "plant_identifier",
        "crop_identifier",
        "growth_stage",
        "food_product_identifier",
    ):
        value = getattr(parameters, field, None)
        if not isinstance(value, str) or not value.strip():
            raise FoodParameterError(f"{field} is required")
    require_unit(
        parameters.harvest_fraction_unit,
        HARVEST_FRACTION_UNIT,
        field="harvest_fraction",
    )
    require_unit(
        parameters.harvest_area_unit,
        HARVEST_AREA_UNIT,
        field="harvest_area",
    )
    validate_fraction(
        parameters.harvest_fraction,
        field="harvest_fraction",
        error_type=FoodParameterError,
    )
    if parameters.tfwt_harvest_fraction is not None:
        validate_fraction(
            parameters.tfwt_harvest_fraction,
            field="tfwt_harvest_fraction",
            error_type=FoodParameterError,
        )
    area = require_finite(
        parameters.harvest_area_m2,
        field="harvest_area_m2",
    )
    if area <= 0.0:
        raise FoodParameterError("harvest_area_m2 must be strictly positive")
    if parameters.parameter_status != "provisional":
        raise FoodParameterError(
            "P6.5 harvest-transfer parameters must remain provisional"
        )
    validate_provenance(parameters.provenance)
