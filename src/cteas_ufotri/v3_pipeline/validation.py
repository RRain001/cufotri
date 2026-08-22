"""Fail-closed validation for the V3 P7.5 orchestration boundary."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Any

from ..coupling.atmos_v3 import AtmosphericForcingMetadata, AtmosphericHTOForcing
from ..plant.food_v3 import HarvestParameters
from ..plant.leaf_exchange_resistance import ResistanceState
from ..plant.obt_v3 import OBTParameters, PlantBiologicalForcing
from ..plant.root_v3 import RootParameters
from ..plant.soil_v3 import SoilParameters
from ..exposure.dose_v3 import DoseParameters
from ..exposure.intake_v3 import ConsumptionParameters


class V3PipelineValidationError(ValueError):
    """Base error for invalid P7.5 pipeline inputs or state."""


class PipelineInputError(V3PipelineValidationError):
    """A forcing, initial state, or explicit pipeline parameter is invalid."""


class PipelineStateError(V3PipelineValidationError):
    """A pipeline state violates its cross-module consistency contract."""


class PipelineSerializationError(V3PipelineValidationError):
    """A serialized pipeline state cannot be decoded safely."""


def require_finite(value: Any, *, field: str) -> float:
    """Return a finite numeric value without accepting strings or booleans."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PipelineInputError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise PipelineInputError(f"{field} must be finite")
    return result


def require_identifier(value: Any, *, field: str) -> str:
    """Require a non-empty stable identifier."""

    if not isinstance(value, str) or not value.strip():
        raise PipelineInputError(f"{field} is required")
    return value


def validate_utc_timestamp(
    timestamp: Any,
    *,
    field: str,
    error_type: type[V3PipelineValidationError] = PipelineInputError,
) -> None:
    """Require a timezone-aware UTC timestamp."""

    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise error_type(f"{field} must be timezone-aware UTC")
    if timestamp.utcoffset() != timedelta(0):
        raise error_type(f"{field} must use UTC")


def validate_forcing(forcing: Any) -> None:
    """Require the complete P7 atmospheric forcing contract."""

    if not isinstance(forcing, AtmosphericHTOForcing):
        raise PipelineInputError(
            "atmospheric_forcing must be the P7 AtmosphericHTOForcing"
        )
    if not isinstance(forcing.metadata, AtmosphericForcingMetadata):
        raise PipelineInputError(
            "atmospheric_forcing.metadata is required for the pipeline"
        )


def validate_parameters(parameters: Any) -> None:
    """Validate the explicit orchestration configuration by type and value."""

    if not isinstance(parameters.resistance, ResistanceState):
        raise PipelineInputError("resistance must be a ResistanceState")
    if not isinstance(parameters.soil_parameters, SoilParameters):
        raise PipelineInputError(
            "soil_parameters must be SoilParameters"
        )
    if not isinstance(parameters.root_parameters, RootParameters):
        raise PipelineInputError(
            "root_parameters must be RootParameters"
        )
    if not isinstance(parameters.obt_parameters, OBTParameters):
        raise PipelineInputError(
            "obt_parameters must be OBTParameters"
        )
    if not isinstance(parameters.biological_forcing, PlantBiologicalForcing):
        raise PipelineInputError(
            "biological_forcing must be PlantBiologicalForcing"
        )
    if not isinstance(parameters.harvest_parameters, HarvestParameters):
        raise PipelineInputError(
            "harvest_parameters must be HarvestParameters"
        )
    if not isinstance(parameters.consumption_parameters, ConsumptionParameters):
        raise PipelineInputError(
            "consumption_parameters must be ConsumptionParameters"
        )
    if not isinstance(parameters.dose_parameters, DoseParameters):
        raise PipelineInputError(
            "dose_parameters must be DoseParameters"
        )

    interval = require_finite(
        parameters.interval_seconds,
        field="interval_seconds",
    )
    if interval <= 0.0:
        raise PipelineInputError("interval_seconds must be strictly positive")
    equilibrium = require_finite(
        parameters.equilibrium_air_concentration_bq_m3,
        field="equilibrium_air_concentration_bq_m3",
    )
    if equilibrium < 0.0:
        raise PipelineInputError(
            "equilibrium_air_concentration_bq_m3 must be non-negative"
        )
    require_identifier(
        parameters.root_zone_identifier,
        field="root_zone_identifier",
    )
    require_identifier(
        parameters.consumer_identifier,
        field="consumer_identifier",
    )


def validate_initial_state(
    forcing: AtmosphericHTOForcing,
    soil_state: Any,
    tfwt_state: Any,
    obt_state: Any,
) -> None:
    """Validate the three initial public states before one pipeline step."""

    from ..plant.obt_v3 import OBTState
    from ..plant.soil_v3 import SoilState
    from ..plant.tfwt_v3 import TFWTState

    validate_forcing(forcing)
    if not isinstance(soil_state, SoilState):
        raise PipelineInputError("soil_state must be a V3 SoilState")
    if not isinstance(tfwt_state, TFWTState):
        raise PipelineInputError("tfwt_state must be a V3 TFWTState")
    if not isinstance(obt_state, OBTState):
        raise PipelineInputError("obt_state must be a V3 OBTState")

    validate_utc_timestamp(
        forcing.timestamp,
        field="atmospheric_forcing.timestamp",
    )
    validate_utc_timestamp(
        soil_state.timestamp,
        field="soil_state.timestamp",
    )
    validate_utc_timestamp(
        tfwt_state.time,
        field="tfwt_state.time",
    )
    validate_utc_timestamp(
        obt_state.timestamp,
        field="obt_state.timestamp",
    )
    if not (
        soil_state.timestamp
        == tfwt_state.time
        == obt_state.timestamp
        == forcing.timestamp
    ):
        raise PipelineInputError(
            "forcing, soil, TFWT, and OBT timestamps must share the step start"
        )
    if not (
        soil_state.soil_identifier
        and tfwt_state.plant_identifier
        and obt_state.plant_identifier
    ):
        raise PipelineInputError("initial state identifiers are required")
    if tfwt_state.plant_identifier != obt_state.plant_identifier:
        raise PipelineInputError(
            "TFWT and OBT plant identifiers must match"
        )


def validate_restart_timestamp(
    forcing: AtmosphericHTOForcing,
    state_timestamp: datetime,
) -> None:
    """Require a restart forcing to begin at the stored state timestamp."""

    validate_forcing(forcing)
    validate_utc_timestamp(
        state_timestamp,
        field="simulation_state.timestamp",
        error_type=PipelineStateError,
    )
    if forcing.timestamp != state_timestamp:
        raise PipelineInputError(
            "restart forcing.timestamp must equal simulation_state.timestamp"
        )


__all__ = [
    "PipelineInputError",
    "PipelineSerializationError",
    "PipelineStateError",
    "V3PipelineValidationError",
    "require_finite",
    "require_identifier",
    "validate_forcing",
    "validate_initial_state",
    "validate_parameters",
    "validate_restart_timestamp",
    "validate_utc_timestamp",
]
