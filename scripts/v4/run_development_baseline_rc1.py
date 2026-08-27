#!/usr/bin/env python3
"""Machine-visible final V4 internal development-baseline RC1 composition gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
CURRENT_STATE = ROOT / "docs/v4/governance/v4_current_system_state.yaml"

COMPONENTS = (
    (
        "controlled_ufotri_e2e",
        "scripts/v4/run_controlled_ufotri_end_to_end_numerical_integration_r1.py",
        "PASS_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION",
    ),
    (
        "sensitivity_screening",
        "scripts/v4/run_system_sensitivity_screening_r1.py",
        "PASS_SOFTWARE_SCREENING",
    ),
    (
        "root_operator_split",
        "scripts/v4/run_root_operator_split_comparison_r1.py",
        "PASS_SELECTION",
    ),
    (
        "soil_root_tfwt_obt",
        "scripts/v4/run_soil_root_tfwt_obt_integration_r1.py",
        "PASS_INTEGRATION",
    ),
    (
        "replay_orchestration",
        "scripts/v4/run_replay_input_orchestration_r1.py",
        "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION",
    ),
    (
        "food_intake_dose",
        "scripts/v4/run_food_intake_dose_endpoint_adapter_r1.py",
        "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION",
    ),
)


def _status_from_stdout(stdout: str, expected_status: str) -> str | None:
    for line in stdout.splitlines():
        if "_STATUS=" not in line:
            continue
        value = line.split("=", 1)[1].strip()
        if value == expected_status:
            return value
    return None


def _run_component(name: str, script: str, expected_status: str, temp: Path) -> dict[str, object]:
    output = temp / f"{name}.json"
    completed = subprocess.run(
        [sys.executable, str(ROOT / script), "--output", str(output)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    if not output.exists():
        raise RuntimeError(f"{name} did not write {output}")
    payload = json.loads(output.read_text(encoding="utf-8"))
    actual = payload.get("status")
    if actual is None:
        actual = _status_from_stdout(completed.stdout, expected_status)
    if actual != expected_status:
        raise RuntimeError(f"{name} status {actual!r} != {expected_status!r}")
    return payload


def build_result() -> dict[str, object]:
    current = yaml.safe_load(CURRENT_STATE.read_text(encoding="utf-8"))
    component_statuses: dict[str, str] = {}
    component_boundaries: dict[str, dict[str, object]] = {}

    with tempfile.TemporaryDirectory(prefix="cteas_ufotri_v4_rc1_") as directory:
        temp = Path(directory)
        for name, script, expected in COMPONENTS:
            payload = _run_component(name, script, expected, temp)
            component_statuses[name] = expected
            boundaries = payload.get("hard_boundaries")
            if isinstance(boundaries, dict):
                component_boundaries[name] = boundaries

    baseline = current["controlled_baseline_state"]
    readiness = current["readiness_boundaries"]
    gates = {
        "all_component_machine_gates_pass": all(
            component_statuses[name] == expected
            for name, _, expected in COMPONENTS
        ),
        "software_chain_connected": baseline["software_chain_connected_with_controlled_ufotri_profiles"] is True,
        "three_layer_soil_selected": baseline["soil_layers"] == ["L1_0_5_cm", "L2_5_15_cm", "L3_15_30_cm"],
        "eq39_selected": baseline["root_eq39_controlled_baseline_active"] is True,
        "root_20_40_40_selected": baseline["root_layer_profile_20_40_40_active"] is True,
        "root_controlled_construction_resolved": baseline["root_q_w_controlled_construction_path_resolved"] is True,
        "root_production_case_input_still_deferred": baseline["root_q_w_production_case_input_ready"] is False,
        "baseline_leaf_connected": baseline["leaf_baseline_resistance_path_connected"] is True,
        "tfwt_connected": baseline["tfwt_solver_connected"] is True,
        "reduced_ufotri_obt_connected": baseline["obt_reduced_ufotri_baseline_connected"] is True,
        "harvest_boundary_frozen": baseline["terminal_harvest_boundary"] == "KEEP_HARVEST_EVENT",
        "operator_split_frozen": baseline["operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN",
        "endpoint_connected": baseline["food_intake_dose_endpoint_connected"] is True,
        "production_readiness_fail_closed": readiness["full_model_production_ready"] is False,
        "production_input_packet_fail_closed": readiness["production_input_packet_ready"] is False,
        "real_atmos_fail_closed": readiness["real_cteas_atmos_binding"] is False,
        "empirical_validation_fail_closed": readiness["empirical_validation"] is False,
        "physical_accuracy_claim_fail_closed": readiness["physical_accuracy_claim"] is False,
        "calibration_not_started": readiness["calibration_started"] is False,
        "no_active_production_parameters": readiness["active_parameters"] == 0,
        "v3_default_unchanged": readiness["v3_default_path_changed"] is False,
    }

    status = (
        "PASS_V4_DEVELOPMENT_BASELINE_RC1_MACHINE_COMPOSITION"
        if all(gates.values())
        else "FAIL_V4_DEVELOPMENT_BASELINE_RC1_MACHINE_COMPOSITION"
    )
    return {
        "schema_version": "v1",
        "stage": "V4_DEVELOPMENT_BASELINE_RC1",
        "status": status,
        "source_kind": "CONTROLLED_INTERNAL_DEVELOPMENT_BASELINE_ONLY",
        "component_statuses": component_statuses,
        "component_hard_boundaries": component_boundaries,
        "gates": gates,
        "selected_baseline": {
            "atmosphere_input_mode": baseline["atmosphere_input_mode_for_internal_development"],
            "soil_layers": baseline["soil_layers"],
            "root_total_uptake": "UFOTRI_EQ39_EQUILIBRIUM_RADIATION_BASELINE",
            "root_distribution": [0.2, 0.4, 0.4],
            "leaf_exchange": "BASELINE_RESISTANCE_CHAIN",
            "tfwt": "CONNECTED",
            "obt": "REDUCED_UFOTRI_KF_KR_BASELINE",
            "operator_split": baseline["operator_split"],
            "harvest_boundary": baseline["terminal_harvest_boundary"],
            "food_intake_dose_endpoint": "CONNECTED",
        },
        "hard_boundaries": {
            "full_model_production_ready": False,
            "production_input_packet_ready": False,
            "real_cteas_atmos_binding": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "calibration_started": False,
            "active_parameters": 0,
            "v3_default_path_changed": False,
            "leaf_r5": False,
            "full_richards_darcy_hydrology": False,
            "multi_pool_obt": False,
            "ufotri_short_term_3h_delay": False,
            "penman_eq38_aerodynamic_term": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"V4_DEVELOPMENT_BASELINE_RC1_STATUS={result['status']}")
    print(f"V4_DEVELOPMENT_BASELINE_RC1_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if not str(result["status"]).startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
