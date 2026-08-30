#!/usr/bin/env python3
"""H6 corrected final gate for manual-based UFOTRI functional reconstruction."""

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
ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_NATIVE_ATMOSPHERE_RECOVERY_PLAN.md"
MASTER = ROOT / "docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md"
G4_GOV = ROOT / "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r1.yaml"
H4_GOV = ROOT / "docs/v4/governance/ufotri_native_atmospheric_process_reconciliation_r1.yaml"
H5_GOV = ROOT / "docs/v4/governance/ufotri_native_atmosphere_to_dose_qualification_r1.yaml"
G3_SCRIPT = ROOT / "scripts/v4/check_ufotri_cross_module_fidelity_qualification_r1.py"
STAGE = "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2"
BASE = "23ca602fe136a805d9be268acf33194b8ce9fd35"

NATIVE = {
    "H1": ("UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1", "scripts/v4/run_ufotri_native_primary_atmosphere_core_r1.py", "PASS_UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE"),
    "H2": ("UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1", "scripts/v4/run_ufotri_native_hourly_trajectory_r1.py", "PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY"),
    "H3": ("UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1", "scripts/v4/run_ufotri_native_atmospheric_forcing_adapter_r1.py", "PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER"),
    "H4": ("UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1", "scripts/v4/run_ufotri_native_atmospheric_process_reconciliation_r1.py", "PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION"),
    "H5": ("UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1", "scripts/v4/run_ufotri_native_atmosphere_to_dose_qualification_r1.py", "PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION"),
}
ALLOWED = {
    "docs/v4/adr/ADR-084-ufotri-manual-based-functional-reconstruction-final-gate-r2.md",
    "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r2.yaml",
    "docs/v4/reports/ufotri_manual_based_functional_reconstruction_final_gate_r2.md",
    "scripts/v4/check_ufotri_manual_based_functional_reconstruction_final_gate_r2.py",
    "tests/v4/test_ufotri_manual_based_functional_reconstruction_final_gate_r2.py",
}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return value


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed\n{result.stdout}\n{result.stderr}")
    return result


def _gt(*args: str) -> str:
    return _git(*args).stdout.strip()


def _section(text: str, stage: str) -> str:
    chunks = re.split(r"(?=^### H[1-6] — )", text, flags=re.MULTILINE)
    matches = [chunk for chunk in chunks if f"- Stage: `{stage}`" in chunk]
    if len(matches) != 1:
        raise RuntimeError(f"expected one roadmap section for {stage}")
    return matches[0]


def _sha(section: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}: `([0-9a-f]{{40}})`", section, re.MULTILINE)
    if match is None:
        raise RuntimeError(f"missing {label}")
    return match.group(1)


def _h6_complete(roadmap: str) -> bool:
    return "- Status: `COMPLETE`" in _section(roadmap, STAGE)


def _ledger(roadmap: str) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for key, (stage, _script, _token) in NATIVE.items():
        section = _section(roadmap, stage)
        head = _sha(section, "Certified head")
        merge = _sha(section, "Merge SHA")
        recorded_tree = _sha(section, "Merge tree")
        head_tree = _gt("rev-parse", f"{head}^{{tree}}")
        merge_tree = _gt("rev-parse", f"{merge}^{{tree}}")
        parents = _gt("show", "-s", "--format=%P", merge).split()
        checks = {
            "complete": "- Status: `COMPLETE`" in section,
            "ci_pass_recorded": "SUCCESS" in section and "Existing five V4 integration gates: `PASS`" in section,
            "no_drift_recorded": "MERGE_TREE_DRIFT=FALSE" in section,
            "head_is_merge_parent": head in parents,
            "head_tree_equals_merge_tree": head_tree == merge_tree,
            "recorded_tree_matches_git": recorded_tree == merge_tree,
            "merge_ancestor_of_candidate": _git("merge-base", "--is-ancestor", merge, "HEAD", check=False).returncode == 0,
        }
        records[key] = {"stage": stage, "head": head, "merge": merge, "tree": merge_tree, "checks": checks, "pass": all(checks.values())}
    h6 = _section(roadmap, STAGE)
    complete = "- Status: `COMPLETE`" in h6
    h6_lifecycle_valid = (
        "- Validation: `PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`" in h6
        and "MERGE_TREE_DRIFT=FALSE" in h6
    ) if complete else "- Status: `AUTHORIZED_NOT_STARTED`" in h6
    return {
        "stages": records,
        "all_h1_h5_complete_no_drift": all(record["pass"] for record in records.values()),
        "h6_lifecycle_state": "COMPLETE_POST_MERGE" if complete else "CANDIDATE_PRE_MERGE",
        "h6_lifecycle_valid": h6_lifecycle_valid,
    }


