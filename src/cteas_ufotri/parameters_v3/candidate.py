"""V3 parameter-candidate construction and registry for P7.6B-2A.

The candidate layer is a preparation control plane.  It records which
parameter records may be handed to a future validation protocol, but it never
resolves a value, validates a parameter, activates a database, or exposes a
solver lookup.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .applicability import ApplicabilityAssessmentStatus
from .evidence import (
    EvidenceProvenance,
    EvidenceStatus,
    ParameterClass,
    ParameterEvidenceRecord,
    ReviewStatus,
    SourceType,
    UNRESOLVED_SOURCE,
)
from .registry import ParameterEvidenceRegistry
from .review import ParameterReviewEntry, ParameterReviewMatrix
from .validation import (
    ParameterLifecycleError,
    ParameterRegistryError,
    ParameterSchemaError,
    coerce_enum,
    require_identifier,
    require_mapping,
    require_text,
)


class CandidateStatus(str, Enum):
    """Candidate-preparation lifecycle layered after P7.6A evidence."""

    PROVISIONAL = "PROVISIONAL"
    EVIDENCE_FOUND = "EVIDENCE_FOUND"
    APPLICABILITY_REVIEWED = "APPLICABILITY_REVIEWED"
    VALIDATION_CANDIDATE = "VALIDATION_CANDIDATE"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class CandidateScreeningDisposition(str, Enum):
    """P7.6B-2A screening outcome for every reviewed inventory record."""

    CANDIDATE = "CANDIDATE"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


class ValidationPlan(str, Enum):
    """Allowed future validation-plan descriptors; none executes here."""

    LITERATURE_COMPARISON = "LITERATURE_COMPARISON"
    BENCHMARK_CASE = "BENCHMARK_CASE"
    SENSITIVITY_ANALYSIS = "SENSITIVITY_ANALYSIS"
    EXPERIMENTAL_DATA_REQUIRED = "EXPERIMENTAL_DATA_REQUIRED"
    UFOTRI_REFERENCE_COMPARISON = "UFOTRI_REFERENCE_COMPARISON"


# Discoverable aliases for callers that use the shorter vocabulary.
CandidateDisposition = CandidateScreeningDisposition
CandidateLifecycleStatus = CandidateStatus


_CANDIDATE_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROVISIONAL": frozenset({"PROVISIONAL", "EVIDENCE_FOUND", "REJECTED"}),
    "EVIDENCE_FOUND": frozenset({"EVIDENCE_FOUND", "APPLICABILITY_REVIEWED", "REJECTED"}),
    "APPLICABILITY_REVIEWED": frozenset({"APPLICABILITY_REVIEWED", "VALIDATION_CANDIDATE", "REJECTED"}),
    "VALIDATION_CANDIDATE": frozenset({"VALIDATION_CANDIDATE", "VALIDATED", "REJECTED"}),
    "VALIDATED": frozenset({"VALIDATED", "ACTIVE", "REJECTED"}),
    "ACTIVE": frozenset({"ACTIVE"}),
    "REJECTED": frozenset({"REJECTED"}),
}


def candidate_transition(current: Any, target: Any) -> tuple[str, str]:
    """Validate one adjacent candidate lifecycle transition."""

    current_token = getattr(current, "value", current)
    target_token = getattr(target, "value", target)
    if not isinstance(current_token, str) or not current_token.strip():
        raise ParameterLifecycleError("current_candidate_status must be non-empty")
    if not isinstance(target_token, str) or not target_token.strip():
        raise ParameterLifecycleError("target_candidate_status must be non-empty")
    current_token = current_token.upper()
    target_token = target_token.upper()
    if current_token not in _CANDIDATE_TRANSITIONS:
        raise ParameterLifecycleError(
            f"unknown current candidate status {current_token!r}"
        )
    if target_token not in _CANDIDATE_TRANSITIONS[current_token]:
        raise ParameterLifecycleError(
            f"candidate transition {current_token} -> {target_token} is not allowed"
        )
    return current_token, target_token


transition_candidate_status = candidate_transition


class ParameterCandidateError(ParameterRegistryError):
    """A candidate record or registry violates the P7.6B-2A contract."""


def _coerce_string_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ParameterSchemaError(f"{field} must be a list or tuple")
    result = tuple(value)
    for index, item in enumerate(result):
        require_text(item, field=f"{field}[{index}]")
        if item == UNRESOLVED_SOURCE:
            raise ParameterSchemaError(
                f"{field}[{index}] cannot be {UNRESOLVED_SOURCE!r}; use an empty list"
            )
    return result


@dataclass(frozen=True)
class ParameterCandidateRecord:
    """One immutable candidate-preparation record."""

    parameter_id: str
    parameter_name: str
    subsystem: str
    parameter_class: ParameterClass
    evidence_ids: tuple[str, ...]
    applicability_status: ApplicabilityAssessmentStatus
    candidate_status: CandidateStatus
    candidate_reason: str
    validation_required: bool
    validation_plan: tuple[ValidationPlan, ...]
    uncertainty_source: str
    review_notes: str
    provenance: EvidenceProvenance
    candidate_screening: CandidateScreeningDisposition | None = None
    priority_tier: int | None = None

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        require_text(self.parameter_name, field="parameter_name")
        require_identifier(self.subsystem, field="subsystem")
        for field, enum_type in (
            ("parameter_class", ParameterClass),
            ("applicability_status", ApplicabilityAssessmentStatus),
            ("candidate_status", CandidateStatus),
        ):
            object.__setattr__(
                self,
                field,
                coerce_enum(getattr(self, field), enum_type, field=field),
            )
        object.__setattr__(
            self,
            "evidence_ids",
            _coerce_string_tuple(self.evidence_ids, field="evidence_ids"),
        )
        object.__setattr__(
            self,
            "validation_plan",
            tuple(
                coerce_enum(item, ValidationPlan, field="validation_plan")
                for item in _coerce_string_tuple(
                    self.validation_plan, field="validation_plan"
                )
            ),
        )
        if not isinstance(self.validation_required, bool):
            raise ParameterSchemaError("validation_required must be a boolean")
        require_text(self.candidate_reason, field="candidate_reason")
        require_text(self.uncertainty_source, field="uncertainty_source")
        require_text(self.review_notes, field="review_notes")
        if not isinstance(self.provenance, EvidenceProvenance):
            object.__setattr__(
                self,
                "provenance",
                EvidenceProvenance.from_mapping(self.provenance),
            )
        screening = self.candidate_screening
        if screening is None:
            inferred = (
                CandidateScreeningDisposition.CANDIDATE
                if self.candidate_status
                in {
                    CandidateStatus.VALIDATION_CANDIDATE,
                    CandidateStatus.VALIDATED,
                    CandidateStatus.ACTIVE,
                }
                else CandidateScreeningDisposition.REJECTED
                if self.candidate_status is CandidateStatus.REJECTED
                else CandidateScreeningDisposition.DEFERRED
            )
            screening = inferred
        else:
            screening = coerce_enum(
                screening,
                CandidateScreeningDisposition,
                field="candidate_screening",
            )
        object.__setattr__(self, "candidate_screening", screening)
        if self.priority_tier is not None and self.priority_tier not in {1, 2, 3}:
            raise ParameterSchemaError("priority_tier must be 1, 2, 3, or null")

        if self.candidate_status is CandidateStatus.VALIDATION_CANDIDATE:
            if screening is not CandidateScreeningDisposition.CANDIDATE:
                raise ParameterCandidateError(
                    "VALIDATION_CANDIDATE requires candidate screening disposition"
                )
            if not self.validation_required:
                raise ParameterCandidateError(
                    "VALIDATION_CANDIDATE requires validation_required=true"
                )
            if self.applicability_status in {
                ApplicabilityAssessmentStatus.UNKNOWN,
                ApplicabilityAssessmentStatus.NOT_APPLICABLE,
            }:
                raise ParameterCandidateError(
                    "unknown or not-applicable records cannot be candidates"
                )
            if not self.evidence_ids:
                raise ParameterCandidateError(
                    "VALIDATION_CANDIDATE requires at least one evidence_id"
                )
            if not self.validation_plan:
                raise ParameterCandidateError(
                    "VALIDATION_CANDIDATE requires a validation plan"
                )
        if self.candidate_status is CandidateStatus.PROVISIONAL and (
            screening is not CandidateScreeningDisposition.DEFERRED
        ):
            raise ParameterCandidateError("PROVISIONAL records must be deferred")
        if self.candidate_status is CandidateStatus.REJECTED and (
            screening is not CandidateScreeningDisposition.REJECTED
        ):
            raise ParameterCandidateError("REJECTED records must be rejected in screening")
        if screening is CandidateScreeningDisposition.REJECTED and self.validation_required:
            raise ParameterCandidateError(
                "rejected records cannot require validation in this stage"
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterCandidateRecord":
        payload = dict(require_mapping(value, field="parameter_candidate"))
        required = (
            "parameter_id",
            "parameter_name",
            "subsystem",
            "parameter_class",
            "evidence_ids",
            "applicability_status",
            "candidate_status",
            "candidate_reason",
            "validation_required",
            "validation_plan",
            "uncertainty_source",
            "review_notes",
            "provenance",
        )
        missing = [field for field in required if field not in payload]
        if missing:
            raise ParameterSchemaError(
                "parameter_candidate missing required fields: " + ", ".join(missing)
            )
        try:
            return cls(
                parameter_id=payload["parameter_id"],
                parameter_name=payload["parameter_name"],
                subsystem=payload["subsystem"],
                parameter_class=payload["parameter_class"],
                evidence_ids=payload["evidence_ids"],
                applicability_status=payload["applicability_status"],
                candidate_status=payload["candidate_status"],
                candidate_reason=payload["candidate_reason"],
                validation_required=payload["validation_required"],
                validation_plan=payload["validation_plan"],
                uncertainty_source=payload["uncertainty_source"],
                review_notes=payload["review_notes"],
                provenance=payload["provenance"],
                candidate_screening=payload.get("candidate_screening"),
                priority_tier=payload.get("priority_tier"),
            )
        except TypeError as exc:
            raise ParameterSchemaError(f"invalid parameter candidate: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "parameter_name": self.parameter_name,
            "subsystem": self.subsystem,
            "parameter_class": self.parameter_class.value,
            "evidence_ids": list(self.evidence_ids),
            "applicability_status": self.applicability_status.value,
            "candidate_status": self.candidate_status.value,
            "candidate_screening": self.candidate_screening.value,
            "candidate_reason": self.candidate_reason,
            "validation_required": self.validation_required,
            "validation_plan": [item.value for item in self.validation_plan],
            "uncertainty_source": self.uncertainty_source,
            "review_notes": self.review_notes,
            "priority_tier": self.priority_tier,
            "provenance": self.provenance.to_mapping(),
        }

    @property
    def can_enter_validation(self) -> bool:
        """Return whether a later validation protocol may admit this record."""

        return (
            self.candidate_status is CandidateStatus.VALIDATION_CANDIDATE
            and self.candidate_screening is CandidateScreeningDisposition.CANDIDATE
            and self.validation_required
            and bool(self.evidence_ids)
            and self.applicability_status
            not in {
                ApplicabilityAssessmentStatus.UNKNOWN,
                ApplicabilityAssessmentStatus.NOT_APPLICABLE,
            }
        )

    def transition_to(self, target: CandidateStatus) -> "ParameterCandidateRecord":
        """Return a new record after one legal candidate lifecycle transition."""

        _, target_token = candidate_transition(self.candidate_status, target)
        target_status = CandidateStatus(target_token)
        if target_status is CandidateStatus.VALIDATION_CANDIDATE:
            disposition = CandidateScreeningDisposition.CANDIDATE
        elif target_status is CandidateStatus.REJECTED:
            disposition = CandidateScreeningDisposition.REJECTED
        else:
            disposition = self.candidate_screening
        return replace(
            self,
            candidate_status=target_status,
            candidate_screening=disposition,
            validation_required=(
                False
                if target_status is CandidateStatus.REJECTED
                else True
                if target_status is CandidateStatus.VALIDATION_CANDIDATE
                else self.validation_required
            ),
        )


def _priority_for_subsystem(subsystem: str) -> int | None:
    if subsystem in {
        "leaf_exchange_resistance",
        "tfwt_v3",
        "obt_v3",
        "soil_v3",
        "root_v3",
    }:
        return 1
    if subsystem == "food_v3":
        return 2
    if subsystem in {"intake_v3", "dose_v3"}:
        return 3
    return None


def _validation_plan_for(subsystem: str, *, deferred: bool) -> tuple[ValidationPlan, ...]:
    if not deferred and subsystem == "food_v3":
        return (
            ValidationPlan.LITERATURE_COMPARISON,
            ValidationPlan.BENCHMARK_CASE,
            ValidationPlan.SENSITIVITY_ANALYSIS,
        )
    if not deferred and subsystem in {
        "leaf_exchange_resistance",
        "tfwt_v3",
        "obt_v3",
        "soil_v3",
        "root_v3",
    }:
        return (
            ValidationPlan.LITERATURE_COMPARISON,
            ValidationPlan.SENSITIVITY_ANALYSIS,
            ValidationPlan.EXPERIMENTAL_DATA_REQUIRED,
        )
    if not deferred and subsystem in {"intake_v3", "dose_v3"}:
        return (
            ValidationPlan.LITERATURE_COMPARISON,
            ValidationPlan.UFOTRI_REFERENCE_COMPARISON,
            ValidationPlan.EXPERIMENTAL_DATA_REQUIRED,
        )
    if deferred:
        return (
            ValidationPlan.LITERATURE_COMPARISON,
            ValidationPlan.SENSITIVITY_ANALYSIS,
            ValidationPlan.EXPERIMENTAL_DATA_REQUIRED,
        )
    return ()


def construct_candidate_record(
    evidence: ParameterEvidenceRecord,
    review: ParameterReviewEntry,
) -> ParameterCandidateRecord:
    """Construct one screening record without importing a parameter value."""

    if review.parameter_id != evidence.parameter_id:
        raise ParameterCandidateError("evidence and applicability IDs do not match")
    applicability = review.applicability.assessment_status
    has_evidence = (
        evidence.status is EvidenceStatus.EVIDENCE_FOUND
        and evidence.source_identifier != UNRESOLVED_SOURCE
        and evidence.source_type is not SourceType.PROJECT_ASSUMPTION
        and evidence.source_type is not SourceType.TEST_ONLY
        and evidence.parameter_class is not ParameterClass.TEST_ONLY_PARAMETER
    )
    evidence_ids = (
        (evidence.source_identifier,)
        if evidence.source_identifier != UNRESOLVED_SOURCE
        else ()
    )
    if applicability is ApplicabilityAssessmentStatus.NOT_APPLICABLE:
        status = CandidateStatus.REJECTED
        disposition = CandidateScreeningDisposition.REJECTED
        reason = (
            "Rejected: NOT_APPLICABLE is a scenario input, numerical control, "
            "or test-only record and cannot enter physical validation."
        )
        validation_required = False
        plan = ()
        uncertainty_source = "NOT_APPLICABLE"
    elif applicability is ApplicabilityAssessmentStatus.UNKNOWN or not has_evidence:
        status = CandidateStatus.PROVISIONAL
        disposition = CandidateScreeningDisposition.DEFERRED
        reason = (
            "Deferred: source evidence and applicability are not sufficiently resolved; "
            "retain the P7.6A provisional boundary."
        )
        validation_required = True
        plan = _validation_plan_for(evidence.subsystem, deferred=True)
        uncertainty_source = (
            evidence.source_identifier
            if evidence.source_identifier != UNRESOLVED_SOURCE
            else UNRESOLVED_SOURCE
        )
    elif applicability in {
        ApplicabilityAssessmentStatus.DIRECT_MATCH,
        ApplicabilityAssessmentStatus.PARTIAL_MATCH,
        ApplicabilityAssessmentStatus.TRANSFER_REQUIRED,
    } and has_evidence:
        status = CandidateStatus.VALIDATION_CANDIDATE
        disposition = CandidateScreeningDisposition.CANDIDATE
        reason = (
            f"Candidate: evidence exists and applicability is {applicability.value}; "
            "future validation is required before any scientific or production use."
        )
        validation_required = True
        plan = _validation_plan_for(evidence.subsystem, deferred=False)
        uncertainty_source = evidence.source_identifier
    else:
        status = CandidateStatus.PROVISIONAL
        disposition = CandidateScreeningDisposition.DEFERRED
        reason = "Deferred: candidate eligibility prerequisites are not met."
        validation_required = True
        plan = _validation_plan_for(evidence.subsystem, deferred=True)
        uncertainty_source = UNRESOLVED_SOURCE

    return ParameterCandidateRecord(
        parameter_id=evidence.parameter_id,
        parameter_name=evidence.parameter_name,
        subsystem=evidence.subsystem,
        parameter_class=evidence.parameter_class,
        evidence_ids=evidence_ids,
        applicability_status=applicability,
        candidate_status=status,
        candidate_screening=disposition,
        candidate_reason=reason,
        validation_required=validation_required,
        validation_plan=plan,
        uncertainty_source=uncertainty_source,
        review_notes=review.applicability.review_notes,
        provenance=evidence.provenance,
        priority_tier=_priority_for_subsystem(evidence.subsystem),
    )


@dataclass(frozen=True)
class ParameterCandidateRegistry:
    """Deterministic candidate-screening records for all reviewed parameters."""

    records: tuple[ParameterCandidateRecord, ...]
    stage: str = "P7.6B-2A"
    schema_version: str = "v1"

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        require_text(self.schema_version, field="schema_version")
        records = tuple(self.records)
        if any(not isinstance(record, ParameterCandidateRecord) for record in records):
            raise ParameterCandidateError(
                "records must contain ParameterCandidateRecord values"
            )
        records = tuple(sorted(records, key=lambda record: record.parameter_id))
        ids = [record.parameter_id for record in records]
        duplicates = sorted(
            parameter_id for parameter_id, count in Counter(ids).items() if count > 1
        )
        if duplicates:
            raise ParameterCandidateError(
                "duplicate candidate parameter_id values: " + ", ".join(duplicates)
            )
        object.__setattr__(self, "records", records)
        self.assert_no_activation()

    @classmethod
    def from_records(
        cls,
        records: Iterable[ParameterCandidateRecord],
        *,
        stage: str = "P7.6B-2A",
        schema_version: str = "v1",
    ) -> "ParameterCandidateRegistry":
        return cls(tuple(records), stage=stage, schema_version=schema_version)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterCandidateRegistry":
        payload = require_mapping(value, field="parameter_candidate_registry")
        raw_records = payload.get("parameters", payload.get("records", payload.get("candidates")))
        if not isinstance(raw_records, list):
            raise ParameterSchemaError(
                "parameter_candidate_registry.parameters must be a list"
            )
        records = (
            ParameterCandidateRecord.from_mapping(item) for item in raw_records
        )
        registry = cls.from_records(
            records,
            stage=str(payload.get("stage", "P7.6B-2A")),
            schema_version=str(payload.get("schema_version", "v1")),
        )
        checks = {
            "candidate_registry": True,
            "calibration_started": False,
            "ufotri_active_database": False,
            "v3_physics_ready": False,
        }
        for field, expected in checks.items():
            if payload.get(field, expected) is not expected:
                raise ParameterCandidateError(
                    f"{field} must remain {expected!r} during P7.6B-2A"
                )
        for field in ("validated_parameters", "active_parameters"):
            if payload.get(field, 0) != 0:
                raise ParameterCandidateError(f"{field} must remain zero")
        declared = {
            "reviewed_parameter_count": len(registry.records),
            "candidate_count": registry.candidate_count,
            "deferred_count": registry.deferred_count,
            "rejected_count": registry.rejected_count,
        }
        for field, actual in declared.items():
            if field in payload and payload[field] != actual:
                raise ParameterCandidateError(
                    f"{field} disagrees with candidate registry records"
                )
        return registry

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "ParameterCandidateRegistry":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - project dependency
            raise ParameterCandidateError(
                "PyYAML is required to load a candidate registry"
            ) from exc
        registry_path = Path(path)
        try:
            payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterCandidateError(
                f"cannot read candidate registry {registry_path}"
            ) from exc
        return cls.from_mapping(payload)

    def assert_no_activation(self) -> None:
        for record in self.records:
            if record.candidate_status in {
                CandidateStatus.VALIDATED,
                CandidateStatus.ACTIVE,
            }:
                raise ParameterCandidateError(
                    "P7.6B-2A cannot validate or activate candidate records"
                )

    def validate_references(
        self,
        inventory: ParameterEvidenceRegistry,
        matrix: ParameterReviewMatrix,
    ) -> None:
        """Require exact inventory coverage and evidence/applicability links."""

        matrix.validate_against_inventory(inventory)
        inventory_ids = {record.parameter_id for record in inventory.records}
        candidate_ids = {record.parameter_id for record in self.records}
        if inventory_ids != candidate_ids:
            missing = sorted(inventory_ids - candidate_ids)
            extra = sorted(candidate_ids - inventory_ids)
            raise ParameterCandidateError(
                "candidate registry does not exactly cover inventory: "
                f"missing={missing}; extra={extra}"
            )
        for record in self.records:
            evidence = inventory.get(record.parameter_id)
            review = matrix.get(record.parameter_id)
            if record.parameter_name != evidence.parameter_name:
                raise ParameterCandidateError(
                    f"{record.parameter_id}: parameter_name reference mismatch"
                )
            if record.subsystem != evidence.subsystem:
                raise ParameterCandidateError(
                    f"{record.parameter_id}: subsystem reference mismatch"
                )
            if record.parameter_class is not evidence.parameter_class:
                raise ParameterCandidateError(
                    f"{record.parameter_id}: parameter_class reference mismatch"
                )
            if record.applicability_status is not review.applicability.assessment_status:
                raise ParameterCandidateError(
                    f"{record.parameter_id}: applicability reference mismatch"
                )
            expected_evidence = (
                ()
                if evidence.source_identifier == UNRESOLVED_SOURCE
                else (evidence.source_identifier,)
            )
            if record.evidence_ids != expected_evidence:
                raise ParameterCandidateError(
                    f"{record.parameter_id}: evidence_ids reference mismatch"
                )
            if record.candidate_status is CandidateStatus.VALIDATION_CANDIDATE:
                if not expected_evidence:
                    raise ParameterCandidateError(
                        f"{record.parameter_id}: candidate has no evidence reference"
                    )
                if evidence.status is not EvidenceStatus.EVIDENCE_FOUND:
                    raise ParameterCandidateError(
                        f"{record.parameter_id}: candidate evidence is not EVIDENCE_FOUND"
                    )

    def get(self, parameter_id: str) -> ParameterCandidateRecord:
        for record in self.records:
            if record.parameter_id == parameter_id:
                return record
        raise KeyError(parameter_id)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(
            record.parameter_id
            for record in self.records
            if record.candidate_screening is CandidateScreeningDisposition.CANDIDATE
        )

    @property
    def deferred_ids(self) -> tuple[str, ...]:
        return tuple(
            record.parameter_id
            for record in self.records
            if record.candidate_screening is CandidateScreeningDisposition.DEFERRED
        )

    @property
    def rejected_ids(self) -> tuple[str, ...]:
        return tuple(
            record.parameter_id
            for record in self.records
            if record.candidate_screening is CandidateScreeningDisposition.REJECTED
        )

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_ids)

    @property
    def deferred_count(self) -> int:
        return len(self.deferred_ids)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_ids)

    def counts_by_status(self) -> dict[str, int]:
        counts = Counter(record.candidate_status.value for record in self.records)
        return {status.value: counts.get(status.value, 0) for status in CandidateStatus}

    def counts_by_screening(self) -> dict[str, int]:
        counts = Counter(record.candidate_screening.value for record in self.records)
        return {
            disposition.value: counts.get(disposition.value, 0)
            for disposition in CandidateScreeningDisposition
        }

    def counts_by_subsystem(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for subsystem in sorted({record.subsystem for record in self.records}):
            subset = [record for record in self.records if record.subsystem == subsystem]
            result[subsystem] = {
                "CANDIDATE": sum(
                    record.candidate_screening is CandidateScreeningDisposition.CANDIDATE
                    for record in subset
                ),
                "DEFERRED": sum(
                    record.candidate_screening is CandidateScreeningDisposition.DEFERRED
                    for record in subset
                ),
                "REJECTED": sum(
                    record.candidate_screening is CandidateScreeningDisposition.REJECTED
                    for record in subset
                ),
            }
        return result

    def to_mapping(self) -> dict[str, Any]:
        self.assert_no_activation()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "candidate_registry": True,
            "reviewed_parameter_count": len(self.records),
            "candidate_count": self.candidate_count,
            "deferred_count": self.deferred_count,
            "rejected_count": self.rejected_count,
            "validation_candidates_identified": True,
            "validated_parameters": 0,
            "active_parameters": 0,
            "calibration_started": False,
            "ufotri_active_database": False,
            "v3_physics_ready": False,
            "parameters": [record.to_mapping() for record in self.records],
        }


def build_candidate_registry(
    inventory: ParameterEvidenceRegistry,
    matrix: ParameterReviewMatrix,
) -> ParameterCandidateRegistry:
    """Construct the deterministic 76-record screening registry."""

    matrix.validate_against_inventory(inventory)
    records = [
        construct_candidate_record(inventory.get(entry.parameter_id), entry)
        for entry in matrix.entries
    ]
    registry = ParameterCandidateRegistry.from_records(records)
    registry.validate_references(inventory, matrix)
    return registry


__all__ = [
    "CandidateDisposition",
    "CandidateLifecycleStatus",
    "CandidateScreeningDisposition",
    "CandidateStatus",
    "ParameterCandidateError",
    "ParameterCandidateRecord",
    "ParameterCandidateRegistry",
    "ValidationPlan",
    "build_candidate_registry",
    "candidate_transition",
    "construct_candidate_record",
    "transition_candidate_status",
]
