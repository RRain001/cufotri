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
from .migration import (
    ParameterMigrationAudit,
    ParameterMigrationRecord,
    migration_audit_report,
    transition_parameter,
)
from .provenance import ParameterProvenance, sha256_json
from .registry import SourceRegistry
from .schema import ParameterEntry, validate_parameter_document
from .validation import validate_parameter


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
        migration_records: Iterable[ParameterMigrationRecord] = (),
    ) -> None:
        if not entries:
            raise ParameterDatabaseError("Parameter database must not be empty")
        self._entries = dict(entries)
        self._source_registry = source_registry
        self._migration_audit = ParameterMigrationAudit(migration_records)
        schema_version = "2.0" if any(
            entry._format == "migration" for entry in self._entries.values()
        ) else "1.0"
        document: dict[str, Any] = {
            "schema_version": schema_version,
            "parameters": [
                self._entries[name].to_mapping()
                for name in sorted(self._entries)
            ],
        }
        if schema_version == "2.0":
            document["migration_records"] = self._migration_audit.to_mapping()
        validate_parameter_document(
            document
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
        records = tuple(
            ParameterMigrationRecord.from_mapping(raw_record)
            for raw_record in document.get("migration_records", [])
        )
        return cls(entries, source_registry, migration_records=records)

    @classmethod
    def from_entries(
        cls,
        entries: Iterable[ParameterEntry],
        *,
        source_registry: SourceRegistry,
        migration_records: Iterable[ParameterMigrationRecord] = (),
    ) -> "ParameterDatabase":
        mapped: dict[str, ParameterEntry] = {}
        for entry in entries:
            if entry.name in mapped:
                raise ParameterDatabaseError(f"Duplicate parameter name: {entry.name!r}")
            mapped[entry.name] = entry
        return cls(mapped, source_registry, migration_records=migration_records)

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
        production_blocked = (
            not source.production_allowed
            or source.status != "validated"
            or entry.confidence != "validated"
            or entry.applicability.status != "applicable"
        )
        if entry._format == "migration":
            production_blocked = production_blocked or entry.status != "ACTIVE"
        if production and production_blocked:
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
            status=entry.status,
            source_type=entry.source_type,
            module=entry.module,
            uncertainty=entry.uncertainty,
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
            if entry._format == "migration":
                validate_parameter(entry, source_registry=self._source_registry)

        if any(entry._format == "migration" for entry in self._entries.values()):
            for record in self._migration_audit.records:
                if record.parameter_id not in self._entries:
                    raise ParameterDatabaseError(
                        f"Migration record references unknown parameter: {record.parameter_id!r}"
                    )
            for name, entry in self._entries.items():
                if entry.status == "ACTIVE" and not self._migration_audit.has_activation_record(name):
                    raise ParameterDatabaseError(
                        f"ACTIVE parameter {name!r} requires an activation migration record"
                    )

    def validate_parameter(self, name: str) -> None:
        """Validate one P5.1 entry against this database's source registry."""

        entry = self.get_entry(name)
        validate_parameter(entry, source_registry=self._source_registry)

    def to_mapping(self) -> dict[str, Any]:
        version = "2.0" if any(
            entry._format == "migration" for entry in self._entries.values()
        ) else "1.0"
        result: dict[str, Any] = {
            "schema_version": version,
            "parameters": [
                self._entries[name].to_mapping() for name in self.list_parameters()
            ],
        }
        if version == "2.0":
            result["migration_records"] = self._migration_audit.to_mapping()
        return result

    def package_mapping(self) -> dict[str, Any]:
        """Return the canonical parameter-plus-source package for hashing."""

        return {
            "parameter_database": self.to_mapping(),
            "parameter_sources": self._source_registry.to_mapping(),
            "migration_audit": self._migration_audit.to_mapping(),
        }

    def hash(self) -> str:
        """Return a deterministic SHA-256 package hash."""

        return sha256_json(self.package_mapping())

    @property
    def migration_records(self) -> tuple[ParameterMigrationRecord, ...]:
        """Return immutable audit records in declared order."""

        return self._migration_audit.records

    def migration_audit_report(self) -> dict[str, object]:
        """Return a deterministic report without activating or changing values."""

        return migration_audit_report(self._entries.values(), self._migration_audit)

    def transition(
        self,
        parameter_id: str,
        new_status: str,
        *,
        changed_by: str,
        reason: str,
        timestamp: Any = None,
    ) -> "ParameterDatabase":
        """Return a database with one auditable lifecycle transition applied."""

        entry = self.get_entry(parameter_id)
        updated, record = transition_parameter(
            entry,
            new_status,
            changed_by=changed_by,
            reason=reason,
            timestamp=timestamp,
        )
        entries = dict(self._entries)
        entries[parameter_id] = updated
        return ParameterDatabase(
            entries,
            self._source_registry,
            migration_records=(*self._migration_audit.records, record),
        )
