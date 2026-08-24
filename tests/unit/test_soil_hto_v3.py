from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.soil_v3 import (
    SoilForcing,
    SoilInputError,
    SoilParameterError,
    SoilParameters,
    SoilProvenance,
    SoilState,
    SoilStateError,
    SoilStorageSolver,
)


PROVENANCE = SoilProvenance(
    source_id="p6-3-unit-test",
    source_version="1",
    artifact_sha256="c" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def state(inventory: float, layer_id: str = "surface") -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="soil-001",
        layer_id=layer_id,
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=inventory,
        timestamp=START,
        provenance=PROVENANCE,
    )


def solver(half_life_s: float = 1000.0) -> SoilStorageSolver:
    return SoilStorageSolver(
        parameters=SoilParameters(tritium_half_life_s=half_life_s)
    )


def test_positive_deposition_increases_soil_inventory() -> None:
    result = solver().advance(
        state(0.0),
        SoilForcing(deposition_flux_bq_m2_s=2.0),
        10.0,
    )

    assert result.state.inventory() > 0.0
    assert result.balance.deposition_input_bq_m2 == pytest.approx(20.0)
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_zero_input_causes_soil_inventory_to_decay() -> None:
    result = solver().advance(state(20.0), SoilForcing(), 100.0)

    assert result.state.inventory() < 20.0
    assert result.balance.decay_loss_bq_m2 > 0.0
    assert result.balance.residual_bq_m2 == pytest.approx(0.0)


def test_soil_input_equals_storage_change_transport_loss_and_decay() -> None:
    result = solver().advance(
        state(10.0),
        SoilForcing(
            deposition_flux_bq_m2_s=0.5,
            transport_flux_bq_m2_s=-0.1,
        ),
        10.0,
    )

    balance = result.balance
    assert balance.input_bq_m2 == pytest.approx(
        balance.storage_change_bq_m2
        + balance.transport_loss_bq_m2
        + balance.decay_loss_bq_m2
    )
    assert balance.residual_bq_m2 == pytest.approx(0.0)


def test_upper_layer_loss_equals_lower_layer_gain_plus_remaining_loss() -> None:
    upper_result = solver(1.0e30).advance(
        state(100.0, "surface"),
        SoilForcing(transport_flux_bq_m2_s=-0.2),
        10.0,
    )
    lower_result = solver(1.0e30).advance(
        state(0.0, "lower"),
        SoilForcing(transport_flux_bq_m2_s=0.2),
        10.0,
    )

    upper_loss = 100.0 - upper_result.state.inventory()
    lower_gain = lower_result.state.inventory()
    remaining_loss = (
        upper_result.balance.decay_loss_bq_m2
        + lower_result.balance.decay_loss_bq_m2
    )
    assert upper_loss == pytest.approx(lower_gain + remaining_loss)
    assert upper_result.balance.transport_loss_bq_m2 == pytest.approx(
        lower_result.balance.transport_input_bq_m2
    )


def test_state_concentration_is_derived_and_state_update_is_immutable() -> None:
    initial = state(8.0)
    next_state = solver().step(initial, SoilForcing(), 10.0)

    assert initial.inventory() == pytest.approx(8.0)
    assert initial.concentration() == pytest.approx(400.0)
    assert next_state is not initial
    assert next_state.concentration() == pytest.approx(
        next_state.inventory() / 0.02
    )
    assert not hasattr(initial, "root_uptake")
    assert not hasattr(initial, "plant_inventory")


def test_state_advance_requires_explicit_half_life() -> None:
    with pytest.raises(SoilParameterError, match="explicit tritium_half_life_s"):
        state(0.0).advance(10.0, SoilForcing())


def test_negative_deposition_and_excess_transport_fail_closed() -> None:
    with pytest.raises(SoilInputError):
        SoilForcing(deposition_flux_bq_m2_s=-1.0)
    with pytest.raises(SoilInputError, match="negative inventory"):
        solver().step(
            state(0.0),
            SoilForcing(transport_flux_bq_m2_s=-1.0),
            10.0,
        )


def test_inconsistent_soil_concentration_fails_closed() -> None:
    with pytest.raises(SoilStateError):
        SoilState(
            soil_identifier="soil-001",
            layer_id="surface",
            layer_depth_m=0.05,
            soil_water_content=0.02,
            soil_water_inventory_bq_m2=8.0,
            soil_water_concentration=1.0,
            timestamp=START,
            provenance=PROVENANCE,
        )
