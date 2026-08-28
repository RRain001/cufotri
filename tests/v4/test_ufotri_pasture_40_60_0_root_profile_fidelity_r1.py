"""D2 tests for the opt-in UFOTRI grass/pasture 40/60/0 root profile."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from cteas_ufotri.plant.root_v4 import (
    RootV4InputError,
    RootV4UnitError,
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_three_layer_root_water_flux_forcing,
)
from cteas_ufotri.plant.root_v4.pasture_profile import (
    UFOTRI_PASTURE_ROOT_PROFILE_ID,
    UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS,
    ufotri_pasture_root_water_uptake_fluxes,
    ufotri_pasture_three_layer_root_water_flux_forcing,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState

UTC = timezone.utc
TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)


def root_provenance(context: str = UFOTRI_PASTURE_ROOT_PROFILE_ID) -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="TEST_EXPLICIT_D2_TOTAL_PLANT_WATER_UPTAKE",
        source_locator="tests/v4/test_ufotri_pasture_40_60_0_root_profile_fidelity_r1.py",
        revision="r1",
        artifact_sha256="f" * 64,
        profile_context=context,
    )


def soil_state(concentrations: tuple[float, float, float]) -> ThreeLayerSoilState:
    water = (0.10, 0.15, 0.20)
    return ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-d2-soil",
        water_inventories_m=water,
        hto_inventories_bq_m2=tuple(
            concentration * inventory
            for concentration, inventory in zip(concentrations, water, strict=True)
        ),
        timestamp=TIMESTAMP,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_D2_SOIL",
            source_version="r1",
            artifact_sha256="a" * 64,
            spatial_reference="soil_surface_area",
            temporal_resolution_s=1800.0,
        ),
    )


def test_pasture_fractions_are_exact_and_crop_profile_remains_unchanged() -> None:
    assert UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS == (0.4, 0.6, 0.0)
    assert sum(UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS) == 1.0
    assert UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS == (0.2, 0.4, 0.4)


def test_pasture_profile_only_redistributes_explicit_total_flux() -> None:
    total = 4.0e-8
    layer_fluxes = ufotri_pasture_root_water_uptake_fluxes(total)
    assert layer_fluxes == (1.6e-8, 2.4e-8, 0.0)
    assert math.isclose(sum(layer_fluxes), total, rel_tol=1.0e-15)
    assert ufotri_pasture_root_water_uptake_fluxes(0.0) == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("value", [-1.0e-8, float("nan"), float("inf"), float("-inf")])
def test_invalid_total_flux_fails_closed(value: float) -> None:
    with pytest.raises(RootV4InputError):
        ufotri_pasture_root_water_uptake_fluxes(value)


def test_wrong_total_flux_unit_fails_closed() -> None:
    with pytest.raises(RootV4UnitError):
        ufotri_pasture_root_water_uptake_fluxes(1.0e-8, water_flux_unit="mm d^-1")


def test_typed_pasture_forcing_preserves_identity_time_provenance_and_l3_zero() -> None:
    provenance = root_provenance()
    forcing = ufotri_pasture_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=4.0e-8,
        plant_identifier="synthetic-pasture",
        timestamp=TIMESTAMP,
        provenance=provenance,
    )
    assert forcing.plant_identifier == "synthetic-pasture"
    assert forcing.timestamp == TIMESTAMP
    assert forcing.provenance == provenance
    assert forcing.interval_semantics == "start"
    assert forcing.water_uptake_fluxes_m_s == (1.6e-8, 2.4e-8, 0.0)


def test_equal_concentration_changes_only_layer_allocation_not_total_transfer() -> None:
    total = 4.0e-8
    soil = soil_state((100.0, 100.0, 100.0))
    pasture = ufotri_pasture_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=total,
        plant_identifier="synthetic-pasture",
        timestamp=TIMESTAMP,
        provenance=root_provenance(),
    )
    crop = ufotri_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=total,
        plant_identifier="synthetic-crop",
        timestamp=TIMESTAMP,
        provenance=root_provenance("UFOTRI_CROP_20_40_40_CONTROL"),
    )
    solver = ThreeLayerRootFluxSolverV4()
    pasture_plan = solver.plan(soil, pasture, interval_seconds=1800.0)
    crop_plan = solver.plan(soil, crop, interval_seconds=1800.0)

    assert pasture_plan.water_uptake_fluxes_m_s != crop_plan.water_uptake_fluxes_m_s
    assert pasture_plan.water_uptake_fluxes_m_s[2] == 0.0
    assert math.isclose(
        pasture_plan.total_water_transfer_m,
        crop_plan.total_water_transfer_m,
        rel_tol=1.0e-15,
    )
    assert math.isclose(
        pasture_plan.total_hto_transfer_bq_m2,
        crop_plan.total_hto_transfer_bq_m2,
        rel_tol=1.0e-15,
    )


def test_existing_root_solver_preserves_j_equals_qc_and_conservation() -> None:
    soil = soil_state((100.0, 200.0, 300.0))
    forcing = ufotri_pasture_three_layer_root_water_flux_forcing(
        total_water_uptake_flux_m_s=4.0e-8,
        plant_identifier="synthetic-pasture",
        timestamp=TIMESTAMP,
        provenance=root_provenance(),
    )
    plan = ThreeLayerRootFluxSolverV4().plan(soil, forcing, interval_seconds=1800.0)

    for transfer, layer in zip(plan.layer_transfers, soil.layers, strict=True):
        assert math.isclose(
            transfer.hto_uptake_flux_bq_m2_s,
            transfer.water_uptake_flux_m_s * layer.hto_concentration_bq_m3_water,
            rel_tol=1.0e-15,
            abs_tol=0.0,
        )
    assert plan.layer_transfers[2].water_transfer_m == 0.0
    assert plan.layer_transfers[2].hto_transfer_bq_m2 == 0.0
    assert plan.max_abs_water_balance_residual_m <= 1.0e-15
    assert plan.max_abs_hto_balance_residual_bq_m2 <= 1.0e-12
    assert math.isclose(plan.total_water_transfer_m, 4.0e-8 * 1800.0, rel_tol=1.0e-15)


def test_machine_gate_passes_and_keeps_hard_boundaries(tmp_path: Path) -> None:
    output = tmp_path / "d2.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/v4/run_ufotri_pasture_40_60_0_root_profile_fidelity_r1.py",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(output.read_text(encoding="utf-8"))
    assert "D2_PASTURE_ROOT_PROFILE_STATUS=PASS_PASTURE_ROOT_PROFILE_FIDELITY" in completed.stdout
    assert result["status"] == "PASS_PASTURE_ROOT_PROFILE_FIDELITY"
    assert all(result["invariants"].values())
    assert result["hard_boundaries"] == {
        "calibration": False,
        "empirical_validation": False,
        "existing_20_40_40_source_changed": False,
        "original_executable_equivalence": False,
        "physical_accuracy_claim": False,
        "production_parameter_activation": False,
        "real_cteas_atmos_binding": False,
        "root_solver_changed": False,
        "total_uptake_inferred": False,
    }
