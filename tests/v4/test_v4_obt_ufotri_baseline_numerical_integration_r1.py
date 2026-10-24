"""V4 UFOTRI OBT baseline numerical integration R1 tests."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from cteas_ufotri.plant.obt_v3 import (
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    ufotri_obt_baseline_parameters,
)
from cteas_ufotri.v4_integration import SELECTED_OPERATOR_SPLIT


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_obt_ufotri_baseline_numerical_integration_r1.py"


def test_ufotri_profile_is_the_numerical_integration_parameter_source() -> None:
    params = ufotri_obt_baseline_parameters()
    assert params.kf_s == UFOTRI_OBT_KF_S
    assert params.kr_s == UFOTRI_OBT_KR_S
    assert params.daylight_multiplier == 1.0
    assert params.nighttime_multiplier == 1.0
    assert SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN"


def test_machine_runner_passes_all_numerical_gates() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    line = next(
        item
        for item in completed.stdout.splitlines()
        if item.startswith("V4_OBT_UFOTRI_BASELINE_NUMERICAL_RESULT_JSON=")
    )
    result = json.loads(line.split("=", 1)[1])
    assert result["status"] == "PASS_UFOTRI_BASELINE_NUMERICAL_INTEGRATION"
    assert all(result["gates"].values())
    assert result["hard_boundaries"]["calibration"] is False
    assert result["hard_boundaries"]["empirical_validation"] is False
    assert result["hard_boundaries"]["physical_accuracy_claim"] is False
    assert result["hard_boundaries"]["production_root_q_w"] is False
    assert result["hard_boundaries"]["real_cteas_atmos_binding"] is False


# P9: retained tests from test_v4_obt_ufotri_baseline_r1.py
import math

from cteas_ufotri.plant.obt_v3 import (
    UFOTRI_OBT_DAYLIGHT_MULTIPLIER,
    UFOTRI_OBT_FORMATION_PER_HOUR,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    UFOTRI_OBT_LOSS_PER_HOUR,
    UFOTRI_OBT_NIGHTTIME_MULTIPLIER,
    ufotri_obt_baseline_parameters,
)


def test_ufotri_direct_rates_are_converted_without_reinterpretation() -> None:
    assert math.isclose(UFOTRI_OBT_FORMATION_PER_HOUR, 0.0006, rel_tol=0.0, abs_tol=0.0)
    assert math.isclose(UFOTRI_OBT_LOSS_PER_HOUR, 0.003, rel_tol=0.0, abs_tol=0.0)
    assert math.isclose(UFOTRI_OBT_KF_S * 3600.0, 0.0006, rel_tol=1e-15)
    assert math.isclose(UFOTRI_OBT_KR_S * 3600.0, 0.003, rel_tol=1e-15)


def test_ufotri_profile_preserves_daily_average_without_invented_day_night_split() -> None:
    params = ufotri_obt_baseline_parameters()
    assert params.kf_s == UFOTRI_OBT_KF_S
    assert params.kr_s == UFOTRI_OBT_KR_S
    assert params.daylight_multiplier == UFOTRI_OBT_DAYLIGHT_MULTIPLIER == 1.0
    assert params.nighttime_multiplier == UFOTRI_OBT_NIGHTTIME_MULTIPLIER == 1.0


def test_ufotri_profile_returns_fresh_immutable_parameter_records() -> None:
    left = ufotri_obt_baseline_parameters()
    right = ufotri_obt_baseline_parameters()
    assert left == right
    assert left is not right
