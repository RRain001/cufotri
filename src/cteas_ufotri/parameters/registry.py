"""Parameter-source registry used by the parameter database."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator
import yaml

from .exceptions import ParameterSchemaError, ParameterSourceError


@dataclass(frozen=True)
class ParameterSource:
    """A declared provenance source; declaration is not validation approval."""

    identifier: str
    status: str
    description: str
    reference: str
    production_allowed: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "description": self.description,
            "reference": self.reference,
            "production_allowed": self.production_allowed,
        }


class SourceRegistry:
    """Immutable, fail-closed collection of known parameter sources."""

    def __init__(self, sources: Mapping[str, ParameterSource]):
        if not sources:
            raise ParameterSourceError("Parameter source registry must not be empty")
        normalized = dict(sources)
        if set(normalized) != {source.identifier for source in normalized.values()}:
            raise ParameterSourceError("Source identifiers do not match registry keys")
        self._sources = normalized

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
        schema_path = (
            Path(__file__).resolve().parents[3]
            / "schemas"
            / "parameter_sources.schema.json"
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
        if document.get("schema_version") != "1.0":
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
        return {
            "schema_version": "1.0",
            "sources": {
                identifier: self._sources[identifier].to_mapping()
                for identifier in sorted(self._sources)
            },
        }
