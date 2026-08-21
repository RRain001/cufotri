"""V3 parameter database and P5.1 migration layer; not connected to V2 physics."""

from .database import ParameterDatabase
from .exceptions import (
    ParameterBoundsError,
    ParameterDatabaseError,
    ParameterNotFoundError,
    ParameterSchemaError,
    ParameterSourceError,
    ParameterUnavailableError,
    ParameterUseNotAllowedError,
    ParameterMigrationError,
    ParameterValidationError,
)
from .migration import (
    ParameterMigrationAudit,
    ParameterMigrationRecord,
    migration_audit_report,
    transition_parameter,
)
from .legacy import LegacyParameterAdapter
from .provenance import ParameterProvenance
from .registry import ParameterSource, ParameterSourceRegistry, SourceRegistry
from .schema import (
    ParameterApplicability,
    ParameterBounds,
    ParameterEntry,
    ParameterStatus,
    validate_parameter_document,
)
from .validation import MODULE_PARAMETER_PATHS, validate_parameter, validate_parameter_module_path

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
    "ParameterMigrationAudit",
    "ParameterMigrationError",
    "ParameterMigrationRecord",
    "ParameterSourceRegistry",
    "ParameterStatus",
    "ParameterValidationError",
    "MODULE_PARAMETER_PATHS",
    "SourceRegistry",
    "transition_parameter",
    "migration_audit_report",
    "validate_parameter",
    "validate_parameter_module_path",
    "validate_parameter_document",
]
