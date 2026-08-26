from __future__ import annotations

import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = "175c5d7ed7fbec916485aa44c0ae733d330b661f"
CONTENT_TIP = "a47ac41a48a691b6b24aea0b948abf4533a9ed60"
REGISTRY = ROOT / "docs/v4/contracts/v4_data_state_contract_registry.yaml"
COMMON = ROOT / "docs/v4/contracts/v4_common_data_contract.yaml"
LEAF = ROOT / "docs/v4/contracts/leaf_dynamic_stomatal_contract.yaml"
OBT = ROOT / "docs/v4/contracts/obt_formation_package_contract.yaml"
ROOT_CONTRACT = ROOT / "docs/v4/contracts/root_water_flux_contract.yaml"
SCHEMA = ROOT / "schemas/v4/v4_validation_case_envelope.schema.json"
ADR = ROOT / "docs/v4/adr/ADR-024-v4-data-state-contracts.md"
REPORT = ROOT / "docs/v4/reports/v4_1_data_state_contracts_review.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sample_empirical_case() -> dict:
    return {
        "schema_version": "v1",
        "case_id": "leaf-case-001",
        "case_type": "EMPIRICAL_VALIDATION",
        "candidate_item": "LEAF_DYNAMIC_STOMATAL_RESPONSE",
        "baseline_profile": "v3_frozen_baseline",
        "replicate_id": "bio-rep-01",
        "time_contract": {
            "timezone_or_offset": "+00:00",
            "interval_semantics": "instantaneous",
            "alignment_rule": "nearest observation within preregistered tolerance",
        },
        "variables": [
            {
                "name": "stomatal_conductance",
                "role": "OBSERVATION",
                "unit": "m s^-1",
                "provenance": {
                    "source_id": "dataset-a",
                    "source_locator": "table-2-column-gs",
                    "revision": "rev-1",
                    "variable_name": "stomatal_conductance",
                    "declared_unit": "m s^-1",
                    "timestamp_basis": "UTC",
                },
                "missing_data_policy": "CASE_INVALID",
            }
        ],
        "preregistered_metrics": [
            {
                "metric_id": "gs_rmse",
                "definition": "RMSE on stomatal conductance",
                "aggregation_rule": "per replicate then report distribution",
            }
        ],
    }


def test_registry_is_bound_to_p7_8c_control_plane_authorization() -> None:
    data = load_yaml(REGISTRY)
    assert data["stage"] == "V4-1"
    assert data["item_id"] == "V4_DATA_AND_STATE_CONTRACTS"
    assert data["source_authorization"]["p7_8c_main_sha"] == BASE_MAIN
    assert data["source_authorization"]["authorization_status"] == "AUTHORIZED_CONTROL_PLANE_ONLY"
    scope = data["scope"]
    assert scope["control_plane_only"] is True
    for key in (
        "production_runtime_changes",
        "solver_equation_implementation",
        "runtime_state_activation",
        "existing_state_serialization_changes",
        "numerical_coupling_changes",
        "p7_5_semantics_changes",
        "p7_5b_semantics_changes",
        "candidate_parameter_values_admitted",
        "calibration_started",
        "physical_validation_claimed",
    ):
        assert scope[key] is False
    hard = data["hard_invariants"]
    assert hard["active_parameters"] == 0
    assert hard["ufotri_active_database"] is False
    assert hard["v3_physics_ready"] is False
    assert hard["v4_selected_model_implementation_authorized"] is False
    assert hard["physical_validation_complete"] is False


def test_common_contract_freezes_units_ownership_restart_and_validation_boundaries() -> None:
    data = load_yaml(COMMON)
    assert data["unit_policy"]["explicit_unit_required_for_quantitative_variable"] is True
    assert data["unit_policy"]["implicit_unit_conversion"] == "FORBIDDEN"
    assert data["time_contract"]["implicit_local_time"] == "FORBIDDEN"
    assert data["missing_data_contract"]["silent_zero_fill"] == "FORBIDDEN"
    assert data["missing_data_contract"]["silent_forward_fill"] == "FORBIDDEN"
    assert data["state_ownership_contract"]["prognostic_state_single_owner"] is True
    assert data["state_ownership_contract"]["external_forcing_is_prognostic_state"] is False
    assert data["state_ownership_contract"]["transfer_flux_may_be_applied_by_multiple_owners"] is False
    assert data["restart_contract"]["automatic_mapping_from_v3_scalar_to_v4_multistate"] == "FORBIDDEN"
    assert data["restart_contract"]["missing_required_future_restart_field"] == "FAIL_CLOSED"
    assert data["validation_contract"]["software_synthetic_case_is_empirical_validation"] is False
    assert data["validation_contract"]["production_arithmetic_is_expected_data"] is False
    assert data["parameter_contract"]["numerical_candidate_values_allowed_in_v4_1"] is False
    assert data["parameter_contract"]["unreviewed_ufotri_value_import"] == "FORBIDDEN"


