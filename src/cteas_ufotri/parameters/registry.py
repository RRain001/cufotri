"""Parameter-source registry used by the parameter database."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
import yaml

from .exceptions import ParameterSchemaError, ParameterSourceError


@dataclass(frozen=True)
class ParameterSource:
    """A declared provenance source; declaration is not validation approval."""

    identifier: str | None = None
    status: str = "declared"
    description: str = ""
    reference: str = ""
    production_allowed: bool = False
    source_id: str | None = None
    citation: str | None = None
    organization: str = "UNSPECIFIED"
    year: int | None = None
    document: str = "UNSPECIFIED"
    location: str = "UNSPECIFIED"
    accessibility: str = "UNSPECIFIED"
    _format: str = field(default="legacy", init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        migration = (
            self.source_id is not None
            or self.citation is not None
            or self.year is not None
            or self.organization != "UNSPECIFIED"
            or self.document != "UNSPECIFIED"
            or self.location != "UNSPECIFIED"
            or self.accessibility != "UNSPECIFIED"
        )
        identifier = self.source_id or self.identifier
        if not isinstance(identifier, str) or not identifier.strip():
            raise ParameterSourceError("Parameter source requires a source_id")
        if self.identifier is not None and self.identifier != identifier:
            raise ParameterSourceError("Source identifier and source_id must match")
        if not isinstance(self.status, str) or not self.status.strip():
            raise ParameterSourceError(f"Source {identifier!r} requires a status")
        if not isinstance(self.production_allowed, bool):
            raise ParameterSourceError(
                f"Source {identifier!r}.production_allowed must be boolean"
            )
        object.__setattr__(self, "identifier", identifier)
        object.__setattr__(self, "source_id", identifier)
        object.__setattr__(self, "citation", self.citation or self.reference)
        object.__setattr__(self, "_format", "migration" if migration else "legacy")

    def to_mapping(self) -> dict[str, Any]:
        if self._format == "migration":
            return {
                "source_id": self.source_id,
                "citation": self.citation,
                "organization": self.organization,
                "year": self.year,
                "document": self.document,
                "location": self.location,
                "accessibility": self.accessibility,
                "status": self.status,
                "production_allowed": self.production_allowed,
            }
        return {
            "status": self.status,
            "description": self.description,
            "reference": self.reference,
            "production_allowed": self.production_allowed,
        }


class SourceRegistry:
    """Immutable, fail-closed collection of known parameter sources."""

    def __init__(self, sources: Mapping[str, ParameterSource] | None = None):
        normalized = dict(sources or {})
        if set(normalized) != {source.identifier for source in normalized.values()}:
            raise ParameterSourceError("Source identifiers do not match registry keys")
        self._sources = normalized

    def register(self, source: ParameterSource) -> None:
        """Register one source, rejecting duplicate identifiers."""

        if not isinstance(source, ParameterSource):
            raise ParameterSourceError("Registry accepts ParameterSource instances")
        identifier = source.identifier
        if identifier in self._sources:
            raise ParameterSourceError(f"Duplicate parameter source: {identifier!r}")
        self._sources[identifier] = source

    add_source = register

    @classmethod
    def from_file(cls, path: str | Path) -> "SourceRegistry":
        source_path = Path(path)
        try:
            with source_path.open(encoding="utf-8") as stream:
                document = yaml.safe_load(stream)
        except (OSError, yaml.YAMLError) as exc:
            raise ParameterSchemaError(
                f"Unable to load parameter source registry {source_path}: {exc}"
            ) from exc
        return cls.from_mapping(document, source_path=source_path)

    @classmethod
    def from_mapping(
        cls,
        document: Mapping[str, Any],
        *,
        source_path: str | Path | None = None,
    ) -> "SourceRegistry":
        if not isinstance(document, Mapping):
            raise ParameterSchemaError("Parameter source registry must be a mapping")
        version = document.get("schema_version")
        schema_path = Path(__file__).resolve().parents[3] / "schemas" / (
            "parameter_sources_migration.schema.json"
            if version == "2.0"
            else "parameter_sources.schema.json"
        )
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ParameterSchemaError(
                f"Unable to load parameter source schema {schema_path}: {exc}"
            ) from exc
        errors = sorted(
            Draft202012Validator(schema).iter_errors(document),
            key=lambda error: list(error.path),
        )
        if errors:
            error = errors[0]
            location = ".".join(str(part) for part in error.path) or "document"
            raise ParameterSchemaError(
                f"Invalid parameter source registry at {location}: {error.message}"
            )
        if version not in {"1.0", "2.0"}:
            raise ParameterSchemaError(
                f"Unsupported parameter source schema version in {source_path or 'mapping'}"
            )
        raw_sources = document.get("sources")
        if not isinstance(raw_sources, Mapping) or not raw_sources:
            raise ParameterSourceError("Parameter source registry has no sources")

        sources: dict[str, ParameterSource] = {}
        for identifier, raw in raw_sources.items():
            if not isinstance(identifier, str) or not identifier:
                raise ParameterSourceError("Parameter source identifiers must be non-empty strings")
            if not isinstance(raw, Mapping):
                raise ParameterSourceError(f"Source {identifier!r} must be a mapping")
            if version == "2.0":
                source_id = raw.get("source_id", identifier)
                if source_id != identifier:
                    raise ParameterSourceError(
                        f"Source key {identifier!r} does not match source_id {source_id!r}"
                    )
                sources[identifier] = ParameterSource(
                    source_id=source_id,
                    citation=str(raw["citation"]),
                    organization=str(raw["organization"]),
                    year=raw["year"],
                    document=str(raw["document"]),
                    location=str(raw["location"]),
                    accessibility=str(raw["accessibility"]),
                    status=str(raw.get("status", "declared")),
                    production_allowed=bool(raw.get("production_allowed", False)),
                )
                continue
            required = ("status", "description", "reference", "production_allowed")
            missing = [field for field in required if field not in raw]
            if missing:
                raise ParameterSourceError(
                    f"Source {identifier!r} is missing fields: {', '.join(missing)}"
                )
            if not isinstance(raw["production_allowed"], bool):
                raise ParameterSourceError(
                    f"Source {identifier!r}.production_allowed must be boolean"
                )
            sources[identifier] = ParameterSource(
                identifier=identifier,
                status=str(raw["status"]),
                description=str(raw["description"]),
                reference=str(raw["reference"]),
                production_allowed=raw["production_allowed"],
            )
        return cls(sources)

    def get(self, identifier: str) -> ParameterSource:
        try:
            return self._sources[identifier]
        except KeyError as exc:
            raise ParameterSourceError(
                f"Unknown parameter source: {identifier!r}"
            ) from exc

    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._sources))

    def to_mapping(self) -> dict[str, Any]:
        migration = any(
            source.document != "UNSPECIFIED"
            or source.location != "UNSPECIFIED"
            or source.accessibility != "UNSPECIFIED"
            or source.year is not None
            or source.organization != "UNSPECIFIED"
            for source in self._sources.values()
        )
        return {
            "schema_version": "2.0" if migration else "1.0",
            "sources": {
                identifier: self._sources[identifier].to_mapping()
                for identifier in sorted(self._sources)
            },
        }


# P5.1 uses the descriptive name; retain SourceRegistry for P0 callers.
ParameterSourceRegistry = SourceRegistry
