"""Provenance records and deterministic hashing for parameter packages."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value without nondeterministic whitespace."""

    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_json(value: Any) -> str:
    """Return the SHA-256 of the canonical JSON representation of ``value``."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ParameterProvenance:
    """The source-facing provenance attached to one parameter entry."""

    source: str
    source_status: str
    reference: str
    confidence: str
    applicability: Mapping[str, Any]
    production_allowed: bool
    status: str | None = None
    source_type: str | None = None
    module: str | None = None
    uncertainty: Any = None

    def to_mapping(self) -> dict[str, Any]:
        result = {
            "source": self.source,
            "source_status": self.source_status,
            "reference": self.reference,
            "confidence": self.confidence,
            "applicability": dict(self.applicability),
            "production_allowed": self.production_allowed,
        }
        if self.status is not None:
            result.update(
                {
                    "status": self.status,
                    "source_type": self.source_type,
                    "module": self.module,
                    "uncertainty": self.uncertainty,
                }
            )
        return result
