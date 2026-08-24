from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    ForcingProvenance,
    ResistanceChain,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.plant.v3 import V3PlantPathway, V3PlantState


PROVENANCE = ForcingProvenance(
    source_id="v3-pathway-toy",
    source_version="1",
    artifact_sha256="b" * 64,
    spatial_reference="toy-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_forcing(time: datetime, air_hto: float) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        time=time,
        air_hto_concentration_bq_m3=air_hto,
        air_temperature_k=293.15,
        relative_humidity=0.5,
        provenance=PROVENANCE,
    )


def make_state(inventory: float = 0.0) -> V3PlantState:
    return V3PlantState(
        tfwt=TFWTState.from_inventory(
            plant_identifier="toy-plant",
            crop="toy_crop",
            growth_stage="vegetative",
            tfwt_inventory_bq_m2=inventory,
            water_content_kg_m2=1.0,
            time=START,
            provenance=PROVENANCE,
        )
    )


def test_constant_forcing_closes_leaf_to_tfwt_inventory_balance() -> None:
    pathway = V3PlantPathway(
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0)
    )
    state = make_state()
    interval_seconds = 10.0
    total_input = 0.0

    for step_index in range(3):
        step = pathway.advance(
            state,
            make_forcing(START, 60.0),
            equilibrium_air_concentration_bq_m3=0.0,
            interval_seconds=interval_seconds,
        )
        flux = step.leaf_exchange_flux.air_to_leaf_flux_bq_m2_s
        total_input += flux * interval_seconds
        state = step.state

        residual = (
            state.inventory() - make_state().inventory() - total_input
        )
        assert residual == pytest.approx(0.0, abs=1.0e-12)
        assert state.tfwt.time == START + timedelta(
            seconds=(step_index + 1) * interval_seconds
        )

    assert state.inventory() == pytest.approx(30.0)
    assert total_input == pytest.approx(30.0)


def test_constant_reverse_forcing_decreases_tfwt_without_second_flux() -> None:
    pathway = V3PlantPathway(
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0)
    )
    step = pathway.advance(
        make_state(20.0),
        make_forcing(START, 0.0),
        equilibrium_air_concentration_bq_m3=60.0,
        interval_seconds=10.0,
    )

    assert step.leaf_exchange_flux.air_to_leaf_flux_bq_m2_s == pytest.approx(-1.0)
    assert step.state.inventory() == pytest.approx(10.0)
    assert step.leaf_exchange_flux.has_separate_reemission_flux is False
    assert not hasattr(step.state, "uptake_flux")
    assert not hasattr(step.state, "reemission_flux")
