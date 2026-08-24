from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.parameters_v3 import (
    CandidateScreeningDisposition,
    CandidateStatus,
    ParameterCandidateError,
    ParameterCandidateRegistry,
    ParameterEvidenceRegistry,
    ParameterReviewMatrix,
    build_candidate_registry,
    evaluate_candidate_gate,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/parameter_evidence/parameter_inventory.yaml"
MATRIX = ROOT / "docs/v3/parameter_evidence/parameter_applicability_matrix.yaml"
REGISTRY = ROOT / "docs/v3/parameter_evidence/parameter_candidate_registry.yaml"


def load_inputs() -> tuple[ParameterEvidenceRegistry, ParameterReviewMatrix]:
    inventory = ParameterEvidenceRegistry.from_yaml_file(MANIFEST)
    matrix = ParameterReviewMatrix.from_yaml_file(MATRIX)
    matrix.validate_against_inventory(inventory)
    return inventory, matrix


def test_candidate_registry_covers_all_76_and_is_fail_closed() -> None:
    inventory, matrix = load_inputs()
    registry = ParameterCandidateRegistry.from_yaml_file(REGISTRY)
    registry.validate_references(inventory, matrix)

    assert len(registry.records) == 76
    assert registry.counts_by_screening() == {
        "CANDIDATE": 0,
        "DEFERRED": 26,
        "REJECTED": 50,
    }
    assert registry.counts_by_status() == {
        "PROVISIONAL": 26,
        "EVIDENCE_FOUND": 0,
        "APPLICABILITY_REVIEWED": 0,
        "VALIDATION_CANDIDATE": 0,
        "VALIDATED": 0,
        "ACTIVE": 0,
        "REJECTED": 50,
    }
    assert registry.candidate_ids == ()
    assert registry.deferred_count == 26
    assert registry.rejected_count == 50
    assert all(
        record.candidate_status in {CandidateStatus.PROVISIONAL, CandidateStatus.REJECTED}
        for record in registry.records
    )


def test_constructed_registry_round_trips_and_gate_identifies_empty_set() -> None:
    inventory, matrix = load_inputs()
    constructed = build_candidate_registry(inventory, matrix)
    loaded = ParameterCandidateRegistry.from_yaml_file(REGISTRY)
    assert constructed == loaded

    restored = ParameterCandidateRegistry.from_mapping(loaded.to_mapping())
    assert restored == loaded
    gate = evaluate_candidate_gate(loaded)
    assert gate.validation_candidates_identified is True
    assert gate.candidate_ids == ()
    assert gate.candidate_count == 0
    assert len(gate.blocked_reasons) == 76
    assert gate.validated_parameters == 0
    assert gate.active_parameters == 0
    assert gate.calibration_started is False
    assert gate.ufotri_active_database is False
    assert gate.v3_physics_ready is False


def test_candidate_registry_rejects_future_validated_or_active_states() -> None:
    registry = ParameterCandidateRegistry.from_yaml_file(REGISTRY)
    for status in (CandidateStatus.VALIDATED, CandidateStatus.ACTIVE):
        promoted = replace(
            registry.records[0],
            candidate_status=status,
            candidate_screening=CandidateScreeningDisposition.CANDIDATE,
        )
        with pytest.raises(ParameterCandidateError, match="cannot validate or activate"):
            ParameterCandidateRegistry.from_records(
                [promoted, *registry.records[1:]]
            )


def test_candidate_registry_rejects_missing_duplicate_and_tampered_references() -> None:
    inventory, matrix = load_inputs()
    registry = ParameterCandidateRegistry.from_yaml_file(REGISTRY)
    with pytest.raises(ParameterCandidateError, match="exactly cover inventory"):
        ParameterCandidateRegistry.from_records(registry.records[:-1]).validate_references(
            inventory, matrix
        )

    with pytest.raises(ParameterCandidateError, match="duplicate"):
        ParameterCandidateRegistry.from_records(
            [registry.records[0], registry.records[0]]
        )

    tampered_record = replace(
        registry.records[0],
        applicability_status="DIRECT_MATCH",
    )
    tampered = ParameterCandidateRegistry.from_records(
        [tampered_record, *registry.records[1:]]
    )
    with pytest.raises(ParameterCandidateError, match="applicability reference"):
        tampered.validate_references(inventory, matrix)


def test_screening_dispositions_are_explicit() -> None:
    registry = ParameterCandidateRegistry.from_yaml_file(REGISTRY)
    assert all(
        record.candidate_screening
        in {
            CandidateScreeningDisposition.DEFERRED,
            CandidateScreeningDisposition.REJECTED,
        }
        for record in registry.records
    )
    assert all(
        record.validation_required
        for record in registry.records
        if record.candidate_screening is CandidateScreeningDisposition.DEFERRED
    )
    assert all(
        not record.validation_required
        for record in registry.records
        if record.candidate_screening is CandidateScreeningDisposition.REJECTED
    )
