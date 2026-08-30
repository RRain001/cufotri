from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r2.py"
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r2.yaml"
ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md"
PREFIX = "UFOTRI_H6_R2_RESULT_JSON="


def _run_gate() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    lines = [line for line in completed.stdout.splitlines() if line.startswith(PREFIX)]
    assert len(lines) == 1
    return json.loads(lines[0][len(PREFIX) :])


def test_h6_r2_machine_gate_passes() -> None:
    result = _run_gate()
    assert result["status"] == "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
    assert all(result["gates"].values())
    assert result["candidate_target_flag_value"] is False
    assert result["target_flag_value_after_clean_merge_no_drift_and_status_sync"] is True
    assert result["broader_replication_complete"] is False
    assert result["ufotri_original_numerical_equivalence"] == "NOT_ESTABLISHED"
    assert result["lifecycle_state"] in {"CANDIDATE_PRE_MERGE", "COMPLETE_POST_MERGE"}


def test_h6_r2_governance_does_not_preempt_claim() -> None:
    governance = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert governance["stage"] == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
    assert governance["candidate_target_flag_value"] is False
    assert governance["target_flag_eligible_after_clean_merge_no_drift_and_status_sync"] is True
    assert governance["claim_boundary"]["remains_false_or_not_established"][
        "UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE"
    ] is False
    assert governance["claim_boundary"]["remains_false_or_not_established"][
        "UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE"
    ] == "NOT_ESTABLISHED"
    assert governance["cteas_atmos_role"]["blocks_standalone_manual_reconstruction"] is False


def test_h6_r2_roadmap_lifecycle_is_consistent() -> None:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    assert "### H5 — Native atmosphere → environmental chain → dose qualification" in roadmap
    assert "### H6 — Corrected final reconstruction gate" in roadmap
    if "- Status: `COMPLETE`\n- Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`" in roadmap:
        assert "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`" in roadmap
        assert (
            "## 6. Immediate next stage\n\n`NO_IMMEDIATE_INTERNAL_MANUAL_RECONSTRUCTION_STAGE`"
            in roadmap
        )
    else:
        assert (
            "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE_PENDING_NATIVE_ATMOSPHERE_CLOSURE`"
            in roadmap
        )
        assert "- Status: `AUTHORIZED_NOT_STARTED`\n- Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`" in roadmap
        assert (
            "## 6. Immediate next stage\n\n`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`"
            in roadmap
        )
