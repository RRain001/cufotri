"""P7.6C-3 validation-feasibility control-plane tests."""

from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.parameters_v3.validation import (
    ParameterEvidenceError,
    ParameterLifecycleError,
    ParameterSchemaError,
)
from cteas_ufotri.parameters_v3.validation_feasibility import (
    ParameterValidationFeasibilityRecord,
    ParameterValidationFeasibilityRegistry,
    ValidationFeasibility,
    admit_for_validation,
    can_activate,
    can_enter_validation,
    reject_activation,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/parameter_evidence/parameter_validation_feasibility.yaml"


def load_registry() -> ParameterValidationFeasibilityRegistry:
    return ParameterValidationFeasibilityRegistry.from_yaml_file(MANIFEST)


def test_matrix_covers_all_mapping_records_and_freezes_counts() -> None:
    registry = load_registry()
    assert registry.mapped_parameter_count == 26
    assert registry.derived_quantity_count == 1
    assert len(registry.records) == 27
    assert registry.counts_by_feasibility() == {
        "VALIDATION_FEASIBLE": 4,
        "VALIDATION_FEASIBLE_WITH_LIMITATIONS": 8,
        "PHYSICS_REDESIGN_REQUIRED": 9,
        "NOT_IMPORTABLE": 4,
        "INSUFFICIENT_INFORMATION": 1,
    }
    assert registry.all_parameters_assessed is True


def test_allowed_and_blocked_validation_gate_states() -> None:
    registry = load_registry()
    for parameter_id in (
        "leaf.r_a",
        "obt.kf",
        "soil.transport_flux",
        "soil.tritium_half_life",
        "leaf.g_ex",
    ):
        record = registry.get(parameter_id)
        assert record.can_enter_validation is True
        assert can_enter_validation(record) is True
        assert admit_for_validation(record) is record

    for parameter_id in (
        "food.harvest_fraction",
        "root.k_root",
        "dose.dose_coefficient",
        "intake.food_product_mass",
    ):
        record = registry.get(parameter_id)
        assert record.can_enter_validation is False
        assert can_enter_validation(record) is False
        with pytest.raises(ParameterEvidenceError, match="blocks validation entry"):
            admit_for_validation(record)


def test_physics_redesign_and_non_importable_records_cannot_be_active() -> None:
    registry = load_registry()
    for parameter_id in (
        "root.k_root",
        "food.harvest_fraction",
        "dose.dose_coefficient",
    ):
        record = registry.get(parameter_id)
        assert can_activate(record) is False
        with pytest.raises(ParameterLifecycleError, match="cannot transition"):
            reject_activation(record)


def test_record_schema_requires_reason_for_blocked_states() -> None:
    record = load_registry().get("root.k_root")
    with pytest.raises(ParameterSchemaError, match="blocking_reason"):
        replace(record, blocking_reason="NONE")


def test_records_are_immutable_and_round_trip_without_values() -> None:
    registry = load_registry()
    record = registry.get("leaf.r_a")
    with pytest.raises(AttributeError):
        record.validation_feasibility = ValidationFeasibility.NOT_IMPORTABLE  # type: ignore[misc]
    restored = ParameterValidationFeasibilityRecord.from_mapping(record.to_mapping())
    assert restored == record
    serialized = registry.to_mapping()
    assert "selected_value" not in str(serialized)
    assert "active_value" not in str(serialized)
