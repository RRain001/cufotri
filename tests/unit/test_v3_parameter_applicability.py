from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from cteas_ufotri.parameters_v3 import (
    ApplicabilityAssessmentStatus,
    ApplicabilityRecord,
    EvidenceProvenance,
    EvidenceStatus,
    ParameterClass,
    ParameterEvidenceRecord,
    ParameterSchemaError,
    ReviewStatus,
    SourceType,
    is_validation_candidate,
)


def make_applicability(**overrides: object) -> ApplicabilityRecord:
    values: dict[str, object] = {
        "parameter_id": "soil.test_parameter",
        "assessment_status": ApplicabilityAssessmentStatus.UNKNOWN,
        "radionuclide": "H-3",
        "chemical_form": "HTO",
        "pathway": "soil_transport_decay",
        "model_component": "V3 soil HTO interface",
        "environment_type": "SOIL_PROFILE",
        "crop_type": "NOT_APPLICABLE",
        "growth_stage": "NOT_APPLICABLE",
        "soil_condition": "UNSPECIFIED_SOIL_CONDITION",
        "time_scale": "UNRESOLVED_SOURCE_TIMESCALE",
        "spatial_scale": "UNRESOLVED_SOURCE_SCALE",
        "source_context": "UNRESOLVED_SOURCE_REQUIRED",
        "model_equation_match": ApplicabilityAssessmentStatus.UNKNOWN,
        "unit_match": ApplicabilityAssessmentStatus.UNKNOWN,
        "uncertainty_available": False,
        "review_notes": "Applicability is unresolved.",
        "reviewer_status": ReviewStatus.INTERNAL_REVIEWED,
    }
    values.update(overrides)
    return ApplicabilityRecord(**values)


def make_evidence(**overrides: object) -> ParameterEvidenceRecord:
    values: dict[str, object] = {
        "parameter_id": "soil.test_parameter",
        "parameter_name": "test parameter",
        "subsystem": "soil_v3",
        "parameter_class": ParameterClass.SOIL_PARAMETER,
        "symbol": "p_test",
        "description": "A test evidence record.",
        "canonical_unit": "s",
        "status": EvidenceStatus.EVIDENCE_FOUND,
        "source_type": SourceType.PRIMARY_LITERATURE,
        "source_identifier": "doi:10.0000/example",
        "reported_value": 1.0,
        "reported_unit": "s",
        "normalized_value": 1.0,
        "normalized_unit": "s",
        "applicability": {"status": "RESOLVED"},
        "evidence_notes": "A source is available for review.",
        "provenance": EvidenceProvenance(
            repository="CTEAS_ufotri",
            revision="test",
            file="tests/unit/test_v3_parameter_applicability.py",
            location="make_evidence",
        ),
        "review_status": ReviewStatus.INTERNAL_REVIEWED,
    }
    values.update(overrides)
    return ParameterEvidenceRecord(**values)


def test_applicability_record_is_immutable_and_alias_round_trips() -> None:
    record = make_applicability(assessment_status="PARTIAL_MATCH")

    assert record.assessment_status is ApplicabilityAssessmentStatus.PARTIAL_MATCH
    assert record.to_mapping()["applicability"] == "PARTIAL_MATCH"
    restored = ApplicabilityRecord.from_mapping(record.to_mapping())
    assert restored == record
    with pytest.raises(FrozenInstanceError):
        record.pathway = "other"  # type: ignore[misc]


def test_applicability_schema_requires_all_coordinates_and_explicit_boolean() -> None:
    payload = make_applicability().to_mapping()
    payload.pop("source_context")
    with pytest.raises(ParameterSchemaError):
        ApplicabilityRecord.from_mapping(payload)
    with pytest.raises(ParameterSchemaError):
        make_applicability(assessment_status="NOT_KNOWN")
    with pytest.raises(ParameterSchemaError):
        make_applicability(uncertainty_available="unknown")


def test_candidate_rule_requires_direct_match_or_resolved_partial_match() -> None:
    evidence = make_evidence()
    direct = make_applicability(
        assessment_status="DIRECT_MATCH",
        model_equation_match="DIRECT_MATCH",
        unit_match="DIRECT_MATCH",
    )
    partial_unresolved = make_applicability(
        assessment_status="PARTIAL_MATCH",
        model_equation_match="PARTIAL_MATCH",
        unit_match="DIRECT_MATCH",
        uncertainty_available=False,
    )
    partial_resolved = make_applicability(
        assessment_status="PARTIAL_MATCH",
        model_equation_match="PARTIAL_MATCH",
        unit_match="DIRECT_MATCH",
        uncertainty_available=True,
    )
    assert is_validation_candidate(evidence, direct)
    assert not is_validation_candidate(evidence, partial_unresolved)
    assert is_validation_candidate(evidence, partial_resolved)
    assert not is_validation_candidate(
        evidence, make_applicability(assessment_status="UNKNOWN")
    )
    assert not is_validation_candidate(
        make_evidence(
            parameter_class=ParameterClass.TEST_ONLY_PARAMETER,
            source_type=SourceType.TEST_ONLY,
        ),
        direct,
    )


def test_candidate_rule_does_not_promote_provisional_evidence() -> None:
    direct = make_applicability(
        assessment_status="DIRECT_MATCH",
        model_equation_match="DIRECT_MATCH",
        unit_match="DIRECT_MATCH",
    )
    provisional = make_evidence(status=EvidenceStatus.PROVISIONAL)
    assert not is_validation_candidate(provisional, direct)
