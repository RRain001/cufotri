from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from cteas_ufotri.parameters_v3 import (
    Applicability,
    ApplicabilityAssessmentStatus,
    ApplicabilityStatus,
    CandidateScreeningDisposition,
    CandidateStatus,
    EvidenceProvenance,
    ParameterCandidateError,
    ParameterCandidateRecord,
    ParameterClass,
    ParameterLifecycleError,
    ReviewStatus,
    SourceType,
    ValidationPlan,
    can_enter_validation,
    candidate_transition,
    construct_candidate_record,
)
from cteas_ufotri.parameters_v3 import (
    EvidenceStatus,
    ParameterEvidenceRecord,
)
from cteas_ufotri.parameters_v3.applicability import ApplicabilityRecord
from cteas_ufotri.parameters_v3.review import ParameterReviewEntry


def make_applicability(
    status: ApplicabilityAssessmentStatus = ApplicabilityAssessmentStatus.DIRECT_MATCH,
) -> ApplicabilityRecord:
    match = (
        ApplicabilityAssessmentStatus.DIRECT_MATCH
        if status is ApplicabilityAssessmentStatus.DIRECT_MATCH
        else status
    )
    return ApplicabilityRecord(
        parameter_id="soil.test_parameter",
        assessment_status=status,
        radionuclide="H-3",
        chemical_form="HTO",
        pathway="soil_transport_decay",
        model_component="V3 soil HTO interface",
        environment_type="SOIL_PROFILE",
        crop_type="NOT_APPLICABLE",
        growth_stage="NOT_APPLICABLE",
        soil_condition="UNSPECIFIED_SOIL_CONDITION",
        time_scale="SOURCE_DEFINED",
        spatial_scale="SOURCE_DEFINED",
        source_context="doi:10.0000/example",
        model_equation_match=match,
        unit_match=match,
        uncertainty_available=True,
        review_notes="A source-specific applicability review is available.",
        reviewer_status=ReviewStatus.INTERNAL_REVIEWED,
    )


def make_candidate(
    *,
    status: CandidateStatus = CandidateStatus.APPLICABILITY_REVIEWED,
    applicability_status: ApplicabilityAssessmentStatus = ApplicabilityAssessmentStatus.DIRECT_MATCH,
    screening: CandidateScreeningDisposition | None = None,
) -> ParameterCandidateRecord:
    return ParameterCandidateRecord(
        parameter_id="soil.test_parameter",
        parameter_name="test parameter",
        subsystem="soil_v3",
        parameter_class=ParameterClass.SOIL_PARAMETER,
        evidence_ids=("doi:10.0000/example",),
        applicability_status=applicability_status,
        candidate_status=status,
        candidate_screening=screening,
        candidate_reason="Candidate requires future validation.",
        validation_required=True,
        validation_plan=(
            ValidationPlan.LITERATURE_COMPARISON,
            ValidationPlan.SENSITIVITY_ANALYSIS,
        ),
        uncertainty_source="doi:10.0000/example",
        review_notes="Candidate construction test record.",
        provenance=EvidenceProvenance(
            repository="CTEAS_ufotri",
            revision="test",
            file="tests/unit/test_v3_parameter_candidate.py",
            location="make_candidate",
        ),
        priority_tier=1,
    )


def make_external_evidence() -> ParameterEvidenceRecord:
    return ParameterEvidenceRecord(
        parameter_id="soil.test_parameter",
        parameter_name="test parameter",
        subsystem="soil_v3",
        parameter_class=ParameterClass.SOIL_PARAMETER,
        symbol="p_test",
        description="A synthetic external-evidence fixture.",
        canonical_unit="s",
        status=EvidenceStatus.EVIDENCE_FOUND,
        source_type=SourceType.PRIMARY_LITERATURE,
        source_identifier="doi:10.0000/example",
        reported_value=1.0,
        reported_unit="s",
        normalized_value=1.0,
        normalized_unit="s",
        applicability=Applicability(
            radionuclide="H-3",
            chemical_form="HTO",
            environment="SOIL_PROFILE",
            pathway="soil_transport_decay",
            status=ApplicabilityStatus.RESOLVED,
        ),
        evidence_notes="Synthetic test fixture; not project evidence.",
        provenance=EvidenceProvenance(
            repository="CTEAS_ufotri",
            revision="test",
            file="tests/unit/test_v3_parameter_candidate.py",
            location="make_external_evidence",
        ),
        review_status=ReviewStatus.INTERNAL_REVIEWED,
    )


def make_review(
    status: ApplicabilityAssessmentStatus,
) -> ParameterReviewEntry:
    evidence = make_external_evidence()
    return ParameterReviewEntry(
        parameter_id=evidence.parameter_id,
        evidence_status=evidence.status,
        parameter_class=evidence.parameter_class,
        source_type=evidence.source_type,
        canonical_unit=evidence.canonical_unit,
        applicability=make_applicability(status),
        required_action="Future validation protocol required.",
    )


@pytest.mark.parametrize(
    "applicability_status",
    [
        ApplicabilityAssessmentStatus.DIRECT_MATCH,
        ApplicabilityAssessmentStatus.PARTIAL_MATCH,
        ApplicabilityAssessmentStatus.TRANSFER_REQUIRED,
    ],
)
def test_resolved_applicability_constructs_validation_candidate(
    applicability_status: ApplicabilityAssessmentStatus,
) -> None:
    record = construct_candidate_record(
        make_external_evidence(), make_review(applicability_status)
    )
    assert record.candidate_status is CandidateStatus.VALIDATION_CANDIDATE
    assert record.candidate_screening is CandidateScreeningDisposition.CANDIDATE
    assert record.validation_required is True
    assert can_enter_validation(record)


