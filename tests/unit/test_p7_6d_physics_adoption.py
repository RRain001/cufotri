"""P7.6D physics-adoption decision and redesign-gate tests."""

from pathlib import Path

import pytest
import yaml

from cteas_ufotri.parameters_v3.physics_adoption import (
    PhysicsAdoptionDecision,
    PhysicsAdoptionRegistry,
    admit_for_validation,
    can_activate,
    can_enter_validation,
)
from cteas_ufotri.parameters_v3.validation import (
    ParameterLifecycleError,
    ParameterSchemaError,
)
from cteas_ufotri.parameters_v3.validation_feasibility import (
    ParameterValidationFeasibilityRegistry,
)


ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "docs/v3/physics/p7_6d_physics_adoption_decision.yaml"
FEASIBILITY = ROOT / "docs/v3/parameter_evidence/parameter_validation_feasibility.yaml"
PRIORITY = ROOT / "docs/v3/physics/p7_6d_redesign_priority_matrix.yaml"

EXPECTED_REDESIGN_IDS = {
    "food.harvest_fraction",
    "food.tfwt_harvest_fraction",
    "leaf.growth_stage",
    "obt.daylight_multiplier",
    "obt.nighttime_multiplier",
    "obt.photosynthetic_activity",
    "obt.plant_mass",
    "obt.temperature",
    "root.k_root",
}


def load_registry() -> PhysicsAdoptionRegistry:
    registry = PhysicsAdoptionRegistry.from_yaml_file(DECISIONS)
    feasibility = ParameterValidationFeasibilityRegistry.from_yaml_file(FEASIBILITY)
    registry.validate_against_feasibility(feasibility)
    return registry


def test_decision_registry_is_complete_and_fail_closed() -> None:
    registry = load_registry()
    payload = yaml.safe_load(DECISIONS.read_text(encoding="utf-8"))

    assert len(registry.records) == 27
    assert registry.counts_by_decision() == {
        "KEEP_CURRENT_V3": 2,
        "VALIDATE_CURRENT_MODEL": 9,
        "EXTEND_V3_PHYSICS": 2,
        "REDESIGN_REQUIRED": 9,
        "DO_NOT_IMPORT": 4,
        "WAIT_FOR_EVIDENCE": 1,
    }
    assert set(registry.redesign_parameter_ids) == EXPECTED_REDESIGN_IDS
    assert registry.current_v3_model == "FROZEN"
    assert registry.all_feasibility_items_reviewed is True
    assert registry.redesign_items_identified is True
    assert registry.implementation_started is False
    assert registry.new_validation_candidates == 0
    assert registry.validated_parameters == 1
    assert registry.active_parameters == 0
    assert registry.calibration_started is False
    assert registry.ufotri_active_database is False
    assert registry.physics_changed is False
    assert registry.numerical_coupling_changed is False
    assert registry.v3_physics_ready is False
    assert payload["decision_counts"] == registry.counts_by_decision()
    assert set(payload["required_redesign_parameter_ids"]) == set(
        registry.redesign_parameter_ids
    )
    registry.assert_safe()


def test_redesign_required_records_are_blocked_from_validation() -> None:
    registry = load_registry()

    for parameter_id in EXPECTED_REDESIGN_IDS:
        record = registry.get(parameter_id)
        assert record.adoption_decision is PhysicsAdoptionDecision.REDESIGN_REQUIRED
        assert record.can_enter_validation is False
        assert can_enter_validation(record) is False
        with pytest.raises(ParameterLifecycleError, match="blocks validation entry"):
            admit_for_validation(record)

    for parameter_id in (
        "leaf.r_a",
        "obt.kf",
        "soil.transport_flux",
        "soil.tritium_half_life",
        "tfwt.water_content",
        "leaf.g_ex",
    ):
        record = registry.get(parameter_id)
        assert record.can_enter_validation is True
        assert can_enter_validation(record) is True
        assert admit_for_validation(record) is record


def test_non_physical_and_unknown_records_are_blocked() -> None:
    registry = load_registry()
    for parameter_id in (
        "dose.dose_coefficient",
        "food.crop",
        "intake.annual_consumption_amount",
        "leaf.crop",
        "intake.food_product_mass",
    ):
        record = registry.get(parameter_id)
        assert record.can_enter_validation is False
        with pytest.raises(ParameterLifecycleError):
            admit_for_validation(record)


def test_no_decision_can_activate_and_records_have_no_values() -> None:
    registry = load_registry()
    for record in registry.records:
        assert record.can_activate is False
        assert can_activate(record) is False
        serialized = str(record.to_mapping())
        assert "selected_value" not in serialized
        assert "active_value" not in serialized
        assert "runtime_lookup" not in serialized


def test_decision_schema_rejects_a_mismatched_redesign_flag() -> None:
    registry = load_registry()
    record = registry.get("root.k_root")
    payload = record.to_mapping()
    payload["required_redesign"] = False
    with pytest.raises(ParameterSchemaError, match="required_redesign"):
        type(record).from_mapping(payload)


def test_priority_matrix_covers_all_and_only_blocking_items() -> None:
    registry = load_registry()
    payload = yaml.safe_load(PRIORITY.read_text(encoding="utf-8"))
    rows = payload["priority_records"]
    covered = {
        parameter_id
        for row in rows
        for parameter_id in row["parameter_ids"]
    }
    assert len(rows) == 4
    assert covered == EXPECTED_REDESIGN_IDS
    assert payload["redesign_item_count"] == 9
    assert payload["implementation_authorized"] is False
    assert sum(
        record.priority.value == "HIGH"
        for record in registry.records
        if record.required_redesign
    ) == 8
    assert sum(
        record.coupling_impact.value == "NUMERICAL_COUPLING_CHANGE_REQUIRED"
        for record in registry.records
        if record.required_redesign
    ) == 3
