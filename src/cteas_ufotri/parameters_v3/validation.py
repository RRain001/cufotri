"""Fail-closed validation helpers for the V3 parameter evidence control plane."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path
import re
from typing import Any, Iterable


class ParameterEvidenceError(ValueError):
    """Base error for malformed parameter evidence."""


class ParameterSchemaError(ParameterEvidenceError):
    """A record or manifest violates the frozen schema."""


class ParameterLifecycleError(ParameterEvidenceError):
    """A requested lifecycle transition is not permitted."""


class ParameterRegistryError(ParameterEvidenceError):
    """A registry violates uniqueness or stage-isolation rules."""


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")


def require_text(value: Any, *, field: str) -> str:
    """Require a non-empty text field without coercing other types."""

    if not isinstance(value, str) or not value.strip():
        raise ParameterSchemaError(f"{field} must be a non-empty string")
    return value


def require_identifier(value: Any, *, field: str) -> str:
    """Require a deterministic machine-readable identifier."""

    text = require_text(value, field=field)
    if _IDENTIFIER.fullmatch(text) is None:
        raise ParameterSchemaError(
            f"{field} must match {_IDENTIFIER.pattern!r}; received {text!r}"
        )
    return text


def require_unit(value: Any, *, field: str) -> str:
    """Require an explicit unit token; no conversion is performed here."""

    return require_text(value, field=field)


def validate_scalar(value: Any, *, field: str) -> None:
    """Validate a JSON-compatible scalar or scalar sequence without coercion."""

    if value is None:
        return
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ParameterSchemaError(f"{field} must be finite")
        return
    if isinstance(value, str):
        return
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            validate_scalar(item, field=f"{field}[{index}]")
        return
    raise ParameterSchemaError(
        f"{field} must be null, scalar text/number/bool, or a scalar sequence"
    )


def coerce_enum(value: Any, enum_type: type[Enum], *, field: str) -> Enum:
    """Parse an enum value without accepting unknown lifecycle tokens."""

    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(repr(item.value) for item in enum_type)
        raise ParameterSchemaError(
            f"{field} must be one of {allowed}; received {value!r}"
        ) from exc


_LIFECYCLE_TRANSITIONS: dict[str, frozenset[str]] = {
    "PROVISIONAL": frozenset({"PROVISIONAL", "EVIDENCE_FOUND", "REJECTED"}),
    "EVIDENCE_FOUND": frozenset({"EVIDENCE_FOUND", "VALIDATED", "REJECTED"}),
    "VALIDATED": frozenset({"VALIDATED", "ACTIVE", "REJECTED"}),
    "ACTIVE": frozenset({"ACTIVE"}),
    "REJECTED": frozenset({"REJECTED"}),
}


def lifecycle_transition(current: Any, target: Any) -> tuple[str, str]:
    """Validate one adjacent lifecycle transition and return its tokens."""

    current_token = getattr(current, "value", current)
    target_token = getattr(target, "value", target)
    current_token = require_text(current_token, field="current_status").upper()
    target_token = require_text(target_token, field="target_status").upper()
    if current_token not in _LIFECYCLE_TRANSITIONS:
        raise ParameterLifecycleError(f"unknown current status {current_token!r}")
    if target_token not in _LIFECYCLE_TRANSITIONS[current_token]:
        raise ParameterLifecycleError(
            f"lifecycle transition {current_token} -> {target_token} is not allowed"
        )
    return current_token, target_token


transition_status = lifecycle_transition


def validate_stage_status(status: Any, *, field: str = "status") -> str:
    """Allow only statuses compatible with the P7.6A evidence freeze."""

    token = getattr(status, "value", status)
    token = require_text(token, field=field).upper()
    if token in {"VALIDATED", "ACTIVE"}:
        raise ParameterRegistryError(
            f"{field}={token} is forbidden during P7.6A; no activation or validation"
        )
    if token not in {"PROVISIONAL", "EVIDENCE_FOUND", "REJECTED"}:
        raise ParameterRegistryError(f"unsupported P7.6A status {token!r}")
    return token


def require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    """Require a mapping for manifest decoding."""

    if not isinstance(value, Mapping):
        raise ParameterSchemaError(f"{field} must be a mapping")
    return value


# ---------------------------------------------------------------------------
# P7.6C-1 physical-constant validation control plane
# ---------------------------------------------------------------------------


class ValidationStatus(str, Enum):
    """Scientific validation disposition; this is not runtime activation."""

    PENDING = "PENDING"
    PASS = "PASS"
    HOLD = "HOLD"
    REJECT = "REJECT"


class ParameterStatus(str, Enum):
    """P7.6C-1 status snapshot for the validated parameter."""

    VALIDATION_CANDIDATE = "VALIDATION_CANDIDATE"
    VALIDATED = "VALIDATED"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class PhysicalConstantSourceKind(str, Enum):
    """Source role for a physical-constant evidence record."""

    PRIMARY_MEASUREMENT = "PRIMARY_MEASUREMENT"
    EVALUATED_RECOMMENDATION = "EVALUATED_RECOMMENDATION"
    SECONDARY_EVALUATION = "SECONDARY_EVALUATION"


class EvidenceIndependence(str, Enum):
    """Lineage disposition between evidence records."""

    INDEPENDENT_EVALUATION = "INDEPENDENT_EVALUATION"
    DERIVED_FROM_EXISTING_EVALUATION = "DERIVED_FROM_EXISTING_EVALUATION"
    DUPLICATE_REPRESENTATION = "DUPLICATE_REPRESENTATION"
    UNKNOWN = "UNKNOWN"


class SourceAgreementStatus(str, Enum):
    """Outcome of source comparison without value averaging."""

    CONSISTENT_INDEPENDENT_EVALUATIONS = "CONSISTENT_INDEPENDENT_EVALUATIONS"
    CONSISTENT_DERIVED_EVALUATIONS = "CONSISTENT_DERIVED_EVALUATIONS"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    CONFLICT = "CONFLICT"
    UNRESOLVED = "UNRESOLVED"


class ValidationReviewStatus(str, Enum):
    """Review state for a P7.6C-1 validation record."""

    PENDING_REVIEW = "PENDING_REVIEW"
    INTERNAL_REVIEWED = "INTERNAL_REVIEWED"
    INDEPENDENT_REVIEWED = "INDEPENDENT_REVIEWED"
    REJECTED = "REJECTED"


class BenchmarkStatus(str, Enum):
    """Status of the semantic half-life benchmark."""

    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ValidationProvenance:
    """Repository traceability for P7.6C-1 control-plane records."""

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
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationProvenance":
        try:
            return cls(**dict(require_mapping(value, field="provenance")))
        except TypeError as exc:
            raise ParameterSchemaError(f"invalid validation provenance: {exc}") from exc

    def to_mapping(self) -> dict[str, str]:
        return {
            "repository": self.repository,
            "revision": self.revision,
            "file": self.file,
            "location": self.location,
        }


def _require_finite_number(
    value: Any,
    *,
    field: str,
    allow_none: bool = False,
    non_negative: bool = False,
) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ParameterSchemaError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ParameterSchemaError(f"{field} must be finite")
    if non_negative and number < 0.0:
        raise ParameterSchemaError(f"{field} must be non-negative")
    return number


def _coerce_text_tuple(value: Any, *, field: str, require_items: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ParameterSchemaError(f"{field} must be a list or tuple")
    result = tuple(value)
    if require_items and not result:
        raise ParameterSchemaError(f"{field} must not be empty")
    for index, item in enumerate(result):
        require_text(item, field=f"{field}[{index}]")
    return result


def _coerce_identifier_tuple(
    value: Any,
    *,
    field: str,
    require_items: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ParameterSchemaError(f"{field} must be a list or tuple")
    result = tuple(value)
    if require_items and not result:
        raise ParameterSchemaError(f"{field} must not be empty")
    for index, item in enumerate(result):
        require_identifier(item, field=f"{field}[{index}]")
    return result


_EVALUATION_DATE = re.compile(r"^\d{4}(?:-\d{2})?(?:-\d{2})?$")


@dataclass(frozen=True)
class PhysicalConstantEvidenceRecord:
    """One reported physical-constant evaluation, kept separate from selection.

    Values are never combined here.  ``normalized_value`` and
    ``normalized_uncertainty`` are explicit SI conversions of the reported
    source values; they are not runtime parameters.
    """

    evidence_id: str
    parameter_id: str
    evaluation_authority: str
    evaluation_date: str
    source_kind: PhysicalConstantSourceKind
    underlying_measurement_basis: str
    source_identifier: str
    source_url: str
    source_locator: str
    reported_quantity: str
    reported_value: float
    reported_uncertainty: float
    reported_unit: str
    uncertainty_convention: str
    canonical_unit: str
    normalized_value: float
    normalized_uncertainty: float
    normalized_unit: str
    conversion_path: str
    evidence_independence: EvidenceIndependence
    applicability_scope: str
    provenance: ValidationProvenance
    lineage_source_evidence_ids: tuple[str, ...] = ()
    reuses_evaluated_recommendation: bool = False
    primary_measurement: bool = False

    def __post_init__(self) -> None:
        require_identifier(self.evidence_id, field="evidence_id")
        require_identifier(self.parameter_id, field="parameter_id")
        for field in (
            "evaluation_authority",
            "underlying_measurement_basis",
            "source_identifier",
            "source_locator",
            "reported_quantity",
            "uncertainty_convention",
            "applicability_scope",
            "conversion_path",
        ):
            require_text(getattr(self, field), field=field)
        require_text(self.evaluation_date, field="evaluation_date")
        if _EVALUATION_DATE.fullmatch(self.evaluation_date) is None:
            raise ParameterSchemaError(
                "evaluation_date must be YYYY, YYYY-MM, or YYYY-MM-DD"
            )
        if not self.source_url.startswith(("http://", "https://")):
            raise ParameterSchemaError("source_url must be an HTTP(S) URL")
        for field in (
            "reported_unit",
            "canonical_unit",
            "normalized_unit",
        ):
            require_unit(getattr(self, field), field=field)
        for field in ("reported_value", "reported_uncertainty", "normalized_value", "normalized_uncertainty"):
            _require_finite_number(
                getattr(self, field),
                field=field,
                non_negative=field.endswith("uncertainty"),
            )
        if self.normalized_unit != self.canonical_unit:
            raise ParameterSchemaError(
                "normalized_unit must equal canonical_unit for physical evidence"
            )
        object.__setattr__(
            self,
            "source_kind",
            coerce_enum(
                self.source_kind,
                PhysicalConstantSourceKind,
                field="source_kind",
            ),
        )
        object.__setattr__(
            self,
            "evidence_independence",
            coerce_enum(
                self.evidence_independence,
                EvidenceIndependence,
                field="evidence_independence",
            ),
        )
        object.__setattr__(
            self,
            "lineage_source_evidence_ids",
            _coerce_identifier_tuple(
                self.lineage_source_evidence_ids,
                field="lineage_source_evidence_ids",
            ),
        )
        if not isinstance(self.reuses_evaluated_recommendation, bool):
            raise ParameterSchemaError("reuses_evaluated_recommendation must be a boolean")
        if not isinstance(self.primary_measurement, bool):
            raise ParameterSchemaError("primary_measurement must be a boolean")
        if self.evidence_independence in {
            EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION,
            EvidenceIndependence.DUPLICATE_REPRESENTATION,
        } and not self.lineage_source_evidence_ids:
            raise ParameterSchemaError(
                "derived or duplicate evidence requires lineage_source_evidence_ids"
            )
        if not isinstance(self.provenance, ValidationProvenance):
            object.__setattr__(
                self,
                "provenance",
                ValidationProvenance.from_mapping(self.provenance),
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PhysicalConstantEvidenceRecord":
        payload = dict(require_mapping(value, field="physical_constant_evidence"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid physical-constant evidence record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "parameter_id": self.parameter_id,
            "evaluation_authority": self.evaluation_authority,
            "evaluation_date": self.evaluation_date,
            "source_kind": self.source_kind.value,
            "underlying_measurement_basis": self.underlying_measurement_basis,
            "source_identifier": self.source_identifier,
            "source_url": self.source_url,
            "source_locator": self.source_locator,
            "reported_quantity": self.reported_quantity,
            "reported_value": self.reported_value,
            "reported_uncertainty": self.reported_uncertainty,
            "reported_unit": self.reported_unit,
            "uncertainty_convention": self.uncertainty_convention,
            "canonical_unit": self.canonical_unit,
            "normalized_value": self.normalized_value,
            "normalized_uncertainty": self.normalized_uncertainty,
            "normalized_unit": self.normalized_unit,
            "conversion_path": self.conversion_path,
            "evidence_independence": self.evidence_independence.value,
            "applicability_scope": self.applicability_scope,
            "lineage_source_evidence_ids": list(self.lineage_source_evidence_ids),
            "reuses_evaluated_recommendation": self.reuses_evaluated_recommendation,
            "primary_measurement": self.primary_measurement,
            "provenance": self.provenance.to_mapping(),
        }


@dataclass(frozen=True)
class SourceAgreementAssessment:
    """Pairwise comparison result; it deliberately contains no pooled value."""

    status: SourceAgreementStatus
    independent_evidence_count: int
    comparable_pair_count: int
    maximum_combined_standard_uncertainty_ratio: float | None
    comparison_rule: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            coerce_enum(self.status, SourceAgreementStatus, field="status"),
        )
        for field in ("independent_evidence_count", "comparable_pair_count"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ParameterSchemaError(f"{field} must be a non-negative integer")
        if self.maximum_combined_standard_uncertainty_ratio is not None:
            _require_finite_number(
                self.maximum_combined_standard_uncertainty_ratio,
                field="maximum_combined_standard_uncertainty_ratio",
                non_negative=True,
            )
        require_text(self.comparison_rule, field="comparison_rule")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "independent_evidence_count": self.independent_evidence_count,
            "comparable_pair_count": self.comparable_pair_count,
            "maximum_combined_standard_uncertainty_ratio": self.maximum_combined_standard_uncertainty_ratio,
            "comparison_rule": self.comparison_rule,
        }


def reconcile_evidence(
    records: Iterable[PhysicalConstantEvidenceRecord],
    *,
    max_combined_standard_uncertainty_ratio: float = 2.0,
) -> SourceAgreementAssessment:
    """Compare normalized source evaluations without averaging them.

    A pair is considered consistent when its absolute difference is no more
    than ``max_combined_standard_uncertainty_ratio`` times the quadrature sum
    of the two stated standard uncertainties.  Derived and duplicate records
    remain visible, but duplicate representations never count as an
    independent evidence stream.
    """

    ratio_limit = _require_finite_number(
        max_combined_standard_uncertainty_ratio,
        field="max_combined_standard_uncertainty_ratio",
        non_negative=True,
    )
    assert ratio_limit is not None
    evidence = tuple(records)
    if not evidence:
        return SourceAgreementAssessment(
            status=SourceAgreementStatus.UNRESOLVED,
            independent_evidence_count=0,
            comparable_pair_count=0,
            maximum_combined_standard_uncertainty_ratio=None,
            comparison_rule=(
                "No source records; reconciliation cannot select or validate a value."
            ),
        )
    ids = [record.evidence_id for record in evidence]
    if len(ids) != len(set(ids)):
        raise ParameterRegistryError("duplicate physical-constant evidence IDs")
    parameter_ids = {record.parameter_id for record in evidence}
    if len(parameter_ids) != 1:
        raise ParameterRegistryError(
            "all physical-constant evidence records must reference one parameter"
        )
    evidence_by_id = {record.evidence_id: record for record in evidence}
    for record in evidence:
        for lineage_id in record.lineage_source_evidence_ids:
            if lineage_id not in evidence_by_id:
                raise ParameterRegistryError(
                    f"{record.evidence_id}: lineage references unknown evidence {lineage_id}"
                )
            if lineage_id == record.evidence_id:
                raise ParameterRegistryError(
                    f"{record.evidence_id}: evidence cannot cite itself as lineage"
                )
    if any(record.evidence_independence is EvidenceIndependence.UNKNOWN for record in evidence):
        return SourceAgreementAssessment(
            status=SourceAgreementStatus.UNRESOLVED,
            independent_evidence_count=sum(
                record.evidence_independence is EvidenceIndependence.INDEPENDENT_EVALUATION
                for record in evidence
            ),
            comparable_pair_count=0,
            maximum_combined_standard_uncertainty_ratio=None,
            comparison_rule=(
                "Evidence independence is UNKNOWN; no source selection is permitted."
            ),
        )
    comparable = tuple(
        record
        for record in evidence
        if record.evidence_independence is not EvidenceIndependence.DUPLICATE_REPRESENTATION
    )
    independent_count = sum(
        record.evidence_independence is EvidenceIndependence.INDEPENDENT_EVALUATION
        for record in comparable
    )
    if len(comparable) < 2:
        return SourceAgreementAssessment(
            status=SourceAgreementStatus.SINGLE_SOURCE,
            independent_evidence_count=independent_count,
            comparable_pair_count=0,
            maximum_combined_standard_uncertainty_ratio=None,
            comparison_rule=(
                "Fewer than two non-duplicate source evaluations; validation remains on hold."
            ),
        )
    maximum_ratio = 0.0
    pair_count = 0
    for index, left in enumerate(comparable):
        for right in comparable[index + 1 :]:
            if left.normalized_unit != right.normalized_unit:
                return SourceAgreementAssessment(
                    status=SourceAgreementStatus.UNRESOLVED,
                    independent_evidence_count=independent_count,
                    comparable_pair_count=pair_count,
                    maximum_combined_standard_uncertainty_ratio=None,
                    comparison_rule=(
                        "Source units are not identical after declared normalization."
                    ),
                )
            combined_uncertainty = math.hypot(
                left.normalized_uncertainty,
                right.normalized_uncertainty,
            )
            difference = abs(left.normalized_value - right.normalized_value)
            ratio = (
                0.0
                if combined_uncertainty == 0.0 and difference == 0.0
                else ratio_limit + 1.0
                if combined_uncertainty == 0.0
                else difference / combined_uncertainty
            )
            pair_count += 1
            maximum_ratio = max(maximum_ratio, ratio)
            if ratio > ratio_limit:
                return SourceAgreementAssessment(
                    status=SourceAgreementStatus.CONFLICT,
                    independent_evidence_count=independent_count,
                    comparable_pair_count=pair_count,
                    maximum_combined_standard_uncertainty_ratio=ratio,
                    comparison_rule=(
                        "No blind averaging: a pair conflicts when |x1-x2| exceeds "
                        f"{ratio_limit:g} times the combined standard uncertainty."
                    ),
                )
    status = (
        SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS
        if any(
            record.evidence_independence
            is EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION
            for record in comparable
        )
        else SourceAgreementStatus.CONSISTENT_INDEPENDENT_EVALUATIONS
    )
    return SourceAgreementAssessment(
        status=status,
        independent_evidence_count=independent_count,
        comparable_pair_count=pair_count,
        maximum_combined_standard_uncertainty_ratio=maximum_ratio,
        comparison_rule=(
            "No blind averaging: sources are compared pairwise after explicit SI "
            "normalization; the selected source value remains unchanged."
        ),
    )


@dataclass(frozen=True)
class ParameterValidationRecord:
    """Immutable P7.6C-1 reconciliation and validation decision."""

    parameter_id: str
    candidate_record_id: str
    validation_status: ValidationStatus
    validated_quantity: str
    canonical_unit: str
    selected_value: float | None
    selected_uncertainty: float | None
    uncertainty_unit: str
    source_evidence_ids: tuple[str, ...]
    selected_source_evidence_id: str | None
    source_agreement_status: SourceAgreementStatus
    reconciliation_method: str
    reconciliation_rationale: str
    equation_match: bool
    unit_match: bool
    applicability_match: bool
    independence_review: str
    remaining_limitations: tuple[str, ...]
    candidate_status: str
    parameter_status: ParameterStatus
    selected_uncertainty_convention: str
    benchmark_id: str
    benchmark_status: BenchmarkStatus
    review_status: ValidationReviewStatus
    provenance: ValidationProvenance
    evidence_status: str = "EVIDENCE_FOUND"

    def __post_init__(self) -> None:
        require_identifier(self.parameter_id, field="parameter_id")
        require_identifier(self.candidate_record_id, field="candidate_record_id")
        if self.candidate_record_id != f"candidate.{self.parameter_id}":
            raise ParameterRegistryError(
                "candidate_record_id must be the deterministic candidate ID"
            )
        object.__setattr__(
            self,
            "validation_status",
            coerce_enum(self.validation_status, ValidationStatus, field="validation_status"),
        )
        object.__setattr__(
            self,
            "source_agreement_status",
            coerce_enum(
                self.source_agreement_status,
                SourceAgreementStatus,
                field="source_agreement_status",
            ),
        )
        object.__setattr__(
            self,
            "parameter_status",
            coerce_enum(self.parameter_status, ParameterStatus, field="parameter_status"),
        )
        object.__setattr__(
            self,
            "benchmark_status",
            coerce_enum(self.benchmark_status, BenchmarkStatus, field="benchmark_status"),
        )
        object.__setattr__(
            self,
            "review_status",
            coerce_enum(
                self.review_status,
                ValidationReviewStatus,
                field="review_status",
            ),
        )
        for field in (
            "validated_quantity",
            "canonical_unit",
            "uncertainty_unit",
            "reconciliation_method",
            "reconciliation_rationale",
            "independence_review",
            "candidate_status",
            "selected_uncertainty_convention",
            "benchmark_id",
            "evidence_status",
        ):
            require_text(getattr(self, field), field=field)
        require_unit(self.canonical_unit, field="canonical_unit")
        require_unit(self.uncertainty_unit, field="uncertainty_unit")
        if self.evidence_status not in {"PROVISIONAL", "EVIDENCE_FOUND"}:
            raise ParameterLifecycleError(
                "P7.6C-1 evidence_status must remain PROVISIONAL or EVIDENCE_FOUND"
            )
        if self.candidate_status != ParameterStatus.VALIDATION_CANDIDATE.value:
            raise ParameterLifecycleError(
                "P7.6C-1 validation records must snapshot a VALIDATION_CANDIDATE"
            )
        object.__setattr__(
            self,
            "source_evidence_ids",
            _coerce_identifier_tuple(
                self.source_evidence_ids,
                field="source_evidence_ids",
                require_items=self.validation_status is ValidationStatus.PASS,
            ),
        )
        if len(self.source_evidence_ids) != len(set(self.source_evidence_ids)):
            raise ParameterRegistryError("source_evidence_ids must be unique")
        if self.selected_source_evidence_id is not None:
            require_identifier(
                self.selected_source_evidence_id,
                field="selected_source_evidence_id",
            )
            if self.selected_source_evidence_id not in self.source_evidence_ids:
                raise ParameterRegistryError(
                    "selected_source_evidence_id must reference source_evidence_ids"
                )
        _require_finite_number(self.selected_value, field="selected_value", allow_none=True)
        _require_finite_number(
            self.selected_uncertainty,
            field="selected_uncertainty",
            allow_none=True,
            non_negative=True,
        )
        object.__setattr__(
            self,
            "remaining_limitations",
            _coerce_text_tuple(
                self.remaining_limitations,
                field="remaining_limitations",
                require_items=True,
            ),
        )
        for field in ("equation_match", "unit_match", "applicability_match"):
            if not isinstance(getattr(self, field), bool):
                raise ParameterSchemaError(f"{field} must be a boolean")
        if not isinstance(self.provenance, ValidationProvenance):
            object.__setattr__(
                self,
                "provenance",
                ValidationProvenance.from_mapping(self.provenance),
            )
        if self.parameter_status is ParameterStatus.ACTIVE:
            raise ParameterLifecycleError("P7.6C-1 cannot set a parameter ACTIVE")
        if self.validation_status is ValidationStatus.PASS:
            if self.parameter_status is not ParameterStatus.VALIDATED:
                raise ParameterLifecycleError(
                    "PASS requires parameter_status=VALIDATED"
                )
            if self.evidence_status != "EVIDENCE_FOUND":
                raise ParameterLifecycleError(
                    "PASS requires evidence_status=EVIDENCE_FOUND"
                )
            if (
                self.selected_value is None
                or self.selected_uncertainty is None
                or self.selected_source_evidence_id is None
            ):
                raise ParameterSchemaError(
                    "PASS requires selected value, uncertainty, and source"
                )
            if not (self.equation_match and self.unit_match and self.applicability_match):
                raise ParameterLifecycleError(
                    "PASS requires equation, unit, and applicability matches"
                )
            if self.source_agreement_status not in {
                SourceAgreementStatus.CONSISTENT_INDEPENDENT_EVALUATIONS,
                SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS,
            }:
                raise ParameterLifecycleError(
                    "PASS requires resolved source reconciliation"
                )
            if self.benchmark_status is not BenchmarkStatus.PASS:
                raise ParameterLifecycleError("PASS requires a passing semantic benchmark")
            if self.review_status is not ValidationReviewStatus.INDEPENDENT_REVIEWED:
                raise ParameterLifecycleError(
                    "PASS requires independent review status"
                )
        elif self.validation_status in {ValidationStatus.PENDING, ValidationStatus.HOLD}:
            if self.parameter_status is not ParameterStatus.VALIDATION_CANDIDATE:
                raise ParameterLifecycleError(
                    "PENDING/HOLD records must remain VALIDATION_CANDIDATE"
                )
        elif self.validation_status is ValidationStatus.REJECT:
            if self.parameter_status is not ParameterStatus.REJECTED:
                raise ParameterLifecycleError("REJECT requires parameter_status=REJECTED")

    @property
    def can_promote_to_validated(self) -> bool:
        return (
            self.validation_status is ValidationStatus.PASS
            and self.parameter_status is ParameterStatus.VALIDATED
            and self.equation_match
            and self.unit_match
            and self.applicability_match
            and self.source_agreement_status
            in {
                SourceAgreementStatus.CONSISTENT_INDEPENDENT_EVALUATIONS,
                SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS,
            }
            and self.benchmark_status is BenchmarkStatus.PASS
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterValidationRecord":
        payload = dict(require_mapping(value, field="parameter_validation"))
        try:
            return cls(**payload)
        except TypeError as exc:
            raise ParameterSchemaError(
                f"invalid parameter validation record: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "parameter_id": self.parameter_id,
            "candidate_record_id": self.candidate_record_id,
            "validation_status": self.validation_status.value,
            "validated_quantity": self.validated_quantity,
            "canonical_unit": self.canonical_unit,
            "selected_value": self.selected_value,
            "selected_uncertainty": self.selected_uncertainty,
            "uncertainty_unit": self.uncertainty_unit,
            "source_evidence_ids": list(self.source_evidence_ids),
            "selected_source_evidence_id": self.selected_source_evidence_id,
            "source_agreement_status": self.source_agreement_status.value,
            "reconciliation_method": self.reconciliation_method,
            "reconciliation_rationale": self.reconciliation_rationale,
            "equation_match": self.equation_match,
            "unit_match": self.unit_match,
            "applicability_match": self.applicability_match,
            "independence_review": self.independence_review,
            "remaining_limitations": list(self.remaining_limitations),
            "candidate_status": self.candidate_status,
            "parameter_status": self.parameter_status.value,
            "selected_uncertainty_convention": self.selected_uncertainty_convention,
            "benchmark_id": self.benchmark_id,
            "benchmark_status": self.benchmark_status.value,
            "review_status": self.review_status.value,
            "provenance": self.provenance.to_mapping(),
            "evidence_status": self.evidence_status,
        }


def validation_candidate_transition(
    current: Any,
    target: Any,
    validation: ParameterValidationRecord | None = None,
) -> tuple[str, str]:
    """Permit only candidate -> validated after a PASS record; never ACTIVE."""

    current_token = require_text(getattr(current, "value", current), field="current_status").upper()
    target_token = require_text(getattr(target, "value", target), field="target_status").upper()
    if current_token != ParameterStatus.VALIDATION_CANDIDATE.value:
        raise ParameterLifecycleError(
            "P7.6C-1 transitions must start from VALIDATION_CANDIDATE"
        )
    if target_token == ParameterStatus.ACTIVE.value:
        raise ParameterLifecycleError("P7.6C-1 cannot transition a parameter to ACTIVE")
    if target_token == ParameterStatus.VALIDATED.value:
        if validation is None or not validation.can_promote_to_validated:
            raise ParameterLifecycleError(
                "VALIDATED requires a passing P7.6C-1 validation record"
            )
        return current_token, target_token
    if target_token in {
        ParameterStatus.VALIDATION_CANDIDATE.value,
        ParameterStatus.REJECTED.value,
    }:
        return current_token, target_token
    raise ParameterLifecycleError(f"unsupported P7.6C-1 target status {target_token!r}")


def build_validation_record(
    *,
    parameter_id: str,
    validated_quantity: str,
    canonical_unit: str,
    evidence_records: Iterable[PhysicalConstantEvidenceRecord],
    selected_source_evidence_id: str | None,
    reconciliation_method: str,
    reconciliation_rationale: str,
    equation_match: bool,
    unit_match: bool,
    applicability_match: bool,
    independence_review: str,
    remaining_limitations: Iterable[str],
    selected_uncertainty_convention: str | None,
    benchmark_id: str,
    benchmark_status: BenchmarkStatus,
    review_status: ValidationReviewStatus,
    provenance: ValidationProvenance,
    evidence_status: str = "EVIDENCE_FOUND",
) -> ParameterValidationRecord:
    """Build a decision record from explicit source records and gates.

    This helper makes a conflict fail closed as ``HOLD``.  It never computes a
    pooled or averaged value; if a selected source is supplied, its normalized
    value is copied verbatim into the decision record.
    """

    evidence = tuple(evidence_records)
    assessment = reconcile_evidence(evidence)
    selected = None
    if selected_source_evidence_id is not None:
        selected = next(
            (
                record
                for record in evidence
                if record.evidence_id == selected_source_evidence_id
            ),
            None,
        )
        if selected is None:
            raise ParameterRegistryError(
                "selected_source_evidence_id does not reference supplied evidence"
            )
    resolved_agreement = assessment.status in {
        SourceAgreementStatus.CONSISTENT_INDEPENDENT_EVALUATIONS,
        SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS,
    }
    review_pass = (
        resolved_agreement
        and equation_match
        and unit_match
        and applicability_match
        and benchmark_status is BenchmarkStatus.PASS
        and review_status is ValidationReviewStatus.INDEPENDENT_REVIEWED
        and selected is not None
    )
    reconciliation_method = require_text(
        reconciliation_method,
        field="reconciliation_method",
    )
    if not reconciliation_method.strip():
        raise ParameterSchemaError("reconciliation_method must be explicit")
    return ParameterValidationRecord(
        parameter_id=parameter_id,
        candidate_record_id=f"candidate.{parameter_id}",
        validation_status=ValidationStatus.PASS if review_pass else ValidationStatus.HOLD,
        validated_quantity=validated_quantity,
        canonical_unit=canonical_unit,
        selected_value=selected.normalized_value if selected is not None else None,
        selected_uncertainty=(
            selected.normalized_uncertainty if selected is not None else None
        ),
        uncertainty_unit=canonical_unit,
        source_evidence_ids=tuple(record.evidence_id for record in evidence),
        selected_source_evidence_id=(
            selected.evidence_id if selected is not None else None
        ),
        source_agreement_status=assessment.status,
        reconciliation_method=reconciliation_method,
        reconciliation_rationale=reconciliation_rationale,
        equation_match=equation_match,
        unit_match=unit_match,
        applicability_match=applicability_match,
        independence_review=independence_review,
        remaining_limitations=tuple(remaining_limitations),
        candidate_status=ParameterStatus.VALIDATION_CANDIDATE.value,
        parameter_status=(
            ParameterStatus.VALIDATED
            if review_pass
            else ParameterStatus.VALIDATION_CANDIDATE
        ),
        selected_uncertainty_convention=(
            selected_uncertainty_convention
            or (selected.uncertainty_convention if selected is not None else "NOT_SELECTED")
        ),
        benchmark_id=benchmark_id,
        benchmark_status=benchmark_status,
        review_status=review_status,
        provenance=provenance,
        evidence_status=evidence_status,
    )


def _registry_declared_bool(
    payload: Mapping[str, Any],
    field: str,
    expected: bool,
) -> None:
    if field in payload and payload[field] is not expected:
        raise ParameterRegistryError(f"{field} must remain {expected!r} in P7.6C-1")


@dataclass(frozen=True)
class ParameterValidationRegistry:
    """Evidence and validation decisions for the P7.6C-1 control plane."""

    records: tuple[ParameterValidationRecord, ...]
    evidence_records: tuple[PhysicalConstantEvidenceRecord, ...]
    stage: str = "P7.6C-1"
    schema_version: str = "v1"
    stage_status: str | None = None
    physical_constant_validation_complete: bool | None = None
    calibration_started: bool = False
    ufotri_parameter_imported: bool = False
    ufotri_active_database: bool = False
    physics_changed: bool = False
    numerical_coupling_changed: bool = False
    v3_physics_ready: bool = False

    def __post_init__(self) -> None:
        require_text(self.stage, field="stage")
        require_text(self.schema_version, field="schema_version")
        if self.stage != "P7.6C-1":
            raise ParameterRegistryError("validation registry stage must be P7.6C-1")
        records = tuple(self.records)
        evidence_records = tuple(self.evidence_records)
        if any(not isinstance(record, ParameterValidationRecord) for record in records):
            raise ParameterRegistryError(
                "records must contain ParameterValidationRecord values"
            )
        if any(
            not isinstance(record, PhysicalConstantEvidenceRecord)
            for record in evidence_records
        ):
            raise ParameterRegistryError(
                "evidence_records must contain PhysicalConstantEvidenceRecord values"
            )
        records = tuple(sorted(records, key=lambda record: record.parameter_id))
        evidence_records = tuple(sorted(evidence_records, key=lambda record: record.evidence_id))
        record_ids = [record.parameter_id for record in records]
        evidence_ids = [record.evidence_id for record in evidence_records]
        if len(record_ids) != len(set(record_ids)):
            raise ParameterRegistryError("duplicate parameter validation records")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ParameterRegistryError("duplicate physical-constant evidence IDs")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "evidence_records", evidence_records)
        for field in (
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        ):
            if not isinstance(getattr(self, field), bool) or getattr(self, field):
                raise ParameterRegistryError(
                    f"{field} must remain false during P7.6C-1"
                )
        complete = bool(records) and all(
            record.validation_status is ValidationStatus.PASS for record in records
        )
        expected_status = (
            "PASS_PHYSICAL_CONSTANT_VALIDATION"
            if complete
            else "HOLD_EVIDENCE_RECONCILIATION_REQUIRED"
        )
        if self.stage_status is None:
            object.__setattr__(self, "stage_status", expected_status)
        elif self.stage_status != expected_status:
            raise ParameterRegistryError(
                f"stage_status must be {expected_status!r} for the contained records"
            )
        if self.physical_constant_validation_complete is None:
            object.__setattr__(self, "physical_constant_validation_complete", complete)
        elif self.physical_constant_validation_complete is not complete:
            raise ParameterRegistryError(
                "physical_constant_validation_complete disagrees with records"
            )

    @classmethod
    def from_records(
        cls,
        records: Iterable[ParameterValidationRecord],
        evidence_records: Iterable[PhysicalConstantEvidenceRecord],
        *,
        stage: str = "P7.6C-1",
        schema_version: str = "v1",
    ) -> "ParameterValidationRegistry":
        return cls(
            tuple(records),
            tuple(evidence_records),
            stage=stage,
            schema_version=schema_version,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ParameterValidationRegistry":
        payload = require_mapping(value, field="parameter_validation_registry")
        if payload.get("validation_registry") is not True:
            raise ParameterSchemaError(
                "parameter_validation_registry.validation_registry must be true"
            )
        raw_records = payload.get("parameters")
        raw_evidence = payload.get("evidence_records", payload.get("evidence"))
        if not isinstance(raw_records, list):
            raise ParameterSchemaError(
                "parameter_validation_registry.parameters must be a list"
            )
        if not isinstance(raw_evidence, list):
            raise ParameterSchemaError(
                "parameter_validation_registry.evidence_records must be a list"
            )
        registry = cls(
            tuple(ParameterValidationRecord.from_mapping(item) for item in raw_records),
            tuple(
                PhysicalConstantEvidenceRecord.from_mapping(item)
                for item in raw_evidence
            ),
            stage=str(payload.get("stage", "P7.6C-1")),
            schema_version=str(payload.get("schema_version", "v1")),
            stage_status=payload.get("stage_status"),
            physical_constant_validation_complete=payload.get(
                "physical_constant_validation_complete"
            ),
        )
        for field in (
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        ):
            _registry_declared_bool(payload, field, False)
        declared = {
            "validated_parameters": registry.validated_parameters,
            "validated_parameter_count": registry.validated_parameters,
            "active_parameters": registry.active_parameters,
            "active_parameter_count": registry.active_parameters,
            "evidence_reconciliation": registry.evidence_reconciliation,
            "uncertainty_provenance": registry.uncertainty_provenance,
            "decay_semantic_benchmark": registry.decay_semantic_benchmark,
        }
        for field, actual in declared.items():
            if field in payload and payload[field] != actual:
                raise ParameterRegistryError(
                    f"{field} disagrees with validation records"
                )
        return registry

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "ParameterValidationRegistry":
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - project dependency
            raise ParameterRegistryError("PyYAML is required to load validation manifests") from exc
        manifest_path = Path(path)
        try:
            payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ParameterRegistryError(
                f"cannot read validation manifest {manifest_path}"
            ) from exc
        return cls.from_mapping(payload)

    @property
    def validated_parameters(self) -> int:
        return sum(
            record.parameter_status is ParameterStatus.VALIDATED
            for record in self.records
        )

    @property
    def active_parameters(self) -> int:
        return sum(
            record.parameter_status is ParameterStatus.ACTIVE
            for record in self.records
        )

    @property
    def evidence_reconciliation(self) -> str:
        return "PASS" if self.records and all(
            record.source_agreement_status
            in {
                SourceAgreementStatus.CONSISTENT_INDEPENDENT_EVALUATIONS,
                SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS,
            }
            for record in self.records
        ) else "HOLD"

    @property
    def uncertainty_provenance(self) -> str:
        return "PASS" if self.records and all(
            record.validation_status is ValidationStatus.PASS
            and record.selected_uncertainty is not None
            and bool(record.selected_uncertainty_convention)
            for record in self.records
        ) else "HOLD"

    @property
    def decay_semantic_benchmark(self) -> str:
        return "PASS" if self.records and all(
            record.validation_status is ValidationStatus.PASS
            and record.benchmark_status is BenchmarkStatus.PASS
            for record in self.records
        ) else "HOLD"

    def evidence_for(self, parameter_id: str) -> tuple[PhysicalConstantEvidenceRecord, ...]:
        return tuple(
            record for record in self.evidence_records if record.parameter_id == parameter_id
        )

    def independent_evidence_count(self, parameter_id: str) -> int:
        return sum(
            record.evidence_independence is EvidenceIndependence.INDEPENDENT_EVALUATION
            for record in self.evidence_for(parameter_id)
        )

    def validate_references(self, candidate_registry: Any) -> None:
        """Require every P7.6B candidate to have one P7.6C decision record."""

        candidate_ids = tuple(sorted(candidate_registry.candidate_ids))
        validation_ids = tuple(record.parameter_id for record in self.records)
        if validation_ids != candidate_ids:
            raise ParameterRegistryError(
                "validation registry must exactly cover candidate IDs: "
                f"candidates={candidate_ids}; validations={validation_ids}"
            )
        evidence_by_id = {record.evidence_id: record for record in self.evidence_records}
        for record in self.records:
            candidate = candidate_registry.get(record.parameter_id)
            if getattr(candidate.candidate_status, "value", candidate.candidate_status) != record.candidate_status:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: candidate status reference mismatch"
                )
            source_records = [
                evidence_by_id.get(evidence_id) for evidence_id in record.source_evidence_ids
            ]
            if any(source is None for source in source_records):
                raise ParameterRegistryError(
                    f"{record.parameter_id}: validation record references unknown evidence"
                )
            typed_sources = tuple(source for source in source_records if source is not None)
            if any(source.parameter_id != record.parameter_id for source in typed_sources):
                raise ParameterRegistryError(
                    f"{record.parameter_id}: source evidence belongs to another parameter"
                )
            assessment = reconcile_evidence(typed_sources)
            if assessment.status is not record.source_agreement_status:
                raise ParameterRegistryError(
                    f"{record.parameter_id}: source agreement status mismatch"
                )
            validation_candidate_transition(
                record.candidate_status,
                record.parameter_status,
                record,
            )

    def assert_safe(self) -> None:
        if self.active_parameters:
            raise ParameterRegistryError("P7.6C-1 cannot activate parameters")
        for field in (
            "calibration_started",
            "ufotri_parameter_imported",
            "ufotri_active_database",
            "physics_changed",
            "numerical_coupling_changed",
            "v3_physics_ready",
        ):
            if getattr(self, field):
                raise ParameterRegistryError(f"unsafe P7.6C-1 state: {field}")

    def to_mapping(self) -> dict[str, Any]:
        self.assert_safe()
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "stage_status": self.stage_status,
            "validation_registry": True,
            "physical_constant_validation_complete": self.physical_constant_validation_complete,
            "evidence_reconciliation": self.evidence_reconciliation,
            "uncertainty_provenance": self.uncertainty_provenance,
            "decay_semantic_benchmark": self.decay_semantic_benchmark,
            "validated_parameters": self.validated_parameters,
            "validated_parameter_count": self.validated_parameters,
            "active_parameters": self.active_parameters,
            "active_parameter_count": self.active_parameters,
            "calibration_started": self.calibration_started,
            "ufotri_parameter_imported": self.ufotri_parameter_imported,
            "ufotri_active_database": self.ufotri_active_database,
            "physics_changed": self.physics_changed,
            "numerical_coupling_changed": self.numerical_coupling_changed,
            "v3_physics_ready": self.v3_physics_ready,
            "parameters": [record.to_mapping() for record in self.records],
            "evidence_records": [record.to_mapping() for record in self.evidence_records],
        }


__all__ = [
    "ParameterEvidenceError",
    "ParameterLifecycleError",
    "ParameterRegistryError",
    "ParameterSchemaError",
    "coerce_enum",
    "lifecycle_transition",
    "require_identifier",
    "require_mapping",
    "require_text",
    "require_unit",
    "transition_status",
    "validate_scalar",
    "validate_stage_status",
    "BenchmarkStatus",
    "EvidenceIndependence",
    "ParameterStatus",
    "ParameterValidationRecord",
    "ParameterValidationRegistry",
    "PhysicalConstantEvidenceRecord",
    "PhysicalConstantSourceKind",
    "SourceAgreementAssessment",
    "SourceAgreementStatus",
    "ValidationProvenance",
    "ValidationReviewStatus",
    "ValidationStatus",
    "reconcile_evidence",
    "build_validation_record",
    "validation_candidate_transition",
]
