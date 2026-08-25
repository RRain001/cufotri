from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    InvalidResistanceError,
    LeafExchangeFlux,
    MissingParameterError,
    ParameterUseNotAllowedError,
    ResistanceChain,
    ResistanceCoordinates,
    UnitMismatchError,
    signed_leaf_exchange_flux,
)


PROVENANCE = ForcingProvenance(
    source_id="unit-test-forcing",
    source_version="1",
    artifact_sha256="0" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=3600.0,
)


def forcing(air_concentration: float = 100.0) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        air_hto_concentration_bq_m3=air_concentration,
        air_temperature_k=293.15,
        relative_humidity=0.5,
        provenance=PROVENANCE,
        wind_speed_m_s=2.0,
        shortwave_radiation_w_m2=100.0,
        boundary_layer_height_m=500.0,
        day_night="day",
    )


def test_resistance_sum_and_exchange_coefficient() -> None:
    chain = ResistanceChain.from_components(10.0, 20.0, 30.0)

    assert chain.total_resistance == 60.0
    assert chain.exchange_velocity == pytest.approx(1.0 / 60.0)
    assert chain.resistance_unit == "s m^-1"
    assert chain.exchange_velocity_unit == "m s^-1"


@pytest.mark.parametrize(
    "components",
    [
        (-1.0, 20.0, 30.0),
        (10.0, 0.0, 30.0),
        (10.0, 20.0, -0.1),
    ],
)
def test_zero_or_negative_resistance_fails_closed(
    components: tuple[float, float, float],
) -> None:
    with pytest.raises(InvalidResistanceError):
        ResistanceChain.from_components(*components)


def test_resistance_unit_must_be_explicit_si() -> None:
    with pytest.raises(UnitMismatchError):
        ResistanceChain.from_components(10.0, 20.0, 30.0, resistance_unit="cm s^-1")


def test_parameter_database_lookup_is_required_and_nonproduction() -> None:
    class Provider:
        def lookup(self, name, coordinates, *, production=False):
            assert production is False
            assert coordinates["crop"] == "test_crop"
            return {
                "r_a": 10.0,
                "r_b": 20.0,
                "r_c": 30.0,
            }[name]

    coordinates = ResistanceCoordinates("test_crop", "vegetative", 293.15, 0.5)
    chain = ResistanceChain.from_parameter_database(
        Provider(),
        coordinates,
        parameter_names={
            "aerodynamic_resistance": "r_a",
            "boundary_layer_resistance": "r_b",
            "canopy_resistance": "r_c",
        },
    )

    assert chain.total_resistance == 60.0


def test_missing_parameter_fails_without_default() -> None:
    class MissingProvider:
        def lookup(self, name, coordinates, *, production=False):
            raise KeyError(name)

    with pytest.raises(MissingParameterError):
        ResistanceChain.from_parameter_database(
            MissingProvider(),
            ResistanceCoordinates("test_crop", "vegetative", 293.15, 0.5),
            parameter_names={
                "aerodynamic_resistance": "missing.r_a",
                "boundary_layer_resistance": "missing.r_b",
                "canopy_resistance": "missing.r_c",
            },
        )


def test_active_parameter_is_rejected() -> None:
    class ActiveProvider:
        def get_provenance(self, name):
            return {"status": "ACTIVE"}

        def lookup(self, name, coordinates, *, production=False):
            return 10.0

    with pytest.raises(ParameterUseNotAllowedError):
        ResistanceChain.from_parameter_database(
            ActiveProvider(),
            ResistanceCoordinates("test_crop", "vegetative", 293.15, 0.5),
            parameter_names={
                "aerodynamic_resistance": "active.r_a",
                "boundary_layer_resistance": "active.r_b",
                "canopy_resistance": "active.r_c",
            },
        )


def test_signed_flux_has_one_authoritative_boundary_field() -> None:
    uptake = signed_leaf_exchange_flux(
        forcing(),
        ResistanceChain.from_components(10.0, 20.0, 30.0),
        equilibrium_air_concentration_bq_m3=0.0,
    )
    reemission = signed_leaf_exchange_flux(
        forcing(0.0),
        ResistanceChain.from_components(10.0, 20.0, 30.0),
        equilibrium_air_concentration_bq_m3=100.0,
    )

    assert isinstance(uptake, LeafExchangeFlux)
    assert uptake.air_to_leaf_flux_bq_m2_s > 0.0
    assert reemission.air_to_leaf_flux_bq_m2_s < 0.0
    assert uptake.has_separate_reemission_flux is False
    assert not hasattr(uptake, "reemission_flux")
