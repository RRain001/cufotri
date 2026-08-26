"""V4 system sensitivity screening execution R1 verification."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_system_sensitivity_screening_r1.py"


def test_v4_system_sensitivity_screening_execution_r1(tmp_path: Path) -> None:
    output = tmp_path / "screening.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SOFTWARE_SCREENING"
    assert result["source_kind"] == "SYNTHETIC_TEST_ONLY"
    assert result["physical_uncertainty_ranking"] == "NOT_AVAILABLE"
    assert result["empirical_validation"] is False
    assert result["finite_difference_steps"] == [0.01, 0.005]
    assert result["finite_difference_steps_are_physical_uncertainty"] is False

    profiles = result["profiles"]
    assert set(profiles) == {
        "OBT_ONLY_ENDPOINT",
        "MIXED_OBT_TFWT_ENDPOINT",
        "DAY_NIGHT_SEQUENCE",
    }
    for profile in profiles.values():
        assert len(profile["per_step"]) == 6
        for value in profile["outputs"].values():
            assert isinstance(value, (int, float))
            assert value >= 0.0

    obt_only = profiles["OBT_ONLY_ENDPOINT"]["outputs"]
    mixed = profiles["MIXED_OBT_TFWT_ENDPOINT"]["outputs"]
    day_night = profiles["DAY_NIGHT_SEQUENCE"]["outputs"]
    assert obt_only["final_food_tfwt_inventory_bq"] == pytest.approx(0.0)
    assert mixed["final_food_tfwt_inventory_bq"] > 0.0
    assert mixed["final_food_total_inventory_bq"] > obt_only["final_food_total_inventory_bq"]
    assert day_night["final_committed_dose_sv"] > 0.0
    assert day_night["final_soil_inventory_bq_m2"] > 0.0
    assert day_night["final_tfwt_inventory_bq_m2"] > 0.0
    assert day_night["final_obt_inventory_bq_m2"] > 0.0

    structural = result["structural_zero_verification"]
    assert structural
    assert all(item["pass"] for item in structural.values())
    assert all(item["max_abs_output_delta"] == 0.0 for item in structural.values())

    local = result["local_numeric_response"]
    assert local
    assert all(item["converged"] for item in local.values())
    assert all(
        item["interpretation"]
        == "LOCAL_COMPUTATIONAL_INFLUENCE_NOT_PHYSICAL_UNCERTAINTY"
        for item in local.values()
    )
    fine = "0.005"
    dose_metric = "final_committed_dose_sv"
    assert local["atmos.air_hto_concentration"]["elasticity_by_relative_step"][fine][dose_metric] > 0.0
    assert local["atmos.surface_deposition_flux"]["elasticity_by_relative_step"][fine][dose_metric] > 0.0
    assert local["leaf.total_resistance"]["elasticity_by_relative_step"][fine][dose_metric] < 0.0
    assert local["root.k_root"]["elasticity_by_relative_step"][fine][dose_metric] > 0.0

    invariants = result["invariants"]
    assert invariants["deterministic_repeat_equal"] is True
    assert invariants["restart_equivalence"] is True
    assert invariants["max_abs_balance_residual"] <= 1.0e-9
    assert invariants["finite_nonnegative_continuous_inventories"] is True
    assert invariants["all_structural_zero_checks_pass"] is True
    assert invariants["all_local_response_steps_converged"] is True

    external = result["external_endpoint_scaling"]
    assert external["intake.annual_consumption_amount"]["dose_elasticity"] == pytest.approx(1.0)
    assert external["dose.dose_coefficient"]["dose_elasticity"] == pytest.approx(1.0)
    assert external["food.harvest_area"]["dose_elasticity"] == pytest.approx(1.0)
    assert external["intake.food_product_mass"]["dose_elasticity"] == pytest.approx(
        -1.0, rel=1.0e-4
    )
    assert all(
        item["classification"] == "EXTERNAL_SCENARIO_OR_GEOMETRY_ONLY"
        for item in external.values()
    )

    hard = result["hard_boundaries"]
    assert hard == {
        "production_src_changed": False,
        "solver_physics_changed": False,
        "numerical_coupling_changed": False,
        "parameter_activation": False,
        "calibration": False,
        "real_cteas_atmos_binding": False,
    }
