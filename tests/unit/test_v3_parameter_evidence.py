from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from cteas_ufotri.parameters_v3 import (
    Applicability,
    EvidenceProvenance,
    EvidenceSourceMetadata,
    EvidenceStatus,
    ParameterClass,
    ParameterEvidenceRecord,
    ParameterEvidenceRegistry,
    ParameterLifecycleError,
    ParameterRegistryError,
    ParameterSchemaError,
    ReviewStatus,
    SourceType,
    lifecycle_transition,
)


def make_record(**overrides: object) -> ParameterEvidenceRecord:
    values: dict[str, object] = {
        "parameter_id": "soil.test_parameter",
        "parameter_name": "test parameter",
        "subsystem": "soil_v3",
        "parameter_class": ParameterClass.SOIL_PARAMETER,
        "symbol": "p_test",
        "description": "A test evidence record.",
        "canonical_unit": "s",
        "status": EvidenceStatus.PROVISIONAL,
        "source_type": SourceType.PROJECT_ASSUMPTION,
        "source_identifier": "UNRESOLVED_SOURCE_REQUIRED",
        "reported_value": None,
        "reported_unit": "s",
        "normalized_value": None,
        "normalized_unit": "s",
        "applicability": Applicability(),
        "evidence_notes": "No external evidence is attached.",
        "provenance": EvidenceProvenance(
            repository="CTEAS_ufotri",
            revision="test",
            file="tests/unit/test_v3_parameter_evidence.py",
            location="make_record",
        ),
        "review_status": ReviewStatus.PENDING_REVIEW,
    }
    values.update(overrides)
    return ParameterEvidenceRecord(**values)


def test_record_is_immutable_and_preserves_original_and_normalized_units() -> None:
    record = make_record(
        canonical_unit="m",
        reported_value=1.0,
        reported_unit="cm",
        normalized_value=0.01,
        normalized_unit="m",
        source_identifier="doi:10.0000/example",
    )

    assert record.reported_value == 1.0
    assert record.reported_unit == "cm"
    assert record.normalized_value == 0.01
    assert record.normalized_unit == "m"
    with pytest.raises(FrozenInstanceError):
        record.parameter_id = "other"  # type: ignore[misc]


def test_required_traceability_and_units_fail_closed() -> None:
    with pytest.raises(ParameterSchemaError):
        make_record(source_identifier="")
    with pytest.raises(ParameterSchemaError):
        make_record(canonical_unit="")
    with pytest.raises(ParameterSchemaError):
        make_record(
            provenance=EvidenceProvenance(
                repository="CTEAS_ufotri",
                revision="test",
                file="",
                location="make_record",
            )
        )
    payload = make_record().to_mapping()
    payload.pop("source_identifier")
    with pytest.raises(ParameterSchemaError):
        ParameterEvidenceRecord.from_mapping(payload)

    with pytest.raises(ParameterSchemaError):
        make_record(
            canonical_unit="m",
            normalized_value=1.0,
            normalized_unit="cm",
        )


def test_recovered_physical_evidence_requires_complete_source_metadata() -> None:
    with pytest.raises(ParameterSchemaError, match="source_metadata"):
        make_record(
            status=EvidenceStatus.EVIDENCE_FOUND,
            source_type=SourceType.PRIMARY_LITERATURE,
            source_identifier="doi:10.0000/example",
            equation_role="Test source equation role.",
        )

    source = EvidenceSourceMetadata(
        title="Synthetic source",
        authors=("Test Author",),
        year=2026,
        journal_or_publisher="Synthetic Journal",
        identifier="doi:10.0000/example",
        locator="Equation 1",
        stable_url="https://doi.org/10.0000/example",
        reported_quantity="Synthetic quantity",
        reported_uncertainty="Not quantified",
        conversion_path="No conversion; reported and canonical units are s.",
    )
    record = make_record(
        status=EvidenceStatus.EVIDENCE_FOUND,
        source_type=SourceType.PRIMARY_LITERATURE,
        source_identifier=source.identifier,
        equation_role="Test source equation role.",
        source_metadata=source,
    )
    assert ParameterEvidenceRecord.from_mapping(record.to_mapping()) == record


def test_lifecycle_allows_adjacent_transitions_but_rejects_direct_activation() -> None:
    assert lifecycle_transition("PROVISIONAL", "EVIDENCE_FOUND") == (
        "PROVISIONAL",
        "EVIDENCE_FOUND",
    )
    assert lifecycle_transition("EVIDENCE_FOUND", "VALIDATED") == (
        "EVIDENCE_FOUND",
        "VALIDATED",
    )
    assert lifecycle_transition("VALIDATED", "ACTIVE") == (
        "VALIDATED",
        "ACTIVE",
    )
    with pytest.raises(ParameterLifecycleError):
        lifecycle_transition("PROVISIONAL", "ACTIVE")
    with pytest.raises(ParameterLifecycleError):
        lifecycle_transition("EVIDENCE_FOUND", "ACTIVE")

    record = make_record(
        source_identifier="doi:10.0000/example",
        equation_role="Test source equation role.",
        source_metadata=EvidenceSourceMetadata(
            title="Synthetic source",
            authors=("Test Author",),
            year=2026,
            journal_or_publisher="Synthetic Journal",
            identifier="doi:10.0000/example",
            locator="Equation 1",
            stable_url="https://doi.org/10.0000/example",
            reported_quantity="Synthetic quantity",
            reported_uncertainty="Not quantified",
            conversion_path="No conversion; reported and canonical units are s.",
        ),
    ).transition_to(EvidenceStatus.EVIDENCE_FOUND)
    assert record.status is EvidenceStatus.EVIDENCE_FOUND
    with pytest.raises(ParameterLifecycleError):
        record.transition_to(EvidenceStatus.ACTIVE)


def test_registry_rejects_duplicate_and_p7_6a_forbidden_statuses() -> None:
    with pytest.raises(ParameterRegistryError):
        ParameterEvidenceRegistry.from_records([make_record(), make_record()])

    active = make_record(status=EvidenceStatus.ACTIVE)
    with pytest.raises(ParameterRegistryError):
        ParameterEvidenceRegistry.from_records([active])


def test_string_manifest_tokens_are_decoded_without_parameter_conversion() -> None:
    mapping = make_record(
        source_identifier="doi:10.0000/example",
        applicability=Applicability(status="RESOLVED"),
    ).to_mapping()
    decoded = ParameterEvidenceRecord.from_mapping(mapping)

    assert decoded.parameter_class is ParameterClass.SOIL_PARAMETER
    assert decoded.status is EvidenceStatus.PROVISIONAL
    assert decoded.applicability.status.value == "RESOLVED"
    assert decoded.reported_value is None
