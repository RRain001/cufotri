from datetime import datetime, timezone
import math

import pytest

from cteas_ufotri.plant.soil_v3 import SoilState as V3SoilState
from cteas_ufotri.plant.soil_v4 import (
    CANONICAL_LAYER_GEOMETRY,
    SoilV4InputError,
    SoilV4Provenance,
    SoilV4StateError,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)


PROVENANCE = SoilV4Provenance(
    source_id="ufotri.kfk4605.reference-fixture",
    source_version="r1-test-only",
    artifact_sha256="1" * 64,
    spatial_reference="synthetic-soil-column",
    temporal_resolution_s=3600.0,
)
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def reference_state() -> ThreeLayerSoilState:
    # 25% volumetric water content in UFOTRI's 5/10/15 cm layers gives
    # 0.0125/0.025/0.0375 m water. These are a reference fixture, not active parameters.
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="ufotri-reference-column",
        water_inventories_m=(0.0125, 0.0250, 0.0375),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=T0,
        provenance=PROVENANCE,
    )


def test_canonical_three_layer_geometry_and_reference_water_basis() -> None:
    state = reference_state()
    assert CANONICAL_LAYER_GEOMETRY == (
        ("L1", 0.0, 0.05),
        ("L2", 0.05, 0.15),
        ("L3", 0.15, 0.30),
    )
    assert tuple(layer.thickness_m for layer in state.layers) == (0.05, 0.10, 0.15)
    assert tuple(layer.water_inventory_m for layer in state.layers) == (0.0125, 0.025, 0.0375)
    assert state.total_water_inventory_m == pytest.approx(0.075)
    assert state.total_hto_inventory_bq_m2 == pytest.approx(60.0)
    assert state.layers[0].hto_concentration_bq_m3_water == pytest.approx(800.0)


def test_state_restart_round_trip_is_exact() -> None:
    state = reference_state()
    restored = ThreeLayerSoilState.from_json(state.to_json())
    assert restored == state
    assert restored.to_mapping() == state.to_mapping()


def test_signed_downward_interlayer_flux_conserves_internal_water_and_hto() -> None:
    state = reference_state()
    solver = ThreeLayerSoilStorageSolver(tritium_half_life_s=1000.0)
    forcing = ThreeLayerSoilForcing(
        l1_l2_water_flux_m_s=1.0e-6,
        l2_l3_water_flux_m_s=2.0e-6,
        l1_l2_hto_flux_bq_m2_s=1.0e-3,
        l2_l3_hto_flux_bq_m2_s=2.0e-3,
    )
    result = solver.advance(state, forcing, 10.0)

    assert result.state.layers[0].water_inventory_m == pytest.approx(0.01249)
    assert result.state.layers[1].water_inventory_m == pytest.approx(0.02499)
    assert result.state.layers[2].water_inventory_m == pytest.approx(0.03752)
    assert result.global_balance.interlayer_water_cancellation_m == pytest.approx(0.0)
    assert result.global_balance.interlayer_hto_cancellation_bq_m2 == pytest.approx(0.0)
    assert result.global_balance.water_residual_m == pytest.approx(0.0, abs=1e-14)
    assert result.global_balance.hto_residual_bq_m2 == pytest.approx(0.0, abs=1e-12)
    assert all(abs(item.hto_residual_bq_m2) < 1e-12 for item in result.layer_balances)
    assert result.global_balance.decay_loss_bq_m2 > 0.0


def test_signed_upward_capillary_direction_is_supported_without_hydrology_inference() -> None:
    state = reference_state()
    solver = ThreeLayerSoilStorageSolver(tritium_half_life_s=1000.0)
    result = solver.advance(
        state,
        ThreeLayerSoilForcing(
            l1_l2_water_flux_m_s=-1.0e-6,
            l2_l3_water_flux_m_s=-2.0e-6,
            l1_l2_hto_flux_bq_m2_s=-1.0e-3,
            l2_l3_hto_flux_bq_m2_s=-2.0e-3,
        ),
        10.0,
    )
    assert result.state.layers[0].water_inventory_m > state.layers[0].water_inventory_m
    assert result.state.layers[2].water_inventory_m < state.layers[2].water_inventory_m
    assert result.global_balance.interlayer_water_cancellation_m == pytest.approx(0.0)
    assert result.global_balance.interlayer_hto_cancellation_bq_m2 == pytest.approx(0.0)


def test_external_inputs_sinks_and_decay_close_global_balance() -> None:
    state = reference_state()
    solver = ThreeLayerSoilStorageSolver(tritium_half_life_s=1000.0)
    forcing = ThreeLayerSoilForcing(
        surface_water_input_m_s=1.0e-6,
        surface_deposition_flux_bq_m2_s=5.0e-3,
        lower_boundary_water_loss_m_s=2.0e-7,
        lower_boundary_hto_loss_bq_m2_s=2.0e-4,
        surface_reemission_hto_loss_bq_m2_s=3.0e-4,
        root_water_extraction_m_s=(1.0e-7, 2.0e-7, 1.0e-7),
        root_hto_extraction_bq_m2_s=(1.0e-4, 2.0e-4, 1.0e-4),
    )
    result = solver.advance(state, forcing, 60.0)
    balance = result.global_balance
    assert balance.external_water_input_m == pytest.approx(6.0e-5)
    assert balance.external_water_loss_m == pytest.approx(3.6e-5)
    assert balance.external_hto_input_bq_m2 == pytest.approx(0.3)
    assert balance.external_hto_loss_bq_m2 == pytest.approx(0.054)
    assert abs(balance.water_residual_m) < 1e-14
    assert abs(balance.hto_residual_bq_m2) < 1e-11
    assert balance.decay_loss_bq_m2 > 0.0


def test_fail_closed_on_layer_water_or_hto_overdraw() -> None:
    state = reference_state()
    solver = ThreeLayerSoilStorageSolver(tritium_half_life_s=1000.0)
    with pytest.raises(SoilV4InputError, match="exhausts layer water"):
        solver.advance(
            state,
            ThreeLayerSoilForcing(l1_l2_water_flux_m_s=1.0),
            1.0,
        )
    with pytest.raises(SoilV4InputError, match="exceeds available inventory"):
        solver.advance(
            state,
            ThreeLayerSoilForcing(lower_boundary_hto_loss_bq_m2_s=100.0),
            1.0,
        )


def test_wrong_geometry_fails_closed() -> None:
    state = reference_state()
    layer = state.layers[0]
    with pytest.raises(SoilV4StateError, match="geometry must be"):
        type(layer).from_inventories(
            layer_id="L1",
            depth_top_m=0.0,
            depth_bottom_m=0.06,
            water_inventory_m=0.015,
            hto_inventory_bq_m2=10.0,
        )


def test_v4_core_is_opt_in_and_does_not_replace_v3_type() -> None:
    assert V3SoilState is not ThreeLayerSoilState
    assert "v3" in V3SoilState.__module__
    assert "v4" in ThreeLayerSoilState.__module__
    assert not any("richards" in name.lower() for name in dir(ThreeLayerSoilStorageSolver))
