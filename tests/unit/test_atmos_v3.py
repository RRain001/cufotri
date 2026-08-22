from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cteas_ufotri.coupling.atmos_v3 import (
    AtmosphericForcingError,
    AtmosphericForcingMetadata,
    AtmosphericHTOForcing,
    AtmosphericMetadataError,
    AtmosphericUnitError,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PROVENANCE = ForcingProvenance(
    source_id="p7-unit",
    source_version="1",
    artifact_sha256="a" * 64,
    spatial_reference="toy-grid",
    temporal_resolution_s=60.0,
)


def make_metadata(**overrides: object) -> AtmosphericForcingMetadata:
    values: dict[str, object] = {
        "model_name": "test-atmosphere",
        "version": "0",
        "grid_definition": "toy-grid",
        "time_resolution": 60.0,
        "source_dataset": "synthetic-interface-fixture",
        "creation_time": START,
        "quality_flag": "unreviewed",
    }
    values.update(overrides)
    return AtmosphericForcingMetadata(**values)


def make_forcing(**overrides: object) -> AtmosphericHTOForcing:
    values: dict[str, object] = {
        "timestamp": START,
        "location": "toy-site",
        "air_hto_concentration": 60.0,
        "deposition_flux": 1.0,
        "temperature": 293.15,
        "humidity": 0.5,
        "wind_speed": 2.0,
        "precipitation": 0.0,
        "source": "test-atmosphere",
        "provenance": PROVENANCE,
        "metadata": make_metadata(),
    }
    values.update(overrides)
    return AtmosphericHTOForcing(**values)


def test_metadata_and_forcing_expose_required_fields_and_are_immutable() -> None:
    forcing = make_forcing(location=[31.2, 117.1])

    assert forcing.location == (31.2, 117.1)
    assert forcing.air_hto_concentration == 60.0
    assert forcing.air_ht0_concentration == 60.0
    assert forcing.deposition_flux_unit == "Bq m^-2 s^-1"
    assert forcing.temperature_unit == "K"
    assert forcing.humidity_unit == "1"
    assert forcing.wind_speed_unit == "m s^-1"
    assert forcing.precipitation_unit == "m s^-1"
    assert make_metadata().time_resolution_unit == "s"

    with pytest.raises(FrozenInstanceError):
        forcing.temperature = 300.0  # type: ignore[misc]


def test_zero_spelling_is_accepted_as_the_concentration_alias() -> None:
    forcing = make_forcing(
        air_hto_concentration=None,
        air_ht0_concentration=12.5,
    )

    assert forcing.air_hto_concentration == pytest.approx(12.5)
    assert forcing.air_ht0_concentration == pytest.approx(12.5)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("humidity", 1.1, AtmosphericForcingError),
        ("deposition_flux", -1.0, AtmosphericForcingError),
        ("temperature", 0.0, AtmosphericForcingError),
        ("air_hto_concentration", -1.0, AtmosphericForcingError),
        ("temperature_unit", "degC", AtmosphericUnitError),
    ],
)
def test_forcing_contract_rejects_invalid_values_and_units(
    field: str,
    value: object,
    error: type[ValueError],
) -> None:
    with pytest.raises(error):
        make_forcing(**{field: value})


def test_metadata_requires_utc_and_positive_time_resolution() -> None:
    with pytest.raises(AtmosphericMetadataError):
        make_metadata(creation_time=datetime(2026, 1, 1))
    with pytest.raises(AtmosphericMetadataError):
        make_metadata(time_resolution=0.0)


def test_forcing_adapters_return_existing_leaf_and_soil_input_types() -> None:
    forcing = make_forcing()

    leaf_forcing = forcing.to_leaf_forcing()
    soil_forcing = forcing.to_soil_forcing()

    assert leaf_forcing.time == START
    assert leaf_forcing.air_hto_concentration_bq_m3 == pytest.approx(60.0)
    assert leaf_forcing.air_temperature_k == pytest.approx(293.15)
    assert leaf_forcing.relative_humidity == pytest.approx(0.5)
    assert soil_forcing.deposition_flux_bq_m2_s == pytest.approx(1.0)
    assert forcing.leaf_forcing() == leaf_forcing
    assert forcing.soil_forcing() == soil_forcing