def _run(relative: str, token: str) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(ROOT / relative)], cwd=ROOT, text=True, capture_output=True, check=False)
    return {"script": relative, "returncode": result.returncode, "expected_token": token, "token_present": token in result.stdout, "pass": result.returncode == 0 and token in result.stdout}


def _native_reexecution() -> dict[str, Any]:
    results = {key: _run(script, token) for key, (_stage, script, token) in NATIVE.items()}
    return {"gates": results, "pass": all(result["pass"] for result in results.values())}


def _g3() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ufotri_h6_g3_") as directory:
        output = Path(directory) / "g3.json"
        run = subprocess.run([sys.executable, str(G3_SCRIPT), "--output", str(output)], cwd=ROOT, text=True, capture_output=True, check=False)
        if run.returncode != 0 or not output.exists():
            return {"returncode": run.returncode, "status": "FAILED_TO_REEXECUTE", "pass": False}
        result = json.loads(output.read_text(encoding="utf-8"))
    status = result.get("status")
    runtime = result.get("gates", {})
    return {"returncode": 0, "status": status, "runtime_gates_all_true": bool(runtime) and all(runtime.values()), "pass": status == "PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION" and bool(runtime) and all(runtime.values())}


def _historical_g4() -> dict[str, Any]:
    gov = _yaml(G4_GOV)
    master = MASTER.read_text(encoding="utf-8")
    checks = {
        "stage_preserved": gov.get("stage") == "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1",
        "candidate_did_not_preempt_flag": gov.get("candidate_target_flag_value") is False,
        "historical_19_stage_audit_preserved": gov.get("required_internal_stage_count") == 19,
        "g4_pass_record_preserved": "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1" in master and "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE" in master,
    }
    return {"checks": checks, "pass": all(checks.values())}


def _boundaries(roadmap: str) -> dict[str, Any]:
    h4 = _yaml(H4_GOV)
    h5 = _yaml(H5_GOV)
    a = h4["source_limited"]
    b = h5["source_limited_boundaries_preserved"]
    hard = h5["hard_boundaries"]
    bench = h5["benchmark_boundaries"]
    checks = {
        "air_ht_to_hto_disabled": "`ATMOSPHERIC_HT_TO_HTO_CONVERSION=DISABLED`" in roadmap and h5["native_to_environment"]["atmospheric_ht_to_hto_conversion"] == "DISABLED_KFK4605",
        "iwash1_regtim_source_limited": a["kfk5194_iwash1_regtim"] == "DO_NOT_INVENT" and b["h4_iwash1_regtim_numeric_default"] == "SOURCE_LIMITED",
        "liftoff_eq322_source_limited": a["kfk4332_liftoff_eq322_numeric"] == "OCR_AMBIGUOUS_DO_NOT_IMPLEMENT" and b["kfk4332_liftoff_eq322_numeric"] == "SOURCE_LIMITED_OCR_AMBIGUOUS",
        "building_wake_source_limited": a["building_wake_complete_numerics"] == "NOT_RECOVERED" and b["building_wake_complete_numerics"] == "SOURCE_LIMITED",
        "plume_rise_source_limited": a["plume_rise_plrise_risefx_complete_numerics"] == "NOT_RECOVERED" and b["plume_rise_complete_numerics"] == "SOURCE_LIMITED",
        "eq44_source_limited": b["eq44_reemission_rate_generation"] == "SOURCE_LIMITED",
        "mixed_origin_not_inferred": b["mixed_environmental_hto_origin_partition"] == "NOT_INFERRED",
        "canada_full_replay_false": bench["canada_full_numeric_replay"] is False and bench["canada_empirical_validation"] is False,
        "iter_full_replay_false": bench["iter_full_atmospheric_numeric_replay"] is False and bench["iter_empirical_validation"] is False,
        "production_false": hard["production_parameter_activation"] is False,
        "calibration_false": hard["calibration"] is False,
        "empirical_validation_false": hard["empirical_validation"] is False,
        "physical_accuracy_false": hard["physical_accuracy_claim"] is False,
        "cteas_atmos_false": hard["cteas_atmos_binding"] is False,
        "original_equivalence_false": hard["original_ufotri_executable_equivalence"] is False,
    }
    return {"checks": checks, "pass": all(checks.values())}


