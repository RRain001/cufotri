from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import pytest

from cteas_ufotri.foodchain.ufotri_vegetable_grass_v4 import (
    EQ66_EXACT_FROM_STATED_MASSES,
    EQ66_MANUAL_ROUNDED_0_012_D_1,
    UFOTRIFoodchainInputError,
    UFOTRIVegetableExchangeSolver,
    ufotri_grass_eq67_81_role_map,
    ufotri_vegetable_eq65_66_parameters,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState
from cteas_ufotri.plant.tfwt_v3 import TFWTState

UTC = timezone.utc
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="TEST_D3",
        source_version="r1",
        artifact_sha256="4" * 64,
        spatial_reference="plant_area",
        temporal_resolution_s=3600.0,
    )


def _states(
    *,
    plant_identifier: str = "veg",
    obt_plant_identifier: str | None = None,
    tfwt_time: datetime = T0,
    obt_time: datetime = T0,
) -> tuple[TFWTState, OBTState]:
    provenance = _provenance()
    return (
        TFWTState.from_inventory(
            plant_identifier=plant_identifier,
            crop="green_vegetable",
            growth_stage="controlled",
            tfwt_inventory_bq_m2=10.0,
            water_content_kg_m2=0.4,
            time=tfwt_time,
            provenance=provenance,
            area_basis="plant_area",
        ),
        OBTState.from_inventory(
            plant_identifier=(
                plant_identifier if obt_plant_identifier is None else obt_plant_identifier
            ),
            crop="green_vegetable",
            growth_stage="controlled",
            obt_inventory_bq_m2=2.0,
            plant_mass_kg_m2=0.1,
            timestamp=obt_time,
            provenance=provenance,
            area_basis="plant_area",
        ),
    )


def _load_machine_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "run_ufotri_vegetable_grass_compartment_closure_r1.py"
    )
    spec = importlib.util.spec_from_file_location("d3_machine_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_d3_machine_gate_passes() -> None:
    result = _load_machine_module().build_result()
    assert result["status"] == "PASS_VEGETABLE_GRASS_COMPARTMENT_CLOSURE"
    assert all(result["profile_invariants"].values())
    assert all(result["grass_role_map"]["grass_invariants"].values())
    assert not any(result["hard_boundaries"].values())


def test_eq65_reverse_transfer_is_internal_not_external_loss() -> None:
    parameters = ufotri_vegetable_eq65_66_parameters(
        forward_rate_basis=EQ66_EXACT_FROM_STATED_MASSES
    )
    solver = UFOTRIVegetableExchangeSolver(parameters)
    tfwt, obt = _states()
    initial_total = tfwt.inventory() + obt.inventory()
    result = solver.advance(tfwt, obt, 86400.0)
    assert result.tfwt_state.inventory() + result.obt_state.inventory() == pytest.approx(
        initial_total, abs=1.0e-12
    )
    assert result.balance.total_residual_bq_m2 == pytest.approx(0.0, abs=1.0e-12)


def test_forward_rate_basis_is_explicit_and_profiles_remain_distinct() -> None:
    exact = ufotri_vegetable_eq65_66_parameters(
        forward_rate_basis=EQ66_EXACT_FROM_STATED_MASSES
    )
    rounded = ufotri_vegetable_eq65_66_parameters(
        forward_rate_basis=EQ66_MANUAL_ROUNDED_0_012_D_1
    )
    assert exact.forward_d_1 != rounded.forward_d_1
    assert exact.reverse_d_1 == rounded.reverse_d_1
    with pytest.raises(UFOTRIFoodchainInputError, match="forward_rate_basis"):
        ufotri_vegetable_eq65_66_parameters(forward_rate_basis="AUTO")


def test_solver_fails_closed_on_metadata_mismatch() -> None:
    solver = UFOTRIVegetableExchangeSolver(
        ufotri_vegetable_eq65_66_parameters(
            forward_rate_basis=EQ66_EXACT_FROM_STATED_MASSES
        )
    )
    tfwt, obt = _states(obt_plant_identifier="other")
    with pytest.raises(UFOTRIFoodchainInputError, match="plant identifiers"):
        solver.advance(tfwt, obt, 3600.0)

    tfwt, obt = _states(obt_time=T0 + timedelta(hours=1))
    with pytest.raises(UFOTRIFoodchainInputError, match="timestamps"):
        solver.advance(tfwt, obt, 3600.0)


def test_solver_fails_closed_on_invalid_interval() -> None:
    solver = UFOTRIVegetableExchangeSolver(
        ufotri_vegetable_eq65_66_parameters(
            forward_rate_basis=EQ66_EXACT_FROM_STATED_MASSES
        )
    )
    tfwt, obt = _states()
    for interval in (0.0, -1.0, float("nan"), float("inf")):
        with pytest.raises(UFOTRIFoodchainInputError):
            solver.advance(tfwt, obt, interval)


def test_grass_role_map_is_reference_only_and_keeps_d4_boundary() -> None:
    role_map = ufotri_grass_eq67_81_role_map()
    assert role_map.layer_depths_m == (0.05, 0.10, 0.15)
    assert role_map.root_fractions == (0.4, 0.6, 0.0)
    assert role_map.leaf_exchange_owner == "plant.leaf_ufotri_v4"
    assert role_map.soil_hydrology_owner == "plant.soil_ufotri_v4+plant.soil_v4"
    assert role_map.root_uptake_owner == "plant.root_v4.pasture_profile"
    assert role_map.grass_obt_owner == "D4_EQ99_105_2"
    assert role_map.reference_rates_activated is False
    assert role_map.duplicate_soil_solver_added is False
    assert role_map.production_binding_authorized is False
