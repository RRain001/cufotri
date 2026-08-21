"""Fail-closed parameter database API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .exceptions import (
    ParameterDatabaseError,
    ParameterNotFoundError,
    ParameterUnavailableError,
    ParameterUseNotAllowedError,
)
from .provenance import ParameterProvenance, sha256_json
from .registry import SourceRegistry
from .schema import ParameterEntry, validate_parameter_document


class ParameterDatabase:
    """An immutable collection of typed parameters and source provenance.

    The database is intentionally independent of the V2 configuration loader
    and physics modules.  A missing or pending value is an error; no default,
    nearest match, or missing-to-zero repair is performed.
    """

    def __init__(
        self,
        entries: Mapping[str, ParameterEntry],
        source_registry: SourceRegistry,
    ) -> None:
        if not entries:
            raise ParameterDatabaseError("Parameter database must not be empty")
        self._entries = dict(entries)
        self._source_registry = source_registry
        validate_parameter_document(
            {
                "schema_version": "1.0",
                "parameters": [
                    self._entries[name].to_mapping()
                    for name in sorted(self._entries)
                ],
            }
        )
        self.validate()

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        sources_path: str | Path | None = None,
        schema_path: str | Path | None = None,
    ) -> "ParameterDatabase":
        parameter_path = Path(path)
        try:
            with parameter_path.open(encoding="utf-8") as stream:
                document = yaml.safe_load(stream)
        except (OSError, yaml.YAMLError) as exc:
            raise ParameterDatabaseError(
                f"Unable to load parameter database {parameter_path}: {exc}"
            ) from exc
        if sources_path is None:
            sources_path = parameter_path.parent.parent / "parameter_sources.yaml"
        source_registry = SourceRegistry.from_file(sources_path)
        return cls.from_mapping(
            document,
            source_registry=source_registry,
            schema_path=schema_path,
        )

    @classmethod
    def from_mapping(
        cls,
        document: Mapping[str, Any],
        *,
        source_registry: SourceRegistry,
        schema_path: str | Path | None = None,
    ) -> "ParameterDatabase":
        validate_parameter_document(document, schema_path=schema_path)
        raw_entries = document["parameters"]
        entries: dict[str, ParameterEntry] = {}
        for raw_entry in raw_entries:
            entry = ParameterEntry.from_mapping(raw_entry)
            if entry.name in entries:
                raise ParameterDatabaseError(f"Duplicate parameter name: {entry.name!r}")
            source_registry.get(entry.source)
            entries[entry.name] = entry
        return cls(entries, source_registry)

    @classmethod
    def from_entries(
        cls,
        entries: Iterable[ParameterEntry],
        *,
        source_registry: SourceRegistry,
    ) -> "ParameterDatabase":
        mapped: dict[str, ParameterEntry] = {}
        for entry in entries:
            if entry.name in mapped:
                raise ParameterDatabaseError(f"Duplicate parameter name: {entry.name!r}")
            mapped[entry.name] = entry
        return cls(mapped, source_registry)

    def get_entry(self, name: str) -> ParameterEntry:
        try:
            return self._entries[name]
        except KeyError as exc:
            raise ParameterNotFoundError(f"Unknown parameter: {name!r}") from exc

    def get(self, name: str, *, production: bool = False) -> float:
        """Return one numeric value, failing closed for placeholders.

        ``production=True`` additionally requires an explicitly validated
        source, applicable scope, and source-registry production permission.
        This flag is reserved for future physics integration and is not used
        by the current V2 runtime.
        """

        entry = self.get_entry(name)
        if entry.value is None:
            raise ParameterUnavailableError(
                f"Parameter {name!r} has no value: {entry.confidence}"
            )
        source = self._source_registry.get(entry.source)
        if production and (
            not source.production_allowed
            or source.status != "validated"
            or entry.confidence != "validated"
            or entry.applicability.status != "applicable"
        ):
            raise ParameterUseNotAllowedError(
                f"Parameter {name!r} is not approved for production use"
            )
        return entry.value

    def list_parameters(self) -> list[str]:
        """Return parameter names in deterministic order."""

        return sorted(self._entries)

    def get_provenance(self, name: str) -> ParameterProvenance:
        entry = self.get_entry(name)
        source = self._source_registry.get(entry.source)
        return ParameterProvenance(
            source=entry.source,
            source_status=source.status,
            reference=entry.reference,
            confidence=entry.confidence,
            applicability=entry.applicability.to_mapping(),
            production_allowed=source.production_allowed,
        )

    def validate(self) -> None:
        """Recheck names, provenance, values, and bounds without repair."""

        for name, entry in self._entries.items():
            if name != entry.name:
                raise ParameterDatabaseError(
                    f"Parameter registry key does not match entry name: {name!r}"
                )
            self._source_registry.get(entry.source)
            if entry.value is not None and entry.bounds is not None:
                if not entry.bounds.contains(entry.value):
                    raise ParameterDatabaseError(
                        f"Parameter {name!r} value is outside its bounds"
                    )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "parameters": [
                self._entries[name].to_mapping() for name in self.list_parameters()
            ],
        }

    def package_mapping(self) -> dict[str, Any]:
        """Return the canonical parameter-plus-source package for hashing."""

        return {
            "parameter_database": self.to_mapping(),
            "parameter_sources": self._source_registry.to_mapping(),
        }

    def hash(self) -> str:
        """Return a deterministic SHA-256 package hash."""

        return sha256_json(self.package_mapping())