def test_leaf_contract_is_dimensionally_typed_and_has_no_new_restart_state() -> None:
    data = load_yaml(LEAF)
    q = data["quantity_contracts"]
    assert q["g_s"]["canonical_unit"] == "m s^-1"
    assert q["g_s_max"]["canonical_unit"] == "m s^-1"
    assert q["r_c"]["canonical_unit"] == "s m^-1"
    assert q["r_a"]["canonical_unit"] == "s m^-1"
    assert q["r_b"]["canonical_unit"] == "s m^-1"
    assert q["r_tot"]["canonical_unit"] == "s m^-1"
    assert q["g_ex"]["canonical_unit"] == "m s^-1"
    response = data["response_function_contract"]
    assert response["output_unit"] == "1"
    assert response["declared_domain_required"] is True
    assert response["declared_bounds_required"] is True
    assert response["extrapolation_outside_declared_domain"] == "FAIL_CLOSED"
    assert response["numerical_shape_or_coefficients_allowed_in_v4_1"] is False
    ownership = data["state_ownership"]
    assert ownership["prognostic_candidate_states"] == []
    assert set(ownership["derived_diagnostics"]) == {"g_s", "r_c", "r_tot", "g_ex"}
    restart = data["restart_contract"]
    assert restart["new_persistent_candidate_state_required"] is False
    assert restart["missing_required_forcing_on_restart"] == "FAIL_CLOSED"
    assert data["implementation_authorized"] is False


def test_obt_contract_has_explicit_internal_transfer_conservation_without_new_rate() -> None:
    data = load_yaml(OBT)
    q = data["quantity_contracts"]
    for state in ("P", "B_x", "B_n", "B_total"):
        assert q[state]["canonical_unit"] == "Bq m^-2"
    assert q["u_P"]["canonical_unit"] == "Bq m^-2 s^-1"
    assert q["u_P"]["functional_form_selected_in_v4_1"] is False
    assert q["rate_parameters"]["canonical_unit"] == "s^-1"
    assert set(q["rate_parameters"]["names"]) == {"k_f0", "k_P", "k_PB", "k_xn", "k_x", "k_n"}
    assert "k_P_other" not in q["rate_parameters"]["names"]
    assert q["rate_parameters"]["numerical_values_allowed_in_v4_1"] is False
    descriptors = q["response_function_descriptors"]
    assert descriptors["product_or_other_composition_selected_in_v4_1"] is False
    conservation = data["conservation_contract"]
    assert conservation["internal_transfers"] == ["J_P_to_Bx", "J_Bx_to_Bn"]
    assert set(conservation["external_losses"]) == {"J_P_other", "J_Bx_other", "J_Bn_other"}
    assert conservation["aggregate_B_is_additional_storage"] is False
    relation = conservation["p7_8b2_rate_relation"]
    assert relation["symbolic_relation"] == "J_P_other = (k_P - k_PB) * P"
    assert relation["constraint"] == "0 <= k_PB <= k_P"
    assert relation["additional_precursor_loss_parameter_introduced"] is False
    assert relation["numerical_values_allowed_in_v4_1"] is False
    forcing = data["forcing_contract"]["precursor_source_functional_composition"]
    assert forcing["status"] == "UNRESOLVED_REQUIRES_ITEM_SPECIFIC_REVIEW"
    assert forcing["multiplicative_response_product_assumed"] is False
    assert forcing["additive_or_other_composition_assumed"] is False

    # Pure software algebra check with arbitrary values. These values are not
    # physical parameters or calibration values; they only test cancellation.
    P, bx, bn = 4.0, 3.0, 2.0
    u_p = 7.0
    k_p, k_pb, k_xn, k_x, k_n = 0.3, 0.2, 0.3, 0.05, 0.04
    assert 0.0 <= k_pb <= k_p
    j_p_bx = k_pb * P
    j_p_other = (k_p - k_pb) * P
    j_bx_bn = k_xn * bx
    j_bx_other = k_x * bx
    j_bn_other = k_n * bn
    d_p = u_p - k_p * P
    d_bx = j_p_bx - j_bx_bn - j_bx_other
    d_bn = j_bx_bn - j_bn_other
    composite = d_p + d_bx + d_bn
    external = u_p - j_p_other - j_bx_other - j_bn_other
    assert composite == pytest.approx(external)
    assert data["restart_contract"]["baseline_B_to_component_partition_without_evidence"] == "FORBIDDEN"
    assert data["validation_case_contract"]["aggregate_only_data_sufficient_for_component_validation"] is False
    assert data["implementation_authorized"] is False


