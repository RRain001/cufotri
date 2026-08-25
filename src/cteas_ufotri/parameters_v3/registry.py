"""Deterministic, non-runtime parameter evidence registry for P7.6A."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .evidence import (
    EvidenceStatus,
    GapCategory,
    ParameterClass,
    ParameterEvidenceRecord,
)
from .validation import (
    ParameterRegistryError,
    ParameterSchemaError,
    require_mapping,
    require_text,
    validate_stage_status,
)


@dataclass(frozen=True)
class ParameterEvidenceRegistry:
    """Sorted immutable records with a P7.6A activation gate."""

    records: tuple[ParameterEvidenceRecord, ...]
    stage: str = "P7.6A"
    schema_version: str = "v1"

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        require_text(self.schema_version, field="schema_version")
        records = tuple(self.records)
        if any(not isinstance(record, ParameterEvidenceRecord) for record in records):
            raise ParameterRegistryError("records must contain ParameterEvidenceRecord values")
        ordered = tuple(sorted(records, key=lambda record: record.parameter_id))
        ids = [record.parameter_id for record in ordered]
        duplicates = sorted(
            parameter_id
            for parameter_id, count in Counter(ids).items()
            if count > 1
        )
        if duplicates:
            raise ParameterRegistryError(
                f"duplicate parameter_id values: {', '.join(duplicates)}"
            )
        object.__setattr__(self, "records", ordered)
        self.validate_stage_safety()

    @classmethod
    def from_records(
        cls,
        records: Iterable[ParameterEvidenceRecord],
        *,
        stage: str = "P7.6A",
        schema_version: str = "v1",
    ) -> "ParameterEvidenceRegistry":
        return cls(tuple(records), stage=stage, schema_version=schema_version)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterEvidenceRegistry":
        payload = require_mapping(value, field="parameter_manifest")
        raw_records = payload.get("parameters")
        if not isinstance(raw_records, list):
            raise ParameterSchemaError("parameter_manifest.parameters must be a list")
        records = [ParameterEvidenceRecord.from_mapping(item) for item in raw_records]
        return cls.from_records(
            records,
            stage=str(payload.get("stage", "P7.6A")),
            schema_version=str(payload.get("schema_version", "v1")),
        )

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "ParameterEvidenceRegistry":
        """Load one explicit YAML manifest without importing model modules."""

        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - project dependency
            raise ParameterRegistryError("PyYAML is required to load a manifest") from exc
        manifest_path = Path(path)
        try:
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterRegistryError(f"cannot read manifest {manifest_path}") from exc
        return cls.from_mapping(payload)

    def validate_stage_safety(self) -> None:
        """Reject validated/active records at the P7.6A gate."""

        for record in self.records:
            validate_stage_status(record.status, field=f"{record.parameter_id}.status")

    def assert_no_activation(self) -> None:
        """Explicit gate used by tests and reports."""

        self.validate_stage_safety()
        forbidden = [
            record.parameter_id
            for record in self.records
            if record.status in {EvidenceStatus.VALIDATED, EvidenceStatus.ACTIVE}
        ]
        if forbidden:
            raise ParameterRegistryError(
                "P7.6A cannot activate or validate parameters: "
                + ", ".join(forbidden)
            )

    def get(self, parameter_id: str) -> ParameterEvidenceRecord:
        for record in self.records:
            if record.parameter_id == parameter_id:
                return record
        raise KeyError(parameter_id)

    def counts_by_class(self) -> dict[str, int]:
        counts = Counter(record.parameter_class.value for record in self.records)
        return {parameter_class.value: counts.get(parameter_class.value, 0) for parameter_class in ParameterClass}

    def counts_by_status(self) -> dict[str, int]:
        counts = Counter(record.status.value for record in self.records)
        return {status.value: counts.get(status.value, 0) for status in EvidenceStatus}

    def counts_by_gap(self) -> dict[str, int]:
        counts = Counter(record.gap_category.value for record in self.records)
        return {category.value: counts.get(category.value, 0) for category in GapCategory}

    def gap_matrix(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {
                "parameter_id": record.parameter_id,
                "category": record.gap_category.value,
                "status": record.status.value,
                "rationale": record.evidence_notes,
            }
            for record in self.records
        )

    def to_mapping(self) -> dict[str, Any]:
        self.assert_no_activation()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "parameters": [record.to_mapping() for record in self.records],
        }


__all__ = ["ParameterEvidenceRegistry"]
