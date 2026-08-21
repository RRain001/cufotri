from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import (
    OBTParameters,
    OBTState,
    OBTStateError,
    OBTSolver,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState


PROVENANCE = ForcingProvenance(
    source_id="p6-2c-unit-test",
    source_version="1",
    artifact_sha256="b" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=3600.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PARAMETERS = OBTParameters(
    kf_s=2.0e-3,
    kr_s=5.0e-4,
    daylight_multiplier=1.0,
    nighttime_multiplier=0.0,
)


def tfwt_state(inventory: float) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="plant-001",
        crop="test_crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=2.0,
        time=START,
        provenance=PROVENANCE,
    )


def obt_state(inventory: float) -> OBTState:
    return OBTState.from_inventory(
        plant_identifier="plant-001",
        crop="test_crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=inventory,
        plant_mass_kg_m2=4.0,
        timestamp=START,
        provenance=PROVENANCE,
    )


def forcing(is_daylight: bool) -> PlantBiologicalForcing:
    return PlantBiologicalForcing(is_daylight=is_daylight)


def test_tfwt_driven_obt_formation_increases_inventory() -> None:
    result = OBTSolver(parameters=PARAMETERS).advance(
        tfwt_state(100.0),
        obt_state(0.0),
        3600.0,
        forcing(True),
    )

    assert result.state.inventory() > 0.0
    assert result.balance.obt_formation_bq_m2 > 0.0
    assert result.state.activity_concentration() == pytest.approx(
        result.state.inventory() / 4.0
    )


def test_zero_tfwt_causes_obt_to_decrease() -> None:
    result = OBTSolver(parameters=PARAMETERS).advance(
        tfwt_state(0.0),
        obt_state(20.0),
        3600.0,
        forcing(True),
    )

    assert result.balance.obt_formation_bq_m2 == pytest.approx(0.0)
    assert result.state.inventory() < 20.0
    assert result.balance.other_loss_bq_m2 > 0.0


def test_tfwt_loss_equals_obt_increase_plus_other_loss() -> None:
    result = OBTSolver(parameters=PARAMETERS).advance(
        tfwt_state(100.0),
        obt_state(10.0),
        1800.0,
        forcing(True),
    )

    balance = result.balance
    assert balance.tfwt_loss_bq_m2 == pytest.approx(
        balance.obt_increase_bq_m2 + balance.other_loss_bq_m2
    )
    assert balance.tfwt_loss_bq_m2 == pytest.approx(
        balance.obt_formation_bq_m2
    )
    assert balance.residual_bq_m2 == pytest.approx(0.0)


def test_daytime_formation_exceeds_nighttime_formation() -> None:
    solver = OBTSolver(parameters=PARAMETERS)
    day = solver.advance(tfwt_state(100.0), obt_state(0.0), 3600.0, forcing(True))
    night = solver.advance(
        tfwt_state(100.0),
        obt_state(0.0),
        3600.0,
        forcing(False),
    )

    assert day.balance.obt_formation_bq_m2 > night.balance.obt_formation_bq_m2
    assert night.balance.obt_formation_bq_m2 == pytest.approx(0.0)


def test_obt_state_is_inventory_based_and_does_not_store_tfwt_ratio() -> None:
    state = obt_state(8.0)

    assert state.obt_inventory_bq_m2 == pytest.approx(8.0)
    assert state.obt_concentration == pytest.approx(2.0)
    assert not hasattr(state, "tfwt_obt_ratio")


def test_inconsistent_obt_concentration_fails_closed() -> None:
    with pytest.raises(OBTStateError):
        OBTState(
            plant_identifier="plant-001",
            crop="test_crop",
            growth_stage="vegetative",
            obt_inventory_bq_m2=8.0,
            obt_concentration=1.0,
            plant_mass_kg_m2=4.0,
            timestamp=START,
            provenance=PROVENANCE,
        )


def test_solver_requires_explicit_rates() -> None:
    with pytest.raises(ValueError, match="explicit kf_s and kr_s"):
        OBTSolver()
