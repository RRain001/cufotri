"""V4 system-roadmap reset R1 governance invariants."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/v4/governance/v4_system_roadmap_reset_r1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-026-v4-system-roadmap-reset.md"


def _registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def test_reset_is_control_plane_only_and_preserves_baseline() -> None:
    r = _registry()
    assert r["status"] == "PASS_CONTROL_PLANE"
    assert r["base_main_sha"] == "d4bb2def0e81fe5a26b772a239e8c6de8f0d0dcc"
    b = r["baseline"]
    assert b["default_profile"] == "v3_frozen_baseline"
    assert b["rollback_target"] == "v3_frozen_baseline"
    assert b["v3_1_mass_basis_preserved"] is True
    assert b["solver_equations_changed"] is False
    assert b["numerical_coupling_changed"] is False
    assert b["runtime_state_changed"] is False
    assert b["active_parameters"] == 0
    assert b["calibration_started"] is False
    assert b["v3_physics_ready"] is False


def test_leaf_track_is_frozen_at_r4_checkpoint() -> None:
    leaf = _registry()["leaf_r4_checkpoint"]
    assert leaf["current_status"] == "DESIGN_ONLY_NOT_COLLECTED"
    assert leaf["checkpoint_frozen"] is True
    assert leaf["experiment_executed"] is False
    assert leaf["empirical_packet_collected"] is False
    assert leaf["response_function_selected"] is False
    assert leaf["leaf_solver_implementation_authorized"] is False
    assert leaf["r5_continuation_authorized"] is False


def test_next_stage_is_atmos_exchange_contract_then_system_audit() -> None:
    stages = _registry()["next_stages"]
    assert [s["order"] for s in stages] == [1, 2]
    assert stages[0]["stage_id"] == "V4_SYSTEM_ATMOS_EXCHANGE_CONTRACT"
    assert stages[1]["stage_id"] == "V4_SYSTEM_PHYSICS_GAP_SENSITIVITY_AUDIT"
    required = set(stages[0]["required_contract_fields"])
    assert {
        "timestamp_and_interval_semantics",
        "location_or_grid_identity",
        "air_hto_concentration",
        "deposition_flux_semantics",
        "units",
        "missing_data_policy",
        "model_and_dataset_provenance",
    }.issubset(required)


def test_system_audit_covers_complete_pathway() -> None:
    audit = _registry()["next_stages"][1]
    assert set(audit["required_pathways"]) == {
        "atmosphere",
        "soil",
        "leaf_exchange",
        "TFWT",
        "OBT",
        "root_uptake",
        "food_transfer",
        "intake",
        "dose",
    }
    assert "sensitivity_priority_matrix" in audit["output_requirements"]
    assert "explicit_hold_or_advance_decision_per_subsystem" in audit["output_requirements"]


def test_soil_status_is_one_layer_and_three_layer_is_only_candidate() -> None:
    soil = _registry()["soil_architecture"]
    current = soil["current_runtime"]
    assert current["representation"] == "ONE_LAYER_HTO_INVENTORY"
    assert current["transport_boundary"] == "SIGNED_FLUX_INPUT"
    assert current["full_hydrology"] is False
    future = soil["three_layer_target"]
    assert future["status"] == "CANDIDATE_NOT_IMPLEMENTED"
    assert future["implementation_authorized"] is False
    assert "layer_conservation" in future["minimum_preimplementation_contract"]
    assert "global_conservation" in future["minimum_preimplementation_contract"]
    assert soil["richards_darcy_hydrology"]["status"] == "NOT_AUTHORIZED"


def test_hard_invariants_prevent_physics_activation() -> None:
    inv = _registry()["hard_invariants"]
    assert inv["leaf_r5_authorized"] is False
    assert inv["three_layer_soil_implemented"] is False
    assert inv["full_soil_hydrology_authorized"] is False
    assert inv["solver_changes_authorized"] is False
    assert inv["numerical_coupling_changes_authorized"] is False
    assert inv["real_cteas_atmos_coupling_active"] is False
    assert inv["active_parameters"] == 0
    assert inv["calibration_started"] is False
    assert inv["v3_physics_ready"] is False
    assert inv["physical_validation_complete"] is False


def test_adr_states_project_north_star_and_non_authorization() -> None:
    text = ADR.read_text(encoding="utf-8")
    assert "CTEAS-Atmos forcing" in text
    assert "food transfer" in text
    assert "intake" in text
    assert "dose" in text
    assert "V4-2 R4 is retained as a design checkpoint only" in text
    assert "one-layer HTO inventory model" in text
    assert "Full Richards/Darcy hydrology is not authorized" in text
    assert "SOLVER_CHANGES_AUTHORIZED = FALSE" in text
