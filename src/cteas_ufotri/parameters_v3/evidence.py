"""Immutable parameter evidence records and the frozen P7.6A vocabulary."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Mapping

from .validation import (
    ParameterSchemaError,
    coerce_enum,
    lifecycle_transition,
    require_identifier,
    require_mapping,
    require_text,
    require_unit,
    validate_scalar,
)


class ParameterClass(str, Enum):
    """Primary classification; each record has exactly one value."""

    PHYSICAL_CONSTANT = "PHYSICAL_CONSTANT"
    EMPIRICAL_MODEL_PARAMETER = "EMPIRICAL_MODEL_PARAMETER"
    BIOLOGICAL_PARAMETER = "BIOLOGICAL_PARAMETER"
    CROP_PARAMETER = "CROP_PARAMETER"
    SOIL_PARAMETER = "SOIL_PARAMETER"
    EXPOSURE_PARAMETER = "EXPOSURE_PARAMETER"
    DOSE_PARAMETER = "DOSE_PARAMETER"
    SCENARIO_INPUT = "SCENARIO_INPUT"
    NUMERICAL_CONTROL = "NUMERICAL_CONTROL"
    TEST_ONLY_PARAMETER = "TEST_ONLY_PARAMETER"


class EvidenceStatus(str, Enum):
    """Frozen parameter evidence lifecycle."""

    PROVISIONAL = "PROVISIONAL"
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class SourceType(str, Enum):
    """Allowed source categories for traceable evidence."""

    PRIMARY_LITERATURE = "PRIMARY_LITERATURE"
    SECONDARY_LITERATURE = "SECONDARY_LITERATURE"
    REGULATORY_STANDARD = "REGULATORY_STANDARD"
    INTERNATIONAL_DATABASE = "INTERNATIONAL_DATABASE"
    UFOTRI_DOCUMENTATION = "UFOTRI_DOCUMENTATION"
    UFOTRI_SOURCE_CODE = "UFOTRI_SOURCE_CODE"
    PROJECT_ASSUMPTION = "PROJECT_ASSUMPTION"
    PHYSICAL_CONSTANT_SOURCE = "PHYSICAL_CONSTANT_SOURCE"
    TEST_ONLY = "TEST_ONLY"


class ApplicabilityStatus(str, Enum):
    """Explicit applicability disposition."""

    APPLICABILITY_UNRESOLVED = "APPLICABILITY_UNRESOLVED"
    RESOLVED = "RESOLVED"
    TEST_ONLY_SCOPE = "TEST_ONLY_SCOPE"


class ReviewStatus(str, Enum):
    """Review state, separate from scientific evidence status."""

    PENDING_REVIEW = "PENDING_REVIEW"
    INTERNAL_REVIEWED = "INTERNAL_REVIEWED"
    INDEPENDENT_REVIEWED = "INDEPENDENT_REVIEWED"
    REJECTED = "REJECTED"


class GapCategory(str, Enum):
    """P7.6A parameter gap matrix categories."""

    EVIDENCE_SUFFICIENT_FOR_FUTURE_VALIDATION = "A"
    EVIDENCE_FOUND_APPLICABILITY_UNRESOLVED = "B"
    CONFLICTING_EVIDENCE = "C"
    NO_EVIDENCE = "D"
    SCENARIO_INPUT = "E"
    TEST_ONLY_PARAMETER = "F"


UNRESOLVED_SOURCE = "UNRESOLVED_SOURCE_REQUIRED"


@dataclass(frozen=True)
class Applicability:
    """Applicability coordinates; unknown dimensions remain explicit."""

    radionuclide: str | None = None
    chemical_form: str | None = None
    crop: str | None = None
    growth_stage: str | None = None
    soil_type: str | None = None
    environment: str | None = None
    pathway: str | None = None
    age_group: str | None = None
    status: ApplicabilityStatus = ApplicabilityStatus.APPLICABILITY_UNRESOLVED

    def __post_init__(self) -> None:
        status = coerce_enum(
            self.status,
            ApplicabilityStatus,
            field="applicability.status",
        )
        object.__setattr__(self, "status", status)
        for field in (
            "radionuclide",
            "chemical_form",
            "crop",
            "growth_stage",
            "soil_type",
            "environment",
            "pathway",
            "age_group",
        ):
            value = getattr(self, field)
            if value is not None:
                require_text(value, field=f"applicability.{field}")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Applicability":
        payload = dict(require_mapping(value, field="applicability"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(f"invalid applicability mapping: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            field: getattr(self, field)
            for field in (
                "radionuclide",
                "chemical_form",
                "crop",
                "growth_stage",
                "soil_type",
                "environment",
                "pathway",
                "age_group",
            )
        } | {"status": self.status.value}


@dataclass(frozen=True)
class EvidenceProvenance:
    """Traceability anchor for the evidence record itself."""

    repository: str
    revision: str
    file: str
    location: str

    def __post_init__(self) -> None:
        for field in ("repository", "revision", "file", "location"):
            require_text(getattr(self, field), field=f"provenance.{field}")
        if self.file.startswith("/"):
            raise ParameterSchemaError("provenance.file must be repository-relative")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceProvenance":
        try:
            return cls(**dict(require_mapping(value, field="provenance")))
        except TypeError as exc:
            raise ParameterSchemaError(f"invalid provenance mapping: {exc}") from exc

    def to_mapping(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "revision": self.revision,
            "file": self.file,
            "location": self.location,
        }


@dataclass(frozen=True)
class EvidenceSourceMetadata:
    """Bibliographic and unit-conversion metadata for recovered evidence.

    The metadata is deliberately kept in the control plane.  It describes the
    source quantity and its auditable normalization path; it is not a runtime
    parameter value and is never imported by a solver.
    """

    title: str
    authors: tuple[str, ...]
    year: int
    journal_or_publisher: str
    identifier: str
    locator: str
    stable_url: str
    reported_quantity: str
    reported_uncertainty: str
    conversion_path: str
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "title",
            "journal_or_publisher",
            "identifier",
            "locator",
            "stable_url",
            "reported_quantity",
            "reported_uncertainty",
            "conversion_path",
        ):
            require_text(getattr(self, field), field=f"source_metadata.{field}")
        if not isinstance(self.authors, (list, tuple)) or not self.authors:
            raise ParameterSchemaError(
                "source_metadata.authors must be a non-empty list or tuple"
            )
        authors = tuple(self.authors)
        for index, author in enumerate(authors):
            require_text(author, field=f"source_metadata.authors[{index}]")
        object.__setattr__(self, "authors", authors)
        if not isinstance(self.year, int) or isinstance(self.year, bool) or self.year <= 0:
            raise ParameterSchemaError("source_metadata.year must be a positive integer")
        if not self.stable_url.startswith(("http://", "https://")):
            raise ParameterSchemaError(
                "source_metadata.stable_url must be an HTTP(S) URL"
            )
        for field in ("volume", "issue", "pages"):
            value = getattr(self, field)
            if value is not None:
                require_text(value, field=f"source_metadata.{field}")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvidenceSourceMetadata":
        payload = dict(require_mapping(value, field="source_metadata"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid source metadata mapping: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "authors": list(self.authors),
            "year": self.year,
            "journal_or_publisher": self.journal_or_publisher,
            "identifier": self.identifier,
            "locator": self.locator,
            "stable_url": self.stable_url,
            "reported_quantity": self.reported_quantity,
            "reported_uncertainty": self.reported_uncertainty,
            "conversion_path": self.conversion_path,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
        }


def _derived_gap_category(
    parameter_class: ParameterClass,
    source_type: SourceType,
    source_identifier: str,
    applicability: Applicability,
    evidence_notes: str,
) -> GapCategory:
    if source_type is SourceType.TEST_ONLY:
        return GapCategory.TEST_ONLY_PARAMETER
    if parameter_class is ParameterClass.SCENARIO_INPUT:
        return GapCategory.SCENARIO_INPUT
    if "conflicting" in evidence_notes.lower():
        return GapCategory.CONFLICTING_EVIDENCE
    if source_identifier == UNRESOLVED_SOURCE:
        return GapCategory.NO_EVIDENCE
    if applicability.status is ApplicabilityStatus.APPLICABILITY_UNRESOLVED:
        return GapCategory.EVIDENCE_FOUND_APPLICABILITY_UNRESOLVED
    return GapCategory.EVIDENCE_SUFFICIENT_FOR_FUTURE_VALIDATION


@dataclass(frozen=True)
class ParameterEvidenceRecord:
    """One immutable, traceable parameter record."""

    parameter_id: str
    parameter_name: str
    subsystem: str
    parameter_class: ParameterClass
    symbol: str
    description: str
    canonical_unit: str
    status: EvidenceStatus
    source_type: SourceType
    source_identifier: str
    reported_value: Any
    reported_unit: str
    normalized_value: Any
    normalized_unit: str
    applicability: Applicability
    evidence_notes: str
    provenance: EvidenceProvenance
    review_status: ReviewStatus
    gap_category: GapCategory | None = None
    equation_role: str = "UNRESOLVED_EQUATION_ROLE"
    source_metadata: EvidenceSourceMetadata | None = None

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        require_text(self.parameter_name, field="parameter_name")
        require_identifier(self.subsystem, field="subsystem")
        require_text(self.symbol, field="symbol")
        require_text(self.description, field="description")
        require_unit(self.canonical_unit, field="canonical_unit")
        require_text(self.source_identifier, field="source_identifier")
        require_unit(self.reported_unit, field="reported_unit")
        require_unit(self.normalized_unit, field="normalized_unit")
        require_text(self.evidence_notes, field="evidence_notes")
        require_text(self.equation_role, field="equation_role")

        for field, enum_type in (
            ("parameter_class", ParameterClass),
            ("status", EvidenceStatus),
            ("source_type", SourceType),
            ("review_status", ReviewStatus),
        ):
            object.__setattr__(
                self,
                field,
                coerce_enum(getattr(self, field), enum_type, field=field),
            )

        if not isinstance(self.applicability, Applicability):
            object.__setattr__(
                self,
                "applicability",
                Applicability.from_mapping(self.applicability),
            )
        if not isinstance(self.provenance, EvidenceProvenance):
            object.__setattr__(
                self,
                "provenance",
                EvidenceProvenance.from_mapping(self.provenance),
            )
        if self.source_metadata is not None and not isinstance(
            self.source_metadata, EvidenceSourceMetadata
        ):
            object.__setattr__(
                self,
                "source_metadata",
                EvidenceSourceMetadata.from_mapping(self.source_metadata),
            )
        validate_scalar(self.reported_value, field="reported_value")
        validate_scalar(self.normalized_value, field="normalized_value")
        if self.normalized_value is not None and self.normalized_unit != self.canonical_unit:
            raise ParameterSchemaError(
                "normalized_unit must equal canonical_unit when normalized_value is present"
            )
        if self.source_type is SourceType.TEST_ONLY and (
            self.parameter_class is not ParameterClass.TEST_ONLY_PARAMETER
        ):
            raise ParameterSchemaError(
                "TEST_ONLY source_type requires TEST_ONLY_PARAMETER class"
            )
        if self.parameter_class is ParameterClass.TEST_ONLY_PARAMETER and (
            self.source_type is not SourceType.TEST_ONLY
        ):
            raise ParameterSchemaError(
                "TEST_ONLY_PARAMETER class requires TEST_ONLY source_type"
            )
        if (
            self.status is EvidenceStatus.EVIDENCE_FOUND
            and self.source_type is not SourceType.TEST_ONLY
        ):
            if self.source_identifier == UNRESOLVED_SOURCE:
                raise ParameterSchemaError(
                    "EVIDENCE_FOUND physical records require a resolved source_identifier"
                )
            if self.source_metadata is None:
                raise ParameterSchemaError(
                    "EVIDENCE_FOUND physical records require complete source_metadata"
                )
            if self.source_metadata.identifier != self.source_identifier:
                raise ParameterSchemaError(
                    "source_metadata.identifier must equal source_identifier"
                )
            if self.equation_role == "UNRESOLVED_EQUATION_ROLE":
                raise ParameterSchemaError(
                    "EVIDENCE_FOUND physical records require equation_role"
                )

        derived = _derived_gap_category(
            self.parameter_class,
            self.source_type,
            self.source_identifier,
            self.applicability,
            self.evidence_notes,
        )
        if self.gap_category is None:
            object.__setattr__(self, "gap_category", derived)
        else:
            gap = coerce_enum(self.gap_category, GapCategory, field="gap_category")
            if gap is not derived:
                raise ParameterSchemaError(
                    f"gap_category {gap.value!r} contradicts derived category {derived.value!r}"
                )
            object.__setattr__(self, "gap_category", gap)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterEvidenceRecord":
        payload = dict(require_mapping(value, field="parameter"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(f"invalid parameter evidence record: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "parameter_name": self.parameter_name,
            "subsystem": self.subsystem,
            "parameter_class": self.parameter_class.value,
            "symbol": self.symbol,
            "description": self.description,
            "canonical_unit": self.canonical_unit,
            "status": self.status.value,
            "source_type": self.source_type.value,
            "source_identifier": self.source_identifier,
            "reported_value": self.reported_value,
            "reported_unit": self.reported_unit,
            "normalized_value": self.normalized_value,
            "normalized_unit": self.normalized_unit,
            "applicability": self.applicability.to_mapping(),
            "evidence_notes": self.evidence_notes,
            "provenance": self.provenance.to_mapping(),
            "review_status": self.review_status.value,
            "gap_category": self.gap_category.value,
            "equation_role": self.equation_role,
            "source_metadata": (
                self.source_metadata.to_mapping()
                if self.source_metadata is not None
                else None
            ),
        }

    def transition_to(self, target: EvidenceStatus) -> "ParameterEvidenceRecord":
        """Return a new record after one legal adjacent lifecycle transition."""

        _, target_token = lifecycle_transition(self.status, target)
        return replace(self, status=EvidenceStatus(target_token))


__all__ = [
    "Applicability",
    "ApplicabilityStatus",
    "EvidenceProvenance",
    "EvidenceSourceMetadata",
    "EvidenceStatus",
    "GapCategory",
    "ParameterClass",
    "ParameterEvidenceRecord",
    "ReviewStatus",
    "SourceType",
    "UNRESOLVED_SOURCE",
]
