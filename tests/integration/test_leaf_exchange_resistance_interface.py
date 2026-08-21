from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    ResistanceChain,
    signed_leaf_exchange_flux,
)


def make_forcing(air_hto: float) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        air_hto_concentration_bq_m3=air_hto,
        air_temperature_k=293.15,
        relative_humidity=0.5,
        wind_speed_m_s=2.0,
        shortwave_radiation_w_m2=100.0,
        boundary_layer_height_m=500.0,
        day_night="day",
        provenance=ForcingProvenance(
            source_id="resistance-integration",
            source_version="1",
            artifact_sha256="1" * 64,
            spatial_reference="test-grid",
            temporal_resolution_s=3600.0,
        ),
    )


def test_forcing_resistance_chain_and_signed_flux_boundary() -> None:
    chain = ResistanceChain.from_components(10.0, 20.0, 30.0)

    uptake = signed_leaf_exchange_flux(make_forcing(100.0), chain, 0.0)
    reemission = signed_leaf_exchange_flux(make_forcing(0.0), chain, 100.0)

    assert chain.total_resistance == 60.0
    assert uptake.air_to_leaf_flux_bq_m2_s == pytest.approx(100.0 / 60.0)
    assert reemission.air_to_leaf_flux_bq_m2_s == pytest.approx(-100.0 / 60.0)
    assert uptake.has_separate_reemission_flux is False
    assert reemission.has_separate_reemission_flux is False
