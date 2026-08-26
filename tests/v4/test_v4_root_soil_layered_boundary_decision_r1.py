from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / "docs/v4/governance/v4_root_soil_layered_boundary_decision_r1.yaml"


def _decision() -> dict:
    return yaml.safe_load(DECISION.read_text(encoding="utf-8"))


def test_three_layer_target_and_geometry() -> None:
    data = _decision()
    assert data["stage"] == "V4_ROOT_SOIL_LAYERED_BOUNDARY_DECISION_R1"
    assert data["status"] == "PASS_THREE_LAYER_UFOTRI_TARGET_SELECTED"
    target = data["selected_v4_target"]
    assert target["implementation_authorized"] is True
    assert target["opt_in_only"] is True
    assert target["v3_one_layer_baseline_preserved"] is True
    assert target["layers"] == [
        {"layer_id": "L1", "depth_top_m": 0.0, "depth_bottom_m": 0.05},
        {"layer_id": "L2", "depth_top_m": 0.05, "depth_bottom_m": 0.15},
        {"layer_id": "L3", "depth_top_m": 0.15, "depth_bottom_m": 0.30},
    ]


def test_hydrology_boundary_is_not_full_richards() -> None:
    data = _decision()
    background = data["manual_findings"]["hydrology_background"]
    assert background["darcy_law_applied"] is True
    assert background["nonlinear_unsaturated_flow_equation"] == "EQ37"
    assert background["modern_classification"] == "RICHARDS_TYPE_DARCY_CONTINUITY_BACKGROUND"
    assert background["full_model_selected_by_ufotri"] is False
    hydrology = data["hydrology_decision"]
    assert hydrology["full_richards_darcy_solver"]["authorized"] is False
    assert hydrology["selected_v4_hydrology_class"] == "UFOTRI_STYLE_THREE_LAYER_COMPARTMENT_TRANSPORT"
    assert hydrology["interlayer_flux_semantics"]["signed"] is True
    assert hydrology["interlayer_flux_semantics"]["upward_capillary_flux_allowed"] is True


def test_short_term_and_ingestion_evidence_are_not_conflated() -> None:
    data = _decision()["manual_findings"]
    assert data["long_term_ingestion_soil_compartments"]["explicit_three_layer_structure"] is True
    short = data["short_term_secondary_soil_model"]
    assert short["explicit_three_layer_runtime_proven"] is False
    assert short["top_layer_depth_m"] == 0.05
    assert short["agricultural_root_depth_m"] == 0.30
    assert short["root_water_fraction_top_5_cm"] == 0.20
    assert short["root_water_fraction_deeper_layers"] == 0.80


def test_next_stage_is_three_layer_core_only() -> None:
    data = _decision()
    auth = data["next_stage_authorization"]
    assert auth["stage"] == "V4_THREE_LAYER_SOIL_CORE_IMPLEMENTATION_R1"
    assert auth["authorized"] is True
    forbidden = set(auth["forbidden_changes"])
    assert "modify_v3_soil_solver_equations" in forbidden
    assert "activate_three_layer_path_as_default" in forbidden
    assert "full_richards_solver" in forbidden
    assert "calibrate_transport_rates" in forbidden
    assert data["hard_invariants"]["three_layer_soil_implemented"] is False
    assert data["hard_invariants"]["active_parameters"] == 0
