"""Adapter for inspecting legacy YAML values without changing V2 behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .database import ParameterDatabase
from .registry import SourceRegistry
from .schema import (
    ParameterApplicability,
    ParameterBounds,
    ParameterEntry,
)


class LegacyParameterAdapter:
    """Expose numeric legacy mapping leaves through the new typed interface.

    This adapter is deliberately opt-in and has no call sites in the V2
    configuration or physics paths.  Exact-value bounds document that a
    migrated legacy value is a compatibility snapshot, not a newly inferred
    physical range.
    """

    def __init__(self, database: ParameterDatabase):
        self.database = database

    @classmethod
    def from_mapping(
        cls,
        legacy_mapping: Mapping[str, Any],
        *,
        source_registry: SourceRegistry,
        source: str = "CTEAS_DEFAULT",
        reference: str = "legacy YAML configuration snapshot",
    ) -> "LegacyParameterAdapter":
        entries: list[ParameterEntry] = []
        for name, raw_value in _numeric_leaves(legacy_mapping):
            value = float(raw_value)
            entries.append(
                ParameterEntry(
                    name=name,
                    value=value,
                    unit="legacy_unspecified",
                    category=name.split(".", 1)[0],
                    source=source,
                    reference=reference,
                    confidence="internal_default",
                    applicability=ParameterApplicability(
                        status="applicable",
                        scope="legacy configuration snapshot",
                    ),
                    transform="IDENTITY",
                    bounds=ParameterBounds(
                        lower=value,
                        upper=value,
                        lower_inclusive=True,
                        upper_inclusive=True,
                    ),
                )
            )
        return cls(
            ParameterDatabase.from_entries(
                entries,
                source_registry=source_registry,
            )
        )

    def get(self, name: str, *, production: bool = False) -> float:
        return self.database.get(name, production=production)

    def get_entry(self, name: str) -> ParameterEntry:
        return self.database.get_entry(name)

    def list_parameters(self) -> list[str]:
        return self.database.list_parameters()

    def hash(self) -> str:
        return self.database.hash()


def _numeric_leaves(
    mapping: Mapping[str, Any],
    prefix: str = "",
):
    for key, value in mapping.items():
        if not isinstance(key, str):
            raise ValueError("Legacy parameter keys must be strings")
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, Mapping):
            yield from _numeric_leaves(value, name)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            yield name, value
