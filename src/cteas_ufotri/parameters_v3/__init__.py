"""P7.6A/P7.6B-1 parameter evidence and applicability control plane.

This package is intentionally not imported by any V3 physics or pipeline
module. It records evidence, applicability, and candidate-gate state; it
never resolves a runtime parameter and never activates a solver value.
"""

from .applicability import (
    ApplicabilityAssessmentStatus,
    ApplicabilityRecord,
)
from .evidence import (
    Applicability,
    ApplicabilityStatus,
    EvidenceProvenance,
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
    ValidationGateError,
    ValidationGateResult,
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
    "EvidenceProvenance",
    "EvidenceStatus",
    "GapCategory",
    "ParameterClass",
    "ParameterEvidenceError",
    "ParameterEvidenceRecord",
    "ParameterEvidenceRegistry",
    "ParameterLifecycleError",
    "ParameterRegistryError",
    "ParameterReviewEntry",
    "ParameterReviewError",
    "ParameterReviewMatrix",
    "ParameterSchemaError",
    "ReviewStatus",
    "SourceType",
    "UNRESOLVED_SOURCE",
    "ValidationGateError",
    "ValidationGateResult",
    "evaluate_validation_gate",
    "is_validation_candidate",
    "load_review_matrix",
    "lifecycle_transition",
    "transition_status",
]
