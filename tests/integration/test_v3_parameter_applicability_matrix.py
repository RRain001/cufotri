from __future__ import annotations

from pathlib import Path

import pytest

from cteas_ufotri.parameters_v3 import (
    ParameterEvidenceRegistry,
    ParameterReviewError,
    ParameterReviewMatrix,
    evaluate_validation_gate,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/parameter_evidence/parameter_inventory.yaml"
MATRIX = ROOT / "docs/v3/parameter_evidence/parameter_applicability_matrix.yaml"


def load_pair() -> tuple[ParameterEvidenceRegistry, ParameterReviewMatrix]:
    inventory = ParameterEvidenceRegistry.from_yaml_file(MANIFEST)
    matrix = ParameterReviewMatrix.from_yaml_file(MATRIX)
    matrix.validate_against_inventory(inventory)
    return inventory, matrix


def test_all_76_inventory_parameters_have_complete_applicability_reviews() -> None:
    inventory, matrix = load_pair()

    assert len(inventory.records) == 76
    assert len(matrix.entries) == 76
    assert matrix.counts_by_assessment() == {
        "DIRECT_MATCH": 0,
        "PARTIAL_MATCH": 0,
        "TRANSFER_REQUIRED": 0,
        "NOT_APPLICABLE": 50,
        "UNKNOWN": 26,
    }
    assert matrix.validation_candidates_identified is True
    assert matrix.candidate_count == 0
    for entry in matrix.entries:
        record = entry.applicability
        assert record.parameter_id
        assert record.model_component
        assert record.source_context
        assert record.review_notes
        assert entry.required_action
        assert record.reviewer_status.value == "INTERNAL_REVIEWED"
        assert entry.validation_candidate is False


def test_matrix_round_trip_and_gate_are_deterministic_and_fail_closed() -> None:
    inventory, matrix = load_pair()
    restored = ParameterReviewMatrix.from_mapping(matrix.to_mapping())
    assert restored == matrix
    assert restored.candidate_count == 0

    gate = evaluate_validation_gate(inventory, matrix)
    assert gate.validation_candidates_identified is True
    assert gate.candidate_ids == ()
    assert gate.candidate_count == 0
    assert len(gate.blocked_reasons) == 76
    assert gate.calibration_started is False
    assert gate.active_database is False
    assert gate.to_mapping()["active_database"] is False


def test_matrix_requires_exact_inventory_coverage() -> None:
    inventory, matrix = load_pair()
    incomplete = ParameterReviewMatrix.from_entries(matrix.entries[:-1])

    with pytest.raises(ParameterReviewError, match="exactly cover inventory"):
        incomplete.validate_against_inventory(inventory)
