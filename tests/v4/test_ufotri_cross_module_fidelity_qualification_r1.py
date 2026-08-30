from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_cross_module_fidelity_qualification_r1.yaml"
ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md"
SCRIPT = ROOT / "scripts/v4/check_ufotri_cross_module_fidelity_qualification_r1.py"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_g3_contract_keeps_scope_fail_closed() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "UFOTRI_CROSS_MODULE_FIDELITY_QUALIFICATION_R1"
    assert data["status"] == "CANDIDATE_PENDING_EXACT_HEAD_CI"
    strategy = data["qualification_strategy"]
    assert strategy["new_production_pipeline"] is False
    assert strategy["production_source_change_required"] is False
    assert strategy["real_atmos_checks"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    boundaries = data["hard_boundaries"]
    assert boundaries["production_source_change"] is False
    assert boundaries["rc1_default_changed"] is False
    assert boundaries["parameter_activation"] is False
    assert boundaries["calibration_started"] is False
    assert boundaries["empirical_validation_claimed"] is False
    assert boundaries["physical_accuracy_claimed"] is False
    assert boundaries["real_cteas_atmos_binding_claimed"] is False
    assert boundaries["original_executable_equivalence_claimed"] is False
    assert boundaries["g4_final_gate_preempted"] is False


def test_all_thirty_gap_entries_have_explicit_allowed_dispositions() -> None:
    data = load_yaml(GOVERNANCE)
    dispositions = data["gap_dispositions"]
    assert list(dispositions) == [f"UFR-{index:02d}" for index in range(1, 31)]
    allowed = set(data["allowed_gap_dispositions"])
    assert all(entry["disposition"] in allowed for entry in dispositions.values())
    external = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    }
    assert external == {"UFR-01", "UFR-03", "UFR-04", "UFR-05"}
    blocked = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "BLOCKED_SOURCE_UNAVAILABLE"
    }
    assert blocked == {"UFR-29", "UFR-30"}
    assert dispositions["UFR-16"]["disposition"] == "RECONCILED_EXISTING_OPTION"


def test_root_delay_reconciliation_is_optional_and_not_promoted_to_root_v4() -> None:
    data = load_yaml(GOVERNANCE)
    delay = data["root_delay_reconciliation"]
    assert delay["manual_delay_seconds"] == 10800
    assert delay["reference_dt_seconds"] == 600
    assert delay["reference_delay_steps"] == 18
    assert delay["current_root_v4_hidden_delay"] is False
    assert delay["disposition"] == "RECONCILED_EXISTING_HISTORICAL_OPTION_NO_NEW_PHYSICS"


def test_rc1_vs_fidelity_comparison_preserves_distinct_paths() -> None:
    data = load_yaml(GOVERNANCE)
    comparison = data["rc1_vs_fidelity"]
    assert comparison["equality_required"] is False
    assert set(comparison["differences"]) == {
        "leaf_exchange",
        "obt",
        "soil_hydrology",
        "foodchain",
        "ht_branch",
        "reemission_area_source",
        "short_term_root_delay",
    }
    assert comparison["differences"]["short_term_root_delay"]["rc1"] == "INACTIVE"
    assert "REQUALIFIED" in comparison["differences"]["short_term_root_delay"]["fidelity"]


def test_roadmap_preserves_g3_boundary_across_final_gate_transition() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "#### G3. Cross-module fidelity qualification" in text
    assert "Stage: `UFOTRI_CROSS_MODULE_FIDELITY_QUALIFICATION_R1`" in text
    heading = "#### G4. Final UFOTRI manual-based reconstruction gate"
    assert heading in text
    g4 = text.split(heading, 1)[1].split("## 7.", 1)[0]
    if "- Status: `COMPLETE`" in g4:
        assert "`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`" in text
        assert "`UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`" in text
        assert "E4/E5 real CTEAS-Atmos" in g4
        assert "`DEFERRED_EXTERNAL_DEPENDENCY`" in g4
    else:
        assert "- Status: `NOT_STARTED`" in g4
        assert "`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE` remains unchanged" in text


def test_g3_machine_gate_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    assert (
        "UFOTRI_G3_STATUS=PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION"
        in completed.stdout
    )