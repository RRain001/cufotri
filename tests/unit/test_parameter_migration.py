from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.parameters import (
    MODULE_PARAMETER_PATHS,
    ParameterDatabase,
    ParameterMigrationAudit,
    ParameterMigrationError,
    ParameterMigrationRecord,
    ParameterSchemaError,
    ParameterSource,
    ParameterSourceError,
    ParameterSourceRegistry,
    ParameterStatus,
    ParameterValidationError,
    validate_parameter,
)
from cteas_ufotri.parameters.schema import ParameterEntry
from cteas_ufotri.parameters.exceptions import ParameterBoundsError


TIMESTAMP = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


def _registry() -> ParameterSourceRegistry:
    return ParameterSourceRegistry.from_mapping(
        {
            "schema_version": "2.0",
            "sources": {
                "TEST_MANUAL": {
                    "source_id": "TEST_MANUAL",
                    "citation": "Test manual citation",
                    "organization": "Test organization",
                    "year": 2026,
                    "document": "test-manual.md",
                    "location": "section 1",
                    "accessibility": "local_fixture",
                }
            },
        }
    )


def _entry(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "parameter_id": "leaf_exchange.exchange_rate",
        "value": 1.0,
        "unit": "s-1",
        "description": "Test-only migration parameter",
        "module": "leaf_exchange",
        "status": "CANDIDATE",
        "source": "TEST_MANUAL",
        "source_type": "manual",
        "reference": "test-manual.md:section 1",
        "uncertainty": {"type": "absolute", "value": 0.1},
        "valid_range": {
            "lower": 0.0,
            "upper": 2.0,
            "lower_inclusive": True,
            "upper_inclusive": True,
        },
        "notes": "TEST_ONLY; no UFOTRI value.",
    }
    value.update(overrides)
    return value


def _database(*, status: str = "CANDIDATE") -> ParameterDatabase:
    entry = _entry(status=status)
    return ParameterDatabase.from_mapping(
        {"schema_version": "2.0", "parameters": [entry]},
        source_registry=_registry(),
    )


def test_valid_entry_and_required_migration_fields() -> None:
    database = _database()
    entry = database.get_entry("leaf_exchange.exchange_rate")

    assert entry.parameter_id == "leaf_exchange.exchange_rate"
    assert entry.module == "leaf_exchange"
    assert entry.status == ParameterStatus.CANDIDATE.value
    validate_parameter(entry, source_registry=_registry(), expected_unit="s-1")


@pytest.mark.parametrize("missing", ["unit", "source", "status"])
def test_missing_required_migration_field_fails_closed(missing: str) -> None:
    document = _entry()
    document.pop(missing)
    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            {"schema_version": "2.0", "parameters": [document]},
            source_registry=_registry(),
        )


def test_placeholder_is_default_and_cannot_be_activated_without_value() -> None:
    entry = _entry(value=None, status="PLACEHOLDER", valid_range=None)
    database = ParameterDatabase.from_mapping(
        {"schema_version": "2.0", "parameters": [entry]},
        source_registry=_registry(),
    )
    assert database.get_entry("leaf_exchange.exchange_rate").status == "PLACEHOLDER"
    with pytest.raises(ParameterMigrationError):
        database.transition(
            "leaf_exchange.exchange_rate",
            "ACTIVE",
            changed_by="test",
            reason="illegal direct activation",
            timestamp=TIMESTAMP,
        )


def test_lifecycle_transition_creates_audit_record() -> None:
    database = _database()
    reviewed = database.transition(
        "leaf_exchange.exchange_rate",
        "REVIEWED",
        changed_by="reviewer",
        reason="source record reviewed",
        timestamp=TIMESTAMP,
    )
    assert reviewed.get_entry("leaf_exchange.exchange_rate").status == "REVIEWED"
    assert reviewed.migration_records[0].to_mapping()["new_status"] == "REVIEWED"
    assert reviewed.migration_audit_report()["framework_status"] == "FRAMEWORK_COMPLETE"

    with pytest.raises(ParameterMigrationError):
        ParameterMigrationRecord.create(
            "leaf_exchange.exchange_rate",
            "CANDIDATE",
            "ACTIVE",
            changed_by="reviewer",
            reason="skip lifecycle",
            timestamp=TIMESTAMP,
        )

    with pytest.raises(ParameterMigrationError):
        ParameterMigrationAudit(
            [
                ParameterMigrationRecord.create(
                    "leaf_exchange.exchange_rate",
                    "PLACEHOLDER",
                    "CANDIDATE",
                    changed_by="r",
                    reason="candidate",
                    timestamp=TIMESTAMP,
                ),
                ParameterMigrationRecord.create(
                    "leaf_exchange.exchange_rate",
                    "REVIEWED",
                    "VALIDATED",
                    changed_by="v",
                    reason="validated",
                    timestamp=TIMESTAMP,
                ),
            ]
        )


