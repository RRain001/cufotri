from __future__ import annotations

import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE_MAIN = "61dfee175d5b16fe358417e0beba75a776d6f394"
CONTENT_TIP = "d7e2915bddfbeeb11d1c14d352024e8f0bf132b8"
READINESS = ROOT / "docs/v4/leaf/v4_2_leaf_dynamic_stomatal_readiness.yaml"
ONTOLOGY = ROOT / "docs/v4/leaf/v4_2_growth_stage_ontology_contract.yaml"
DOMAIN = ROOT / "docs/v4/leaf/v4_2_response_domain_admission.yaml"
PROTOCOL = ROOT / "docs/v4/leaf/v4_2_validation_protocol.yaml"
EVIDENCE = ROOT / "docs/v4/leaf/v4_2_evidence_acquisition_requirements.yaml"
SCHEMA = ROOT / "schemas/v4/v4_leaf_empirical_evidence_packet.schema.json"
ADR = ROOT / "docs/v4/adr/ADR-025-v4-2-leaf-dynamic-stomatal-readiness.md"
REPORT = ROOT / "docs/v4/reports/v4_2_leaf_dynamic_stomatal_readiness_review.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def provenance(name: str, unit: str) -> dict:
    return {
        "source_id": "leaf-dataset-a",
        "source_locator": f"table-1/{name}",
        "revision": "rev-1",
        "variable_name": name,
        "declared_unit": unit,
        "timestamp_basis": "UTC",
    }


def variable(name: str, role: str, unit: str) -> dict:
    return {
        "name": name,
        "role": role,
        "unit": unit,
        "measurement_basis": "dataset-declared measurement basis",
        "provenance": provenance(name, unit),
        "independent_group_field": "replicate_id",
        "missing_data_policy": "CASE_INVALID",
    }


def numeric_domain(name: str, unit: str, low: float, high: float) -> dict:
    return {
        "domain_type": "NUMERIC",
        "variable_name": name,
        "source_id": "leaf-dataset-a",
        "source_locator": f"analysis/{name}-support",
        "revision": "rev-1",
        "declared_unit": unit,
        "lower_support_boundary": low,
        "upper_support_boundary": high,
        "boundary_derivation_rule": "preregistered support estimator placeholder",
        "included_groups": ["rep-1"],
        "timestamp_window": "declared observation window",
    }


