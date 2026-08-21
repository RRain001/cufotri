"""Exceptions raised by the fail-closed parameter database layer."""

from __future__ import annotations


class ParameterDatabaseError(ValueError):
    """Base class for invalid or unusable parameter database content."""


class ParameterSchemaError(ParameterDatabaseError):
    """The parameter document does not satisfy its versioned schema."""


class ParameterNotFoundError(ParameterDatabaseError):
    """A requested parameter name is not present in the database."""


class ParameterSourceError(ParameterDatabaseError):
    """A parameter source is missing, unknown, or internally inconsistent."""


class ParameterBoundsError(ParameterDatabaseError):
    """A parameter bound is malformed or does not contain its value."""


class ParameterUnavailableError(ParameterDatabaseError):
    """A parameter is declared but has no usable value."""


class ParameterUseNotAllowedError(ParameterDatabaseError):
    """A parameter cannot be used in the requested production context."""
