from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.root_v3 import (
    RootInputError,
    RootParameterError,
    RootParameters,
    RootState,
    RootUptakeForcing,
    RootUptakeSolver,
)
from cteas_ufotri.plant.soil_v3 import SoilProvenance, SoilState


ROOT_PROVENANCE = ForcingProvenance(
    source_id="p6-4-root-unit-test",
    source_version="1",
    artifact_sha256="a" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p6-4-soil-unit-test",
    source_version="1",
    artifact_sha256="b" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def soil_state(inventory: float) -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="soil-001",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=inventory,
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )


def forcing(interval_seconds: float = 10.0) -> RootUptakeForcing:
    return RootUptakeForcing(
        plant_identifier="plant-001",
        root_zone_identifier="root-zone-001",
        interval_seconds=interval_seconds,
        provenance=ROOT_PROVENANCE,
    )


def solver(k_root_m_s: float = 1.0e-3) -> RootUptakeSolver:
    return RootUptakeSolver(k_root_m_s=k_root_m_s)


def test_positive_soil_concentration_produces_positive_root_flux() -> None:
    root_flux = solver().advance(soil_state(10.0), forcing())

    assert root_flux.uptake_flux_bq_m2_s == pytest.approx(0.5)
    assert root_flux.flux() == pytest.approx(0.5)
    assert root_flux.inventory() == pytest.approx(5.0)
    assert root_flux.timestamp.timestamp() == pytest.approx(
        START.timestamp() + 10.0
    )


def test_zero_soil_concentration_produces_zero_root_flux() -> None:
    root_flux = solver().advance(soil_state(0.0), forcing())

    assert root_flux.uptake_flux_bq_m2_s == pytest.approx(0.0)
    assert root_flux.inventory() == pytest.approx(0.0)


def test_soil_root_inventory_balance_closes() -> None:
    result = solver().advance_result(soil_state(10.0), forcing())
    balance = result.balance

    assert balance.initial_soil_inventory_bq_m2 == pytest.approx(10.0)
    assert balance.soil_inventory_decrease_bq_m2 == pytest.approx(5.0)
    assert balance.initial_soil_inventory_bq_m2 == pytest.approx(
        balance.root_transfer_bq_m2
        + balance.remaining_soil_inventory_bq_m2
        + balance.other_loss_bq_m2
    )
    assert balance.residual_bq_m2 == pytest.approx(0.0)


def test_root_state_is_immutable_and_has_no_plant_compartment_fields() -> None:
    root_flux = solver().advance(soil_state(10.0), forcing())

    with pytest.raises(FrozenInstanceError):
        root_flux.uptake_flux_bq_m2_s = 0.0  # type: ignore[misc]
    assert not hasattr(root_flux, "tfwt_inventory_bq_m2")
    assert not hasattr(root_flux, "obt_inventory_bq_m2")
    assert not hasattr(root_flux, "foodchain")
    assert not hasattr(root_flux, "dose")


def test_root_solver_requires_explicit_provisional_parameter() -> None:
    with pytest.raises(RootParameterError, match="explicit provisional"):
        RootUptakeSolver()
    with pytest.raises(RootParameterError, match="provisional"):
        RootParameters(k_root_m_s=1.0e-3, parameter_status="validated")


def test_root_solver_fails_closed_when_transfer_exceeds_soil_inventory() -> None:
    with pytest.raises(RootInputError, match="exceeds soil inventory"):
        solver(k_root_m_s=1.0).advance(soil_state(1.0), forcing())