def sample_packet() -> dict:
    return {
        "schema_version": "v1",
        "packet_id": "leaf-packet-001",
        "candidate_item": "LEAF_DYNAMIC_STOMATAL_RESPONSE",
        "case_type": "EMPIRICAL_VALIDATION",
        "dataset": {
            "dataset_id": "leaf-dataset-a",
            "dataset_revision": "rev-1",
            "source_locator": "doi-or-archive-record",
            "license_or_access_basis": "documented research access",
        },
        "crop_identity": {
            "crop_id": "crop-a",
            "source_taxonomy": "dataset-native taxonomy",
            "source_locator": "methods/crop",
        },
        "stage_ontology": {
            "ontology_id": "dataset-a-stage-v1",
            "ontology_revision": "1",
            "source_stage_field": "growth_stage",
            "stage_records": [
                {
                    "source_stage_value": "S1",
                    "admitted_stage_id": "stage-s1",
                    "semantic_label": "dataset-native stage S1",
                    "provenance_locator": "methods/stage-table",
                },
                {
                    "source_stage_value": "S2",
                    "admitted_stage_id": "stage-s2",
                    "semantic_label": "dataset-native stage S2",
                    "provenance_locator": "methods/stage-table",
                },
            ],
        },
        "time_contract": {
            "timezone_or_offset": "+00:00",
            "interval_semantics": "instantaneous",
            "alignment_rule": "exact timestamp or preregistered tolerance",
        },
        "independent_groups": ["rep-1", "rep-2"],
        "variables": [
            variable("stomatal_conductance", "OBSERVATION", "m s^-1"),
            variable("PAR", "FORCING", "umol m^-2 s^-1"),
            variable("VPD", "FORCING", "Pa"),
            variable("leaf_temperature", "FORCING", "K"),
            variable("growth_stage", "CONTEXT", "1"),
        ],
        "response_domain_records": [
            numeric_domain("light_or_PAR", "umol m^-2 s^-1", 10.0, 1200.0),
            numeric_domain("VPD", "Pa", 100.0, 2000.0),
            numeric_domain("T_leaf", "K", 285.0, 310.0),
            {
                "domain_type": "CATEGORICAL",
                "variable_name": "stage",
                "ontology_id": "dataset-a-stage-v1",
                "ontology_revision": "1",
                "admitted_stage_ids": ["stage-s1", "stage-s2"],
                "source_id": "leaf-dataset-a",
                "source_locator": "analysis/stage-support",
                "included_groups": ["rep-1"],
            },
        ],
        "validation_split": {
            "grouping_unit": "biological_replicate",
            "calibration_groups": ["rep-1"],
            "final_validation_groups": ["rep-2"],
            "split_rule": "group-disjoint split fixed before candidate fit",
            "final_holdout_used_for_domain_estimation": False,
        },
        "preregistered_metrics": [
            {
                "metric_id": "conductance_or_resistance_trajectory_error",
                "definition": "prediction error on the declared target basis",
                "aggregation_rule": "per independent group then summarize",
                "acceptance_rule_status": "PENDING_DATASET_SPECIFIC_PREREGISTRATION",
            },
            {
                "metric_id": "reciprocal_identity_residual",
                "definition": "residual of declared g_s/r_c reciprocal identity",
                "aggregation_rule": "maximum absolute residual",
                "acceptance_rule_status": "PENDING_DATASET_SPECIFIC_PREREGISTRATION",
            },
            {
                "metric_id": "domain_and_bound_violation_count",
                "definition": "count of forcing/domain violations",
                "aggregation_rule": "count by independent group",
                "acceptance_rule_status": "PREREGISTERED",
            },
            {
                "metric_id": "cross_condition_generalization_error",
                "definition": "error across preregistered condition groups",
                "aggregation_rule": "per condition group then summarize",
                "acceptance_rule_status": "PENDING_DATASET_SPECIFIC_PREREGISTRATION",
            },
        ],
    }


def schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def assert_cross_field_packet_invariants(packet: dict) -> None:
    groups = set(packet["independent_groups"])
    split = packet["validation_split"]
    calibration = set(split["calibration_groups"])
    final = set(split["final_validation_groups"])
    assert calibration.isdisjoint(final)
    assert calibration <= groups
    assert final <= groups
    assert split["final_holdout_used_for_domain_estimation"] is False

    for item in packet["variables"]:
        assert item["unit"] == item["provenance"]["declared_unit"]

    ontology = packet["stage_ontology"]
    source_values = [item["source_stage_value"] for item in ontology["stage_records"]]
    admitted_values = [item["admitted_stage_id"] for item in ontology["stage_records"]]
    assert len(source_values) == len(set(source_values))
    assert len(admitted_values) == len(set(admitted_values))

    stage_domain = next(item for item in packet["response_domain_records"] if item["variable_name"] == "stage")
    assert stage_domain["ontology_id"] == ontology["ontology_id"]
    assert stage_domain["ontology_revision"] == ontology["ontology_revision"]
    assert set(stage_domain["admitted_stage_ids"]) <= set(admitted_values)

    for item in packet["response_domain_records"]:
        included = set(item["included_groups"])
        assert included <= groups
        assert included.isdisjoint(final)
        if item["domain_type"] == "NUMERIC":
            assert item["lower_support_boundary"] <= item["upper_support_boundary"]


