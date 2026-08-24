"""P7.6A parameter evidence and provenance control plane.

This package is intentionally not imported by any V3 physics or pipeline
module. It records evidence and lifecycle state; it never resolves a runtime
parameter and never activates a solver value.
"""

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
    "ApplicabilityStatus",
    "EvidenceProvenance",
    "EvidenceStatus",
    "GapCategory",
    "ParameterClass",
    "ParameterEvidenceError",
    "ParameterEvidenceRecord",
    "ParameterEvidenceRegistry",
    "ParameterLifecycleError",
    "ParameterRegistryError",
    "ParameterSchemaError",
    "ReviewStatus",
    "SourceType",
    "UNRESOLVED_SOURCE",
    "lifecycle_transition",
    "transition_status",
]
