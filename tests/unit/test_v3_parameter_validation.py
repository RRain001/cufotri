from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import math

import pytest

from cteas_ufotri.parameters_v3 import (
    BenchmarkStatus,
    EvidenceIndependence,
    ParameterLifecycleError,
    ParameterSchemaError,
    ParameterStatus,
    PhysicalConstantEvidenceRecord,
    PhysicalConstantSourceKind,
    SourceAgreementStatus,
    ValidationProvenance,
    ValidationReviewStatus,
    ValidationStatus,
    build_validation_record,
    reconcile_evidence,
    validation_candidate_transition,
)
from cteas_ufotri.plant.soil_v3 import SoilForcing, SoilParameters, SoilProvenance, SoilState, SoilStorageSolver


PROVENANCE = ValidationProvenance(
    repository="CTEAS_ufotri",
    revision="test",
    file="tests/unit/test_v3_parameter_validation.py",
    location="test",
)


def make_evidence(
    evidence_id: str,
    *,
    value: float = 100.0,
    uncertainty: float = 1.0,
    independence: EvidenceIndependence = EvidenceIndependence.INDEPENDENT_EVALUATION,
    lineage: tuple[str, ...] = (),
) -> PhysicalConstantEvidenceRecord:
    return PhysicalConstantEvidenceRecord(
        evidence_id=evidence_id,
        parameter_id="soil.test_half_life",
        evaluation_authority="Test evaluation authority",
        evaluation_date="2026-08-24",
        source_kind=PhysicalConstantSourceKind.EVALUATED_RECOMMENDATION,
        underlying_measurement_basis="Test measurement set and evaluation note.",
        source_identifier=f"source:{evidence_id}",
        source_url="https://example.invalid/evidence",
        source_locator="Table 1",
        reported_quantity="test physical half-life",
        reported_value=value,
        reported_uncertainty=uncertainty,
        reported_unit="d",
        uncertainty_convention="one standard uncertainty",
        canonical_unit="s",
        normalized_value=value,
        normalized_uncertainty=uncertainty,
        normalized_unit="s",
        conversion_path="test source unit is already represented in the fixture normalization",
        evidence_independence=independence,
        applicability_scope="test decay term only",
        provenance=PROVENANCE,
        lineage_source_evidence_ids=lineage,
        reuses_evaluated_recommendation=independence
        in {
            EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION,
            EvidenceIndependence.DUPLICATE_REPRESENTATION,
        },
    )


def make_record(
    evidence: tuple[PhysicalConstantEvidenceRecord, ...],
    *,
    selected: str | None = None,
    equation_match: bool = True,
    unit_match: bool = True,
    applicability_match: bool = True,
    benchmark_status: BenchmarkStatus = BenchmarkStatus.PASS,
    review_status: ValidationReviewStatus = ValidationReviewStatus.INDEPENDENT_REVIEWED,
    method: str = "EXPLICIT_TEST_RECONCILIATION",
) :
    return build_validation_record(
        parameter_id="soil.test_half_life",
        validated_quantity="test physical half-life",
        canonical_unit="s",
        evidence_records=evidence,
        selected_source_evidence_id=selected or evidence[-1].evidence_id,
        reconciliation_method=method,
        reconciliation_rationale="Select one reported evaluation without averaging.",
        equation_match=equation_match,
        unit_match=unit_match,
        applicability_match=applicability_match,
        independence_review="Lineage was checked in the test fixture.",
        remaining_limitations=("Test-only control-plane record.",),
        selected_uncertainty_convention="one standard uncertainty",
        benchmark_id="test.decay_half_life",
        benchmark_status=benchmark_status,
        review_status=review_status,
        provenance=PROVENANCE,
    )


def test_evidence_records_preserve_reported_and_normalized_values() -> None:
    source = make_evidence(
        "evidence.test.source",
        value=4500.0,
        uncertainty=8.0,
    )
    assert source.reported_value == 4500.0
    assert source.reported_unit == "d"
    assert source.normalized_value == 4500.0
    assert source.normalized_unit == "s"
    assert PhysicalConstantEvidenceRecord.from_mapping(source.to_mapping()) == source
    with pytest.raises(FrozenInstanceError):
        source.evidence_id = "other"  # type: ignore[misc]


def test_derived_and_duplicate_evidence_do_not_count_as_independent() -> None:
    primary = make_evidence("evidence.test.primary")
    derived = make_evidence(
        "evidence.test.derived",
        value=100.5,
        independence=EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION,
        lineage=(primary.evidence_id,),
    )
    duplicate = make_evidence(
        "evidence.test.duplicate",
        independence=EvidenceIndependence.DUPLICATE_REPRESENTATION,
        lineage=(primary.evidence_id,),
    )

    assessment = reconcile_evidence((primary, derived, duplicate))

    assert assessment.status is SourceAgreementStatus.CONSISTENT_DERIVED_EVALUATIONS
    assert assessment.independent_evidence_count == 1
    assert assessment.comparable_pair_count == 1


def test_conflicting_sources_fail_closed_to_hold() -> None:
    first = make_evidence("evidence.test.first", value=100.0, uncertainty=1.0)
    second = make_evidence(
        "evidence.test.second",
        value=200.0,
        uncertainty=1.0,
        independence=EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION,
        lineage=(first.evidence_id,),
    )

    record = make_record((first, second))

    assert record.validation_status is ValidationStatus.HOLD
    assert record.parameter_status is ParameterStatus.VALIDATION_CANDIDATE
    assert record.source_agreement_status is SourceAgreementStatus.CONFLICT


def test_reconciliation_method_is_required() -> None:
    first = make_evidence("evidence.test.first")
    with pytest.raises(ParameterSchemaError, match="reconciliation_method"):
        make_record((first,), method="")


def test_only_candidate_to_validated_is_allowed_and_active_is_forbidden() -> None:
    first = make_evidence("evidence.test.first")
    second = make_evidence(
        "evidence.test.second",
        value=100.5,
        independence=EvidenceIndependence.DERIVED_FROM_EXISTING_EVALUATION,
        lineage=(first.evidence_id,),
    )
    record = make_record((first, second))

    assert validation_candidate_transition(
        ParameterStatus.VALIDATION_CANDIDATE,
        ParameterStatus.VALIDATED,
        record,
    ) == ("VALIDATION_CANDIDATE", "VALIDATED")
    with pytest.raises(ParameterLifecycleError):
        validation_candidate_transition(
            ParameterStatus.VALIDATION_CANDIDATE,
            ParameterStatus.ACTIVE,
            record,
        )
    with pytest.raises(ParameterLifecycleError):
        validation_candidate_transition("PROVISIONAL", "VALIDATED", record)


def test_half_life_semantic_benchmark_matches_existing_decay_equation() -> None:
    half_life_s = 388540800.0
    provenance = SoilProvenance(
        source_id="p7-6c1-test",
        source_version="1",
        artifact_sha256="a" * 64,
        spatial_reference="test-grid",
        temporal_resolution_s=half_life_s,
    )
    state = SoilState.from_inventory(
        soil_identifier="soil-001",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=100.0,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=provenance,
    )
    result = SoilStorageSolver(
        parameters=SoilParameters(tritium_half_life_s=half_life_s)
    ).advance(state, SoilForcing(), half_life_s)

    expected_fraction = math.exp(-math.log(2.0))
    assert result.state.inventory() / state.inventory() == pytest.approx(
        expected_fraction,
        abs=1.0e-14,
    )
    assert result.state.inventory() / state.inventory() == pytest.approx(0.5)
