"""P7.6C-3 mapping-to-feasibility integration tests."""

from pathlib import Path

from cteas_ufotri.parameters_v3.ufotri_mapping import UFOTRIMappingRegistry
from cteas_ufotri.parameters_v3.validation_feasibility import (
    ParameterValidationFeasibilityRegistry,
)


ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / "docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml"
FEASIBILITY = ROOT / "docs/v3/parameter_evidence/parameter_validation_feasibility.yaml"


def test_every_p7_6c2_mapping_record_has_one_feasibility_decision() -> None:
    mapping = UFOTRIMappingRegistry.from_yaml_file(MAPPING)
    feasibility = ParameterValidationFeasibilityRegistry.from_yaml_file(FEASIBILITY)
    feasibility.validate_against_mapping(mapping)
    assessed = {
        record.parameter_id
        for record in feasibility.records
        if not record.derived_quantity
    }
    assert assessed == {record.v3_parameter_id for record in mapping.records}


def test_p7_6c3_preserves_validation_and_activation_boundaries() -> None:
    registry = ParameterValidationFeasibilityRegistry.from_yaml_file(FEASIBILITY)
    assert registry.status == "PASS_VALIDATION_FEASIBILITY_ASSESSMENT"
    assert registry.new_validation_candidates == 0
    assert registry.validated_parameters == 1
    assert registry.active_parameters == 0
    assert registry.calibration_started is False
    assert registry.ufotri_parameter_imported is False
    assert registry.ufotri_active_database is False
    assert registry.physics_changed is False
    assert registry.numerical_coupling_changed is False
    assert registry.v3_physics_ready is False


def test_no_parameter_values_or_active_database_artifact_was_created() -> None:
    text = FEASIBILITY.read_text(encoding="utf-8")
    assert "selected_value" not in text
    assert "validated_parameter_values" not in text
    assert "active_value" not in text
    assert not (FEASIBILITY.parent / "validated_parameter_values.yaml").exists()
