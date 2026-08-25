from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cteas_ufotri.exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    INTAKE_INVENTORY_UNIT,
    ConsumptionParameters,
    FoodIntakeSolver,
    IntakeInputError,
    IntakeParameterError,
    IntakeUnitError,
)
from cteas_ufotri.plant.food_v3 import FoodInventory
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance


PROVENANCE = ForcingProvenance(
    source_id="p6-6a-intake-unit-test",
    source_version="1",
    artifact_sha256="a" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=1.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def food_inventory(
    activity_bq: float,
    *,
    product: str = "food-001",
) -> FoodInventory:
    return FoodInventory.from_components(
        food_product_identifier=product,
        obt_inventory_bq=activity_bq,
        tfwt_inventory_bq=0.0,
        timestamp=START,
        provenance=PROVENANCE,
    )


def parameters(
    *,
    amount_kg_year: float = 2.0,
    food_mass_kg: float = 4.0,
    age_group: str = "adult",
    product: str = "food-001",
) -> ConsumptionParameters:
    return ConsumptionParameters(
        food_product_identifier=product,
        age_group_identifier=age_group,
        annual_consumption_amount=amount_kg_year,
        consumption_unit=CONSUMPTION_RATE_UNIT,
        provenance=PROVENANCE,
        food_product_mass_kg=food_mass_kg,
    )


def test_positive_food_inventory_produces_positive_annual_intake() -> None:
    state = FoodIntakeSolver(consumer_identifier="consumer-001").advance(
        food_inventory(40.0),
        parameters(),
    )

    assert state.inventory() == pytest.approx(20.0)
    assert state.inventory_unit == INTAKE_INVENTORY_UNIT
    assert state.consumption_rate == pytest.approx(2.0)
    assert state.consumption_rate_unit == CONSUMPTION_RATE_UNIT
    assert state.consumer() == "consumer-001"
    assert state.food_product() == "food-001"


def test_zero_food_inventory_produces_zero_annual_intake() -> None:
    state = FoodIntakeSolver(consumer_identifier="consumer-001").advance(
        food_inventory(0.0),
        parameters(),
    )

    assert state.inventory() == pytest.approx(0.0)


def test_consumption_equation_closes_with_explicit_units() -> None:
    state = FoodIntakeSolver(consumer_identifier="consumer-001").advance(
        food_inventory(75.0),
        parameters(amount_kg_year=3.0, food_mass_kg=5.0),
    )

    food_concentration_bq_kg = 75.0 / 5.0
    expected_bq_year = food_concentration_bq_kg * 3.0
    assert state.inventory() == pytest.approx(expected_bq_year)


def test_adult_and_child_inputs_remain_separate_states() -> None:
    solver = FoodIntakeSolver(consumer_identifier="consumer-001")
    adult = solver.advance(
        food_inventory(40.0),
        parameters(age_group="adult", amount_kg_year=2.0),
    )
    child = solver.advance(
        food_inventory(40.0),
        parameters(age_group="child", amount_kg_year=1.0),
    )

    assert adult.age_group_identifier == "adult"
    assert child.age_group_identifier == "child"
    assert adult is not child
    assert adult.inventory() == pytest.approx(20.0)
    assert child.inventory() == pytest.approx(10.0)


def test_intake_state_is_immutable_and_has_no_downstream_result_fields() -> None:
    state = FoodIntakeSolver(consumer_identifier="consumer-001").advance(
        food_inventory(1.0),
        parameters(amount_kg_year=1.0, food_mass_kg=1.0),
    )

    with pytest.raises(FrozenInstanceError):
        state.intake_inventory_bq = 0.0  # type: ignore[misc]
    assert not hasattr(state, "dose")
    assert not hasattr(state, "dose_coefficient")
    assert not hasattr(state, "committed_dose")
    assert not hasattr(state, "regulatory_status")


def test_intake_requires_matching_product_and_provisional_parameters() -> None:
    with pytest.raises(IntakeInputError, match="identifiers"):
        FoodIntakeSolver(consumer_identifier="consumer-001").advance(
            food_inventory(1.0, product="food-a"),
            parameters(product="food-b"),
        )
    with pytest.raises(IntakeParameterError, match="provisional"):
        ConsumptionParameters(
            food_product_identifier="food-001",
            age_group_identifier="adult",
            annual_consumption_amount=1.0,
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=PROVENANCE,
            food_product_mass_kg=1.0,
            parameter_status="validated",
        )


def test_intake_rejects_implicit_unit_conversion() -> None:
    with pytest.raises(IntakeUnitError, match="kg/year"):
        ConsumptionParameters(
            food_product_identifier="food-001",
            age_group_identifier="adult",
            annual_consumption_amount=1.0,
            consumption_unit="kg/day",
            provenance=PROVENANCE,
            food_product_mass_kg=1.0,
        )
