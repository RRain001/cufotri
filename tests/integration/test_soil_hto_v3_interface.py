from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.soil_v3 import (
    SoilForcing,
    SoilParameters,
    SoilProvenance,
    SoilState,
    SoilStorageSolver,
)


PROVENANCE = SoilProvenance(
    source_id="p6-3-integration-test",
    source_version="1",
    artifact_sha256="d" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=60.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PARAMETERS = SoilParameters(tritium_half_life_s=1000.0)


def make_state(inventory: float, layer_id: str) -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="soil-integration-001",
        layer_id=layer_id,
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=inventory,
        timestamp=START,
        provenance=PROVENANCE,
    )


def test_state_public_advance_uses_explicit_deposition_and_half_life() -> None:
    next_state = make_state(0.0, "surface").advance(
        60.0,
        SoilForcing(deposition_flux_bq_m2_s=1.0),
        parameters=PARAMETERS,
    )

    assert next_state.inventory() > 0.0
    assert next_state.timestamp.timestamp() == pytest.approx(
        START.timestamp() + 60.0
    )


def test_signed_transport_can_be_chained_between_two_public_layer_states() -> None:
    solver = SoilStorageSolver(parameters=PARAMETERS)
    upper = solver.advance(
        make_state(50.0, "surface"),
        SoilForcing(transport_flux_bq_m2_s=-0.25),
        60.0,
    )
    lower = solver.advance(
        make_state(0.0, "lower"),
        SoilForcing(transport_flux_bq_m2_s=0.25),
        60.0,
    )

    assert upper.state.inventory() < 50.0
    assert lower.state.inventory() > 0.0
    assert upper.balance.transport_loss_bq_m2 == pytest.approx(
        lower.balance.transport_input_bq_m2
    )
