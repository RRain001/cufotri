"""Executable contract examples for the V3-P5.3 atmospheric boundary.

P5.3 intentionally adds no production record class. These tests validate the
frozen data rules as a test-only contract model and check that the canonical
field names and units are present in the normative document.
"""

from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
from typing import Any, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/v3/interfaces/atmospheric_hto_forcing_contract.md"
REQUIRED = (
    "time",
    "air_hto_concentration",
    "air_temperature",
    "relative_humidity",
)
OPTIONAL = (
    "precipitation",
    "shortwave_radiation",
    "longwave_radiation",
    "wind_speed",
    "boundary_layer_height",
    "surface_deposition_flux",
)


def _finite(value: Any, name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite")
    return numeric


def _validate_record(record: Mapping[str, Any]) -> None:
    missing = [name for name in REQUIRED if name not in record]
    if missing:
        raise ValueError(f"missing required fields: {missing}")

    timestamp = record["time"]
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise ValueError("time must be timezone-aware")
    if timestamp.utcoffset() != timedelta(0):
        raise ValueError("time must be UTC")

    concentration = _finite(record["air_hto_concentration"], "air_hto_concentration")
    temperature = _finite(record["air_temperature"], "air_temperature")
    humidity = _finite(record["relative_humidity"], "relative_humidity")
    if concentration < 0.0:
        raise ValueError("air_hto_concentration must be non-negative")
    if temperature <= 0.0:
        raise ValueError("air_temperature must be positive")
    if not 0.0 <= humidity <= 1.0:
        raise ValueError("relative_humidity must be in [0, 1]")

    nonnegative_optional = {
        "precipitation",
        "shortwave_radiation",
        "wind_speed",
        "surface_deposition_flux",
    }
    positive_optional = {"boundary_layer_height"}
    for name in OPTIONAL:
        if name not in record or record[name] is None:
            continue
        value = _finite(record[name], name)
        if name in nonnegative_optional and value < 0.0:
            raise ValueError(f"{name} must be non-negative")
        if name in positive_optional and value <= 0.0:
            raise ValueError(f"{name} must be positive")


def _validate_sequence(records: list[Mapping[str, Any]], cadence_s: float) -> None:
    if not math.isfinite(cadence_s) or cadence_s <= 0.0:
        raise ValueError("cadence must be positive and finite")
    for record in records:
        _validate_record(record)
    for previous, current in zip(records, records[1:]):
        delta_s = (current["time"] - previous["time"]).total_seconds()
        if delta_s != cadence_s:
            raise ValueError("forcing sequence is not continuous")


def _record(timestamp: datetime, **overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "time": timestamp,
        "air_hto_concentration": 1.0,
        "air_temperature": 293.15,
        "relative_humidity": 0.5,
    }
    record.update(overrides)
    return record


def test_document_freezes_canonical_fields_and_units() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for field in REQUIRED + OPTIONAL:
        assert f"`{field}`" in contract
    for unit in ("Bq/m3", "K", "0, 1", "m/s", "W/m2", "Bq/m2/s"):
        assert unit in contract
    assert "FAIL_CLOSED" in contract
    assert "Timezone-aware UTC" in contract


@pytest.mark.parametrize("field", REQUIRED)
def test_missing_required_field_is_rejected(field: str) -> None:
    record = _record(datetime(2026, 1, 1, tzinfo=timezone.utc))
    record.pop(field)
    with pytest.raises(ValueError):
        _validate_record(record)


@pytest.mark.parametrize(
    "field",
    ("air_hto_concentration", "air_temperature", "relative_humidity", *OPTIONAL),
)
def test_nonfinite_field_is_rejected(field: str) -> None:
    record = _record(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        **{field: math.nan},
    )
    with pytest.raises(ValueError):
        _validate_record(record)


def test_time_sequence_must_be_utc_strict_and_contiguous() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = [_record(start), _record(start + timedelta(hours=1))]
    _validate_sequence(records, 3600.0)

    with pytest.raises(ValueError):
        _validate_sequence(
            [_record(start), _record(start + timedelta(hours=2))], 3600.0
        )
    with pytest.raises(ValueError):
        _validate_sequence(
            [_record(start), _record(start + timedelta(hours=1, minutes=1))],
            3600.0,
        )


def test_optional_fields_may_be_absent_without_hidden_defaults() -> None:
    record = _record(datetime(2026, 1, 1, tzinfo=timezone.utc))
    _validate_record(record)
    assert all(field not in record for field in OPTIONAL)
