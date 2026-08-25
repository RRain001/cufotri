from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.food_v3 import (
    FoodParameterError,
    FoodTransferSolver,
    HarvestParameters,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState
from cteas_ufotri.plant.tfwt_v3 import TFWTState


PROVENANCE = ForcingProvenance(
    source_id="p6-5-food-unit-test",
    source_version="1",
    artifact_sha256="e" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=1.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def obt_state(inventory: float) -> OBTState:
    return OBTState.from_inventory(
        plant_identifier="plant-001",
        crop="test-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=inventory,
        plant_mass_kg_m2=1.0,
        timestamp=START,
        provenance=PROVENANCE,
    )


def tfwt_state(inventory: float) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-001",
        crop="test-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=1.0,
        time=START,
        provenance=PROVENANCE,
    )


def parameters(
    *,
    harvest_fraction: float = 0.5,
    tfwt_harvest_fraction: float | None = None,
) -> HarvestParameters:
    return HarvestParameters(
        plant_identifier="plant-001",
        crop_identifier="test-crop",
        growth_stage="vegetative",
        food_product_identifier="food-001",
        harvest_fraction=harvest_fraction,
        harvest_area_m2=2.0,
        tfwt_harvest_fraction=tfwt_harvest_fraction,
        provenance=PROVENANCE,
    )


def test_positive_obt_inventory_transfers_to_food_product() -> None:
    result = FoodTransferSolver().advance(
        obt_state(10.0),
        tfwt_state(0.0),
        parameters(),
    )

    assert result.harvest_state.inventory() == pytest.approx(10.0)
    assert result.harvest_state.product() == "food-001"
    assert result.food_inventory.inventory() == pytest.approx(10.0)
    assert result.food_inventory.obt_inventory_bq == pytest.approx(10.0)
    assert result.food_inventory.product() == "food-001"


def test_zero_plant_inventory_produces_zero_food_inventory() -> None:
    result = FoodTransferSolver(parameters=parameters()).advance(
        obt_state(0.0),
        tfwt_state(0.0),
    )

    assert result.harvest_state.inventory() == pytest.approx(0.0)
    assert result.food_inventory.inventory() == pytest.approx(0.0)


def test_harvest_conservation_closes_for_obt_and_tfwt_components() -> None:
    result = FoodTransferSolver().advance(
        obt_state(10.0),
        tfwt_state(20.0),
        parameters(harvest_fraction=0.5, tfwt_harvest_fraction=0.25),
    )
    balance = result.balance

    assert balance.obt_source_bq == pytest.approx(20.0)
    assert balance.tfwt_source_bq == pytest.approx(40.0)
    assert balance.harvest_transfer_bq == pytest.approx(20.0)
    assert balance.remaining_plant_inventory_bq == pytest.approx(40.0)
    assert balance.plant_inventory_bq == pytest.approx(
        balance.harvest_transfer_bq
        + balance.remaining_plant_inventory_bq
    )
    assert balance.residual_bq == pytest.approx(0.0)


def test_harvest_and_food_states_are_immutable_and_have_no_downstream_fields() -> None:
    result = FoodTransferSolver().advance(
        obt_state(1.0),
        tfwt_state(0.0),
        parameters(),
    )

    with pytest.raises(FrozenInstanceError):
        result.harvest_state.harvest_inventory_bq = 0.0  # type: ignore[misc]
    assert not hasattr(result.harvest_state, "dose")
    assert not hasattr(result.harvest_state, "ingestion")
    assert not hasattr(result.harvest_state, "population")
    assert not hasattr(result.food_inventory, "dose")


def test_food_transfer_requires_explicit_provisional_parameters() -> None:
    with pytest.raises(FoodParameterError, match="HarvestParameters"):
        FoodTransferSolver().advance(obt_state(1.0), tfwt_state(0.0))
    with pytest.raises(FoodParameterError, match="provisional"):
        HarvestParameters(
            plant_identifier="plant-001",
            crop_identifier="test-crop",
            growth_stage="vegetative",
            food_product_identifier="food-001",
            harvest_fraction=0.5,
            harvest_area_m2=2.0,
            provenance=PROVENANCE,
            parameter_status="validated",
        )


def test_result_supports_explicit_harvest_and_food_unpacking() -> None:
    harvest, food = FoodTransferSolver().advance(
        obt_state(1.0),
        tfwt_state(0.0),
        parameters(),
    )

    assert harvest.product() == food.product()
    assert harvest.inventory() == pytest.approx(food.inventory())
