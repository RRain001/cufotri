from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path

import pytest

from cteas_ufotri.food_chain import (
    CropCompartment,
    FoodChainMassBalance,
    FoodChainMassBalanceError,
    FoodChainModel,
    FoodChainModelError,
    FoodChainParameterError,
    FoodChainParameters,
    FoodChainStateError,
    HarvestProduct,
    PlantInputs,
    PlantState,
    SyntheticTransferKernel,
    ZeroTransferKernel,
    advance,
    receive_leaf_activity,
    receive_root_zone_activity,
)
from cteas_ufotri.parameters import ParameterDatabase, ParameterUnavailableError
from cteas_ufotri.parameters.registry import SourceRegistry


ROOT = Path(__file__).resolve().parents[2]


def _source_registry() -> SourceRegistry:
    return SourceRegistry.from_file(ROOT / "parameters" / "parameter_sources.yaml")


PARAMETER_ROLES = {
    "transfer_rate_s": "food_chain.transfer_rate",
    "decay_rate_s": "food_chain.decay_rate",
}


def _database(*, placeholder: bool = False) -> ParameterDatabase:
    entries = []
    values = {"transfer_rate_s": 0.1, "decay_rate_s": 0.01}
    for role, name in PARAMETER_ROLES.items():
        if placeholder:
            entries.append(
                {
                    "name": name,
                    "value": None,
                    "unit": "PENDING_VALIDATION",
                    "category": "food_chain",
                    "source": "UFOTRI_VALIDATED",
                    "reference": "TEST_ONLY placeholder",
                    "confidence": "placeholder_pending_validation",
                    "applicability": {
                        "status": "pending_validation",
                        "scope": "test_only",
                    },
                    "transform": "IDENTITY",
                    "bounds": None,
                }
            )
            continue
        entries.append(
            {
                "name": name,
                "value": values[role],
                "unit": "s-1",
                "category": "food_chain",
                "source": "PROJECT_CUSTOM",
                "reference": "TEST_ONLY synthetic parameter",
                "confidence": "internal_default",
                "applicability": {"status": "applicable", "scope": "test_only"},
                "transform": "IDENTITY",
                "bounds": {
                    "lower": 0.0,
                    "upper": 10.0,
                    "lower_inclusive": True,
                    "upper_inclusive": True,
                },
            }
        )
    return ParameterDatabase.from_mapping(
        {"schema_version": "1.0", "parameters": entries},
        source_registry=_source_registry(),
    )


def _parameters() -> FoodChainParameters:
    return FoodChainParameters.from_database(
        _database(), parameter_names=PARAMETER_ROLES
    )


def _state() -> PlantState:
    return PlantState(
        plant_id="plant-A",
        growth_stage="vegetative",
        total_activity=100.0,
        tfwt_activity=70.0,
        obt_activity=30.0,
        dry_matter_inventory=2.0,
    )


def test_plant_state_initialization_and_inventory_aliases() -> None:
    state = _state()

    assert state.total_inventory == pytest.approx(100.0)
    assert state.tfwt_inventory == pytest.approx(70.0)
    assert state.obt_inventory == pytest.approx(30.0)
    assert state.copy(growth_stage="mature").growth_stage == "mature"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: PlantState("p", "stage", -1.0, 0.0, 0.0, 1.0),
        lambda: PlantState("p", "stage", 1.0, 1.0, 1.0, 1.0),
        lambda: PlantState("p", "stage", math.nan, 0.0, 0.0, 1.0),
        lambda: PlantState("p", "stage", math.inf, 0.0, 0.0, 1.0),
        lambda: PlantState("p", "stage", 0.0, 0.0, 0.0, -1.0),
    ],
)
def test_invalid_plant_inventory_fails_closed(factory) -> None:
    with pytest.raises(FoodChainStateError):
        factory()


def test_crop_compartment_is_crop_agnostic_and_harvest_state_is_explicit() -> None:
    crop = CropCompartment("unlisted-crop", _state(), edible_fraction=0.25)

    assert crop.crop_id == "unlisted-crop"
    assert crop.harvest_state == "NOT_HARVESTED"
    assert crop.mark_harvested().harvest_state == "HARVESTED"


def test_leaf_and_soil_coupling_inputs_are_accumulated_without_root_uptake() -> None:
    inputs = PlantInputs()
    inputs = inputs.receive_leaf_activity(10.0, 2.0, 3600.0)
    inputs = receive_leaf_activity(3.0, 1.0, 1800.0, inputs=inputs)
    inputs = receive_root_zone_activity(50.0, 500.0, inputs=inputs)

    assert inputs.leaf_input == pytest.approx(16.0)
    assert inputs.tfwt_activity == pytest.approx(13.0)
    assert inputs.obt_activity == pytest.approx(3.0)
    assert inputs.exposure_time_s == pytest.approx(5400.0)
    assert inputs.root_zone_activity == pytest.approx(50.0)
    assert inputs.soil_water_activity == pytest.approx(500.0)

    model = FoodChainModel(parameters=_parameters(), physics=ZeroTransferKernel())
    final, balance = model.advance(_state(), inputs, 60.0)
    assert final.total_activity == pytest.approx(116.0)
    assert final.tfwt_activity == pytest.approx(83.0)
    assert final.obt_activity == pytest.approx(33.0)
    assert balance.soil_input == pytest.approx(0.0)
    assert balance.closure_error == pytest.approx(0.0)


