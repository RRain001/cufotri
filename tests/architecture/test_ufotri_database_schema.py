from __future__ import annotations

from itertools import product
from pathlib import Path
import subprocess

import pytest

from cteas_ufotri.parameters import (
    ParameterDatabase,
    ParameterUnavailableError,
    ParameterUseNotAllowedError,
    SourceRegistry,
)


ROOT = Path(__file__).resolve().parents[2]
BASE_SHA = "40c403d"
SOURCE_PATH = ROOT / "parameters" / "parameter_sources.yaml"
AUDIT_PATH = ROOT / "docs" / "v3" / "ufotri_database" / "ufotri_database_source_audit.md"
STATUS_PATH = ROOT / "docs" / "implementation_status.md"


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(SOURCE_PATH)


def _table_entry() -> dict[str, object]:
    dimensions = ["crop", "growth_stage", "temperature", "humidity"]
    axes = {
        "crop": {"unit": "1", "values": ["grass", "nutrient_plant"]},
        "growth_stage": {"unit": "1", "values": ["vegetative", "mature"]},
        "temperature": {"unit": "K", "values": [293.15, 303.15]},
        "humidity": {"unit": "1", "values": [0.4, 0.8]},
    }
    cells = []
    for crop, stage, temperature, humidity in product(
        axes["crop"]["values"],
        axes["growth_stage"]["values"],
        axes["temperature"]["values"],
        axes["humidity"]["values"],
    ):
        cells.append(
            {
                "coordinates": {
                    "crop": crop,
                    "growth_stage": stage,
                    "temperature": temperature,
                    "humidity": humidity,
                },
                "value": (
                    (0.0 if crop == "grass" else 100.0)
                    + (0.0 if stage == "vegetative" else 10.0)
                    + (0.0 if temperature == 293.15 else 1.0)
                    + (0.0 if humidity == 0.4 else 2.0)
                ),
            }
        )
    return {
        "parameter_id": "leaf_exchange.leaf_exchange_resistance",
        "value": None,
        "unit": "s m-1",
        "description": "Synthetic schema fixture; no UFOTRI value imported.",
        "module": "leaf_exchange",
        "status": "REVIEWED",
        "source": "UFOTRI_VALIDATED",
        "source_type": "manual",
        "reference": "ufotri_manual.md:2.2.2 and 3.3.1; schema fixture only",
        "uncertainty": {"classification": "not_quantified_in_source_audit"},
        "valid_range": None,
        "notes": "TEST_ONLY; synthetic table; REVIEWED is not VALIDATED or ACTIVE.",
        "type": "table",
        "dimensions": dimensions,
        "axes": axes,
        "interpolation": "linear",
        "extrapolation": "reject",
        "lookup_table": cells,
    }


def _table_database() -> ParameterDatabase:
    return ParameterDatabase.from_mapping(
        {"schema_version": "2.0", "parameters": [_table_entry()]},
        source_registry=_source_registry(),
    )


def test_table_parameter_supports_crop_stage_temperature_humidity_and_interpolation() -> None:
    database = _table_database()
    entry = database.get_entry("leaf_exchange.leaf_exchange_resistance")

    assert entry.type == "table"
    assert entry.table is not None
    assert entry.table.dimensions == ("crop", "growth_stage", "temperature", "humidity")
    assert entry.table.interpolation == "linear"
    assert database.lookup(
        entry.name,
        {
            "crop": "nutrient_plant",
            "growth_stage": "mature",
            "temperature": 298.15,
            "humidity": 0.6,
        },
    ) == pytest.approx(111.5)


def test_table_provenance_is_complete_and_source_is_not_production_approved() -> None:
    database = _table_database()
    entry = database.get_entry("leaf_exchange.leaf_exchange_resistance")
    provenance = database.get_provenance(entry.name).to_mapping()

    assert entry.status == "REVIEWED"
    assert entry.confidence == "provisional"
    assert entry.source_type == "manual"
    assert entry.reference
    assert entry.uncertainty is not None
    assert provenance["source"] == "UFOTRI_VALIDATED"
    assert provenance["source_status"] == "external_reference_required"
    assert provenance["production_allowed"] is False


def test_unvalidated_table_cannot_enter_runtime() -> None:
    database = _table_database()
    name = "leaf_exchange.leaf_exchange_resistance"

    with pytest.raises(ParameterUnavailableError):
        database.get(name)
    with pytest.raises(ParameterUseNotAllowedError):
        database.lookup(name, {"crop": "grass", "growth_stage": "mature", "temperature": 298.15, "humidity": 0.6}, production=True)
    with pytest.raises(ValueError):
        database.lookup(name, {"crop": "grass", "growth_stage": "mature", "temperature": 288.15, "humidity": 0.6})


def test_table_package_round_trips_deterministically() -> None:
    database = _table_database()
    roundtrip = ParameterDatabase.from_mapping(
        database.to_mapping(),
        source_registry=_source_registry(),
    )
    assert database.hash() == roundtrip.hash()


def test_legacy_parameter_document_can_carry_the_same_table_shape() -> None:
    migration_entry = _table_entry()
    legacy_entry = {
        "name": migration_entry["parameter_id"],
        "value": None,
        "unit": migration_entry["unit"],
        "category": "leaf_exchange",
        "source": migration_entry["source"],
        "reference": migration_entry["reference"],
        "confidence": "provisional",
        "applicability": {"status": "applicable", "scope": "test_only"},
        "transform": "IDENTITY",
        "bounds": None,
        "type": migration_entry["type"],
        "dimensions": migration_entry["dimensions"],
        "axes": migration_entry["axes"],
        "interpolation": migration_entry["interpolation"],
        "extrapolation": migration_entry["extrapolation"],
        "lookup_table": migration_entry["lookup_table"],
    }
    database = ParameterDatabase.from_mapping(
        {"schema_version": "1.0", "parameters": [legacy_entry]},
        source_registry=_source_registry(),
    )
    assert database.get_entry(legacy_entry["name"]).type == "table"


def test_ufotri_audit_and_status_declare_review_only_no_import_or_activation() -> None:
    audit = AUDIT_PATH.read_text(encoding="utf-8")
    status = STATUS_PATH.read_text(encoding="utf-8")
    for marker in (
        "P6_1_STATUS = PASS_DATABASE_READY",
        "UFOTRI_PARAMETER_IMPORTED = FALSE",
        "UFOTRI_ACTIVE_DATABASE = FALSE",
        "LEAF_EXCHANGE_IMPLEMENTATION = FALSE",
        "NEXT_PHASE = P6_2_LEAF_EXCHANGE_PHYSICS",
    ):
        assert marker in audit
        assert marker in status
    assert "status: ACTIVE" not in audit
    assert "manual values are not validated" in audit


def test_independent_review_protects_atmosphere_physics_soil_dose_defaults_and_values() -> None:
    protected = (
        "src/cteas_ufotri/atmosphere",
        "src/cteas_ufotri/leaf_exchange",
        "src/cteas_ufotri/soil",
        "src/cteas_ufotri/dose",
        "configs",
        "parameters/databases",
    )
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE_SHA, "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert changed.stdout.strip() == ""
    assert untracked.stdout.strip() == ""

    placeholder = ParameterDatabase.load(ROOT / "parameters" / "databases" / "ufotri_leaf_exchange.yaml")
    assert all(placeholder.get_entry(name).value is None for name in placeholder.list_parameters())
