#!/usr/bin/env python3
"""Machine-visible G4 UFOTRI manual-based reconstruction final gate R1."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_manual_based_functional_reconstruction_final_gate_r1.yaml"
G3_GOVERNANCE = ROOT / "docs/v4/governance/ufotri_cross_module_fidelity_qualification_r1.yaml"
ROADMAP = ROOT / "docs/v4/roadmap/UFOTRI_REPLICATION_MASTER_PLAN.md"
G3_SCRIPT = ROOT / "scripts/v4/check_ufotri_cross_module_fidelity_qualification_r1.py"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return data


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def _git_text(*args: str) -> str:
    return _git(*args).stdout.strip()


def _roadmap_section_for_stage(text: str, stage: str) -> str:
    matches = [
        section
        for section in re.split(r"(?=^#### )", text, flags=re.MULTILINE)
        if f"- Stage: `{stage}`" in section
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one roadmap section for {stage}, got {len(matches)}")
    return matches[0]


def _roadmap_heading_section(text: str, heading_prefix: str) -> str:
    matches = [
        section
        for section in re.split(r"(?=^#### )", text, flags=re.MULTILINE)
        if section.startswith(heading_prefix)
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one roadmap heading {heading_prefix!r}")
    return matches[0]


def _single_sha(section: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}: `([0-9a-f]{{40}})`", section, flags=re.MULTILINE)
    if match is None:
        raise RuntimeError(f"missing {label} SHA in roadmap section")
    return match.group(1)


def _g4_section(roadmap_text: str) -> str:
    return _roadmap_section_for_stage(
        roadmap_text,
        "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1",
    )


def _g4_is_complete(roadmap_text: str) -> bool:
    return "- Status: `COMPLETE`" in _g4_section(roadmap_text)


def _stage_ledger_probe(governance: dict[str, Any], roadmap_text: str) -> dict[str, Any]:
    required = list(governance["required_internal_stages"])
    results: dict[str, dict[str, Any]] = {}
    for stage in required:
        section = _roadmap_section_for_stage(roadmap_text, stage)
        certified_head = _single_sha(section, "Certified head")
        merge_sha = _single_sha(section, "Merge SHA")
        certified_tree = _git_text("rev-parse", f"{certified_head}^{{tree}}")
        merge_tree = _git_text("rev-parse", f"{merge_sha}^{{tree}}")
        parents = _git_text("show", "-s", "--format=%P", merge_sha).split()
        ancestor = _git("merge-base", "--is-ancestor", merge_sha, "HEAD", check=False).returncode == 0
        roadmap_merge_tree_match = re.search(
            r"^- Merge tree: `([0-9a-f]{40})`", section, flags=re.MULTILINE
        )
        recorded_merge_tree = roadmap_merge_tree_match.group(1) if roadmap_merge_tree_match else None
        checks = {
            "roadmap_status_complete": "- Status: `COMPLETE`" in section,
            "roadmap_no_drift_recorded": (
                "- No-drift:" in section and "MERGE_TREE_DRIFT=FALSE" in section
            ),
            "certified_head_is_merge_parent": certified_head in parents,
            "certified_head_tree_equals_merge_tree": certified_tree == merge_tree,
            "recorded_merge_tree_matches_git": recorded_merge_tree == merge_tree,
            "merge_is_ancestor_of_candidate": ancestor,
        }
        results[stage] = {
            "certified_head": certified_head,
            "merge_sha": merge_sha,
            "certified_tree": certified_tree,
            "merge_tree": merge_tree,
            "checks": checks,
            "pass": all(checks.values()),
        }
    return {
        "required_stage_count": len(required),
        "expected_stage_count": governance["required_internal_stage_count"],
        "stages": results,
        "all_stage_ledgers_pass": (
            len(required) == governance["required_internal_stage_count"]
            and all(entry["pass"] for entry in results.values())
        ),
    }


def _run_g3_gate() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ufotri_g4_g3_") as directory:
        output = Path(directory) / "g3.json"
        completed = subprocess.run(
            [sys.executable, str(G3_SCRIPT), "--output", str(output)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "G3 aggregate gate failed during G4 requalification\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        payload = json.loads(output.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION":
        raise RuntimeError("G3 aggregate gate did not retain its PASS status")
    return payload


def _gap_probe(governance: dict[str, Any], g3_governance: dict[str, Any]) -> dict[str, Any]:
    dispositions = g3_governance["gap_dispositions"]
    counts = Counter(entry["disposition"] for entry in dispositions.values())
    required_counts = governance["required_gap_disposition_counts"]
    external = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    }
    blocked = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "BLOCKED_SOURCE_UNAVAILABLE"
    }
    source_limited = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "COMPLETE_WITH_SOURCE_LIMIT"
    }
    reconciled = {
        key for key, entry in dispositions.items()
        if entry["disposition"] == "RECONCILED_EXISTING_OPTION"
    }
    expected_external = set(governance["required_external_gap_ids"])
    expected_blocked = set(governance["required_source_blocked_gap_ids"])
    expected_source_limited = set(governance["required_source_limited_gap_ids"])
    expected_reconciled = set(governance["required_reconciled_existing_gap_ids"])
    count_match = all(counts[key] == value for key, value in required_counts.items())
    return {
        "gap_count": len(dispositions),
        "disposition_counts": dict(counts),
        "required_counts": required_counts,
        "counts_match": count_match,
        "external_exact": external == expected_external,
        "blocked_exact": blocked == expected_blocked,
        "source_limited_exact": source_limited == expected_source_limited,
        "reconciled_existing_exact": reconciled == expected_reconciled,
        "unimplemented_recoverable_internal_gap_count": 0 if count_match else -1,
        "pass": (
            len(dispositions) == 30
            and count_match
            and external == expected_external
            and blocked == expected_blocked
            and source_limited == expected_source_limited
            and reconciled == expected_reconciled
        ),
    }


def _boundary_probe(governance: dict[str, Any], g3_governance: dict[str, Any], roadmap_text: str) -> dict[str, Any]:
    e4 = _roadmap_heading_section(roadmap_text, "#### E4.")
    e5 = _roadmap_heading_section(roadmap_text, "#### E5.")
    g4 = _g4_section(roadmap_text)
    g4_complete = "- Status: `COMPLETE`" in g4
    source = governance["source_and_validation_boundaries"]
    claim = governance["claim_boundary"]
    g3_bench = g3_governance["benchmark_boundaries"]
    lifecycle_checks = (
        {
            "roadmap_records_completed_g4": (
                "- Status: `COMPLETE`" in g4
                and "- Validation: `PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE`" in g4
                and "MERGE_TREE_DRIFT=FALSE" in g4
            ),
            "roadmap_records_reconstruction_true": (
                "`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`" in roadmap_text
            ),
            "roadmap_keeps_broader_replication_false": (
                "`UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`" in roadmap_text
            ),
            "roadmap_records_no_immediate_internal_stage": (
                "`NO_IMMEDIATE_INTERNAL_REPLICATION_STAGE`" in roadmap_text
            ),
        }
        if g4_complete
        else {
            "roadmap_authorizes_g4": (
                "- Control-plane authorization: `AUTHORIZED_AFTER_G3_ROADMAP_SYNC`" in g4
            ),
            "roadmap_flag_still_false_before_g4_merge": (
                "`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE` remains unchanged until G4 itself passes exact-head CI and merge/no-drift audit."
                in roadmap_text
            ),
        }
    )
    checks = {
        "e4_remains_deferred": "- Status: `DEFERRED_EXTERNAL_DEPENDENCY`" in e4,
        "e5_remains_deferred": "- Status: `DEFERRED_EXTERNAL_DEPENDENCY`" in e5,
        "canada_full_replay_remains_false": g3_bench["canada_full_numeric_replay_ready"] is False,
        "canada_empirical_remains_false": g3_bench["canada_empirical_validation_complete"] is False,
        "iter_full_atmos_replay_remains_false": g3_bench["iter_full_atmospheric_numeric_replay_complete"] is False,
        "iter_empirical_remains_false": g3_bench["iter_empirical_validation_complete"] is False,
        "original_equivalence_remains_false": g3_bench["original_executable_equivalence"] is False,
        "complete_eq44_not_claimed": source["complete_eq44_rate_recovery"] is False,
        "production_readiness_not_claimed": source["production_readiness_claimed"] is False,
        "physical_accuracy_not_claimed": source["physical_accuracy_claimed"] is False,
        "historical_candidate_flag_not_preempted": governance["candidate_target_flag_value"] is False,
        "post_merge_flag_eligibility_explicit": governance["target_flag_eligible_after_clean_merge_no_drift_and_roadmap_sync"] is True,
        "original_numerical_equivalence_not_established": (
            claim["remains_false_or_not_established"]["UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE"]
            == "NOT_ESTABLISHED"
        ),
        **lifecycle_checks,
    }
    return {
        "lifecycle_state": "COMPLETE_POST_MERGE" if g4_complete else "CANDIDATE_PRE_MERGE",
        "checks": checks,
        "pass": all(checks.values()),
    }


def _candidate_scope_probe(governance: dict[str, Any], roadmap_text: str) -> dict[str, Any]:
    base = governance["base_main_sha"]
    allowed = set(governance["candidate_scope"]["allowed_changed_paths"])
    g4 = _g4_section(roadmap_text)
    g4_complete = "- Status: `COMPLETE`" in g4

    if g4_complete:
        certified_head = _single_sha(g4, "Certified head")
        merge_sha = _single_sha(g4, "Merge SHA")
        audit_target = merge_sha
        certified_tree = _git_text("rev-parse", f"{certified_head}^{{tree}}")
        merge_tree = _git_text("rev-parse", f"{merge_sha}^{{tree}}")
        parents = _git_text("show", "-s", "--format=%P", merge_sha).split()
        lifecycle_checks = {
            "certified_head_is_g4_merge_parent": certified_head in parents,
            "certified_head_tree_equals_g4_merge_tree": certified_tree == merge_tree,
            "g4_merge_is_ancestor_of_current_head": (
                _git("merge-base", "--is-ancestor", merge_sha, "HEAD", check=False).returncode == 0
            ),
        }
        mode = "CERTIFIED_G4_HISTORICAL_SCOPE"
    else:
        audit_target = "HEAD"
        lifecycle_checks = {}
        mode = "G4_CANDIDATE_SCOPE"

    changed = {
        line.strip()
        for line in _git_text("diff", "--name-only", f"{base}..{audit_target}").splitlines()
        if line.strip()
    }
    exact_scope_match = changed == allowed
    checks = {
        "exact_five_file_scope": exact_scope_match,
        **lifecycle_checks,
    }
    return {
        "mode": mode,
        "base_main_sha": base,
        "audit_target": audit_target,
        "changed_paths": sorted(changed),
        "allowed_paths": sorted(allowed),
        "exact_scope_match": exact_scope_match,
        "checks": checks,
        "pass": all(checks.values()),
    }


def build_result() -> dict[str, Any]:
    governance = _load_yaml(GOVERNANCE)
    g3_governance = _load_yaml(G3_GOVERNANCE)
    roadmap_text = ROADMAP.read_text(encoding="utf-8")

    stage_ledger = _stage_ledger_probe(governance, roadmap_text)
    g3_result = _run_g3_gate()
    gaps = _gap_probe(governance, g3_governance)
    boundaries = _boundary_probe(governance, g3_governance, roadmap_text)
    scope = _candidate_scope_probe(governance, roadmap_text)
    g4_complete = _g4_is_complete(roadmap_text)

    gates = {
        "all_19_internal_stage_ledgers_complete_and_no_drift": stage_ledger["all_stage_ledgers_pass"],
        "g3_aggregate_gate_reexecutes_pass": g3_result["status"] == "PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION",
        "g3_runtime_gates_all_true": all(g3_result["gates"].values()),
        "all_30_gaps_have_final_allowed_dispositions": gaps["pass"],
        "no_unimplemented_recoverable_internal_gap": gaps["unimplemented_recoverable_internal_gap_count"] == 0,
        "deferred_and_source_limited_boundaries_preserved": boundaries["pass"],
        "g4_stage_scope_remains_exactly_five_qualification_artifacts": scope["pass"],
    }
    pass_gate = all(gates.values())
    status = (
        "PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE"
        if pass_gate
        else "FAIL_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE"
    )
    return {
        "schema_version": "v1",
        "stage": governance["stage"],
        "status": status,
        "lifecycle_state": "COMPLETE_POST_MERGE" if g4_complete else "CANDIDATE_PRE_MERGE",
        "gate_scope": "RECOVERABLE_INTERNAL_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_ONLY",
        "stage_ledger_probe": stage_ledger,
        "g3_reexecution_status": g3_result["status"],
        "gap_probe": gaps,
        "boundary_probe": boundaries,
        "candidate_scope_probe": scope,
        "gates": gates,
        "candidate_target_flag_value": False,
        "reconstruction_completion_eligible_after_clean_merge_no_drift_and_roadmap_sync": pass_gate,
        "target_flag_value_after_clean_merge_no_drift_and_roadmap_sync": True if pass_gate else False,
        "real_cteas_atmos_binding_complete": False,
        "full_real_atmos_ufotri_replication_complete": False,
        "empirical_validation_complete": False,
        "production_readiness": False,
        "physical_accuracy_validated": False,
        "ufotri_original_numerical_equivalence": "NOT_ESTABLISHED",
        "next_action_if_clean_merge_no_drift": (
            "NO_FURTHER_INTERNAL_REPLICATION_STAGE"
            if pass_gate and g4_complete
            else (
                "ROADMAP_STATUS_SYNC_SET_UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE_TRUE"
                if pass_gate
                else "DO_NOT_PROMOTE_FLAG"
            )
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
    print(f"UFOTRI_G4_STATUS={result['status']}")
    print("UFOTRI_G4_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if str(result["status"]).startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())