def test_readiness_matrix_closes_control_plane_but_holds_implementation() -> None:
    data = load_yaml(READINESS)
    assert data["status"] == "HOLD_EMPIRICAL_EVIDENCE_REQUIRED"
    gates = data["readiness_gates"]
    assert gates["growth_stage_ontology_contract"]["status"] == "PASS_DATASET_BOUND_RULE_DEFINED"
    assert gates["dataset_specific_growth_stage_ontology"]["status"] == "HOLD_NOT_AVAILABLE"
    assert gates["response_domain_admission_rule"]["status"] == "PASS_RULE_DEFINED"
    assert gates["empirical_response_domains"]["status"] == "HOLD_NOT_AVAILABLE"
    assert gates["evidence_packet_contract"]["status"] == "PASS_SCHEMA_AND_REQUIREMENTS_DEFINED"
    assert gates["matched_validation_dataset"]["status"] == "HOLD_NOT_AVAILABLE_IN_REPOSITORY"
    assert gates["preregistered_validation_protocol"]["status"] == "PASS_PROTOCOL_DEFINED_NOT_EXECUTED"
    assert gates["independent_item_review"]["status"] == "HOLD_NOT_STARTED"
    hard = data["hard_invariants"]
    assert hard["leaf_implementation_authorized"] is False
    assert hard["production_solver_changed"] is False
    assert hard["candidate_parameter_values_admitted"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["physical_validation_complete"] is False
    assert data["exit_policy"]["may_start_leaf_solver_implementation"] is False


def test_stage_ontology_is_dataset_bound_and_cross_mapping_fails_closed() -> None:
    data = load_yaml(ONTOLOGY)
    assert data["ontology_identity_contract"]["dataset_bound"] is True
    assert data["ontology_identity_contract"]["universal_cross_crop_ontology_selected"] is False
    assert data["stage_record_contract"]["stage_ordering"]["default"] == "UNORDERED_CATEGORICAL"
    assert data["stage_record_contract"]["stage_ordering"]["inferred_numeric_spacing_between_stages"] == "FORBIDDEN"
    mapping = data["cross_dataset_mapping_policy"]
    assert mapping["automatic_mapping"] == "FORBIDDEN"
    assert mapping["label_string_equality_implies_semantic_equivalence"] is False
    assert mapping["numeric_code_equality_implies_semantic_equivalence"] is False
    assert mapping["missing_mapping"] == "FAIL_CLOSED"
    assert data["forcing_contract"]["unknown_stage_value"] == "FAIL_CLOSED"


def test_response_domain_and_validation_rules_are_fail_closed() -> None:
    domain = load_yaml(DOMAIN)
    admission = domain["admission_policy"]
    assert admission["empirical_observations_required"] is True
    assert admission["synthetic_values_may_define_empirical_domain"] is False
    assert admission["production_solver_outputs_may_define_empirical_domain"] is False
    assert admission["convenient_default_bounds"] == "FORBIDDEN"
    assert admission["domain_boundary_estimator_selected_here"] is False
    assert domain["multivariate_support_policy"]["independent_univariate_bounds_imply_joint_support"] is False
    failure = domain["runtime_failure_policy_for_future_implementation"]
    assert failure["forcing_outside_admitted_domain"] == "FAIL_CLOSED"
    assert failure["silent_clipping"] == "FORBIDDEN"
    assert failure["silent_extrapolation"] == "FORBIDDEN"

    protocol = load_yaml(PROTOCOL)
    leakage = protocol["split_and_leakage_policy"]
    assert leakage["random_row_split_across_same_independent_group"] == "FORBIDDEN_FOR_FINAL_VALIDATION"
    assert leakage["calibration_group_and_final_validation_group_overlap"] == "FORBIDDEN"
    assert leakage["response_domain_estimation_from_final_holdout"] == "FORBIDDEN"
    assert leakage["metric_or_model_selection_from_final_holdout"] == "FORBIDDEN"
    assert leakage["preprocessing_leakage_from_final_holdout"] == "FORBIDDEN"
    assert protocol["calibration_boundary"]["calibration_started"] is False
    assert protocol["review_boundary"]["independent_item_review_required"] is True


def test_evidence_requirements_define_cross_field_validation_without_claiming_data() -> None:
    data = load_yaml(EVIDENCE)
    availability = data["current_repository_availability"]
    assert availability["complete_packet_found"] is False
    assert availability["checked_in_matched_dynamic_stomatal_dataset_found"] is False
    assert availability["dataset_specific_stage_ontology_found"] is False
    assert availability["empirical_response_domains_found"] is False
    assert availability["physical_validation_executed"] is False
    assert data["required_target"]["measurement_basis_must_be_explicit"] is True
    assert data["measurement_and_provenance_policy"]["software_expectation_as_empirical_observation"] == "FORBIDDEN"
    cross = data["cross_field_validation_contract"]
    assert cross["application_level_validation_required_in_addition_to_json_schema"] is True
    assert cross["calibration_groups_must_be_disjoint_from_final_validation_groups"] is True
    assert cross["response_domain_included_groups_must_exclude_final_validation_groups"] is True
    assert cross["stage_domain_ontology_id_and_revision_must_match_packet_ontology"] is True
    assert cross["numeric_lower_support_boundary_must_not_exceed_upper_boundary"] is True
    assert data["admission_rule"]["implementation_authorization_requires_independent_item_review"] is True


def test_leaf_empirical_packet_schema_accepts_complete_reference_packet() -> None:
    packet = sample_packet()
    schema_validator().validate(packet)
    assert_cross_field_packet_invariants(packet)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_target",
        "missing_target_measurement_basis",
        "wrong_target_unit",
        "missing_light",
        "wrong_vpd_unit",
        "missing_leaf_temperature",
        "wrong_leaf_temperature_unit",
        "missing_growth_stage",
        "wrong_growth_stage_unit",
        "missing_vpd_basis",
        "wrong_vpd_domain_unit",
        "wrong_tleaf_domain_unit",
        "missing_stage_domain",
        "missing_final_validation_group",
        "blank_dataset_id",
    ],
)
def test_leaf_empirical_packet_schema_fails_closed_on_missing_or_incompatible_evidence(mutation: str) -> None:
    packet = sample_packet()
    if mutation == "missing_target":
        packet["variables"] = [item for item in packet["variables"] if item["name"] != "stomatal_conductance"]
    elif mutation == "missing_target_measurement_basis":
        del packet["variables"][0]["measurement_basis"]
    elif mutation == "wrong_target_unit":
        packet["variables"][0]["unit"] = "mm s^-1"
        packet["variables"][0]["provenance"]["declared_unit"] = "mm s^-1"
    elif mutation == "missing_light":
        packet["variables"] = [item for item in packet["variables"] if item["name"] != "PAR"]
    elif mutation == "wrong_vpd_unit":
        item = next(item for item in packet["variables"] if item["name"] == "VPD")
        item["unit"] = "kPa"
        item["provenance"]["declared_unit"] = "kPa"
    elif mutation == "missing_leaf_temperature":
        packet["variables"] = [item for item in packet["variables"] if item["name"] != "leaf_temperature"]
    elif mutation == "wrong_leaf_temperature_unit":
        item = next(item for item in packet["variables"] if item["name"] == "leaf_temperature")
        item["unit"] = "degC"
        item["provenance"]["declared_unit"] = "degC"
    elif mutation == "missing_growth_stage":
        packet["variables"] = [item for item in packet["variables"] if item["name"] != "growth_stage"]
    elif mutation == "wrong_growth_stage_unit":
        item = next(item for item in packet["variables"] if item["name"] == "growth_stage")
        item["unit"] = "stage-code"
        item["provenance"]["declared_unit"] = "stage-code"
    elif mutation == "missing_vpd_basis":
        packet["variables"] = [item for item in packet["variables"] if item["name"] != "VPD"]
        packet["variables"].append(variable("relative_humidity", "FORCING", "%"))
    elif mutation == "wrong_vpd_domain_unit":
        next(item for item in packet["response_domain_records"] if item["variable_name"] == "VPD")["declared_unit"] = "kPa"
    elif mutation == "wrong_tleaf_domain_unit":
        next(item for item in packet["response_domain_records"] if item["variable_name"] == "T_leaf")["declared_unit"] = "degC"
    elif mutation == "missing_stage_domain":
        packet["response_domain_records"] = [item for item in packet["response_domain_records"] if item["variable_name"] != "stage"]
    elif mutation == "missing_final_validation_group":
        packet["validation_split"]["final_validation_groups"] = []
    else:
        packet["dataset"]["dataset_id"] = "   "
    with pytest.raises(Exception):
        schema_validator().validate(packet)


