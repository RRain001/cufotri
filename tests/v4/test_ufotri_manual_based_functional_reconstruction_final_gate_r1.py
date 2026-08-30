from pathlib import Path
import json
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r1.yaml"
ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md"
SCRIPT = ROOT / "scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r1.py"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_g4_is_qualification_only_and_does_not_preempt_completion_flag() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1"
    assert data["status"] == "CANDIDATE_PENDING_EXACT_HEAD_CI"
    assert data["target_flag"] == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE"
    assert data["candidate_target_flag_value"] is False
    assert data["target_flag_eligible_after_clean_merge_no_drift_and_roadmap_sync"] is True
    strategy = data["qualification_strategy"]
    assert strategy["qualification_only"] is True
    assert strategy["new_production_pipeline"] is False
    assert strategy["production_source_change_required"] is False
    assert strategy["roadmap_flag_changed_in_candidate"] is False


def test_g4_has_exact_internal_stage_and_gap_accounting() -> None:
    data = load_yaml(GOVERNANCE)
    assert len(data["required_internal_stages"]) == 19
    assert data["required_internal_stage_count"] == 19
    assert data["required_gap_disposition_counts"] == {
        "COMPLETE_INTERNAL": 20,
        "RECONCILED_EXISTING_OPTION": 1,
        "COMPLETE_WITH_SOURCE_LIMIT": 3,
        "DEFERRED_EXTERNAL_DEPENDENCY": 4,
        "BLOCKED_SOURCE_UNAVAILABLE": 2,
    }
    assert set(data["required_external_gap_ids"]) == {"UFR-01", "UFR-03", "UFR-04", "UFR-05"}
    assert set(data["required_source_blocked_gap_ids"]) == {"UFR-29", "UFR-30"}
    assert set(data["required_source_limited_gap_ids"]) == {"UFR-12", "UFR-27", "UFR-28"}
    assert data["required_reconciled_existing_gap_ids"] == ["UFR-16"]


def test_real_atmos_and_original_asset_boundaries_remain_fail_closed() -> None:
    data = load_yaml(GOVERNANCE)
    atmos = data["real_atmos_boundaries"]
    assert atmos["e4_status"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    assert atmos["e5_status"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    assert atmos["real_cteas_atmos_hto_binding_complete"] is False
    assert atmos["real_cteas_atmos_ht_binding_complete"] is False
    assert atmos["real_atmos_end_to_end_ht_to_hto_complete"] is False
    source = data["source_and_validation_boundaries"]
    assert source["complete_eq44_rate_recovery"] is False
    assert source["canada_full_numeric_replay_ready"] is False
    assert source["canada_empirical_validation_complete"] is False
    assert source["iter_full_atmospheric_numeric_replay_complete"] is False
    assert source["iter_empirical_validation_complete"] is False
    assert source["production_readiness_claimed"] is False
    assert source["physical_accuracy_claimed"] is False
    assert source["original_executable_equivalence"] is False


def test_candidate_scope_forbids_source_defaults_workflow_and_roadmap_changes() -> None:
    data = load_yaml(GOVERNANCE)
    scope = data["candidate_scope"]
    assert len(scope["allowed_changed_paths"]) == 5
    assert scope["src_changes_allowed"] is False
    assert scope["default_changes_allowed"] is False
    assert scope["workflow_changes_allowed"] is False
    assert scope["roadmap_changes_allowed"] is False


def test_roadmap_authorizes_only_the_internal_g4_gate() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "#### G4. Final UFOTRI manual-based reconstruction gate" in text
    assert "Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1`" in text
    assert "Control-plane authorization: `AUTHORIZED_AFTER_G3_ROADMAP_SYNC`" in text
    assert "E4/E5 real CTEAS-Atmos work remains `DEFERRED_EXTERNAL_DEPENDENCY`" in text
    assert (
        "`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE` remains unchanged until G4 itself passes exact-head CI and merge/no-drift audit."
        in text
    )


def test_g4_machine_gate_passes_and_only_makes_post_merge_flag_eligible(tmp_path: Path) -> None:
    output = tmp_path / "g4.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    assert "UFOTRI_G4_STATUS=PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE" in completed.stdout
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["candidate_target_flag_value"] is False
    assert result["reconstruction_completion_eligible_after_clean_merge_no_drift_and_roadmap_sync"] is True
    assert result["target_flag_value_after_clean_merge_no_drift_and_roadmap_sync"] is True
    assert result["real_cteas_atmos_binding_complete"] is False
    assert result["full_real_atmos_ufotri_replication_complete"] is False
    assert result["empirical_validation_complete"] is False
    assert result["production_readiness"] is False
    assert result["physical_accuracy_validated"] is False
    assert result["ufotri_original_numerical_equivalence"] == "NOT_ESTABLISHED"
    assert all(result["gates"].values())