def test_root_contract_preserves_water_flux_dimensions_and_ownership() -> None:
    data = load_yaml(ROOT_CONTRACT)
    q = data["quantity_contracts"]
    assert q["M_s_i"]["canonical_unit"] == "Bq m^-2"
    assert q["theta_i"]["equivalent_dimension"] == "1"
    assert q["Delta_z_i"]["canonical_unit"] == "m"
    assert q["C_w_i"]["canonical_unit"] == "Bq m^-3 water"
    assert q["q_w_i"]["canonical_unit"] == "m s^-1"
    assert q["J_root_i"]["canonical_unit"] == "Bq m^-2 s^-1"
    water = data["water_basis_contract"]
    assert water["inferred_effective_storage_length"] == "FORBIDDEN"
    assert water["root_rate_s_inverse_to_velocity_m_per_s_conversion"] == "FORBIDDEN"
    ownership = data["state_ownership"]
    assert ownership["q_w_owner_must_be_external_or_separately_reviewed_water_model"] is True
    assert ownership["v4_root_boundary_may_generate_q_w"] is False
    assert ownership["v4_root_boundary_may_modify_soil_water_content"] is False
    assert ownership["extraction_and_plant_input_are_same_transfer_identity"] is True
    assert data["p7_5_p7_5b_re_review_required_before_implementation"] is True
    assert data["coupling_review_contract"]["required_before_implementation"] is True
    assert data["failure_policy"]["guessed_q_w"] == "FORBIDDEN"
    assert data["failure_policy"]["inferred_hydrology"] == "FORBIDDEN"
    assert data["implementation_authorized"] is False


def test_validation_schema_accepts_complete_empirical_case() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(sample_empirical_case())


@pytest.mark.parametrize("mutation", ["missing_unit", "missing_provenance", "blank_replicate"])
def test_validation_schema_fails_closed_on_required_metadata(mutation: str) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    case = sample_empirical_case()
    if mutation == "missing_unit":
        del case["variables"][0]["unit"]
    elif mutation == "missing_provenance":
        del case["variables"][0]["provenance"]
    else:
        case["replicate_id"] = "   "
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(case)


def test_empirical_case_cannot_use_software_expectation_as_observation() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    case = sample_empirical_case()
    case["variables"][0]["role"] = "SOFTWARE_EXPECTATION"
    with pytest.raises(Exception):
        Draft202012Validator(schema).validate(case)


def test_synthetic_software_case_may_use_software_expectation_but_is_not_empirical() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    case = sample_empirical_case()
    case["case_type"] = "SYNTHETIC_SOFTWARE_VERIFICATION"
    case["variables"][0]["role"] = "SOFTWARE_EXPECTATION"
    Draft202012Validator(schema).validate(case)
    common = load_yaml(COMMON)
    assert common["validation_contract"]["software_synthetic_case_is_empirical_validation"] is False


def test_provenance_declared_unit_matches_envelope_unit_in_reference_case() -> None:
    case = sample_empirical_case()
    for variable in case["variables"]:
        assert variable["unit"] == variable["provenance"]["declared_unit"]


def test_v4_1_content_tip_is_control_plane_only() -> None:
    changed = {
        line
        for line in git("diff", "--name-only", BASE_MAIN, CONTENT_TIP).splitlines()
        if line
    }
    assert changed == {
        ".github/workflows/v3-integration-gate.yml",
        "docs/v4/adr/ADR-024-v4-data-state-contracts.md",
        "docs/v4/contracts/leaf_dynamic_stomatal_contract.yaml",
        "docs/v4/contracts/obt_formation_package_contract.yaml",
        "docs/v4/contracts/root_water_flux_contract.yaml",
        "docs/v4/contracts/v4_common_data_contract.yaml",
        "docs/v4/contracts/v4_data_state_contract_registry.yaml",
        "docs/v4/reports/v4_1_data_state_contracts_review.md",
        "schemas/v4/v4_validation_case_envelope.schema.json",
        "tests/v4/test_v4_1_data_state_contracts.py",
    }
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("configs/") for path in changed)
    assert not any(path.startswith("parameters/") for path in changed)


def test_contract_registry_matches_candidate_contract_files() -> None:
    registry = load_yaml(REGISTRY)
    candidates = {item["item_id"]: item for item in registry["candidate_contracts"]}
    assert set(candidates) == {
        "LEAF_DYNAMIC_STOMATAL_RESPONSE",
        "OBT_FORMATION_PACKAGE",
        "ROOT_UPTAKE_WATER_FLUX_BOUNDARY",
    }
    assert candidates["LEAF_DYNAMIC_STOMATAL_RESPONSE"]["implementation_authorized"] is False
    assert candidates["OBT_FORMATION_PACKAGE"]["implementation_authorized"] is False
    assert candidates["ROOT_UPTAKE_WATER_FLUX_BOUNDARY"]["implementation_authorized"] is False
    assert candidates["ROOT_UPTAKE_WATER_FLUX_BOUNDARY"][
        "p7_5_p7_5b_re_review_required_before_implementation"
    ] is True


def test_review_documents_do_not_claim_v4_physics_readiness() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for text in (adr, report):
        assert "ACTIVE_PARAMETERS = 0" in text
        assert "V3_PHYSICS_READY = FALSE" in text
    assert "SOLVER_IMPLEMENTATION_AUTHORIZED = FALSE" in adr
    assert "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE" in report
    assert "OBT_IMPLEMENTATION_AUTHORIZED = FALSE" in report
    assert "ROOT_IMPLEMENTATION_AUTHORIZED = FALSE" in report


def test_content_tip_is_ancestor_of_current_head() -> None:
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", CONTENT_TIP, "HEAD"],
        cwd=ROOT,
        check=True,
    )
