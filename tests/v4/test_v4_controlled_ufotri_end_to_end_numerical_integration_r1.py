"""Controlled UFOTRI replay-to-dose numerical integration R1 tests."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml

from cteas_ufotri.plant.obt_v3 import UFOTRI_OBT_KF_S, UFOTRI_OBT_KR_S, ufotri_obt_baseline_parameters
from cteas_ufotri.plant.root_v4 import UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS
from cteas_ufotri.v4_integration import SELECTED_OPERATOR_SPLIT

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_controlled_ufotri_end_to_end_numerical_integration_r1.py"
GOVERNANCE = ROOT / "docs/v4/governance/v4_controlled_ufotri_end_to_end_numerical_integration_r1.yaml"


def test_controlled_profiles_are_the_selected_sources() -> None:
    params = ufotri_obt_baseline_parameters()
    assert params.kf_s == UFOTRI_OBT_KF_S
    assert params.kr_s == UFOTRI_OBT_KR_S
    assert params.daylight_multiplier == 1.0
    assert params.nighttime_multiplier == 1.0
    assert UFOTRI_ROOT_WATER_UPTAKE_FRACTIONS == (0.2, 0.4, 0.4)
    assert SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"


def test_machine_runner_passes_the_controlled_end_to_end_gates() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, (
        "controlled UFOTRI E2E runner failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    line = next(
        item
        for item in completed.stdout.splitlines()
        if item.startswith("V4_CONTROLLED_UFOTRI_E2E_RESULT_JSON=")
    )
    result = json.loads(line.split("=", 1)[1])
    assert result["status"] == "PASS_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION"
    assert all(result["gates"].values())
    assert result["dynamic_metrics"]["total_root_water_transfer_m"] > 0.0
    assert result["dynamic_metrics"]["total_root_hto_transfer_bq_m2"] > 0.0
    assert result["final_state"]["obt_bq_m2"] > 0.0
    assert result["endpoint"]["food_inventory_bq"] > 0.0
    assert result["endpoint"]["annual_intake_bq"] > 0.0
    assert result["endpoint"]["committed_dose_sv"] > 0.0

    resolution = result["resolution_state"]
    assert resolution["eq39_controlled_baseline_active"] is True
    assert resolution["ufotri_20_40_40_controlled_profile_active"] is True
    assert resolution["root_q_w_production_input_resolved"] is True
    assert resolution["ufotri_obt_controlled_baseline_active"] is True
    assert resolution["software_chain_connected_with_controlled_ufotri_profiles"] is True
    assert resolution["full_model_production_ready"] is False
    assert all(value is False for value in result["hard_boundaries"].values())


def test_governance_requires_post_integration_review_before_more_physics() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION_R1"
    assert data["scope"]["production_source_changed"] is False
    assert data["scope"]["solver_equations_changed"] is False
    assert data["resolution_state_if_pass"]["root_q_w_production_input_resolved"] is True
    assert data["resolution_state_if_pass"]["full_model_production_ready"] is False
    assert data["next_stage_if_clean_merge"]["selected"] == "V4_POST_CONTROLLED_UFOTRI_SYSTEM_REVIEW_R1"
    assert data["next_stage_if_clean_merge"]["new_physics_implementation_authorized"] is False
    assert all(value is False for value in data["hard_boundaries"].values())
