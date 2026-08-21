"""V3-P0 parameter database layer; not connected to V2 physics."""

from .database import ParameterDatabase
from .exceptions import (
    ParameterBoundsError,
    ParameterDatabaseError,
    ParameterNotFoundError,
    ParameterSchemaError,
    ParameterSourceError,
    ParameterUnavailableError,
    ParameterUseNotAllowedError,
)
from .legacy import LegacyParameterAdapter
from .provenance import ParameterProvenance
from .registry import ParameterSource, SourceRegistry
from .schema import (
    ParameterApplicability,
    ParameterBounds,
    ParameterEntry,
    validate_parameter_document,
)

__all__ = [
    "LegacyParameterAdapter",
    "ParameterApplicability",
    "ParameterBounds",
    "ParameterBoundsError",
    "ParameterDatabase",
    "ParameterDatabaseError",
    "ParameterEntry",
    "ParameterNotFoundError",
    "ParameterProvenance",
    "ParameterSchemaError",
    "ParameterSource",
    "ParameterSourceError",
    "ParameterUnavailableError",
    "ParameterUseNotAllowedError",
    "SourceRegistry",
    "validate_parameter_document",
]
