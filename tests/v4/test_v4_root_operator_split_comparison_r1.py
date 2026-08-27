import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/run_root_operator_split_comparison_r1.py"
GOVERNANCE = ROOT / "docs/v4/governance/v4_root_operator_split_comparison_r1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-030-v4-root-operator-split-comparison.md"
REPORT = ROOT / "docs/v4/reports/v4_root_operator_split_comparison_r1.md"
POST = "PRESERVE_V3_POST_OBT_ROOT_GAIN"
PRE = "ROOT_GAIN_BEFORE_OBT"
TOL = 1.0e-10


@pytest.fixture(scope="module")
def comparison_result(tmp_path_factory: pytest.TempPathFactory) -> dict:
    output = tmp_path_factory.mktemp("root-split") / "result.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    assert "V4_ROOT_OPERATOR_SPLIT_STATUS=PASS_SELECTION" in completed.stdout
    return json.loads(output.read_text(encoding="utf-8"))


def test_comparison_is_synthetic_and_selects_post_only_after_all_gates(comparison_result: dict) -> None:
    result = comparison_result
    assert result["stage"] == "V4_ROOT_OPERATOR_SPLIT_COMPARISON_R1"
    assert result["source_kind"] == "SYNTHETIC_NUMERICAL_SEMANTICS_ONLY"
    assert result["empirical_validation"] is False
    assert result["physical_accuracy_claim"] is False
    assert result["candidates"] == [POST, PRE]
    assert all(result["gates"].values())
    assert result["selection"]["selected_candidate"] == POST
    assert result["selection"]["pre_obt_candidate_disposition"] == "NOT_SELECTED_RIGHT_BIASED_LIE_SPLIT"


def test_both_candidates_refine_monotonically(comparison_result: dict) -> None:
    for candidate in (POST, PRE):
        record = comparison_result["refinement"][candidate]
        assert record["converged_monotonically"] is True
        errors = record["l1_tfwt_obt_error_vs_reference"]
        assert errors["900.0"] < errors["1800.0"] < errors["3600.0"]


def test_single_application_and_coupled_conservation_close(comparison_result: dict) -> None:
    for candidate in (POST, PRE):
        for run in comparison_result["refinement"][candidate]["runs"].values():
            assert run["max_abs_soil_root_identity_residual_bq_m2"] <= TOL
            assert run["max_abs_plant_conservation_residual_bq_m2"] <= TOL
            assert run["max_abs_coupled_balance_residual_bq_m2"] <= TOL
            assert run["total_root_transfer_bq_m2"] > 0.0


def test_restart_and_deterministic_repeat_pass_for_both_candidates(comparison_result: dict) -> None:
    assert comparison_result["deterministic_repeat"] == {POST: True, PRE: True}
    for candidate in (POST, PRE):
        restart = comparison_result["restart_equivalence"][candidate]
        assert restart["equivalent"] is True
        for key in (
            "final_soil_hto_bq_m2",
            "final_tfwt_bq_m2",
            "final_obt_bq_m2",
            "final_plant_total_bq_m2",
            "total_root_transfer_bq_m2",
        ):
            assert restart["direct"][key] == pytest.approx(restart["restarted"][key], abs=TOL)


def test_pulse_probe_makes_root_to_obt_lag_difference_explicit(comparison_result: dict) -> None:
    pulse = comparison_result["pulse_lag_probe"]
    assert pulse[POST]["first_step_root_transfer_bq_m2"] > 0.0
    assert pulse[POST]["first_step_obt_formation_bq_m2"] == pytest.approx(0.0, abs=TOL)
    assert pulse[POST]["second_step_obt_formation_bq_m2"] > 0.0
    assert pulse[PRE]["first_step_obt_formation_bq_m2"] > 0.0
    assert pulse[PRE]["obt_after_first_step_bq_m2"] > pulse[POST]["obt_after_first_step_bq_m2"]


def test_area_basis_and_ufotri_reference_boundaries_remain_explicit(comparison_result: dict) -> None:
    assert comparison_result["area_basis"] == "soil_surface_area"
    assert comparison_result["area_basis_conversion"] is False
    assert comparison_result["ufotri_reference_profile_active"] is False
    assert comparison_result["three_hour_delay_active"] is False
    hard = comparison_result["hard_boundaries"]
    assert hard == {
        "production_pipeline_changed": False,
        "v3_changed": False,
        "parameter_activation": False,
        "calibration": False,
        "real_cteas_atmos_binding": False,
    }


def test_governance_keeps_integration_closed_until_machine_gate() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["status"] == "COMPARISON_IMPLEMENTED_AWAITING_MACHINE_GATE"
    assert data["candidates"] == [POST, PRE]
    assert data["selection_rule"]["if_all_gates_pass"] == POST
    assert data["selection_rule"]["otherwise"] == "HOLD_NO_SELECTION"
    assert data["integration_boundary"]["future_soil_root_tfwt_obt_integration_authorized_now"] is False
    assert data["integration_boundary"]["silent_soil_area_to_plant_area_conversion"] == "forbidden"
    assert data["hard_invariants"]["active_parameters"] == 0
    assert data["hard_invariants"]["physical_validation_complete"] is False


def test_adr_and_report_do_not_claim_physical_validation() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    assert "Status: Proposed pending exact-head machine gate" in adr
    assert "Synthetic error magnitude is not used as physical evidence" in adr
    assert "does not modify a production pipeline" in report
    assert "no physical validation claim is made" in report
