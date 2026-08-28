"""Execute the C1 machine-visible Eq. (33)-(37) hydrology gate under pytest."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_ufotri_eq33_37_soil_hydrology_reconstruction_r1.py"


def test_c1_machine_visible_gate_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    status_line = next(
        line
        for line in completed.stdout.splitlines()
        if line.startswith("UFOTRI_EQ33_37_SOIL_HYDROLOGY_STATUS=")
    )
    result_line = next(
        line
        for line in completed.stdout.splitlines()
        if line.startswith("UFOTRI_EQ33_37_SOIL_HYDROLOGY_RESULT_JSON=")
    )
    assert status_line.endswith("PASS_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION")
    result = json.loads(result_line.split("=", 1)[1])
    assert result["status"] == "PASS_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION"
    assert all(result["gates"].values())
    assert result["hard_boundaries"]["built_in_constitutive_parameterization"] is False
    assert result["hard_boundaries"]["production_hydrology"] is False
    assert result["hard_boundaries"]["frozen_soil_v4_modified"] is False
