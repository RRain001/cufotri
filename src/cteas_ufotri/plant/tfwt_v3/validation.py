"""Fail-closed validation for the V3 TFWT storage-only pathway."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any

from ..leaf_exchange_resistance.validation import validate_provenance


TFWT_CONCENTRATION_UNIT = "Bq kg^-1 water"
TFWT_INVENTORY_UNIT = "Bq m^-2"
WATER_CONTENT_UNIT = "kg water m^-2"
FLUX_UNIT = "Bq m^-2 s^-1"
INTEGRATED_FLUX_UNIT = "Bq m^-2"


class TFWTValidationError(ValueError):
    """Base error for invalid V3 TFWT state or storage terms."""


class TFWTStateError(TFWTValidationError):
    """A TFWT state is malformed or internally inconsistent."""


class TFWTFluxError(TFWTValidationError):
    """A flux or storage term is malformed."""


class TFWTUnitError(TFWTValidationError):
    """A value is not expressed in the frozen TFWT unit."""


def require_finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TFWTValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise TFWTValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    if actual != expected:
        raise TFWTUnitError(
            f"{field} requires unit {expected!r}; received {actual!r}"
        )


def validate_state(state: Any) -> None:
    """Validate identifiers, units, UTC time, inventory, and concentration."""

    for field in ("plant_identifier", "crop", "growth_stage", "area_basis"):
        value = getattr(state, field, None)
        if not isinstance(value, str) or not value.strip():
            raise TFWTStateError(f"{field} is required")
    require_unit(
        state.concentration_unit,
        TFWT_CONCENTRATION_UNIT,
        field="tfwt_concentration",
    )
    require_unit(
        state.inventory_unit,
        TFWT_INVENTORY_UNIT,
        field="tfwt_inventory",
    )
    require_unit(
        state.water_content_unit,
        WATER_CONTENT_UNIT,
        field="water_content",
    )
    timestamp = getattr(state, "time", None)
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise TFWTStateError("time must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise TFWTStateError("time must use UTC")
    concentration = require_finite(
        state.tfwt_concentration_bq_kg_water,
        field="tfwt_concentration_bq_kg_water",
    )
    inventory = require_finite(
        state.tfwt_inventory_bq_m2,
        field="tfwt_inventory_bq_m2",
    )
    water_content = require_finite(
        state.water_content_kg_m2,
        field="water_content_kg_m2",
    )
    if concentration < 0.0 or inventory < 0.0:
        raise TFWTStateError("TFWT concentration and inventory must be non-negative")
    if water_content <= 0.0:
        raise TFWTStateError("water_content_kg_m2 must be strictly positive")
    expected_inventory = concentration * water_content
    if not math.isclose(
        inventory,
        expected_inventory,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise TFWTStateError(
            "tfwt_inventory_bq_m2 must equal concentration times water content"
        )
    validate_provenance(state.provenance)


def validate_interval(interval_seconds: Any) -> float:
    interval = require_finite(interval_seconds, field="interval_seconds")
    if interval <= 0.0:
        raise TFWTFluxError("interval_seconds must be strictly positive")
    return interval


def validate_nonnegative_flux(value: Any, *, field: str) -> float:
    result = require_finite(value, field=field)
    if result < 0.0:
        raise TFWTFluxError(f"{field} must be non-negative")
    return result


def validate_leaf_exchange_flux(flux: Any) -> float:
    """Consume only the existing signed LeafExchangeFlux field."""

    if not hasattr(flux, "air_to_leaf_flux_bq_m2_s"):
        raise TFWTFluxError("leaf_exchange_flux must be a LeafExchangeFlux")
    require_unit(flux.flux_unit, FLUX_UNIT, field="leaf_exchange_flux")
    return require_finite(
        flux.air_to_leaf_flux_bq_m2_s,
        field="leaf_exchange_flux.air_to_leaf_flux_bq_m2_s",
    )


def validate_root_uptake_flux(root_flux: Any) -> float:
    """Consume only the public non-negative RootFlux value."""

    if not hasattr(root_flux, "uptake_flux_bq_m2_s"):
        raise TFWTFluxError("root_uptake_flux must be a RootFlux")
    require_unit(root_flux.flux_unit, FLUX_UNIT, field="root_uptake_flux")
    value = require_finite(
        root_flux.uptake_flux_bq_m2_s,
        field="root_uptake_flux.uptake_flux_bq_m2_s",
    )
    if value < 0.0:
        raise TFWTFluxError("root uptake flux must be non-negative")
    return value
