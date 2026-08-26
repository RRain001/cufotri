from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_three_layer_root_coupling_rereview_r1.yaml"
ROOT_CONTRACT = ROOT / "docs/v4/contracts/root_water_flux_contract.yaml"
REPORT = ROOT / "docs/v4/reports/v4_three_layer_root_coupling_rereview_r1.md"


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_rereview_selects_layer_water_flux_physics_without_pipeline_integration() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "V4_THREE_LAYER_ROOT_COUPLING_REREVIEW_R1"
    assert data["status"] == "PASS_CONTROL_PLANE"
    contract = data["selected_root_flux_contract"]
    assert contract["authoritative_soil_state"] == "interval_start_three_layer_state_S_n"
    assert contract["per_layer_equation"] == "J_root_i = q_w_i * C_w_i(S_n)"
    assert contract["q_w_generation_inside_root_solver"] is False
    assert contract["implicit_rate_to_velocity_conversion"] == "forbidden"
    assert data["p7_5_p7_5b_review"]["v3_default_changed"] is False
    assert data["p7_5_p7_5b_review"]["v4_pipeline_integration_authorized"] is False
    assert data["exit_state"]["root_flux_core_implementation_authorized"] is True
    assert data["exit_state"]["pipeline_operator_split_selected"] is False


def test_ufotri_short_and_long_term_root_semantics_are_kept_separate() -> None:
    data = load_yaml(GOVERNANCE)
    evidence = data["ufotri_evidence"]
    long_term = evidence["long_term_ingestion_reference"]
    short_term = evidence["short_term_secondary_reference"]
    assert long_term["layer_water_uptake_fraction"] == pytest.approx([0.20, 0.40, 0.40])
    assert sum(long_term["layer_water_uptake_fraction"]) == pytest.approx(1.0)
    assert long_term["transfer_rate_d_minus_1_reference"] == pytest.approx([0.026, 0.026, 0.017])
    assert long_term["status"] == "REFERENCE_EVIDENCE_NOT_ACTIVE_PARAMETERIZATION"
    assert short_term["root_uptake_control"] == "plant_transpiration"
    assert short_term["transpiration_to_root_uptake_delay_h"] == pytest.approx(3.0)
    assert short_term["status"] == "REFERENCE_EVIDENCE_NOT_RUNTIME_ACTIVATION"
    assert "must not be silently collapsed" in evidence["semantic_boundary"]


def test_single_application_ownership_is_explicit() -> None:
    data = load_yaml(GOVERNANCE)
    ownership = data["ownership"]
    assert ownership["root_v4_core"]["mutates_soil"] is False
    assert ownership["root_v4_core"]["mutates_tfwt"] is False
    assert ownership["soil_v4"]["owns_application_of_root_water_sink"] is True
    assert ownership["soil_v4"]["owns_application_of_root_hto_sink"] is True
    assert ownership["soil_v4"]["apply_each_root_sink_exactly_once"] is True
    assert ownership["tfwt_boundary"]["future_gain_must_equal_soil_hto_root_loss"] is True
    assert ownership["tfwt_boundary"]["apply_transfer_exactly_once"] is True
    assert ownership["double_application"] == "forbidden"


def test_future_operator_split_requires_comparison_not_guessing() -> None:
    data = load_yaml(GOVERNANCE)
    review = data["p7_5_p7_5b_review"]
    ids = [entry["id"] for entry in review["future_v4_integration_candidates"]]
    assert ids == ["PRESERVE_V3_POST_OBT_ROOT_GAIN", "ROOT_GAIN_BEFORE_OBT"]
    assert review["selection_status"] == "COMPARISON_REQUIRED_NOT_SELECTED"
    required = set(review["required_before_pipeline_selection"])
    assert {
        "single_application_proof",
        "soil_tfwt_transfer_conservation",
        "timestep_refinement",
        "restart_equivalence",
        "deterministic_repeat",
        "multi_step_root_to_obt_lag_comparison",
        "explicit_profile_time_basis",
    } <= required


def test_existing_v4_root_contract_required_this_rereview() -> None:
    contract = load_yaml(ROOT_CONTRACT)
    coupling = contract["coupling_constraints"]
    assert coupling["p7_5_p7_5b_re_review_required_before_implementation"] is True
    assert coupling["soil_to_root_flux_conservation_required"] is True
    assert coupling["root_to_plant_transfer_conservation_required"] is True
    text = REPORT.read_text(encoding="utf-8")
    assert "20%, 40% and 40%" in text
    assert "0.026, 0.026 and 0.017" in text
    assert "approximately 3 h delay" in text


def test_hard_invariants_keep_physics_activation_closed() -> None:
    data = load_yaml(GOVERNANCE)
    invariants = data["hard_invariants"]
    assert invariants["active_parameters"] == 0
    assert invariants["calibration_started"] is False
    assert invariants["leaf_r5_authorized"] is False
    assert invariants["real_cteas_atmos_coupling_active"] is False
    assert invariants["v3_default_profile_changed"] is False
    assert invariants["v4_pipeline_integration_authorized"] is False
    assert invariants["full_richards_darcy_authorized"] is False
    assert invariants["physical_validation_complete"] is False
