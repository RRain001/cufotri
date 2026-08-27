"""V4 controlled UFOTRI 20/40/40 root-distribution profile tests."""

from __future__ import annotations

from datetime import datetime, timezone
import math

import pytest

from cteas_ufotri.plant.root_v4 import (
    RootV4InputError,
    RootV4UnitError,
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_root_water_uptake_fluxes,
    ufotri_three_layer_root_water_flux_forcing,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState

UTC = timezone.utc
TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="TEST_EXPLICIT_TOTAL_PLANT_WATER_UPTAKE",
        source_locator="tests/v4/test_v4_root_ufotri_20_40_40_profile_r1.py",
        revision="r1",
        artifact_sha256="c" * 64,
        profile_context="UFOTRI_20_40_40_CONTROLLED_PROFILE_TEST",
    )


def soil_state() -> ThreeLayerSoilState:
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=TIMESTAMP,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_TEST_SOIL",
            source_version="r1",
            artifact_sha256="b" * 64,
            spatial_reference="soil_surface_area",
            temporal_resolution_s=1800.0,
        ),
    )


def test_ufotri_fractions_are_exact_and_sum_to_one() -> None:
    assert UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS == (0.2, 0.4, 0.4)
    assert math.isclose(sum(UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS), 1.0, rel_tol=0.0, abs_tol=0.0)


def test_explicit_total_flux_is_distributed_without_hidden_generation() -> None:
    total = 4.0e-8
    layer_fluxes = ufotri_root_water_uptake_fluxes(total)
    assert layer_fluxes == (8.0e-9, 1.6e-8, 1.6e-8)
    assert math.isclose(sum(layer_fluxes), total, rel_tol=1e-15)
    assert ufotri_root_water_uptake_fluxes(0.0) == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("value", [-1.0e-8, float("nan"), float("inf"), float("-inf")])
def test_invalid_total_flux_fails_closed(value: float) -> None:
    with pytest.raises(RootV4InputError):
        ufotri_root_water_uptake_fluxes(value)


def test_wrong_total_flux_unit_fails_closed() -> None:
    with pytest.raises(RootV4UnitError):
        ufotri_root_water_uptake_fluxes(1.0e-8, water_flux_unit="mm d^-1")


def test_typed_forcing_preserves_time_provenance_and_total_identity() -> None:
    provenance = root_provenance()
    forcing = ufotri_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=4.0e-8,
        plant_identifier="synthetic-soybean",
        timestamp=TIMESTAMP,
        provenance=provenance,
    )
    assert forcing.timestamp == TIMESTAMP
    assert forcing.provenance == provenance
    assert forcing.water_uptake_fluxes_m_s == (8.0e-9, 1.6e-8, 1.6e-8)
    assert math.isclose(sum(forcing.water_uptake_fluxes_m_s), 4.0e-8, rel_tol=1e-15)


def test_existing_root_solver_preserves_j_equals_q_times_c_and_ledgers() -> None:
    soil = soil_state()
    forcing = ufotri_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=4.0e-8,
        plant_identifier="synthetic-soybean",
        timestamp=TIMESTAMP,
        provenance=root_provenance(),
    )
    plan = ThreeLayerRootFluxSolverV4().plan(soil, forcing, interval_seconds=1800.0)

    for transfer, layer in zip(plan.layer_transfers, soil.layers, strict=True):
        expected = transfer.water_uptake_flux_m_s * layer.hto_concentration_bq_m3_water
        assert math.isclose(transfer.hto_uptake_flux_bq_m2_s, expected, rel_tol=1e-15)
    assert plan.max_abs_water_balance_residual_m <= 1.0e-15
    assert plan.max_abs_hto_balance_residual_bq_m2 <= 1.0e-12
    assert math.isclose(plan.total_water_transfer_m, 4.0e-8 * 1800.0, rel_tol=1e-15)


def test_profile_does_not_expose_reference_compartment_rates_as_water_flux() -> None:
    # UFOTRI's ~0.026/0.026/0.017 d^-1 compartment rates have different
    # semantics and must not appear in the m/s forcing profile.
    layer_fluxes = ufotri_root_water_uptake_fluxes(1.0e-8)
    assert layer_fluxes == (2.0e-9, 4.0e-9, 4.0e-9)
    assert all(value < 1.0e-7 for value in layer_fluxes)
