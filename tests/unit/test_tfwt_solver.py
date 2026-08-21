from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    LeafExchangeFlux,
)
from cteas_ufotri.plant.tfwt_v3 import (
    TFWTFluxError,
    TFWTState,
    TFWTStateError,
    TFWTStorageSolver,
)


PROVENANCE = ForcingProvenance(
    source_id="tfwt-unit-test",
    source_version="1",
    artifact_sha256="2" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=1.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def state(inventory: float = 0.0) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-001",
        crop="test_crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=2.0,
        time=START,
        provenance=PROVENANCE,
    )


def flux(value: float) -> LeafExchangeFlux:
    return LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=value)


def test_constant_positive_air_input_increases_tfwt() -> None:
    result = TFWTStorageSolver().advance(state(), flux(3.0), 10.0)

    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(30.0)
    assert result.state.tfwt_concentration_bq_kg_water == pytest.approx(15.0)
    assert result.state.time.timestamp() == pytest.approx(START.timestamp() + 10.0)
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_zero_air_input_with_outward_flux_decreases_tfwt() -> None:
    result = TFWTStorageSolver().advance(state(20.0), flux(-1.5), 4.0)

    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(14.0)
    assert result.state.tfwt_concentration_bq_kg_water == pytest.approx(7.0)
    assert result.balance.leaf_exchange_input_bq_m2 == pytest.approx(-6.0)


def test_storage_balance_input_equals_storage_plus_losses() -> None:
    result = TFWTStorageSolver().advance(
        state(10.0),
        flux(2.0),
        5.0,
        water_loss_flux_bq_m2_s=0.4,
        transformation_flux_bq_m2_s=0.2,
    )

    assert result.balance.storage_change_bq_m2 == pytest.approx(7.0)
    assert result.state.tfwt_inventory_bq_m2 == pytest.approx(17.0)
    assert result.balance.leaf_exchange_input_bq_m2 == pytest.approx(
        result.balance.storage_change_bq_m2
        + result.balance.water_loss_bq_m2
        + result.balance.transformation_bq_m2
    )
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_solver_consumes_signed_flux_without_creating_obt_state() -> None:
    next_state = TFWTStorageSolver().step(state(), flux(1.0), 1.0)

    assert next_state.tfwt_inventory_bq_m2 == pytest.approx(1.0)
    assert not hasattr(next_state, "obt_inventory_bq_m2")
    assert not hasattr(next_state, "root_uptake")


@pytest.mark.parametrize("interval", [0.0, -1.0])
def test_nonpositive_interval_fails_closed(interval: float) -> None:
    with pytest.raises(TFWTFluxError):
        TFWTStorageSolver().step(state(), flux(1.0), interval)


def test_negative_loss_or_transformation_fails_closed() -> None:
    with pytest.raises(TFWTFluxError):
        TFWTStorageSolver().step(
            state(),
            flux(1.0),
            1.0,
            water_loss_flux_bq_m2_s=-0.1,
        )
    with pytest.raises(TFWTFluxError):
        TFWTStorageSolver().step(
            state(),
            flux(1.0),
            1.0,
            transformation_flux_bq_m2_s=-0.1,
        )


def test_negative_inventory_result_fails_closed() -> None:
    with pytest.raises(TFWTFluxError):
        TFWTStorageSolver().step(state(1.0), flux(-2.0), 1.0)


def test_inconsistent_state_fails_closed() -> None:
    with pytest.raises(TFWTStateError):
        TFWTState(
            plant_identifier="plant-001",
            crop="test_crop",
            growth_stage="vegetative",
            tfwt_concentration_bq_kg_water=1.0,
            tfwt_inventory_bq_m2=3.0,
            water_content_kg_m2=2.0,
            time=START,
            provenance=PROVENANCE,
        )
