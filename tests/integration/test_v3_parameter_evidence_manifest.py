from __future__ import annotations

from pathlib import Path

from cteas_ufotri.parameters_v3 import (
    EvidenceStatus,
    GapCategory,
    ParameterClass,
    ParameterEvidenceRegistry,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/parameter_evidence/parameter_inventory.yaml"


def test_parameter_manifest_is_loadable_deterministic_and_stage_safe() -> None:
    registry = ParameterEvidenceRegistry.from_yaml_file(MANIFEST)

    assert len(registry.records) == 76
    assert [record.parameter_id for record in registry.records] == sorted(
        record.parameter_id for record in registry.records
    )
    assert registry.counts_by_status() == {
        "PROVISIONAL": 56,
        "EVIDENCE_FOUND": 20,
        "VALIDATED": 0,
        "ACTIVE": 0,
        "REJECTED": 0,
    }
    assert registry.counts_by_gap() == {"A": 0, "B": 0, "C": 0, "D": 28, "E": 28, "F": 20}
    registry.assert_no_activation()


def test_manifest_covers_all_required_classes_and_explicit_traceability() -> None:
    registry = ParameterEvidenceRegistry.from_yaml_file(MANIFEST)
    classes = {record.parameter_class for record in registry.records}

    assert classes == set(ParameterClass)
    for record in registry.records:
        assert record.parameter_id
        assert record.canonical_unit
        assert record.reported_unit
        assert record.normalized_unit
        assert record.source_identifier
        assert record.provenance.file
        assert record.provenance.location


def test_manifest_round_trip_keeps_record_identity_and_no_activation() -> None:
    registry = ParameterEvidenceRegistry.from_yaml_file(MANIFEST)
    restored = ParameterEvidenceRegistry.from_mapping(registry.to_mapping())

    assert restored == registry
    assert all(
        record.status in {EvidenceStatus.PROVISIONAL, EvidenceStatus.EVIDENCE_FOUND}
        for record in restored.records
    )
    assert set(restored.counts_by_gap()) == {category.value for category in GapCategory}