def test_placeholder_parameters_fail_closed_and_provenance_is_retained() -> None:
    with pytest.raises(ParameterUnavailableError, match="placeholder"):
        FoodChainParameters.from_database(
            _database(placeholder=True), parameter_names=PARAMETER_ROLES
        )

    parameters = _parameters()
    assert parameters.status == "PLACEHOLDER"
    assert len(parameters.database_hash) == 64
    assert set(parameters.provenance) == set(PARAMETER_ROLES)


def test_invalid_parameter_namespace_and_units_fail_closed() -> None:
    with pytest.raises(FoodChainParameterError, match="namespace"):
        FoodChainParameters.from_database(
            _database(),
            parameter_names={
                "transfer_rate_s": "soil.transfer_rate",
                "decay_rate_s": "food_chain.decay_rate",
            },
        )

    bad_document = _database().to_mapping()
    bad_document["parameters"][0]["unit"] = "kg"
    bad_database = ParameterDatabase.from_mapping(
        bad_document, source_registry=_source_registry()
    )
    with pytest.raises(FoodChainParameterError, match="expected 's-1'"):
        FoodChainParameters.from_database(bad_database, parameter_names=PARAMETER_ROLES)


def test_zero_transfer_updates_state_from_leaf_input_and_closes() -> None:
    model = FoodChainModel(parameters=_parameters(), physics=ZeroTransferKernel())
    inputs = receive_leaf_activity(20.0, 5.0, 600.0)

    final, balance = model.advance(_state(), inputs, 60.0)

    assert final.tfwt_activity == pytest.approx(90.0)
    assert final.obt_activity == pytest.approx(35.0)
    assert final.total_activity == pytest.approx(125.0)
    assert balance.initial_inventory == pytest.approx(100.0)
    assert balance.leaf_input == pytest.approx(25.0)
    assert balance.internal_transfer == pytest.approx(0.0)
    assert balance.harvest_output == pytest.approx(0.0)
    assert balance.decay_loss == pytest.approx(0.0)
    assert balance.final_inventory == pytest.approx(125.0)
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-12)


def test_synthetic_transfer_is_deterministic_and_conservative() -> None:
    model = FoodChainModel(parameters=_parameters(), physics=SyntheticTransferKernel())
    inputs = receive_leaf_activity(10.0, 0.0, 60.0)

    final, balance = model.advance(_state(), inputs, 1.0)
    repeat, repeat_balance = model.advance(_state(), inputs, 1.0)

    assert final == repeat
    assert balance == repeat_balance
    assert balance.internal_transfer > 0.0
    assert balance.decay_loss > 0.0
    assert balance.closure_error == pytest.approx(0.0, abs=1.0e-12)
    assert final.total_activity == pytest.approx(
        balance.initial_inventory + balance.leaf_input - balance.decay_loss
    )
    assert min(final.tfwt_activity, final.obt_activity) >= 0.0


def test_synthetic_large_timestep_fails_before_negative_inventory() -> None:
    model = FoodChainModel(parameters=_parameters(), physics=SyntheticTransferKernel())

    with pytest.raises(FoodChainStateError, match="negative TFWT"):
        model.advance(_state(), PlantInputs(), 20.0)


def test_harvest_product_has_finite_concentration_and_no_intake_interface() -> None:
    crop = CropCompartment("crop-X", _state(), edible_fraction=0.25)
    product = crop.harvest(datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert isinstance(product, HarvestProduct)
    assert product.edible_activity == pytest.approx(25.0)
    assert product.edible_mass == pytest.approx(0.5)
    assert product.activity_concentration == pytest.approx(50.0)
    assert not hasattr(product, "dose_coefficient")


def test_functional_advance_and_default_physics_contract() -> None:
    final, balance = advance(
        _state(),
        receive_leaf_activity(1.0, 2.0, 10.0),
        1.0,
        _parameters(),
        kernel=ZeroTransferKernel(),
    )
    assert final.total_activity == pytest.approx(103.0)
    assert balance.closure_error == pytest.approx(0.0)

    with pytest.raises(RuntimeError, match="physics kernel"):
        FoodChainModel(parameters=_parameters()).advance(_state(), PlantInputs(), 1.0)


def test_invalid_inputs_and_ledger_terms_fail_closed() -> None:
    with pytest.raises(FoodChainStateError):
        receive_leaf_activity(float("nan"), 0.0, 1.0)
    with pytest.raises(FoodChainStateError):
        receive_root_zone_activity(0.0, float("inf"))
    with pytest.raises(FoodChainModelError):
        FoodChainModel(parameters=_parameters(), physics=ZeroTransferKernel()).advance(
            _state(), PlantInputs(), 0.0
        )
    with pytest.raises(FoodChainMassBalanceError):
        FoodChainMassBalance(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0).assert_closed()
