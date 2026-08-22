"""Deterministic parameter applicability review matrix for P7.6B-1."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .applicability import ApplicabilityRecord, ApplicabilityAssessmentStatus
from .evidence import EvidenceStatus, ParameterClass, SourceType
from .registry import ParameterEvidenceRegistry
from .validation import (
    ParameterRegistryError,
    ParameterSchemaError,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)


class ParameterReviewError(ParameterRegistryError):
    """A review matrix is incomplete or inconsistent with the inventory."""


@dataclass(frozen=True)
class ParameterReviewEntry:
    """One inventory record plus its applicability assessment."""

    parameter_id: str
    evidence_status: EvidenceStatus
    parameter_class: ParameterClass
    source_type: SourceType
    canonical_unit: str
    applicability: ApplicabilityRecord
    required_action: str
    validation_candidate: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        for field, enum_type in (
            ("evidence_status", EvidenceStatus),
            ("parameter_class", ParameterClass),
            ("source_type", SourceType),
        ):
            object.__setattr__(
                self,
                field,
                coerce_enum(getattr(self, field), enum_type, field=field),
            )
        require_text(self.canonical_unit, field="canonical_unit")
        if not isinstance(self.applicability, ApplicabilityRecord):
            object.__setattr__(
                self,
                "applicability",
                ApplicabilityRecord.from_mapping(self.applicability),
            )
        if self.applicability.parameter_id != self.parameter_id:
            raise ParameterReviewError(
                "applicability parameter_id does not match review entry"
            )
        require_text(self.required_action, field="required_action")
        if not isinstance(self.validation_candidate, bool):
            raise ParameterSchemaError("validation_candidate must be a boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterReviewEntry":
        payload = dict(require_mapping(value, field="parameter_review"))
        nested = payload.get("applicability_record")
        if nested is None:
            nested = payload.get("applicability_assessment")
        if nested is None:
            app_fields = {
                field: payload[field]
                for field in (
                    "parameter_id",
                    "assessment_status",
                    "applicability",
                    "radionuclide",
                    "chemical_form",
                    "pathway",
                    "model_component",
                    "environment_type",
                    "crop_type",
                    "growth_stage",
                    "soil_condition",
                    "time_scale",
                    "spatial_scale",
                    "source_context",
                    "model_equation_match",
                    "unit_match",
                    "uncertainty_available",
                    "review_notes",
                    "reviewer_status",
                )
                if field in payload
            }
        else:
            app_fields = dict(require_mapping(nested, field="applicability_record"))
        if "parameter_id" not in app_fields:
            app_fields["parameter_id"] = payload.get("parameter_id")
        try:
            applicability = ApplicabilityRecord.from_mapping(app_fields)
            return cls(
                parameter_id=payload["parameter_id"],
                evidence_status=payload["evidence_status"],
                parameter_class=payload["parameter_class"],
                source_type=payload["source_type"],
                canonical_unit=payload["canonical_unit"],
                applicability=applicability,
                required_action=payload["required_action"],
                validation_candidate=payload.get("validation_candidate", False),
            )
        except KeyError as exc:
            raise ParameterSchemaError(
                f"parameter_review missing required field: {exc.args[0]}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        result = {
            "parameter_id": self.parameter_id,
            "evidence_status": self.evidence_status.value,
            "parameter_class": self.parameter_class.value,
            "source_type": self.source_type.value,
            "canonical_unit": self.canonical_unit,
            "required_action": self.required_action,
            "validation_candidate": self.validation_candidate,
        }
        result.update(self.applicability.to_mapping())
        return result


@dataclass(frozen=True)
class ParameterReviewMatrix:
    """Complete, sorted one-to-one review matrix for the P7.6A inventory."""

    entries: tuple[ParameterReviewEntry, ...]
    stage: str = "P7.6B-1"
    schema_version: str = "v1"

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        require_text(self.schema_version, field="schema_version")
        entries = tuple(self.entries)
        if any(not isinstance(entry, ParameterReviewEntry) for entry in entries):
            raise ParameterReviewError(
                "entries must contain ParameterReviewEntry values"
            )
        entries = tuple(sorted(entries, key=lambda entry: entry.parameter_id))
        ids = [entry.parameter_id for entry in entries]
        duplicates = sorted(
            parameter_id
            for parameter_id, count in Counter(ids).items()
            if count > 1
        )
        if duplicates:
            raise ParameterReviewError(
                "duplicate applicability parameter_id values: "
                + ", ".join(duplicates)
            )
        object.__setattr__(self, "entries", entries)

    @classmethod
    def from_entries(
        cls,
        entries: Iterable[ParameterReviewEntry],
        *,
        stage: str = "P7.6B-1",
        schema_version: str = "v1",
    ) -> "ParameterReviewMatrix":
        return cls(tuple(entries), stage=stage, schema_version=schema_version)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterReviewMatrix":
        payload = require_mapping(value, field="parameter_review_matrix")
        raw_entries = payload.get("parameters", payload.get("reviews"))
        if not isinstance(raw_entries, list):
            raise ParameterSchemaError(
                "parameter_review_matrix.parameters must be a list"
            )
        matrix = cls.from_entries(
            (ParameterReviewEntry.from_mapping(item) for item in raw_entries),
            stage=str(payload.get("stage", "P7.6B-1")),
            schema_version=str(payload.get("schema_version", "v1")),
        )
        declared_count = payload.get("reviewed_parameter_count")
        if declared_count is not None and declared_count != len(matrix.entries):
            raise ParameterReviewError(
                "reviewed_parameter_count disagrees with matrix entries"
            )
        declared_candidates = payload.get("candidate_count")
        if declared_candidates is not None and declared_candidates != matrix.candidate_count:
            raise ParameterReviewError(
                "candidate_count disagrees with matrix entries"
            )
        for field in ("calibration_started", "active_database"):
            value = payload.get(field, False)
            if not isinstance(value, bool):
                raise ParameterSchemaError(f"{field} must be a boolean")
            if value:
                raise ParameterReviewError(
                    f"{field}=true is forbidden during P7.6B-1"
                )
        if payload.get("validation_candidates_identified", True) is not True:
            raise ParameterReviewError(
                "validation_candidates_identified must remain true"
            )
        return matrix

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "ParameterReviewMatrix":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - project dependency
            raise ParameterReviewError("PyYAML is required to load a review matrix") from exc
        matrix_path = Path(path)
        try:
            payload = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterReviewError(f"cannot read review matrix {matrix_path}") from exc
        return cls.from_mapping(payload)

    def get(self, parameter_id: str) -> ParameterReviewEntry:
        for entry in self.entries:
            if entry.parameter_id == parameter_id:
                return entry
        raise KeyError(parameter_id)

    def validate_against_inventory(
        self, inventory: ParameterEvidenceRegistry
    ) -> None:
        """Require exact coverage and preserve inventory metadata."""

        inventory_ids = {record.parameter_id for record in inventory.records}
        review_ids = {entry.parameter_id for entry in self.entries}
        missing = sorted(inventory_ids - review_ids)
        extra = sorted(review_ids - inventory_ids)
        if missing or extra:
            details = []
            if missing:
                details.append("missing=" + ",".join(missing))
            if extra:
                details.append("extra=" + ",".join(extra))
            raise ParameterReviewError(
                "applicability matrix does not exactly cover inventory: "
                + "; ".join(details)
            )
        for entry in self.entries:
            source = inventory.get(entry.parameter_id)
            if entry.evidence_status is not source.status:
                raise ParameterReviewError(
                    f"{entry.parameter_id}: evidence_status disagrees with inventory"
                )
            if entry.parameter_class is not source.parameter_class:
                raise ParameterReviewError(
                    f"{entry.parameter_id}: parameter_class disagrees with inventory"
                )
            if entry.source_type is not source.source_type:
                raise ParameterReviewError(
                    f"{entry.parameter_id}: source_type disagrees with inventory"
                )
            if entry.canonical_unit != source.canonical_unit:
                raise ParameterReviewError(
                    f"{entry.parameter_id}: canonical_unit disagrees with inventory"
                )

    def counts_by_assessment(self) -> dict[str, int]:
        counts = Counter(
            entry.applicability.assessment_status.value for entry in self.entries
        )
        return {
            status.value: counts.get(status.value, 0)
            for status in ApplicabilityAssessmentStatus
        }

    def counts_by_class(self) -> dict[str, int]:
        counts = Counter(entry.parameter_class.value for entry in self.entries)
        return {
            parameter_class.value: counts.get(parameter_class.value, 0)
            for parameter_class in ParameterClass
        }

    @property
    def validation_candidate_ids(self) -> tuple[str, ...]:
        return tuple(
            entry.parameter_id
            for entry in self.entries
            if entry.validation_candidate
        )

    @property
    def candidate_count(self) -> int:
        return len(self.validation_candidate_ids)

    @property
    def validation_candidates_identified(self) -> bool:
        """The matrix identifies a candidate set even when it is empty."""

        return True

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "reviewed_parameter_count": len(self.entries),
            "validation_candidates_identified": self.validation_candidates_identified,
            "candidate_count": self.candidate_count,
            "calibration_started": False,
            "active_database": False,
            "parameters": [entry.to_mapping() for entry in self.entries],
        }


def load_review_matrix(
    matrix_path: str | Path,
    inventory: ParameterEvidenceRegistry,
) -> ParameterReviewMatrix:
    """Load and validate one matrix against the frozen P7.6A inventory."""

    matrix = ParameterReviewMatrix.from_yaml_file(matrix_path)
    matrix.validate_against_inventory(inventory)
    return matrix


__all__ = [
    "ParameterReviewEntry",
    "ParameterReviewError",
    "ParameterReviewMatrix",
    "load_review_matrix",
]
