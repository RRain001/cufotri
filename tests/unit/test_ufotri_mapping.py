"""P7.6C-2 UFOTRI semantic-mapping control-plane tests."""

from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.parameters_v3.ufotri_mapping import (
    MappingStatus,
    UFOTRIParameterMappingRecord,
    UFOTRIMappingRegistry,
    can_enter_validation,
)
from cteas_ufotri.parameters_v3.validation import ParameterSchemaError


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml"

EXPECTED_PARAMETER_IDS = {
    "dose.dose_coefficient",
    "food.crop",
    "food.harvest_fraction",
    "food.tfwt_harvest_fraction",
    "intake.annual_consumption_amount",
    "intake.food_product_mass",
    "leaf.crop",
    "leaf.growth_stage",
    "leaf.r_a",
    "leaf.r_b",
    "leaf.r_c",
    "obt.daylight_multiplier",
    "obt.kf",
    "obt.kr",
    "obt.nighttime_multiplier",
    "obt.photosynthetic_activity",
    "obt.plant_mass",
    "obt.temperature",
    "root.k_root",
    "soil.layer_depth",
    "soil.transport_flux",
    "soil.tritium_half_life",
    "soil.water_content",
    "tfwt.transformation_flux",
    "tfwt.water_content",
    "tfwt.water_loss_flux",
}


def load_registry() -> UFOTRIMappingRegistry:
    return UFOTRIMappingRegistry.from_yaml_file(MANIFEST)


def test_manifest_covers_all_deferred_and_c1_related_parameters() -> None:
    registry = load_registry()
    assert len(registry.records) == 26
    assert {item.v3_parameter_id for item in registry.records} == EXPECTED_PARAMETER_IDS
    assert registry.required_v3_parameter_ids == tuple(sorted(EXPECTED_PARAMETER_IDS))
    assert registry.counts_by_status() == {
        "DIRECT_MAPPING": 12,
        "TRANSFORMABLE_MAPPING": 4,
        "CONCEPTUAL_ANALOGUE": 6,
        "NO_MAPPING": 3,
        "SOURCE_UNAVAILABLE": 1,
    }


def test_manifest_preserves_p76c1_and_p76c2_fail_closed_flags() -> None:
    registry = load_registry()
    assert registry.new_validation_candidates == 0
    assert registry.validated_parameters == 1
    assert registry.active_parameters == 0
    assert registry.calibration_started is False
    assert registry.ufotri_parameter_imported is False
    assert registry.ufotri_active_database is False
    assert registry.physics_changed is False
    assert registry.numerical_coupling_changed is False
    assert registry.v3_physics_ready is False


def test_records_are_immutable_and_round_trip() -> None:
    registry = load_registry()
    record = registry.get("leaf.r_a")
    with pytest.raises(AttributeError):
        record.mapping_status = MappingStatus.NO_MAPPING  # type: ignore[misc]
    restored = UFOTRIParameterMappingRecord.from_mapping(record.to_mapping())
    assert restored == record


def test_direct_mapping_requires_compatible_equation_and_units() -> None:
    record = load_registry().get("leaf.r_a")
    with pytest.raises(ParameterSchemaError, match="equation role"):
        replace(record, equation_relationship="INCOMPATIBLE")
    with pytest.raises(ParameterSchemaError, match="units"):
        replace(record, unit_relationship="INCOMPATIBLE")


def test_transformable_mapping_requires_explicit_derivation() -> None:
    record = load_registry().get("soil.transport_flux")
    assert record.mapping_status is MappingStatus.TRANSFORMABLE_MAPPING
    assert record.transformation_possible is True
    assert record.can_enter_validation is True
    with pytest.raises(ParameterSchemaError, match="transformation_possible=true"):
        replace(record, transformation_possible=False)
    with pytest.raises(ParameterSchemaError, match="requires a derivation"):
        replace(record, transformation_derivation="NONE")
    with pytest.raises(ParameterSchemaError, match="compatible state basis"):
        replace(record, state_basis_relationship="INCOMPATIBLE")


def test_blocked_mapping_statuses_cannot_enter_validation() -> None:
    registry = load_registry()
    for parameter_id in (
        "leaf.growth_stage",
        "obt.photosynthetic_activity",
        "obt.temperature",
        "food.harvest_fraction",
        "intake.food_product_mass",
    ):
        record = registry.get(parameter_id)
        assert record.mapping_status in {
            MappingStatus.CONCEPTUAL_ANALOGUE,
            MappingStatus.NO_MAPPING,
            MappingStatus.SOURCE_UNAVAILABLE,
        }
        assert record.can_enter_validation is False
        assert can_enter_validation(record) is False


def test_external_intake_and_dose_mappings_do_not_enter_physical_validation() -> None:
    registry = load_registry()
    for parameter_id in ("intake.annual_consumption_amount", "dose.dose_coefficient"):
        record = registry.get(parameter_id)
        assert record.mapping_status is MappingStatus.DIRECT_MAPPING
        assert record.future_evidence_recovery_allowed is False
        assert record.can_enter_validation is False


def test_runtime_modules_do_not_import_mapping_control_plane() -> None:
    runtime_files = []
    for root in (
        ROOT / "src/cteas_ufotri/plant",
        ROOT / "src/cteas_ufotri/exposure",
        ROOT / "src/cteas_ufotri/coupling",
    ):
        runtime_files.extend(root.rglob("*.py"))
    runtime_files.append(ROOT / "src/cteas_ufotri/v3_pipeline.py")
    offenders = [
        str(path.relative_to(ROOT))
        for path in runtime_files
        if path.exists()
        and "ufotri_mapping" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
