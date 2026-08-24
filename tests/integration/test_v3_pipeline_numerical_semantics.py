from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import math

import pytest

from cteas_ufotri.v3_pipeline import V3PipelineRunner, V3SimulationState
from tests.integration.test_v3_pipeline import (
    START,
    make_forcing,
    make_obt,
    make_parameters,
    make_soil,
    make_tfwt,
)


def _run_horizon(
    interval_seconds: float,
    *,
    total_seconds: float = 40.0,
    soil_half_life_s: float = 1_000.0,
) -> V3SimulationState:
    base_parameters = make_parameters()
    parameters = replace(
        base_parameters,
        interval_seconds=interval_seconds,
        soil_parameters=replace(
            base_parameters.soil_parameters,
            tritium_half_life_s=soil_half_life_s,
        ),
    )
    runner = V3PipelineRunner(parameters=parameters)
    state: V3SimulationState | None = None
    steps = round(total_seconds / interval_seconds)
    assert steps > 0
    assert steps * interval_seconds == pytest.approx(total_seconds)

    for _ in range(steps):
        timestamp = START if state is None else state.timestamp
        forcing = make_forcing(timestamp=timestamp)
        if state is None:
            state = runner.run(
                forcing,
                soil_state=make_soil(inventory=40.0),
                tfwt_state=make_tfwt(inventory=5.0),
                obt_state=make_obt(inventory=2.0),
            )
        else:
            state = runner.advance(state, forcing)

    assert state is not None
    return state


def _continuous_inventories(state: V3SimulationState) -> tuple[float, ...]:
    return (
        state.soil_state.inventory(),
        state.tfwt_state.inventory(),
        state.obt_state.inventory(),
    )


def _assert_step_ledgers_are_finite_and_closed(state: V3SimulationState) -> None:
    assert state.ledger is not None
    balances = (
        state.ledger.soil_balance,
        state.ledger.tfwt_balance,
        state.ledger.obt_balance,
        state.ledger.root_balance,
        state.ledger.food_balance,
    )
    for balance in balances:
        for value in vars(balance).values():
            if isinstance(value, (int, float)):
                assert math.isfinite(float(value))

    assert state.ledger.soil_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.tfwt_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.obt_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.root_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.food_balance.residual_bq == pytest.approx(0.0)
    assert state.root_state.inventory() >= 0.0
    assert state.ledger.root_balance.root_transfer_bq_m2 >= 0.0
    assert state.ledger.soil_balance.decay_loss_bq_m2 >= 0.0
    assert state.ledger.obt_balance.tfwt_loss_bq_m2 >= 0.0


def test_pipeline_operator_order_matches_frozen_semantics() -> None:
    state = V3PipelineRunner(parameters=make_parameters()).run(
        make_forcing(),
        soil_state=make_soil(inventory=40.0),
        tfwt_state=make_tfwt(inventory=0.0),
        obt_state=make_obt(inventory=0.0),
    )

    assert state.ledger is not None
    # Deposition is advanced first, but root reads the original 40 Bq m^-2
    # soil snapshot.  A post-deposition root read would transfer 12.5 here.
    assert state.ledger.soil_balance.deposition_input_bq_m2 == pytest.approx(10.0)
    assert state.ledger.root_balance.initial_soil_inventory_bq_m2 == pytest.approx(40.0)
    assert state.root_state.inventory() == pytest.approx(10.0)
    assert state.soil_state.inventory() == pytest.approx(40.0)

    # OBT consumes the leaf-only TFWT intermediate; root input is applied only
    # after the OBT-reported TFWT loss is reconciled.
    assert state.ledger.tfwt_balance.leaf_exchange_input_bq_m2 == pytest.approx(10.0)
    assert state.ledger.obt_balance.tfwt_loss_bq_m2 == pytest.approx(1.0)
    assert state.obt_state.inventory() == pytest.approx(1.0)
    assert state.tfwt_state.inventory() == pytest.approx(10.0 + 10.0 - 1.0)


def test_interval_forcing_and_endpoint_timestamps_are_consistent() -> None:
    state = _run_horizon(10.0, total_seconds=10.0)

    assert state.atmospheric_state.timestamp == START
    assert state.timestamp == START + timedelta(seconds=10.0)
    endpoint_timestamps = (
        state.soil_state.timestamp,
        state.tfwt_state.time,
        state.obt_state.timestamp,
        state.root_state.timestamp,
        state.harvest_state.timestamp,
        state.food_state.timestamp,
        state.intake_state.timestamp,
        state.dose_state.timestamp,
        state.timestamp,
    )
    assert all(timestamp == state.timestamp for timestamp in endpoint_timestamps)


