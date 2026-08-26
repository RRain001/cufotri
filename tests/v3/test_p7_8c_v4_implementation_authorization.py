from __future__ import annotations

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = "3103d82c5cad3ead37a827f4970e8d649a1107dc"
CONTENT_TIP = "e68d556c9a18966b2cce4af012483ad2f8fe4116"
GATE = ROOT / "docs/v3/physics/p7_8c_v4_implementation_authorization.yaml"
V3_1 = ROOT / "docs/v3_1/contracts/mass_basis_contract.yaml"
SELECTION = ROOT / "docs/v3/physics/p7_8b2_physics_selection.yaml"
ROADMAP = ROOT / "docs/v3/physics/p7_8b2_architecture_roadmap.yaml"
REPORT = ROOT / "docs/v3/reports/v3_p7_8c_v4_implementation_authorization.md"
ADR = ROOT / "docs/v3/adr/ADR-023-p7-8c-v4-authorization-boundary.md"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_p7_8c_entry_requires_closed_v3_1_on_exact_main() -> None:
    gate = load(GATE)
    v31 = load(V3_1)
    assert gate["stage"] == "P7.8C"
    assert gate["status"] == "PASS_CONTRACT_PREPARATION_AUTHORIZATION"
    assert gate["entry_state"]["main_sha"] == BASE_MAIN
    assert gate["entry_state"]["v3_1_exit_gate_pass"] is True
    assert gate["entry_state"]["v3_1_main_merged"] is True
    assert v31["status"] == "PASS_INDEPENDENT_REREVIEW_MAIN_MERGED"
    assert v31["exit_gate"]["v3_1_exit_gate_pass"] is True
    assert v31["exit_gate"]["main_merge_completed"] is True


def test_p7_8c_preserves_every_p7_8b2_model_implementation_prerequisite() -> None:
    gate = load(GATE)
    selection = load(SELECTION)
    required = set(selection["governance"]["required_before_p7_8c"])
    recorded = set(gate["required_before_selected_model_implementation"])
    # P7.8C expands the earlier shorthand into explicit dimensional,
    # provenance and preregistered-metric requirements; it may not omit any
    # P7.8B-2 prerequisite.
    aliases = {
        "equation_and_unit_contract": "equation_and_unit_contract",
        "state_ownership_contract": "state_ownership_contract",
        "dimensional_and_conservation_tests": "dimensional_and_conservation_tests",
        "restart_and_compatibility_tests": "restart_and_compatibility_tests",
        "validation_dataset_and_case_contract": "validation_dataset_and_case_contract",
        "coupling_review_for_selected_numerical_changes": "coupling_review_when_pipeline_or_numerical_boundary_changes",
        "independent_review": "independent_review",
        "explicit_implementation_authorization": "explicit_item_level_implementation_authorization",
    }
    assert required == set(aliases)
    assert set(aliases.values()).issubset(recorded)


def test_only_control_plane_contract_preparation_is_authorized() -> None:
    gate = load(GATE)
    decision = gate["authorization_decision"]["v4_data_and_state_contracts"]
    assert decision["status"] == "AUTHORIZED_CONTROL_PLANE_ONLY"
    assert gate["gate_interpretation"]["control_plane_contract_work_is_model_implementation"] is False
    assert gate["gate_interpretation"]["contract_preparation_may_change_solver_equations"] is False
    assert gate["gate_interpretation"]["contract_preparation_may_change_runtime_state_serialization"] is False
    assert gate["gate_interpretation"]["contract_preparation_may_change_numerical_coupling"] is False
    assert gate["gate_interpretation"]["contract_preparation_may_activate_parameters"] is False
    assert "production_solver_equations" in decision["forbidden_changes"]
    assert "numerical_coupling_change" in decision["forbidden_changes"]
    assert "candidate_parameter_values" in decision["forbidden_changes"]


