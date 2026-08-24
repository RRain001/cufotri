"""Fail-closed applicability assessments for the V3 parameter evidence layer.

This module describes whether an evidence record can be transferred to a
specific V3 model component.  It does not resolve a value, perform a unit
conversion, or change the evidence lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from .evidence import ReviewStatus
from .validation import (
    ParameterSchemaError,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)


class ApplicabilityAssessmentStatus(str, Enum):
    """Frozen dispositions for a source-to-model applicability review."""

    DIRECT_MATCH = "DIRECT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    TRANSFER_REQUIRED = "TRANSFER_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


# This alias makes the vocabulary discoverable from the module while avoiding
# a collision with P7.6A's coordinate-level ApplicabilityStatus.
ApplicabilityStatus = ApplicabilityAssessmentStatus


_REQUIRED_FIELDS = (
    "parameter_id",
    "assessment_status",
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


@dataclass(frozen=True)
class ApplicabilityRecord:
    """One complete, immutable source-to-V3 applicability assessment.

    Unknown dimensions are represented by explicit non-empty tokens such as
    ``UNKNOWN`` or ``NOT_APPLICABLE``.  ``None`` is deliberately not accepted
    for required review coordinates, so an incomplete review cannot pass the
    matrix schema gate.
    """

    parameter_id: str
    assessment_status: ApplicabilityAssessmentStatus
    radionuclide: str
    chemical_form: str
    pathway: str
    model_component: str
    environment_type: str
    crop_type: str
    growth_stage: str
    soil_condition: str
    time_scale: str
    spatial_scale: str
    source_context: str
    model_equation_match: ApplicabilityAssessmentStatus
    unit_match: ApplicabilityAssessmentStatus
    uncertainty_available: bool
    review_notes: str
    reviewer_status: ReviewStatus

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        for field in (
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
            "review_notes",
        ):
            require_text(getattr(self, field), field=field)

        for field in ("assessment_status", "model_equation_match", "unit_match"):
            object.__setattr__(
                self,
                field,
                coerce_enum(
                    getattr(self, field),
                    ApplicabilityAssessmentStatus,
                    field=field,
                ),
            )
        object.__setattr__(
            self,
            "reviewer_status",
            coerce_enum(self.reviewer_status, ReviewStatus, field="reviewer_status"),
        )
        if not isinstance(self.uncertainty_available, bool):
            raise ParameterSchemaError("uncertainty_available must be a boolean")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ApplicabilityRecord":
        """Decode the strict record fields from a matrix row.

        The matrix example used by the project calls the assessment field
        ``applicability``.  Both that spelling and the canonical
        ``assessment_status`` spelling are accepted, but if both are supplied
        they must agree.
        """

        payload = dict(require_mapping(value, field="applicability_record"))
        if "assessment_status" not in payload and "applicability" in payload:
            payload["assessment_status"] = payload["applicability"]
        if "assessment_status" in payload and "applicability" in payload:
            assessment = coerce_enum(
                payload["assessment_status"],
                ApplicabilityAssessmentStatus,
                field="assessment_status",
            )
            alias = coerce_enum(
                payload["applicability"],
                ApplicabilityAssessmentStatus,
                field="applicability",
            )
            if assessment is not alias:
                raise ParameterSchemaError(
                    "assessment_status and applicability must agree"
                )
        missing = [field for field in _REQUIRED_FIELDS if field not in payload]
        if missing:
            raise ParameterSchemaError(
                "applicability_record missing required fields: "
                + ", ".join(missing)
            )
        try:
            return cls(**{field: payload[field] for field in _REQUIRED_FIELDS})
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid applicability record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        """Serialize the frozen assessment using both public status spellings."""

        result = {
            "parameter_id": self.parameter_id,
            "assessment_status": self.assessment_status.value,
            "applicability": self.assessment_status.value,
            "radionuclide": self.radionuclide,
            "chemical_form": self.chemical_form,
            "pathway": self.pathway,
            "model_component": self.model_component,
            "environment_type": self.environment_type,
            "crop_type": self.crop_type,
            "growth_stage": self.growth_stage,
            "soil_condition": self.soil_condition,
            "time_scale": self.time_scale,
            "spatial_scale": self.spatial_scale,
            "source_context": self.source_context,
            "model_equation_match": self.model_equation_match.value,
            "unit_match": self.unit_match.value,
            "uncertainty_available": self.uncertainty_available,
            "review_notes": self.review_notes,
            "reviewer_status": self.reviewer_status.value,
        }
        return result

    @property
    def equation_compatible(self) -> bool:
        """Whether the source equation is compatible enough for review.

        ``PARTIAL_MATCH`` means the equation role is identifiable but still
        requires validation; ``UNKNOWN`` and ``TRANSFER_REQUIRED`` are not
        equation-compatible at this stage.
        """

        return self.model_equation_match in {
            ApplicabilityAssessmentStatus.DIRECT_MATCH,
            ApplicabilityAssessmentStatus.PARTIAL_MATCH,
        }

    @property
    def unit_compatible(self) -> bool:
        """Whether the source unit is directly compatible with V3."""

        return self.unit_match is ApplicabilityAssessmentStatus.DIRECT_MATCH

    @property
    def is_validation_shape(self) -> bool:
        """Return the applicability-only portion of the P7.6B-2 rule."""

        if self.assessment_status is ApplicabilityAssessmentStatus.DIRECT_MATCH:
            return (
                self.model_equation_match
                is ApplicabilityAssessmentStatus.DIRECT_MATCH
                and self.unit_compatible
            )
        if self.assessment_status is ApplicabilityAssessmentStatus.PARTIAL_MATCH:
            return (
                self.uncertainty_available
                and self.equation_compatible
                and self.unit_compatible
            )
        return False


__all__ = [
    "ApplicabilityAssessmentStatus",
    "ApplicabilityRecord",
    "ApplicabilityStatus",
]