def test_food_intake_dose_are_non_mutating_endpoint_readouts() -> None:
    soil = make_soil(inventory=40.0)
    tfwt = make_tfwt(inventory=5.0)
    obt = make_obt(inventory=2.0)
    state = V3PipelineRunner(parameters=make_parameters()).run(
        make_forcing(),
        soil_state=soil,
        tfwt_state=tfwt,
        obt_state=obt,
    )

    assert soil.inventory() == pytest.approx(40.0)
    assert tfwt.inventory() == pytest.approx(5.0)
    assert obt.inventory() == pytest.approx(2.0)
    assert state.food_state.timestamp == state.timestamp
    assert state.intake_state.timestamp == state.timestamp
    assert state.dose_state.timestamp == state.timestamp
    assert state.food_state.inventory() == pytest.approx(
        state.harvest_state.inventory()
    )
    assert state.ledger is not None
    assert state.food_state.inventory() == pytest.approx(
        state.obt_state.inventory()
    )
    assert state.ledger.food_balance.remaining_plant_inventory_bq == pytest.approx(
        state.tfwt_state.inventory()
    )


def test_zero_forcing_remains_zero_across_multiple_steps() -> None:
    runner = V3PipelineRunner(parameters=make_parameters())
    state: V3SimulationState | None = None

    for _ in range(4):
        timestamp = START if state is None else state.timestamp
        forcing = make_forcing(timestamp=timestamp, air_hto=0.0, deposition=0.0)
        if state is None:
            state = runner.run(
                forcing,
                soil_state=make_soil(inventory=0.0),
                tfwt_state=make_tfwt(inventory=0.0),
                obt_state=make_obt(inventory=0.0),
            )
        else:
            state = runner.advance(state, forcing)

        assert state is not None
        assert all(value == pytest.approx(0.0) for value in _continuous_inventories(state))
        assert state.root_state.inventory() == pytest.approx(0.0)
        assert state.food_state.inventory() == pytest.approx(0.0)
        assert state.intake_state.inventory() == pytest.approx(0.0)
        assert state.dose_state.dose() == pytest.approx(0.0)
        _assert_step_ledgers_are_finite_and_closed(state)


def test_timestep_refinement_converges_continuous_states() -> None:
    states = {
        interval: _run_horizon(interval)
        for interval in (10.0, 5.0, 2.5)
    }

    for state in states.values():
        assert all(value >= 0.0 for value in _continuous_inventories(state))
        assert all(math.isfinite(value) for value in _continuous_inventories(state))
        _assert_step_ledgers_are_finite_and_closed(state)

    for index, name in enumerate(("soil", "tfwt", "obt")):
        coarse = _continuous_inventories(states[10.0])[index]
        medium = _continuous_inventories(states[5.0])[index]
        fine = _continuous_inventories(states[2.5])[index]
        e1 = abs(coarse - medium)
        e2 = abs(medium - fine)
        assert e1 > 0.0, name
        assert e2 < e1, name


def test_timestep_refinement_preserves_all_existing_ledgers() -> None:
    for interval in (10.0, 5.0, 2.5):
        state = _run_horizon(interval)
        _assert_step_ledgers_are_finite_and_closed(state)


def test_restart_after_one_step_is_equivalent_to_continuous_path() -> None:
    runner = V3PipelineRunner(parameters=make_parameters())
    first = runner.run(
        make_forcing(),
        soil_state=make_soil(),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )
    second_continuous = runner.advance(
        first,
        make_forcing(timestamp=first.timestamp),
    )

    restored = V3SimulationState.from_json(first.to_json())
    second_restarted = runner.advance(
        restored,
        make_forcing(timestamp=first.timestamp),
    )

    assert second_restarted.timestamp == second_continuous.timestamp
    assert _continuous_inventories(second_restarted) == pytest.approx(
        _continuous_inventories(second_continuous)
    )
    assert second_restarted.root_state.inventory() == pytest.approx(
        second_continuous.root_state.inventory()
    )
    assert second_restarted.food_state.inventory() == pytest.approx(
        second_continuous.food_state.inventory()
    )
    assert second_restarted.intake_state.inventory() == pytest.approx(
        second_continuous.intake_state.inventory()
    )
    assert second_restarted.dose_state.dose() == pytest.approx(
        second_continuous.dose_state.dose()
    )
    assert second_restarted == second_continuous