def test_humidity_alternative_requires_explicit_vpd_derivation_contract() -> None:
    packet = sample_packet()
    packet["variables"] = [item for item in packet["variables"] if item["name"] != "VPD"]
    packet["variables"].append(variable("relative_humidity", "FORCING", "%"))
    packet["vpd_basis"] = {
        "source_variable": "relative_humidity",
        "conversion_rule": "dataset-specific declared conversion",
        "saturation_vapor_pressure_rule": "declared saturation vapor pressure relation",
        "temperature_variable": "leaf_temperature",
    }
    schema_validator().validate(packet)


def test_cross_field_guard_rejects_group_leakage() -> None:
    packet = sample_packet()
    packet["validation_split"]["final_validation_groups"] = ["rep-1"]
    schema_validator().validate(packet)
    with pytest.raises(AssertionError):
        assert_cross_field_packet_invariants(packet)


def test_cross_field_guard_rejects_domain_support_using_final_holdout() -> None:
    packet = sample_packet()
    packet["response_domain_records"][0]["included_groups"] = ["rep-2"]
    schema_validator().validate(packet)
    with pytest.raises(AssertionError):
        assert_cross_field_packet_invariants(packet)


def test_cross_field_guard_rejects_stage_ontology_mismatch_or_duplicate_mapping() -> None:
    packet = sample_packet()
    stage_domain = next(item for item in packet["response_domain_records"] if item["variable_name"] == "stage")
    stage_domain["ontology_revision"] = "other-revision"
    schema_validator().validate(packet)
    with pytest.raises(AssertionError):
        assert_cross_field_packet_invariants(packet)

    packet = sample_packet()
    packet["stage_ontology"]["stage_records"][1]["admitted_stage_id"] = "stage-s1"
    schema_validator().validate(packet)
    with pytest.raises(AssertionError):
        assert_cross_field_packet_invariants(packet)


