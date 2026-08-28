"""Independent pytest assertions for C2 coupled water/HTO qualification."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py"
STATUS_PREFIX = "UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_STATUS="
RESULT_PREFIX = "UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_RESULT_JSON="
DRY_ZERO_FLOW_TOL_M_S = 1.0e-24


@lru_cache(maxsize=1)
def _result() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, (
        "C2 machine gate failed.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}"
    )
    status_line = next(
        line for line in completed.stdout.splitlines() if line.startswith(STATUS_PREFIX)
    )
    result_line = next(
        line for line in completed.stdout.splitlines() if line.startswith(RESULT_PREFIX)
    )
    assert status_line == (
        STATUS_PREFIX + "PASS_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION"
    )
    return json.loads(result_line.split("=", 1)[1])


def test_c2_machine_gate_and_all_named_qualifications_pass() -> None:
    result = _result()
    assert result["stage"] == "UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1"
    assert result["status"] == "PASS_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION"
    assert all(result["gates"].values())


def test_c2_signed_directions_and_wet_dry_limits_are_explicit() -> None:
    diagnostics = _result()["diagnostics"]
    directions = diagnostics["directions"]
    wet_dry = diagnostics["wet_dry"]
    assert diagnostics["dry_zero_flow_tolerance_m_s"] == DRY_ZERO_FLOW_TOL_M_S
    assert all(value > 0.0 for value in directions["down_q_m_s"])
    assert all(value > 0.0 for value in directions["down_hto_bq_m2_s"])
    assert all(value < 0.0 for value in directions["up_q_m_s"])
    assert all(value < 0.0 for value in directions["up_hto_bq_m2_s"])
    assert all(abs(value) <= DRY_ZERO_FLOW_TOL_M_S for value in wet_dry["dry_q_m_s"])
    assert all(value > 0.0 for value in wet_dry["wet_q_m_s"])


def test_c2_boundary_root_and_dynamic_recompute_are_observable() -> None:
    result = _result()
    diagnostics = result["diagnostics"]
    boundary = diagnostics["boundary_root"]
    assert boundary["root_water_transfer_m"] > 0.0
    assert boundary["root_hto_transfer_bq_m2"] > 0.0
    assert boundary["lower_water_loss_m"] > 0.0
    assert boundary["lower_hto_loss_bq_m2"] > 0.0
    assert abs(boundary["root_water_identity_residual_m"]) <= 1.0e-12
    assert abs(boundary["root_hto_identity_residual_bq_m2"]) <= 1.0e-9
    assert diagnostics["dynamic_q_first_m_s"] != diagnostics["dynamic_q_last_m_s"]
    assert result["gates"]["selected_operator_split_preserved"] is True


def test_c2_timestep_refinement_moves_toward_225_second_reference() -> None:
    errors = _result()["diagnostics"]["refinement"]["errors_to_reference"]
    sequence = [float(errors[key]) for key in ("3600", "1800", "900", "450")]
    assert sequence[-1] < sequence[0]
    for coarser, finer in zip(sequence[:-1], sequence[1:], strict=True):
        assert finer <= coarser * 1.05


def test_c2_claim_boundaries_remain_fail_closed() -> None:
    boundaries = _result()["hard_boundaries"]
    assert boundaries["existing_source_modified"] is False
    assert boundaries["second_soil_solver_added"] is False
    assert boundaries["second_hydrology_solver_added"] is False
    assert boundaries["production_hydraulic_parameters"] is False
    assert boundaries["calibration"] is False
    assert boundaries["empirical_validation"] is False
    assert boundaries["physical_accuracy_claim"] is False
    assert boundaries["original_constitutive_curves_recovered"] is False
    assert boundaries["original_numerical_discretization_recovered"] is False
    assert boundaries["real_cteas_atmos_binding"] is False
    assert boundaries["original_executable_equivalence"] is False
