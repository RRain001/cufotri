"""Fail-closed validation for the isolated V3 P6.6B dose boundary."""

from __future__ import annotations

import math
import re
from typing import Any

from ..intake_v3.validation import validate_identifier, validate_utc_timestamp


ANNUAL_TIME_PERIOD = "annual"
COMMITTED_DOSE_UNIT = "Sv"
DOSE_COEFFICIENT_UNIT = "Sv/Bq"
INTAKE_INVENTORY_UNIT = "Bq"


class DoseValidationError(ValueError):
    """Base error for invalid P6.6B dose records."""


class DoseStateError(DoseValidationError):
    """A calculated dose state is malformed."""


class DoseInputError(DoseValidationError):
    """An intake input violates the dose boundary."""


class DoseParameterError(DoseValidationError):
    """A dose parameter is missing or invalid."""


class DoseUnitError(DoseValidationError):
    """A value is not expressed in the frozen P6.6B unit."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite real number without accepting strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DoseValidationError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise DoseValidationError(f"{field} must be finite")
    return result


def require_unit(actual: str, expected: str, *, field: str) -> None:
    """Require an exact unit token; no implicit conversion is performed."""

    if actual != expected:
        raise DoseUnitError(
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
            raise DoseStateError(f"provenance.{field} is required")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", provenance.artifact_sha256):
        raise DoseStateError("provenance.artifact_sha256 must be SHA-256")
    resolution = require_finite(
        provenance.temporal_resolution_s,
        field="provenance.temporal_resolution_s",
    )
    if resolution <= 0.0:
        raise DoseStateError(
            "provenance.temporal_resolution_s must be positive"
        )




def validate_dose_state(state: Any) -> None:
    """Validate an immutable annual committed-dose result."""

    for field in (
        "consumer_identifier",
        "age_group_identifier",
        "pathway_identifier",
    ):
        validate_identifier(
            getattr(state, field, None),
            field=field,
            error_type=DoseStateError,
        )
    require_unit(
        state.intake_inventory_unit,
        INTAKE_INVENTORY_UNIT,
        field="intake_inventory",
    )
    require_unit(
        state.dose_coefficient_unit,
        DOSE_COEFFICIENT_UNIT,
        field="dose_coefficient",
    )
    require_unit(
        state.committed_dose_unit,
        COMMITTED_DOSE_UNIT,
        field="committed_dose",
    )
    if state.time_period != ANNUAL_TIME_PERIOD:
        raise DoseStateError(
            f"time_period must be {ANNUAL_TIME_PERIOD!r}"
        )
    intake = require_finite(
        state.intake_inventory_bq,
        field="intake_inventory_bq",
    )
    coefficient = require_finite(
        state.dose_coefficient,
        field="dose_coefficient",
    )
    committed = require_finite(
        state.committed_dose_sv,
        field="committed_dose_sv",
    )
    if intake < 0.0:
        raise DoseStateError("intake_inventory_bq must be non-negative")
    if coefficient < 0.0:
        raise DoseStateError("dose_coefficient must be non-negative")
    if committed < 0.0:
        raise DoseStateError("committed_dose_sv must be non-negative")
    if not math.isclose(
        committed,
        intake * coefficient,
        rel_tol=1.0e-12,
        abs_tol=1.0e-18,
    ):
        raise DoseStateError(
            "committed_dose_sv must equal intake inventory times coefficient"
        )
    validate_utc_timestamp(state.timestamp, error_type=DoseStateError)
    validate_provenance(state.provenance)


def validate_dose_parameters(parameters: Any) -> None:
    """Validate explicit provisional dose-coefficient parameters."""

    for field in (
        "age_group_identifier",
        "radionuclide_identifier",
        "pathway_identifier",
    ):
        validate_identifier(
            getattr(parameters, field, None),
            field=field,
            error_type=DoseParameterError,
        )
    require_unit(
        parameters.dose_coefficient_unit,
        DOSE_COEFFICIENT_UNIT,
        field="dose_coefficient",
    )
    coefficient = require_finite(
        parameters.dose_coefficient,
        field="dose_coefficient",
    )
    if coefficient < 0.0:
        raise DoseParameterError("dose_coefficient must be non-negative")
    if parameters.parameter_status != "provisional":
        raise DoseParameterError(
            "P6.6B dose parameters must remain provisional"
        )
    validate_provenance(parameters.provenance)


__all__ = [
    "ANNUAL_TIME_PERIOD",
    "COMMITTED_DOSE_UNIT",
    "DOSE_COEFFICIENT_UNIT",
    "INTAKE_INVENTORY_UNIT",
    "DoseInputError",
    "DoseParameterError",
    "DoseStateError",
    "DoseUnitError",
    "DoseValidationError",
    "require_finite",
    "require_unit",
    "validate_dose_parameters",
    "validate_dose_state",
    "validate_provenance",
]
