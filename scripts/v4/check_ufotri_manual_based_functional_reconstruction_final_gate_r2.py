#!/usr/bin/env python3
"""H6 corrected final gate for manual-based UFOTRI functional reconstruction.

R2 treats G4 as historical evidence and the post-G4 native-atmosphere roadmap
as the current authority.  It does not rewrite the historical G4 decision and
it does not promote source-limited mechanisms to recovered status.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CORRECTION_ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md"
MASTER_ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md"
G4_GOVERNANCE = ROOT / "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r1.yaml"
G3_GOVERNANCE = ROOT / "docs/v4/governance/ufotri_cross_module_fidelity_qualification_r1.yaml"
H4_GOVERNANCE = ROOT / "docs/v4/governance/ufotri_native_atmospheric_process_reconciliation_r1.yaml"
H5_GOVERNANCE = ROOT / "docs/v4/governance/ufotri_native_atmosphere_to_dose_qualification_r1.yaml"
G3_SCRIPT = ROOT / "scripts/v4/check_ufotri_cross_module_fidelity_qualification_r1.py"

STAGE = "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
BASE_MAIN_SHA = "23ca602fe136a805d9be268acf33194b8ce9fd35"

NATIVE_GATES = {
    "H1": (
        "scripts/v4/run_ufotri_native_primary_atmosphere_core_r1.py",
        "PASS_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE",
    ),
    "H2": (
        "scripts/v4/run_ufotri_native_hourly_trajectory_r1.py",
        "PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY",
    ),
    "H3": (
        "scripts/v4/run_ufotri_native_atmospheric_forcing_adapter_r1.py",
        "PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER",
    ),
    "H4": (
        "scripts/v4/run_ufotri_native_atmospheric_process_reconciliation_r1.py",
        "PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION",
    ),
    "H5": (
        "scripts/v4/run_ufotri_native_atmosphere_to_dose_qualification_r1.py",
        "PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION",
    ),
}

ALLOWED_CHANGED_PATHS = {
    "docs/v4/adr/ADR-084-ufotri-manual-based-functional-reconstruction-final-gate-r2.md",
    "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r2.yaml",
    "docs/v4/reports/ufotri_manual_based_functional_reconstruction_final_gate_r2.md",
    "scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r2.py",
    "tests/v4/test_ufotri_manual_based_functional_reconstruction_final_gate_r2.py",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return data


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def _git_text(*args: str) -> str:
    return _git(*args).stdout.strip()


def _section_for_stage(text: str, stage: str) -> str:
    chunks = re.split(r"(?=^### H[1-6] — )", text, flags=re.MULTILINE)
    matches = [chunk for chunk in chunks if f"- Stage: `{stage}`" in chunk]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one roadmap section for {stage}")
    return matches[0]


def _sha(section: str, label: str) -> str:
    match = re.search(
        rf"^- {re.escape(label)}: `([0-9a-f]{{40}})`", section, flags=re.MULTILINE
    )
    if match is None:
        raise RuntimeError(f"missing {label} in roadmap section")
    return match.group(1)


def _native_ledger_probe(roadmap: str) -> dict[str, Any]:
    stages = {
        "H1": "UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1",
        "H2": "UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1",
        "H3": "UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1",
        "H4": "UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1",
        "H5": "UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1",
    }
    results: dict[str, Any] = {}
    for key, stage in stages.items():
        section = _section_for_stage(roadmap, stage)
        head = _sha(section, "Certified head")
        merge = _sha(section, "Merge SHA")
        recorded_tree = _sha(section, "Merge tree")
        head_tree = _git_text("rev-parse", f"{head}^{{tree}}")
        merge_tree = _git_text("rev-parse", f"{merge}^{{tree}}")
        parents = _git_text("show", "-s", "--format=%P", merge).split()
        checks = {
            "status_complete": "- Status: `COMPLETE`" in section,
            "validation_pass_recorded": "PASS_" in section,
            "no_drift_recorded": "MERGE_TREE_DRIFT=FALSE" in section,
            "certified_head_is_merge_parent": head in parents,
            "certified_head_tree_equals_merge_tree": head_tree == merge_tree,
            "recorded_merge_tree_matches_git": recorded_tree == merge_tree,
            "merge_is_ancestor_of_candidate": (
                _git("merge-base", "--is-ancestor", merge, "HEAD", check=False).returncode
                == 0
            ),
        }
        results[key] = {
            "stage": stage,
            "certified_head": head,
            "merge_sha": merge,
            "tree": merge_tree,
            "checks": checks,
            "pass": all(checks.values()),
        }
    h6 = _section_for_stage(
        roadmap, "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
    )
    return {
        "stages": results,
        "all_h1_h5_complete_no_drift": all(item["pass"] for item in results.values()),
        "h6_authorized_not_started": "- Status: `AUTHORIZED_NOT_STARTED`" in h6,
    }


def _run_gate(relative: str, expected: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / relative)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "script": relative,
        "returncode": completed.returncode,
        "expected_token": expected,
        "expected_token_present": expected in completed.stdout,
        "pass": completed.returncode == 0 and expected in completed.stdout,
    }


def _native_gate_reexecution() -> dict[str, Any]:
    results = {
        key: _run_gate(relative, expected)
        for key, (relative, expected) in NATIVE_GATES.items()
    }
    return {"gates": results, "all_native_gates_pass": all(v["pass"] for v in results.values())}


def _run_g3() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ufotri_h6_g3_") as directory:
        output = Path(directory) / "g3.json"
        completed = subprocess.run(
            [sys.executable, str(G3_SCRIPT), "--output", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0 or not output.exists():
            return {
                "returncode": completed.returncode,
                "status": "FAILED_TO_REEXECUTE",
                "pass": False,
            }
        payload = json.loads(output.read_text(encoding="utf-8"))
    status = payload.get("status")
    return {
        "returncode": 0,
        "status": status,
        "runtime_gates_all_true": all(payload.get("gates", {}).values()),
        "pass": (
            status == "PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION"
            and all(payload.get("gates", {}).values())
        ),
    }


def _historical_g4_probe() -> dict[str, Any]:
    governance = _load_yaml(G4_GOVERNANCE)
    master = MASTER_ROADMAP.read_text(encoding="utf-8")
    checks = {
        "g4_stage_identity_preserved": (
            governance.get("stage")
            == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1"
        ),
        "historical_candidate_did_not_preempt_flag": (
            governance.get("candidate_target_flag_value") is False
        ),
        "historical_19_stage_audit_preserved": (
            governance.get("required_internal_stage_count") == 19
        ),
        "historical_g4_complete_record_preserved": (
            "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1" in master
            and "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE" in master
        ),
    }
    return {"checks": checks, "pass": all(checks.values())}


def _source_boundary_probe(roadmap: str) -> dict[str, Any]:
    h4 = _load_yaml(H4_GOVERNANCE)
    h5 = _load_yaml(H5_GOVERNANCE)
    h4_limited = h4["source_limited"]
    h5_limited = h5["source_limited_boundaries_preserved"]
    h5_hard = h5["hard_boundaries"]
    checks = {
        "atmospheric_ht_to_hto_remains_disabled": (
            "`ATMOSPHERIC_HT_TO_HTO_CONVERSION=DISABLED`" in roadmap
            and h5["native_to_environment"]["atmospheric_ht_to_hto_conversion"]
            == "DISABLED_KFK4605"
        ),
        "iwash1_regtim_not_invented": (
            h4_limited["kfk5194_iwash1_regtim"] == "DO_NOT_INVENT"
            and h5_limited["h4_iwash1_regtim_numeric_default"] == "SOURCE_LIMITED"
        ),
        "liftoff_eq322_remains_source_limited": (
            h4_limited["kfk4332_liftoff_eq322_numeric"]
            == "OCR_AMBIGUOUS_DO_NOT_IMPLEMENT"
            and h5_limited["kfk4332_liftoff_eq322_numeric"]
            == "SOURCE_LIMITED_OCR_AMBIGUOUS"
        ),
        "building_wake_remains_source_limited": (
            h4_limited["building_wake_complete_numerics"] == "NOT_RECOVERED"
            and h5_limited["building_wake_complete_numerics"] == "SOURCE_LIMITED"
        ),
        "plume_rise_remains_source_limited": (
            h4_limited["plume_rise_plrise_risefx_complete_numerics"]
            == "NOT_RECOVERED"
            and h5_limited["plume_rise_complete_numerics"] == "SOURCE_LIMITED"
        ),
        "eq44_executable_rate_generation_not_promoted": (
            h5_limited["eq44_reemission_rate_generation"] == "SOURCE_LIMITED"
        ),
        "mixed_hto_origin_not_inferred": (
            h5_limited["mixed_environmental_hto_origin_partition"] == "NOT_INFERRED"
        ),
        "canada_full_replay_not_claimed": h5["benchmark_boundaries"]["canada_full_numeric_replay"] is False,
        "iter_full_replay_not_claimed": h5["benchmark_boundaries"]["iter_full_atmospheric_numeric_replay"] is False,
        "production_parameters_not_activated": h5_hard["production_parameter_activation"] is False,
        "calibration_not_started": h5_hard["calibration"] is False,
        "empirical_validation_not_claimed": h5_hard["empirical_validation"] is False,
        "physical_accuracy_not_claimed": h5_hard["physical_accuracy_claim"] is False,
        "cteas_atmos_not_bound": h5_hard["cteas_atmos_binding"] is False,
        "original_executable_equivalence_not_claimed": h5_hard["original_ufotri_executable_equivalence"] is False,
    }
    return {"checks": checks, "pass": all(checks.values())}


def _claim_lifecycle_probe(roadmap: str) -> dict[str, Any]:
    checks = {
        "current_reconstruction_flag_still_pending_h6": (
            "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE_PENDING_NATIVE_ATMOSPHERE_CLOSURE`"
            in roadmap
        ),
        "broader_replication_remains_false": (
            "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`" in roadmap
        ),
        "original_numeric_equivalence_not_established": (
            "- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`" in roadmap
        ),
        "cteas_atmos_is_optional_backend": (
            "- `CTEAS_ATMOS_BACKEND=DEFERRED_OPTIONAL_HIGHER_FIDELITY_BACKEND`" in roadmap
        ),
        "h6_is_immediate_stage": (
            "## 6. Immediate next stage\n\n`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`"
            in roadmap
        ),
    }
    return {"checks": checks, "pass": all(checks.values())}


def _candidate_scope_probe() -> dict[str, Any]:
    changed = {
        item.strip()
        for item in _git_text("diff", "--name-only", f"{BASE_MAIN_SHA}..HEAD").splitlines()
        if item.strip()
    }
    checks = {
        "exact_five_qualification_files": changed == ALLOWED_CHANGED_PATHS,
        "no_src_changes": not any(path.startswith("src/") for path in changed),
        "no_defaults_changes": not any(path.startswith("configs/") for path in changed),
        "no_workflow_changes": not any(path.startswith(".github/workflows/") for path in changed),
        "no_roadmap_changes": not any(path.startswith("docs/v4/roadmap/") for path in changed),
    }
    return {
        "base_main_sha": BASE_MAIN_SHA,
        "changed_paths": sorted(changed),
        "allowed_paths": sorted(ALLOWED_CHANGED_PATHS),
        "checks": checks,
        "pass": all(checks.values()),
    }


def build_result() -> dict[str, Any]:
    roadmap = CORRECTION_ROADMAP.read_text(encoding="utf-8")
    native_ledger = _native_ledger_probe(roadmap)
    native_reexecution = _native_gate_reexecution()
    g3 = _run_g3()
    historical_g4 = _historical_g4_probe()
    source_boundaries = _source_boundary_probe(roadmap)
    lifecycle = _claim_lifecycle_probe(roadmap)
    scope = _candidate_scope_probe()

    gates = {
        "h1_h5_complete_and_merge_no_drift": native_ledger["all_h1_h5_complete_no_drift"],
        "h6_control_plane_authorized": native_ledger["h6_authorized_not_started"],
        "h1_h5_machine_gates_reexecute_pass": native_reexecution["all_native_gates_pass"],
        "historical_g3_aggregate_reexecutes_pass": g3["pass"],
        "historical_g4_evidence_preserved": historical_g4["pass"],
        "source_limited_and_nonclaim_boundaries_preserved": source_boundaries["pass"],
        "claim_lifecycle_not_preempted": lifecycle["pass"],
        "candidate_scope_qualification_only": scope["pass"],
    }
    passed = all(gates.values())
    status = (
        "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
        if passed
        else "FAIL_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
    )
    return {
        "schema_version": "v2",
        "stage": STAGE,
        "status": status,
        "gate_scope": "RECOVERABLE_INTERNAL_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_WITH_NATIVE_ATMOSPHERE",
        "native_stage_ledger": native_ledger,
        "native_gate_reexecution": native_reexecution,
        "historical_g3_reexecution": g3,
        "historical_g4_probe": historical_g4,
        "source_boundary_probe": source_boundaries,
        "claim_lifecycle_probe": lifecycle,
        "candidate_scope_probe": scope,
        "gates": gates,
        "candidate_target_flag_value": False,
        "reconstruction_completion_eligible_after_clean_merge_no_drift_and_status_sync": passed,
        "target_flag_value_after_clean_merge_no_drift_and_status_sync": bool(passed),
        "broader_replication_complete": False,
        "production_readiness": False,
        "empirical_validation_complete": False,
        "physical_accuracy_validated": False,
        "cteas_atmos_binding_complete": False,
        "ufotri_original_numerical_equivalence": "NOT_ESTABLISHED",
        "next_action_if_clean_merge_no_drift": (
            "CORRECTION_ROADMAP_STATUS_SYNC_SET_RECONSTRUCTION_COMPLETE_TRUE"
            if passed
            else "DO_NOT_PROMOTE_RECONSTRUCTION_FLAG"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"UFOTRI_H6_R2_STATUS={result['status']}")
    print("UFOTRI_H6_R2_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if str(result["status"]).startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
