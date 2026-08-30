#!/usr/bin/env python3
"""Machine-visible G3 UFOTRI cross-module fidelity qualification R1."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import yaml

from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_cross_module_fidelity_qualification_r1.yaml"
GAP_AUDIT = ROOT / "docs/v4/governance/ufotri_replication_gap_audit_r1.yaml"
DEFAULTS = ROOT / "configs/default_parameters.yaml"
ADVANCED_CASE = ROOT / "configs/advanced_test_case.yaml"
ROOT_V4_SOLVER = ROOT / "src/cteas_ufotri/plant/root_v4/root_solver.py"

STATUS_SCRIPTS = {
    "obt_numerical": "scripts/v4/run_ufotri_obt_compartment_conservation_numerical_integration_r1.py",
    "hydrology_numerical": "scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py",
    "ht_derived_hto_provenance": "scripts/v4/check_ufotri_ht_derived_hto_reemission_secondary_feedback_reconciliation_r1.py",
    "reemission_area_source": "scripts/v4/check_ufotri_reemission_area_source_reconciliation_r1.py",
    "canada_benchmark_contract": "scripts/v4/check_ufotri_canada_1987_benchmark_reconstruction_r1.py",
    "iter_benchmark_contract": "scripts/v4/check_ufotri_iter_benchmark_reconstruction_r1.py",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return data


def _run_status_script(relative: str) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / relative)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{relative} failed with exit {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    status_lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if "_STATUS=" in line
    ]
    passing = [line for line in status_lines if "=PASS_" in line]
    if not passing:
        raise RuntimeError(f"{relative} produced no PASS status line: {status_lines!r}")
    return {"script": relative, "status_line": passing[-1]}


def _run_json_script(relative: str, output: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(ROOT / relative), "--output", str(output)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{relative} failed with exit {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    payload = json.loads(output.read_text(encoding="utf-8"))
    if not str(payload.get("status", "")).startswith("PASS_"):
        raise RuntimeError(f"{relative} did not return PASS status")
    return payload


def _root_delay_probe() -> dict[str, Any]:
    config = load_configuration(DEFAULTS, ADVANCED_CASE)
    dt = int(config["time_step_seconds"])
    delay_seconds = int(config["soil"].get("root_uptake_delay_seconds", 0))
    if delay_seconds != 10800:
        raise RuntimeError("advanced case must retain the manual-compatible 10800 s root delay")
    if delay_seconds % dt != 0:
        raise RuntimeError("root delay must be an integral number of model steps")
    delay_steps = delay_seconds // dt
    frame = run_short_case(config)
    roots = frame["root_water_uptake"].to_numpy(dtype=float)
    transpiration = frame["plant_transpiration"].to_numpy(dtype=float)
    zero_prefix = all(abs(value) <= 1.0e-18 for value in roots[:delay_steps])
    exact_shift = all(
        math.isclose(
            float(roots[index]),
            float(transpiration[index - delay_steps]),
            rel_tol=1.0e-12,
            abs_tol=1.0e-18,
        )
        for index in range(delay_steps, len(roots))
    )
    root_solver_text = ROOT_V4_SOLVER.read_text(encoding="utf-8")
    root_v4_no_hidden_delay = (
        "It does not infer transpiration, hydrology" in root_solver_text
        and "UFOTRI short-term delay" in root_solver_text
        and "deque" not in root_solver_text
    )
    return {
        "manual_delay_seconds": delay_seconds,
        "dt_seconds": dt,
        "delay_steps": delay_steps,
        "initial_delay_window_zero": zero_prefix,
        "post_delay_equals_transpiration_exact_shift": exact_shift,
        "root_v4_no_hidden_delay": root_v4_no_hidden_delay,
        "pass": zero_prefix and exact_shift and root_v4_no_hidden_delay,
    }


def _gap_disposition_probe(governance: dict[str, Any]) -> dict[str, Any]:
    audit = _load_yaml(GAP_AUDIT)
    audit_entries = audit["replication_matrix"]
    audit_ids = [entry["id"] for entry in audit_entries]
    dispositions = governance["gap_dispositions"]
    allowed = set(governance["allowed_gap_dispositions"])
    ids_exact = audit_ids == [f"UFR-{index:02d}" for index in range(1, 31)]
    mapping_exact = set(dispositions) == set(audit_ids)
    allowed_only = all(
        entry["disposition"] in allowed
        for entry in dispositions.values()
    )
    required_unresolved = [
        entry["id"]
        for entry in audit_entries
        if entry.get("required_for_manual_reconstruction") is True
        and entry["id"] not in dispositions
    ]
    external = {
        key
        for key, value in dispositions.items()
        if value["disposition"] == "DEFERRED_EXTERNAL_DEPENDENCY"
    }
    expected_external = {"UFR-01", "UFR-03", "UFR-04", "UFR-05"}
    blocked = {
        key
        for key, value in dispositions.items()
        if value["disposition"] == "BLOCKED_SOURCE_UNAVAILABLE"
    }
    expected_blocked = {"UFR-29", "UFR-30"}
    return {
        "audit_item_count": len(audit_ids),
        "disposition_item_count": len(dispositions),
        "ids_exact_01_to_30": ids_exact,
        "mapping_exact": mapping_exact,
        "allowed_dispositions_only": allowed_only,
        "required_unresolved": required_unresolved,
        "external_dependencies_exact": external == expected_external,
        "source_blocked_exact": blocked == expected_blocked,
        "pass": (
            len(audit_ids) == 30
            and len(dispositions) == 30
            and ids_exact
            and mapping_exact
            and allowed_only
            and not required_unresolved
            and external == expected_external
            and blocked == expected_blocked
        ),
    }


def build_result() -> dict[str, Any]:
    governance = _load_yaml(GOVERNANCE)
    status_results: dict[str, dict[str, Any]] = {}

    with tempfile.TemporaryDirectory(prefix="ufotri_g3_") as directory:
        temp = Path(directory)
        rc1 = _run_json_script(
            "scripts/v4/run_development_baseline_rc1.py",
            temp / "rc1.json",
        )
        controlled = _run_json_script(
            "scripts/v4/run_controlled_ufotri_end_to_end_numerical_integration_r1.py",
            temp / "controlled_e2e.json",
        )
        for name, script in STATUS_SCRIPTS.items():
            status_results[name] = _run_status_script(script)

    controlled_gates = controlled["gates"]
    runtime = {
        "rc1_composition_pass": str(rc1["status"]).startswith("PASS_"),
        "controlled_e2e_pass": str(controlled["status"]).startswith("PASS_"),
        "deterministic_repeat": controlled_gates["deterministic_repeat"] is True,
        "restart_equivalence": controlled_gates["restart_equivalence"] is True,
        "cross_module_plant_balance": controlled_gates["plant_balance_closed"] is True,
        "cross_module_coupled_balance": controlled_gates["coupled_balance_closed"] is True,
        "soil_root_identity": controlled_gates["root_j_equals_q_times_c"] is True,
        "food_inventory_nonzero": controlled_gates["food_inventory_nonzero"] is True,
        "annual_intake_nonzero": controlled_gates["annual_intake_nonzero"] is True,
        "dose_nonzero": controlled_gates["dose_nonzero"] is True,
        "all_fidelity_status_scripts_pass": len(status_results) == len(STATUS_SCRIPTS),
        "obt_timestep_refinement_gate_reexecuted": "obt_numerical" in status_results,
        "hydrology_timestep_refinement_gate_reexecuted": "hydrology_numerical" in status_results,
        "ht_hto_provenance_gate_reexecuted": "ht_derived_hto_provenance" in status_results,
        "reemission_handoff_gate_reexecuted": "reemission_area_source" in status_results,
        "canada_contract_gate_reexecuted": "canada_benchmark_contract" in status_results,
        "iter_contract_gate_reexecuted": "iter_benchmark_contract" in status_results,
    }

    delay = _root_delay_probe()
    gaps = _gap_disposition_probe(governance)
    rc1_vs_fidelity = governance["rc1_vs_fidelity"]
    comparison = {
        "numerical_equality_required": rc1_vs_fidelity["equality_required"] is False,
        "difference_count": len(rc1_vs_fidelity["differences"]),
        "all_required_difference_axes_present": set(rc1_vs_fidelity["differences"]) == {
            "leaf_exchange",
            "obt",
            "soil_hydrology",
            "foodchain",
            "ht_branch",
            "reemission_area_source",
            "short_term_root_delay",
        },
    }
    comparison["pass"] = (
        comparison["numerical_equality_required"]
        and comparison["difference_count"] == 7
        and comparison["all_required_difference_axes_present"]
    )

    external = governance["external_dependencies"]
    boundaries = governance["hard_boundaries"]
    fail_closed = {
        "real_hto_atmos_deferred": external["real_cteas_atmos_hto_binding"] == "DEFERRED_EXTERNAL_DEPENDENCY",
        "real_ht_atmos_deferred": external["real_cteas_atmos_ht_binding"] == "DEFERRED_EXTERNAL_DEPENDENCY",
        "real_e2e_atmos_deferred": external["real_atmos_end_to_end_ht_to_hto"] == "DEFERRED_EXTERNAL_DEPENDENCY",
        "no_production_source_change": boundaries["production_source_change"] is False,
        "rc1_default_unchanged": boundaries["rc1_default_changed"] is False,
        "no_parameter_activation": boundaries["parameter_activation"] is False,
        "no_empirical_claim": boundaries["empirical_validation_claimed"] is False,
        "g4_not_preempted": boundaries["g4_final_gate_preempted"] is False,
    }

    gates = {
        **runtime,
        "root_delay_reconciled": delay["pass"] is True,
        "all_30_gaps_disposed": gaps["pass"] is True,
        "rc1_vs_fidelity_explicit": comparison["pass"] is True,
        "fail_closed_boundaries": all(fail_closed.values()),
    }
    status = (
        "PASS_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION"
        if all(gates.values())
        else "FAIL_CONTROLLED_CROSS_MODULE_FIDELITY_QUALIFICATION"
    )
    return {
        "schema_version": "v1",
        "stage": "UFOTRI_CROSS_MODULE_FIDELITY_QUALIFICATION_R1",
        "status": status,
        "source_kind": "CONTROLLED_SYNTHETIC_REPLAY_MANUAL_COMPATIBLE_ONLY",
        "runtime_gates": runtime,
        "component_statuses": status_results,
        "root_delay_probe": delay,
        "gap_disposition_probe": gaps,
        "rc1_vs_fidelity_probe": comparison,
        "fail_closed_boundaries": fail_closed,
        "gates": gates,
        "remaining_external_dependencies": [
            "REAL_CTEAS_ATMOS_HTO_BINDING",
            "REAL_CTEAS_ATMOS_HT_BINDING",
            "REAL_ATMOS_END_TO_END_HT_TO_HTO",
        ],
        "remaining_source_limits": [
            "COMPLETE_EQ44_RATE_RECOVERY",
            "CANADA_FULL_NUMERIC_EMPIRICAL_REPLAY",
            "ITER_FULL_ATMOSPHERIC_NUMERIC_REPLAY",
            "ORIGINAL_UFOTRI_EXECUTABLE_NUMERICAL_EQUIVALENCE",
            "ORIGINAL_PARAMETER_LOADER_AND_HIDDEN_DEFAULTS",
        ],
        "manual_based_functional_reconstruction_complete": False,
        "next_stage_after_clean_merge_and_roadmap_sync": "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"UFOTRI_G3_STATUS={result['status']}")
    print("UFOTRI_G3_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if str(result["status"]).startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