def test_cross_field_guard_rejects_inverted_numeric_support_boundaries() -> None:
    packet = sample_packet()
    numeric = next(item for item in packet["response_domain_records"] if item["variable_name"] == "VPD")
    numeric["lower_support_boundary"] = 2500.0
    numeric["upper_support_boundary"] = 100.0
    schema_validator().validate(packet)
    with pytest.raises(AssertionError):
        assert_cross_field_packet_invariants(packet)


def test_v4_2_content_tip_is_readiness_only_and_does_not_touch_runtime() -> None:
    changed = {line for line in git("diff", "--name-only", BASE_MAIN, CONTENT_TIP).splitlines() if line}
    assert changed == {
        ".github/workflows/v3-integration-gate.yml",
        "docs/v4/adr/ADR-025-v4-2-leaf-dynamic-stomatal-readiness.md",
        "docs/v4/leaf/v4_2_evidence_acquisition_requirements.yaml",
        "docs/v4/leaf/v4_2_growth_stage_ontology_contract.yaml",
        "docs/v4/leaf/v4_2_leaf_dynamic_stomatal_readiness.yaml",
        "docs/v4/leaf/v4_2_response_domain_admission.yaml",
        "docs/v4/leaf/v4_2_validation_protocol.yaml",
        "docs/v4/reports/v4_2_leaf_dynamic_stomatal_readiness_review.md",
        "schemas/v4/v4_leaf_empirical_evidence_packet.schema.json",
        "tests/v4/test_v4_2_leaf_readiness.py",
    }
    assert not any(path.startswith("src/") for path in changed)
    assert not any(path.startswith("configs/") for path in changed)
    assert not any(path.startswith("parameters/") for path in changed)


def test_adr_and_report_keep_solver_authorization_false() -> None:
    for text in (ADR.read_text(encoding="utf-8"), REPORT.read_text(encoding="utf-8")):
        assert "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE" in text
        assert "ACTIVE_PARAMETERS = 0" in text
        assert "CALIBRATION_STARTED = FALSE" in text
        assert "PHYSICAL_VALIDATION_COMPLETE = FALSE" in text