def test_active_requires_record_and_full_transition_path() -> None:
    database = _database()
    database = database.transition(
        "leaf_exchange.exchange_rate", "REVIEWED", changed_by="r", reason="review", timestamp=TIMESTAMP
    )
    database = database.transition(
        "leaf_exchange.exchange_rate", "VALIDATED", changed_by="v", reason="validate", timestamp=TIMESTAMP
    )
    database = database.transition(
        "leaf_exchange.exchange_rate", "ACTIVE", changed_by="a", reason="activate", timestamp=TIMESTAMP
    )
    assert database.get_entry("leaf_exchange.exchange_rate").status == "ACTIVE"
    assert database.migration_records[-1].new_status == "ACTIVE"


def test_source_registry_registration_and_duplicate_rejection() -> None:
    registry = ParameterSourceRegistry()
    registry.register(
        ParameterSource(
            source_id="TEST_MANUAL",
            citation="citation",
            organization="org",
            year=2026,
            document="doc",
            location="loc",
            accessibility="local",
        )
    )
    with pytest.raises(ParameterSourceError):
        registry.register(
            ParameterSource(
                source_id="TEST_MANUAL",
                citation="duplicate",
                organization="org",
                year=2026,
                document="doc",
                location="loc",
                accessibility="local",
            )
        )


def test_validation_rejects_range_nan_provenance_and_unit_errors() -> None:
    database = _database()
    entry = database.get_entry("leaf_exchange.exchange_rate")
    with pytest.raises(ParameterValidationError):
        validate_parameter(entry, expected_unit="kg")

    with pytest.raises(ParameterBoundsError):
        validate_parameter(
            ParameterEntry(
                parameter_id=entry.parameter_id,
                value=3.0,
                unit=entry.unit,
                description=entry.description,
                module=entry.module,
                status=entry.status,
                source=entry.source,
                source_type=entry.source_type,
                reference=entry.reference,
                uncertainty=entry.uncertainty,
                valid_range=entry.valid_range,
                notes=entry.notes,
            ),
            source_registry=_registry(),
        )

    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            {"schema_version": "2.0", "parameters": [_entry(value=float("nan"))]},
            source_registry=_registry(),
        )

    missing_source_type = _entry(source_type="")
    with pytest.raises(ParameterSchemaError):
        ParameterDatabase.from_mapping(
            {"schema_version": "2.0", "parameters": [missing_source_type]},
            source_registry=_registry(),
        )


def test_module_mapping_and_hash_reproducibility_include_registry_and_status() -> None:
    assert MODULE_PARAMETER_PATHS == {
        "leaf_exchange": "leaf_exchange.*",
        "soil": "soil.*",
        "food_chain": "food_chain.*",
        "dose": "dose.*",
    }
    first = _database()
    second = _database()
    assert first.hash() == second.hash()
    roundtrip = ParameterDatabase.from_mapping(
        first.to_mapping(), source_registry=_registry()
    )
    assert first.hash() == roundtrip.hash()
    reviewed = first.transition(
        "leaf_exchange.exchange_rate", "REVIEWED", changed_by="r", reason="review", timestamp=TIMESTAMP
    )
    assert first.hash() != reviewed.hash()

    changed_registry = _registry()
    changed_registry.register(
        ParameterSource(
            source_id="SECOND_SOURCE",
            citation="second citation",
            organization="org",
            year=2026,
            document="doc",
            location="loc",
            accessibility="local",
        )
    )
    changed = ParameterDatabase.from_mapping(
        {"schema_version": "2.0", "parameters": [_entry()]},
        source_registry=changed_registry,
    )
    assert first.hash() != changed.hash()