def _lifecycle(roadmap: str) -> dict[str, Any]:
    complete = _h6_complete(roadmap)
    common = {
        "broader_replication_false": "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`" in roadmap,
        "original_equivalence_not_established": "- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`" in roadmap,
        "cteas_atmos_optional": "- `CTEAS_ATMOS_BACKEND=DEFERRED_OPTIONAL_HIGHER_FIDELITY_BACKEND`" in roadmap,
    }
    if complete:
        specific = {
            "reconstruction_true_post_merge": "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`" in roadmap,
            "no_immediate_internal_stage": "## 6. Immediate next stage\n\n`NO_IMMEDIATE_INTERNAL_MANUAL_RECONSTRUCTION_STAGE`" in roadmap,
        }
        state = "COMPLETE_POST_MERGE"
    else:
        specific = {
            "reconstruction_still_pending": "- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE_PENDING_NATIVE_ATMOSPHERE_CLOSURE`" in roadmap,
            "h6_immediate": "## 6. Immediate next stage\n\n`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`" in roadmap,
        }
        state = "CANDIDATE_PRE_MERGE"
    checks = {**common, **specific}
    return {"state": state, "checks": checks, "pass": all(checks.values())}


def _scope(roadmap: str) -> dict[str, Any]:
    complete = _h6_complete(roadmap)
    lifecycle_checks: dict[str, bool] = {}
    if complete:
        h6 = _section(roadmap, STAGE)
        head = _sha(h6, "Certified head")
        merge = _sha(h6, "Merge SHA")
        target = head
        head_tree = _gt("rev-parse", f"{head}^{{tree}}")
        merge_tree = _gt("rev-parse", f"{merge}^{{tree}}")
        parents = _gt("show", "-s", "--format=%P", merge).split()
        lifecycle_checks = {
            "h6_head_is_merge_parent": head in parents,
            "h6_head_tree_equals_merge_tree": head_tree == merge_tree,
            "h6_merge_ancestor_of_current_head": _git("merge-base", "--is-ancestor", merge, "HEAD", check=False).returncode == 0,
        }
        mode = "CERTIFIED_H6_HISTORICAL_SCOPE"
    else:
        target = "HEAD"
        mode = "H6_CANDIDATE_SCOPE"
    changed = {line.strip() for line in _gt("diff", "--name-only", f"{BASE}..{target}").splitlines() if line.strip()}
    checks = {
        "exact_five_files": changed == ALLOWED,
        "no_src": not any(path.startswith("src/") for path in changed),
        "no_configs": not any(path.startswith("configs/") for path in changed),
        "no_workflows": not any(path.startswith(".github/workflows/") for path in changed),
        "no_roadmap": not any(path.startswith("docs/v4/roadmap/") for path in changed),
        **lifecycle_checks,
    }
    return {"mode": mode, "audit_target": target, "changed_paths": sorted(changed), "allowed_paths": sorted(ALLOWED), "checks": checks, "pass": all(checks.values())}


def build_result() -> dict[str, Any]:
    roadmap = ROADMAP.read_text(encoding="utf-8")
    ledger = _ledger(roadmap)
    native = _native_reexecution()
    g3 = _g3()
    g4 = _historical_g4()
    boundaries = _boundaries(roadmap)
    lifecycle = _lifecycle(roadmap)
    scope = _scope(roadmap)
    gates = {
        "h1_h5_complete_and_merge_no_drift": ledger["all_h1_h5_complete_no_drift"],
        "h6_lifecycle_valid": ledger["h6_lifecycle_valid"],
        "h1_h5_machine_reexecution": native["pass"],
        "historical_g3_reexecution": g3["pass"],
        "historical_g4_preserved": g4["pass"],
        "source_limited_boundaries_preserved": boundaries["pass"],
        "claim_lifecycle_valid": lifecycle["pass"],
        "qualification_only_scope": scope["pass"],
    }
    passed = all(gates.values())
    complete = _h6_complete(roadmap)
    return {
        "schema_version": "v2",
        "stage": STAGE,
        "status": "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2" if passed else "FAIL_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2",
        "lifecycle_state": "COMPLETE_POST_MERGE" if complete else "CANDIDATE_PRE_MERGE",
        "ledger": ledger,
        "native_gate_reexecution": native,
        "historical_g3": g3,
        "historical_g4": g4,
        "source_boundaries": boundaries,
        "lifecycle": lifecycle,
        "scope": scope,
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
            "NO_IMMEDIATE_INTERNAL_MANUAL_RECONSTRUCTION_STAGE"
            if complete and passed
            else "CORRECTION_ROADMAP_STATUS_SYNC_SET_RECONSTRUCTION_COMPLETE_TRUE"
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
