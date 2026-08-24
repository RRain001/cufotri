from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.parameters_v3 import (
    ParameterCandidateError,
    ParameterCandidateRegistry,
    ParameterValidationRegistry,
    ParameterStatus,
    ValidationStatus,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "docs/v3/parameter_evidence/parameter_candidate_registry.yaml"
VALIDATION = ROOT / "docs/v3/parameter_evidence/physical_constant_validation_registry.yaml"


def test_physical_constant_validation_manifest_is_pass_and_fail_closed() -> None:
    candidates = ParameterCandidateRegistry.from_yaml_file(CANDIDATES)
    validation = ParameterValidationRegistry.from_yaml_file(VALIDATION)

    validation.validate_references(candidates)
    assert validation.stage_status == "PASS_PHYSICAL_CONSTANT_VALIDATION"
    assert validation.physical_constant_validation_complete is True
    assert validation.validated_parameters == 1
    assert validation.active_parameters == 0
    assert validation.evidence_reconciliation == "PASS"
    assert validation.uncertainty_provenance == "PASS"
    assert validation.decay_semantic_benchmark == "PASS"
    assert validation.independent_evidence_count("soil.tritium_half_life") == 1

    record = validation.records[0]
    assert record.validation_status is ValidationStatus.PASS
    assert record.parameter_status is ParameterStatus.VALIDATED
    assert record.evidence_status == "EVIDENCE_FOUND"
    assert record.candidate_status == "VALIDATION_CANDIDATE"
    assert record.selected_value == 388540800.0
    assert record.selected_uncertainty == 777600.0
    assert record.to_mapping()["source_evidence_ids"] == [
        "evidence.nist.tritium_half_life.2000",
        "evidence.ddep.tritium_half_life.2006",
    ]


def test_validation_manifest_round_trip_preserves_all_source_records() -> None:
    validation = ParameterValidationRegistry.from_yaml_file(VALIDATION)
    restored = ParameterValidationRegistry.from_mapping(validation.to_mapping())

    assert restored == validation
    assert [record.evidence_id for record in restored.evidence_records] == [
        "evidence.ddep.tritium_half_life.2006",
        "evidence.nist.tritium_half_life.2000",
    ]


def test_validation_registry_rejects_tampered_candidate_or_active_status() -> None:
    candidates = ParameterCandidateRegistry.from_yaml_file(CANDIDATES)
    validation = ParameterValidationRegistry.from_yaml_file(VALIDATION)
    record = validation.records[0]

    with pytest.raises(ParameterCandidateError):
        ParameterCandidateRegistry.from_records(
            [
                replace(
                    candidates.records[0],
                    candidate_status="ACTIVE",
                    candidate_screening="CANDIDATE",
                ),
                *candidates.records[1:],
            ]
        )

    with pytest.raises(ValueError):
        replace(record, parameter_status="ACTIVE")
