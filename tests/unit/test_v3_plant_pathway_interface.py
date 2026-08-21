from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    LeafExchangeFlux,
    ResistanceChain,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.plant.v3 import (
    V3PlantPathway,
    V3PlantState,
    validate_pathway_state,
)


PROVENANCE = ForcingProvenance(
    source_id="v3-pathway-unit-test",
    source_version="1",
    artifact_sha256="a" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_tfwt_state(inventory: float = 0.0) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-001",
        crop="test_crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=2.0,
        time=START,
        provenance=PROVENANCE,
    )


def make_forcing(air_hto: float) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        time=START,
        air_hto_concentration_bq_m3=air_hto,
        air_temperature_k=293.15,
        relative_humidity=0.5,
        provenance=PROVENANCE,
    )


def test_tfwt_public_api_exposes_inventory_concentration_and_advance() -> None:
    state = make_tfwt_state(4.0)

    assert state.inventory() == pytest.approx(4.0)
    assert state.activity_concentration() == pytest.approx(2.0)

    next_state = state.advance(10.0, LeafExchangeFlux(1.5))

    assert next_state.inventory() == pytest.approx(19.0)
    assert next_state.activity_concentration() == pytest.approx(9.5)


def test_v3_pathway_connects_resistance_flux_to_tfwt_state() -> None:
    pathway = V3PlantPathway(
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0)
    )
    step = pathway.advance(
        V3PlantState(tfwt=make_tfwt_state()),
        make_forcing(60.0),
        equilibrium_air_concentration_bq_m3=0.0,
        interval_seconds=10.0,
    )

    assert step.leaf_exchange_flux.air_to_leaf_flux_bq_m2_s == pytest.approx(1.0)
    assert step.state.inventory() == pytest.approx(10.0)
    assert step.state.obt is None


def test_reserved_obt_slot_is_rejected_without_an_obt_solver() -> None:
    state_with_reserved_obt = V3PlantState(
        tfwt=make_tfwt_state(),
        obt=object(),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="OBT pathway is reserved"):
        validate_pathway_state(state_with_reserved_obt)
