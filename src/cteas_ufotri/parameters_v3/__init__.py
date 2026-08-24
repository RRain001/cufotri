"""P7.6A/P7.6B-2B parameter evidence, applicability, and candidate control plane.

This package is intentionally not imported by any V3 physics or pipeline
module. It records evidence, applicability, and candidate-gate state; it never
resolves a runtime parameter and never activates a solver value.
"""

from .applicability import (
    ApplicabilityAssessmentStatus,
    ApplicabilityRecord,
)
from .candidate import (
    CandidateDisposition,
    CandidateLifecycleStatus,
    CandidateScreeningDisposition,
    CandidateStatus,
    ParameterCandidateError,
    ParameterCandidateRecord,
    ParameterCandidateRegistry,
    ValidationPlan,
    build_candidate_registry,
    candidate_transition,
    construct_candidate_record,
    transition_candidate_status,
)
from .evidence import (
    Applicability,
    ApplicabilityStatus,
    EvidenceProvenance,
    EvidenceSourceMetadata,
    EvidenceStatus,
    GapCategory,
    ParameterClass,
    ParameterEvidenceRecord,
    ReviewStatus,
    SourceType,
    UNRESOLVED_SOURCE,
)
from .registry import ParameterEvidenceRegistry
from .review import (
    ParameterReviewEntry,
    ParameterReviewError,
    ParameterReviewMatrix,
    load_review_matrix,
)
from .validation_gate import (
    CandidateValidationGateResult,
    ValidationGateError,
    ValidationGateResult,
    can_enter_validation,
    evaluate_candidate_gate,
    evaluate_candidate_validation_gate,
    evaluate_validation_gate,
    is_validation_candidate,
)
from .validation import (
    ParameterEvidenceError,
    ParameterLifecycleError,
    ParameterRegistryError,
    ParameterSchemaError,
    lifecycle_transition,
    transition_status,
)

__all__ = [
    "Applicability",
    "ApplicabilityAssessmentStatus",
    "ApplicabilityStatus",
    "ApplicabilityRecord",
    "CandidateDisposition",
    "CandidateLifecycleStatus",
    "CandidateScreeningDisposition",
    "CandidateStatus",
    "CandidateValidationGateResult",
    "EvidenceProvenance",
    "EvidenceSourceMetadata",
    "EvidenceStatus",
    "GapCategory",
    "ParameterClass",
    "ParameterEvidenceError",
    "ParameterEvidenceRecord",
    "ParameterEvidenceRegistry",
    "ParameterCandidateError",
    "ParameterCandidateRecord",
    "ParameterCandidateRegistry",
    "ParameterLifecycleError",
    "ParameterRegistryError",
    "ParameterReviewEntry",
    "ParameterReviewError",
    "ParameterReviewMatrix",
    "ParameterSchemaError",
    "ReviewStatus",
    "SourceType",
    "UNRESOLVED_SOURCE",
    "ValidationPlan",
    "ValidationGateError",
    "ValidationGateResult",
    "build_candidate_registry",
    "can_enter_validation",
    "candidate_transition",
    "construct_candidate_record",
    "evaluate_candidate_gate",
    "evaluate_candidate_validation_gate",
    "evaluate_validation_gate",
    "is_validation_candidate",
    "load_review_matrix",
    "lifecycle_transition",
    "transition_candidate_status",
    "transition_status",
]
