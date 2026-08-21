from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    LeafExchangeFlux,
)
from cteas_ufotri.plant.root_v3 import RootUptakeForcing, RootUptakeSolver
from cteas_ufotri.plant.soil_v3 import SoilProvenance, SoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState, TFWTStorageSolver


PROVENANCE = ForcingProvenance(
    source_id="p6-4-root-tfwt-integration",
    source_version="1",
    artifact_sha256="c" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p6-4-soil-interface",
    source_version="1",
    artifact_sha256="d" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_soil(inventory: float) -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="soil-interface-001",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=inventory,
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )


def make_tfwt(inventory: float = 0.0) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-interface-001",
        crop="test-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=1.0,
        time=START,
        provenance=PROVENANCE,
    )


def make_root_forcing(interval_seconds: float = 10.0) -> RootUptakeForcing:
    return RootUptakeForcing(
        plant_identifier="plant-interface-001",
        root_zone_identifier="root-zone-001",
        interval_seconds=interval_seconds,
        provenance=PROVENANCE,
    )


def test_soil_root_tfwt_toy_pathway_closes_transfer_and_storage() -> None:
    soil = make_soil(40.0)
    root_flux = RootUptakeSolver(k_root_m_s=5.0e-4).advance(
        soil,
        make_root_forcing(),
    )

    result = TFWTStorageSolver().advance(
        make_tfwt(2.0),
        LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=0.0),
        10.0,
        root_uptake_flux=root_flux,
    )

    assert root_flux.uptake_flux_bq_m2_s == pytest.approx(1.0)
    assert root_flux.inventory() == pytest.approx(10.0)
    assert result.state.inventory() == pytest.approx(12.0)
    assert result.balance.root_uptake_input_bq_m2 == pytest.approx(10.0)
    assert result.balance.storage_change_bq_m2 == pytest.approx(10.0)
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_public_tfwt_state_advance_consumes_root_flux_without_root_state() -> None:
    root_flux = RootUptakeSolver(k_root_m_s=1.0e-3).advance(
        make_soil(10.0),
        make_root_forcing(),
    )

    next_tfwt = make_tfwt().advance(
        10.0,
        LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=0.0),
        root_uptake_flux=root_flux,
    )

    assert next_tfwt.inventory() == pytest.approx(root_flux.inventory())
    assert not hasattr(next_tfwt, "root_uptake")
    assert not hasattr(next_tfwt, "soil_inventory")
