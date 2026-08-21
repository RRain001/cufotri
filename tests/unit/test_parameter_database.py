from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cteas_ufotri.parameters import (
    LegacyParameterAdapter,
    ParameterDatabase,
    ParameterNotFoundError,
    ParameterSchemaError,
    ParameterSourceError,
    ParameterUnavailableError,
    ParameterUseNotAllowedError,
    SourceRegistry,
    validate_parameter_document,
)
from cteas_ufotri.parameters.exceptions import ParameterBoundsError


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "parameters" / "parameter_sources.yaml"
LEAF_PATH = ROOT / "parameters" / "databases" / "ufotri_leaf_exchange.yaml"


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(SOURCE_PATH)


def _scalar_document(**overrides):
    entry = {
        "name": "soil.diffusion_rate",
        "value": 1.0e-9,
        "unit": "m2 s-1",
        "category": "soil",
        "source": "CTEAS_DEFAULT",
        "reference": "test fixture",
        "confidence": "internal_default",
        "applicability": {
            "status": "applicable",
            "scope": "unit test",
        },
        "transform": "IDENTITY",
        "bounds": {
            "lower": 0.0,
            "upper": 1.0e-6,
            "lower_inclusive": True,
            "upper_inclusive": True,
        },
    }
    entry.update(overrides)
    return {"schema_version": "1.0", "parameters": [entry]}


def test_load_placeholder_database_and_fail_closed_get() -> None:
    database = ParameterDatabase.load(LEAF_PATH)

    assert database.list_parameters() == [
        "leaf.boundary_layer_resistance",
        "leaf.humidity_response",
        "leaf.stomatal_resistance_day",
        "leaf.stomatal_resistance_night",
        "leaf.temperature_response",
    ]
    entry = database.get_entry("leaf.stomatal_resistance_day")
    assert entry.unit == "PENDING_VALIDATION"
    assert entry.confidence == "placeholder_pending_validation"
    assert entry.bounds is None
    assert database.get_provenance(entry.name).production_allowed is False
    with pytest.raises(ParameterUnavailableError):
        database.get(entry.name)


def test_hash_is_deterministic_and_includes_provenance() -> None:
    first = ParameterDatabase.load(LEAF_PATH)
    second = ParameterDatabase.load(LEAF_PATH)

    assert first.hash() == second.hash()
    assert len(first.hash()) == 64
    assert first.hash() != ParameterDatabase.from_mapping(
        _scalar_document(), source_registry=_source_registry()
    ).hash()


def test_valid_numeric_entry_is_readable_but_not_production_approved() -> None:
    database = ParameterDatabase.from_mapping(
        _scalar_document(), source_registry=_source_registry()
    )

    assert database.get("soil.diffusion_rate") == pytest.approx(1.0e-9)
    with pytest.raises(ParameterUseNotAllowedError):
        database.get("soil.diffusion_rate", production=True)


def test_unknown_parameter_fails_closed() -> None:
    database = ParameterDatabase.from_mapping(
        _scalar_document(), source_registry=_source_registry()
    )

    with pytest.raises(ParameterNotFoundError):
        database.get("unknown.parameter")


def test_missing_unit_is_rejected() -> None:
    document = _scalar_document()
    document["parameters"][0].pop("unit")

    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            document, source_registry=_source_registry()
        )


def test_nan_and_inf_are_rejected_before_hashing() -> None:
    for bad_value in (float("nan"), float("inf"), float("-inf")):
        document = _scalar_document(value=bad_value)
        with pytest.raises(ParameterSchemaError):
            validate_parameter_document(document)


def test_unknown_source_is_rejected() -> None:
    document = _scalar_document(source="UNKNOWN_SOURCE")

    with pytest.raises(ParameterSourceError):
        ParameterDatabase.from_mapping(
            document, source_registry=_source_registry()
        )


def test_missing_source_is_rejected() -> None:
    document = _scalar_document()
    document["parameters"][0].pop("source")

    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            document, source_registry=_source_registry()
        )


def test_illegal_bounds_and_transform_are_rejected() -> None:
    reversed_bounds = _scalar_document(
        bounds={
            "lower": 2.0,
            "upper": 1.0,
            "lower_inclusive": True,
            "upper_inclusive": True,
        }
    )
    with pytest.raises(ParameterBoundsError):
        ParameterDatabase.from_mapping(
            reversed_bounds, source_registry=_source_registry()
        )

    invalid_transform = _scalar_document(transform="GUESS")
    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            invalid_transform, source_registry=_source_registry()
        )


def test_legacy_adapter_exposes_numeric_values_without_touching_v2_config() -> None:
    adapter = LegacyParameterAdapter.from_mapping(
        {
            "soil": {"diffusion_rate": 1.0e-9},
            "plant": {"lai": 1.5, "enabled": True},
        },
        source_registry=_source_registry(),
    )

    assert adapter.get("soil.diffusion_rate") == pytest.approx(1.0e-9)
    assert adapter.get("plant.lai") == pytest.approx(1.5)
    assert "plant.enabled" not in adapter.list_parameters()


def test_source_file_and_parameter_file_are_strict_yaml_documents() -> None:
    source_document = yaml.safe_load(SOURCE_PATH.read_text(encoding="utf-8"))
    parameter_document = yaml.safe_load(LEAF_PATH.read_text(encoding="utf-8"))

    assert source_document["schema_version"] == "1.0"
    validate_parameter_document(parameter_document)
