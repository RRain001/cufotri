"""Fail-closed validation-candidate gate for P7.6B-1.

The gate identifies records that may be considered by the later validation
protocol.  It does not validate, calibrate, activate, or expose a runtime
parameter lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .applicability import ApplicabilityAssessmentStatus, ApplicabilityRecord
from .evidence import EvidenceStatus, ParameterClass, ParameterEvidenceRecord, SourceType
from .registry import ParameterEvidenceRegistry
from .review import ParameterReviewMatrix
from .validation import ParameterRegistryError, require_text


class ValidationGateError(ParameterRegistryError):
    """A validation-candidate gate input violates a fail-closed rule."""


def is_validation_candidate(
    evidence: ParameterEvidenceRecord,
    applicability: ApplicabilityRecord,
) -> bool:
    """Return whether one record may be handed to P7.6B-2 design.

    ``DIRECT_MATCH`` requires direct equation and unit matches.  A
    ``PARTIAL_MATCH`` additionally requires an explicit uncertainty record.
    Evidence must be found but not validated/active, and test-only fixtures
    can never enter the physical validation candidate set.
    """

    if evidence.status is not EvidenceStatus.EVIDENCE_FOUND:
        return False
    if evidence.source_type is SourceType.TEST_ONLY:
        return False
    if evidence.parameter_class is ParameterClass.TEST_ONLY_PARAMETER:
        return False
    return applicability.is_validation_shape


@dataclass(frozen=True)
class ValidationGateResult:
    """Auditable result of candidate identification, never an activation."""

    candidate_ids: tuple[str, ...]
    blocked_reasons: tuple[tuple[str, str], ...]
    stage: str = "P7.6B-1"
    calibration_started: bool = False
    active_database: bool = False

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        if not isinstance(self.calibration_started, bool):
            raise ValidationGateError("calibration_started must be a boolean")
        if not isinstance(self.active_database, bool):
            raise ValidationGateError("active_database must be a boolean")
        if self.calibration_started or self.active_database:
            raise ValidationGateError(
                "P7.6B-1 cannot start calibration or activate a database"
            )
        candidate_ids = tuple(sorted(set(self.candidate_ids)))
        blocked_reasons = tuple(sorted(self.blocked_reasons, key=lambda item: item[0]))
        if any(not isinstance(parameter_id, str) for parameter_id in candidate_ids):
            raise ValidationGateError("candidate_ids must contain strings")
        if any(
            not isinstance(parameter_id, str) or not isinstance(reason, str)
            for parameter_id, reason in blocked_reasons
        ):
            raise ValidationGateError("blocked_reasons must contain string pairs")
        object.__setattr__(self, "candidate_ids", candidate_ids)
        object.__setattr__(self, "blocked_reasons", blocked_reasons)

    @property
    def validation_candidates_identified(self) -> bool:
        """The candidate set is identified even when it is empty."""

        return True

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_ids)

    def assert_safe(self) -> None:
        if self.calibration_started or self.active_database:
            raise ValidationGateError("unsafe P7.6B-1 gate state")

    def to_mapping(self) -> dict[str, Any]:
        self.assert_safe()
        return {
            "stage": self.stage,
            "validation_candidates_identified": self.validation_candidates_identified,
            "candidate_count": self.candidate_count,
            "candidate_ids": list(self.candidate_ids),
            "blocked_reasons": [
                {"parameter_id": parameter_id, "reason": reason}
                for parameter_id, reason in self.blocked_reasons
            ],
            "calibration_started": self.calibration_started,
            "active_database": self.active_database,
        }


def evaluate_validation_gate(
    inventory: ParameterEvidenceRegistry,
    matrix: ParameterReviewMatrix,
) -> ValidationGateResult:
    """Evaluate every reviewed parameter without changing any source record."""

    matrix.validate_against_inventory(inventory)
    candidates: list[str] = []
    blocked: list[tuple[str, str]] = []
    for entry in matrix.entries:
        evidence = inventory.get(entry.parameter_id)
        if is_validation_candidate(evidence, entry.applicability):
            candidates.append(entry.parameter_id)
            continue
        if evidence.status is not EvidenceStatus.EVIDENCE_FOUND:
            reason = f"evidence_status={evidence.status.value} is not EVIDENCE_FOUND"
        elif evidence.source_type is SourceType.TEST_ONLY:
            reason = "TEST_ONLY evidence is software-fixture scope, not physical validation"
        elif entry.applicability.assessment_status is ApplicabilityAssessmentStatus.UNKNOWN:
            reason = "applicability is UNKNOWN"
        elif entry.applicability.assessment_status is ApplicabilityAssessmentStatus.NOT_APPLICABLE:
            reason = "record is not a literature-derived model parameter"
        elif entry.applicability.assessment_status is ApplicabilityAssessmentStatus.TRANSFER_REQUIRED:
            reason = "transfer assumptions are unresolved"
        elif entry.applicability.assessment_status is ApplicabilityAssessmentStatus.PARTIAL_MATCH:
            reason = "PARTIAL_MATCH has no resolved uncertainty or unit/equation match"
        else:
            reason = "applicability shape is not eligible"
        blocked.append((entry.parameter_id, reason))
    return ValidationGateResult(
        candidate_ids=tuple(candidates),
        blocked_reasons=tuple(blocked),
    )


__all__ = [
    "ValidationGateError",
    "ValidationGateResult",
    "evaluate_validation_gate",
    "is_validation_candidate",
]
