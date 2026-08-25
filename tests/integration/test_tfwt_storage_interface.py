from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    ResistanceChain,
    signed_leaf_exchange_flux,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState, TFWTStorageSolver


def make_forcing(air_hto: float) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        air_hto_concentration_bq_m3=air_hto,
        air_temperature_k=293.15,
        relative_humidity=0.5,
        provenance=ForcingProvenance(
            source_id="tfwt-interface-test",
            source_version="1",
            artifact_sha256="3" * 64,
            spatial_reference="test-grid",
            temporal_resolution_s=10.0,
        ),
    )


def make_state(inventory: float = 0.0) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-001",
        crop="test_crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=1.0,
        time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        provenance=ForcingProvenance(
            source_id="tfwt-state-test",
            source_version="1",
            artifact_sha256="4" * 64,
            spatial_reference="test-grid",
            temporal_resolution_s=10.0,
        ),
    )


def test_p6_2b_1_flux_flows_into_tfwt_storage_only() -> None:
    resistance = ResistanceChain.from_components(10.0, 20.0, 30.0)
    leaf_flux = signed_leaf_exchange_flux(
        make_forcing(60.0),
        resistance,
        equilibrium_air_concentration_bq_m3=0.0,
    )

    result = TFWTStorageSolver().advance(make_state(), leaf_flux, 10.0)

    assert leaf_flux.air_to_leaf_flux_bq_m2_s == pytest.approx(1.0)
    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(10.0)
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_zero_air_input_consumes_negative_leaf_flux() -> None:
    resistance = ResistanceChain.from_components(10.0, 20.0, 30.0)
    leaf_flux = signed_leaf_exchange_flux(
        make_forcing(0.0),
        resistance,
        equilibrium_air_concentration_bq_m3=60.0,
    )

    result = TFWTStorageSolver().advance(make_state(20.0), leaf_flux, 10.0)

    assert leaf_flux.air_to_leaf_flux_bq_m2_s == pytest.approx(-1.0)
    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(10.0)