def test_all_selected_future_model_implementations_remain_held() -> None:
    gate = load(GATE)
    decisions = gate["authorization_decision"]
    for key in (
        "leaf_dynamic_stomatal_response",
        "obt_formation_package",
        "root_uptake_water_flux_boundary",
    ):
        item = decisions[key]
        assert item["status"] == "HOLD_PREREQUISITES_INCOMPLETE"
        assert item["implementation_authorized"] is False
        assert item["missing_or_unclosed_gates"]
    assert decisions["root_uptake_water_flux_boundary"]["coupling_classification"] == (
        "NUMERICAL_COUPLING_CHANGE_REQUIRED"
    )
    assert "p7_5_p7_5b_numerical_coupling_review" in (
        decisions["root_uptake_water_flux_boundary"]["missing_or_unclosed_gates"]
    )


def test_deferred_and_rejected_models_cannot_be_reopened_by_p7_8c() -> None:
    gate = load(GATE)
    deferred = gate["unchanged_or_deferred"]
    assert deferred["soil_full_hydrology"] == {
        "status": "INSUFFICIENT_EVIDENCE",
        "implementation_authorized": False,
    }
    assert deferred["tfwt_dynamic_water_turnover"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert deferred["food_continuous_or_hybrid_transfer"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert deferred["obt_organ_specific_growth"]["status"] == "REJECTED"
    assert all(item["implementation_authorized"] is False for item in deferred.values())


def test_frozen_baseline_and_activation_gates_remain_closed() -> None:
    gate = load(GATE)
    hard = gate["hard_invariants"]
    assert hard["implementation_started"] is False
    assert hard["solver_changes_authorized"] is False
    assert hard["numerical_coupling_changes_authorized"] is False
    assert hard["p7_5_semantics_changed"] is False
    assert hard["p7_5b_semantics_changed"] is False
    assert hard["current_v3_runtime_changed_by_p7_8c"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["ufotri_active_database"] is False
    assert hard["v3_physics_ready"] is False
    assert hard["v4_selected_model_implementation_authorized"] is False
    assert hard["physical_validation_complete"] is False


def test_roadmap_order_is_preserved_and_next_item_is_contracts_only() -> None:
    gate = load(GATE)
    roadmap = load(ROADMAP)
    order = [item["item_id"] for item in roadmap["V4"]["implementation_order"]]
    assert order == [
        "V4_DATA_AND_STATE_CONTRACTS",
        "V4_LEAF_DYNAMIC_STOMATAL_RESPONSE",
        "V4_OBT_FORMATION_PACKAGE",
        "V4_ROOT_UPTAKE_WATER_FLUX_BOUNDARY",
    ]
    exit_state = gate["exit_state"]
    assert exit_state["next_item"] == "V4_DATA_AND_STATE_CONTRACTS"
    assert exit_state["next_item_scope"] == "CONTROL_PLANE_ONLY"
    assert exit_state["v4_physics_implementation_authorized"] is False


def test_p7_8c_stage_content_is_governance_only() -> None:
    changed = {
        line
        for line in git("diff", "--name-only", BASE_MAIN, CONTENT_TIP).splitlines()
        if line
    }
    assert changed == {
        ".github/workflows/v3-integration-gate.yml",
        "docs/v3/adr/ADR-023-p7-8c-v4-authorization-boundary.md",
        "docs/v3/physics/p7_8c_v4_implementation_authorization.yaml",
        "docs/v3/reports/v3_p7_8c_v4_implementation_authorization.md",
    }
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("schemas/") for path in changed)
    assert not any(path.startswith("configs/") for path in changed)


def test_report_and_adr_state_the_same_fail_closed_decision() -> None:
    report = REPORT.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    for token in (
        "PASS_CONTRACT_PREPARATION_AUTHORIZATION",
        "V4_DATA_AND_STATE_CONTRACTS",
        "ACTIVE_PARAMETERS = 0",
        "V3_PHYSICS_READY = FALSE",
    ):
        assert token in report
        assert token in adr
    assert "V4_SELECTED_MODEL_IMPLEMENTATION = HOLD_PREREQUISITES_INCOMPLETE" in report
    assert "V4_SELECTED_MODEL_IMPLEMENTATION_AUTHORIZED = FALSE" in adr