@pytest.mark.parametrize(
    "applicability_status,expected_status,expected_screening",
    [
        (
            ApplicabilityAssessmentStatus.UNKNOWN,
            CandidateStatus.PROVISIONAL,
            CandidateScreeningDisposition.DEFERRED,
        ),
        (
            ApplicabilityAssessmentStatus.NOT_APPLICABLE,
            CandidateStatus.REJECTED,
            CandidateScreeningDisposition.REJECTED,
        ),
    ],
)
def test_unresolved_or_inapplicable_records_do_not_construct_candidates(
    applicability_status: ApplicabilityAssessmentStatus,
    expected_status: CandidateStatus,
    expected_screening: CandidateScreeningDisposition,
) -> None:
    record = construct_candidate_record(
        make_external_evidence(), make_review(applicability_status)
    )
    assert record.candidate_status is expected_status
    assert record.candidate_screening is expected_screening
    assert not can_enter_validation(record)


def test_candidate_lifecycle_requires_validation_before_activation() -> None:
    assert candidate_transition("EVIDENCE_FOUND", "APPLICABILITY_REVIEWED") == (
        "EVIDENCE_FOUND",
        "APPLICABILITY_REVIEWED",
    )
    assert candidate_transition(
        "APPLICABILITY_REVIEWED", "VALIDATION_CANDIDATE"
    ) == ("APPLICABILITY_REVIEWED", "VALIDATION_CANDIDATE")
    with pytest.raises(ValueError):
        candidate_transition("VALIDATION_CANDIDATE", "ACTIVE")

    candidate = make_candidate().transition_to(CandidateStatus.VALIDATION_CANDIDATE)
    assert candidate.can_enter_validation
    assert can_enter_validation(candidate)
    with pytest.raises(ParameterLifecycleError):
        candidate.transition_to(CandidateStatus.ACTIVE)
    validated = candidate.transition_to(CandidateStatus.VALIDATED)
    assert validated.candidate_status is CandidateStatus.VALIDATED
    assert not can_enter_validation(validated)
    rejected = candidate.transition_to(CandidateStatus.REJECTED)
    assert rejected.candidate_status is CandidateStatus.REJECTED
    assert rejected.validation_required is False
    assert not can_enter_validation(rejected)


def test_unknown_and_not_applicable_cannot_be_constructed_as_candidates() -> None:
    with pytest.raises(ParameterCandidateError):
        make_candidate(
            status=CandidateStatus.VALIDATION_CANDIDATE,
            applicability_status=ApplicabilityAssessmentStatus.UNKNOWN,
            screening=CandidateScreeningDisposition.CANDIDATE,
        )
    with pytest.raises(ParameterCandidateError):
        make_candidate(
            status=CandidateStatus.VALIDATION_CANDIDATE,
            applicability_status=ApplicabilityAssessmentStatus.NOT_APPLICABLE,
            screening=CandidateScreeningDisposition.CANDIDATE,
        )


def test_candidate_record_is_immutable_and_requires_evidence_plan() -> None:
    candidate = make_candidate()
    assert candidate.to_mapping()["candidate_status"] == "APPLICABILITY_REVIEWED"
    restored = ParameterCandidateRecord.from_mapping(candidate.to_mapping())
    assert restored == candidate
    with pytest.raises(FrozenInstanceError):
        candidate.parameter_id = "other"  # type: ignore[misc]
    payload = candidate.to_mapping()
    payload["candidate_status"] = "VALIDATION_CANDIDATE"
    payload["candidate_screening"] = "CANDIDATE"
    payload["evidence_ids"] = []
    with pytest.raises(ParameterCandidateError):
        ParameterCandidateRecord.from_mapping(payload)


def test_constructor_preserves_deferred_and_rejected_boundaries() -> None:
    evidence = ParameterEvidenceRecord(
        parameter_id="soil.test_parameter",
        parameter_name="test parameter",
        subsystem="soil_v3",
        parameter_class=ParameterClass.SOIL_PARAMETER,
        symbol="p_test",
        description="A test evidence record.",
        canonical_unit="s",
        status=EvidenceStatus.PROVISIONAL,
        source_type=SourceType.PROJECT_ASSUMPTION,
        source_identifier="UNRESOLVED_SOURCE_REQUIRED",
        reported_value=None,
        reported_unit="s",
        normalized_value=None,
        normalized_unit="s",
        applicability={"status": "APPLICABILITY_UNRESOLVED"},
        evidence_notes="No external evidence is attached.",
        provenance=EvidenceProvenance(
            repository="CTEAS_ufotri",
            revision="test",
            file="tests/unit/test_v3_parameter_candidate.py",
            location="test_constructor",
        ),
        review_status=ReviewStatus.PENDING_REVIEW,
    )
    applicability = make_applicability(ApplicabilityAssessmentStatus.UNKNOWN)
    review = ParameterReviewEntry(
        parameter_id="soil.test_parameter",
        evidence_status=evidence.status,
        parameter_class=evidence.parameter_class,
        source_type=evidence.source_type,
        canonical_unit=evidence.canonical_unit,
        applicability=applicability,
        required_action="Acquire source evidence.",
    )
    record = construct_candidate_record(evidence, review)
    assert record.candidate_status is CandidateStatus.PROVISIONAL
    assert record.candidate_screening is CandidateScreeningDisposition.DEFERRED
    assert not can_enter_validation(record)
