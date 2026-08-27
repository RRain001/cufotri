from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/v4/run_development_baseline_rc1.py"
CURRENT = ROOT / "docs/v4/governance/v4_current_system_state.yaml"
GOVERNANCE = ROOT / "docs/v4/governance/v4_development_baseline_rc1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-057-v4-development-baseline-rc1.md"
REPORT = ROOT / "docs/v4/reports/v4_development_baseline_rc1.md"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_rc1_machine_composition_gate_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, (
        "V4 RC1 machine composition failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    line = next(
        item
        for item in completed.stdout.splitlines()
        if item.startswith("V4_DEVELOPMENT_BASELINE_RC1_RESULT_JSON=")
    )
    result = json.loads(line.split("=", 1)[1])
    assert result["status"] == "PASS_V4_DEVELOPMENT_BASELINE_RC1_MACHINE_COMPOSITION"
    assert all(result["gates"].values())
    assert result["component_statuses"] == {
        "controlled_ufotri_e2e": "PASS_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION",
        "sensitivity_screening": "PASS_SOFTWARE_SCREENING",
        "root_operator_split": "PASS_SELECTION",
        "soil_root_tfwt_obt": "PASS_INTEGRATION",
        "replay_orchestration": "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION",
        "food_intake_dose": "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION",
    }
    assert result["selected_baseline"]["root_distribution"] == [0.2, 0.4, 0.4]
    assert result["selected_baseline"]["operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert result["selected_baseline"]["harvest_boundary"] == "KEEP_HARVEST_EVENT"


def test_current_state_closes_internal_mandatory_stage_list() -> None:
    current = _load(CURRENT)
    assert current["current_state_stage"] == "V4_DEVELOPMENT_BASELINE_RC1"
    assert current["project_phase"] == "INTERNAL_V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE"
    assert current["remaining_mandatory_internal_development_stages"] == []
    assert current["current_next_stage"]["selected"] == "NONE_WITHIN_INTERNAL_V4_DEVELOPMENT_BASELINE"
    assert current["completion_target"]["achieved"] is True
    rc = current["development_baseline_rc1"]
    assert rc["verdict"] == "V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE"
    assert rc["mandatory_internal_blocker_count"] == 0
    assert rc["mandatory_internal_stage_count_remaining"] == 0
    assert rc["selected_internal_baseline_frozen"] is True
    assert rc["new_physics_added"] is False


def test_rc1_freezes_selected_baseline_without_promoting_optional_extensions() -> None:
    current = _load(CURRENT)
    baseline = current["controlled_baseline_state"]
    assert baseline["soil_layers"] == ["L1_0_5_cm", "L2_5_15_cm", "L3_15_30_cm"]
    assert baseline["root_eq39_controlled_baseline_active"] is True
    assert baseline["root_layer_profile_20_40_40_active"] is True
    assert baseline["root_q_w_controlled_construction_path_resolved"] is True
    assert baseline["root_q_w_production_case_input_ready"] is False
    assert baseline["leaf_baseline_resistance_path_connected"] is True
    assert baseline["tfwt_solver_connected"] is True
    assert baseline["obt_reduced_ufotri_baseline_connected"] is True
    assert baseline["operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert baseline["terminal_harvest_boundary"] == "KEEP_HARVEST_EVENT"
    assert baseline["food_intake_dose_endpoint_connected"] is True
    assert all(
        item["mandatory_for_v4_internal_completion"] is False
        for item in current["optional_or_held_extensions"].values()
    )


def test_rc1_readiness_boundaries_remain_fail_closed() -> None:
    current = _load(CURRENT)
    assert current["readiness_boundaries"] == {
        "full_model_production_ready": False,
        "production_input_packet_ready": False,
        "real_cteas_atmos_binding": False,
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "calibration_started": False,
        "active_parameters": 0,
        "v3_default_path_changed": False,
    }
    governance = _load(GOVERNANCE)
    boundaries = governance["hard_boundaries"]
    assert boundaries["full_model_production_ready"] is False
    assert boundaries["production_input_packet_ready"] is False
    assert boundaries["real_cteas_atmos_binding"] is False
    assert boundaries["empirical_validation"] is False
    assert boundaries["physical_accuracy_claim"] is False
    assert boundaries["calibration_started"] is False
    assert boundaries["active_parameters"] == 0
    assert boundaries["leaf_r5"] is False
    assert boundaries["full_richards_darcy_hydrology"] is False
    assert boundaries["multi_pool_obt"] is False
    assert boundaries["ufotri_short_term_3h_delay"] is False
    assert boundaries["penman_eq38_aerodynamic_term"] is False
    assert boundaries["v3_default_path_changed"] is False


def test_rc1_scope_and_exact_head_closure_are_locked() -> None:
    governance = _load(GOVERNANCE)
    assert governance["stage"] == "V4_DEVELOPMENT_BASELINE_RC1"
    assert governance["entry_anchor"]["base_main"] == "a9ae81fe1931289c44a860df6eafc6ab2ee16b55"
    assert governance["entry_anchor"]["base_tree"] == "4b483f427b3aaef0f8bd53f3859815949ce1510e"
    scope = governance["scope"]
    assert scope["kind"] == "COMBINED_REGRESSION_AND_DEVELOPMENT_BASELINE_FREEZE_ONLY"
    for key, value in scope.items():
        if key != "kind":
            assert value is False
    cert = governance["exact_head_certification"]
    assert all(value is True for key, value in cert.items() if key.endswith("_required") or key == "no_new_commit_after_certification")
    assert cert["merge_method"] == "merge"
    completion = governance["completion_if_all_gates_pass_and_merge_is_no_drift"]
    assert completion["release_candidate_tag_authorized"] == "v4-development-baseline-rc1"
    assert completion["new_physics_pre_authorized"] is False


def test_rc1_artifacts_explicitly_reject_production_interpretation() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for text in (adr, report):
        lowered = text.lower()
        assert "production" in lowered
        assert "real cteas-atmos" in lowered
        assert "empirical validation" in lowered
        assert "physical" in lowered
        assert "v4_software_development_baseline_complete" in lowered
