from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ACQUISITION = ROOT / "validation" / "external_evidence_acquisition" / "d3"
MAPPING_PATH = ACQUISITION / "d3_ufotri_manual_data_field_mapping.yaml"
MAPPING = yaml.safe_load(MAPPING_PATH.read_text(encoding="utf-8"))
FIELDS = MAPPING["fields"]
FIELD_BY_ID = {field["field_id"]: field for field in FIELDS}
ALLOWED_CATEGORIES = set(MAPPING["classification_enum"])
ALLOWED_ACTIONS = set(MAPPING["action_enum"])
ALLOWED_REQUIREMENTS = set(MAPPING["requirement_enum"])
BASE_MAIN = "f5d18886f3a635cd6c3a813d820b1f3b3e52dd3a"
REVIEW_TARGET = "0164a99cae30ab44411fe98be9ea9cc512c51966"


def _git_diff_is_empty(path: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            f"{BASE_MAIN}...{REVIEW_TARGET}",
            "--",
            path,
        ],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def test_mapping_is_parseable_and_frozen() -> None:
    assert MAPPING["mapping_id"] == "D3_UFOTRI_MANUAL_DATA_FIELD_MAPPING_V1"
    assert MAPPING["status"] == "FROZEN_PRE_LAB"
    assert MAPPING["source"]["file"] == "ufotri_manual.md"
    assert MAPPING["source"]["source_sha256"]


def test_manual_source_sha256_matches_worktree_and_source_commit() -> None:
    source = ROOT / MAPPING["source"]["file"]
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    assert actual == MAPPING["source"]["source_sha256"]
    committed = subprocess.run(
        [
            "git",
            "show",
            f"{MAPPING['source']['source_commit']}:{MAPPING['source']['file']}",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert hashlib.sha256(committed).hexdigest() == actual


def test_each_field_has_required_mapping_keys_and_unique_id() -> None:
    assert len(FIELDS) == 100
    assert len(FIELD_BY_ID) == len(FIELDS)
    required = {
        "field_id",
        "display_name",
        "category",
        "manual_reference",
        "manual_term",
        "manual_unit",
        "d3_field",
        "d3_unit",
        "requirement",
        "controlled_chamber_mapping",
        "existing_template_location",
        "action",
        "notes",
    }
    for field in FIELDS:
        assert required <= field.keys(), field.get("field_id")
        assert field["field_id"]
        assert field["category"]


def test_categories_actions_and_requirements_use_frozen_enumerations() -> None:
    for field in FIELDS:
        assert field["category"]
        assert set(field["category"]) <= ALLOWED_CATEGORIES
        assert field["action"] in ALLOWED_ACTIONS
        assert field["requirement"] in ALLOWED_REQUIREMENTS


def test_manual_explicit_fields_have_manual_authority_and_location() -> None:
    explicit = [field for field in FIELDS if "MANUAL_EXPLICIT" in field["category"]]
    assert len(explicit) == 36
    for field in explicit:
        assert field["manual_reference"]
        assert field["manual_term"]
        assert field["manual_unit"] is not None


def test_manual_derived_fields_have_manual_authority_and_derivation() -> None:
    derived = [field for field in FIELDS if "MANUAL_DERIVED" in field["category"]]
    assert len(derived) == 10
    for field in derived:
        assert field["manual_reference"]
        assert field["manual_term"]
        assert field["notes"]


def test_unresolved_fields_have_no_silent_default_or_runtime_authority() -> None:
    unresolved = [
        field for field in FIELDS if "UNRESOLVED_NO_SOURCE" in field["category"]
    ]
    assert {field["field_id"] for field in unresolved} == {
        "cultivar_specific_resistance_parameter",
        "chamber_mixing_to_outdoor_wind_transform",
        "root_zone_hto_transfer_function",
    }
    for field in unresolved:
        assert field["action"] == "DEFER_UNRESOLVED"
        assert field["default"] is None
        assert field["authorized_for_model_use"] is False
        assert field["authorized_for_acceptance_use"] is False
        assert field["authorized_for_trusted_registry_use"] is False


def test_r1_manual_anchor_corrections_are_frozen() -> None:
    assert FIELD_BY_ID["release_rate"]["manual_reference"] == "5.2.2 Table 3"
    assert "Appendix B" not in FIELD_BY_ID["release_rate"]["manual_reference"]
    assert FIELD_BY_ID["soil_layer_depths"]["manual_reference"] == (
        "2.2.3; 2.2.4; 2.2.5"
    )
    assert "Figure 13" not in FIELD_BY_ID["soil_layer_depths"]["manual_reference"]
    assert FIELD_BY_ID["root_hto_uptake_flux"]["manual_reference"] == (
        "2.2.3; Equation (37); 2.2.5"
    )


def test_controlled_chamber_medium_and_replicate_contract_are_not_overstated() -> None:
    design = yaml.safe_load(
        (ACQUISITION / "controlled_chamber_experiment_design.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert design["exposure_medium"]["air_moisture_water_hto_bq_ml"] == 5270
    assert design["exposure_medium"]["liquid_culture_or_irrigation_water"] is False
    sampling = design["sampling"]
    assert sampling["planned_biological_replicates_per_primary_time"] == 5
    assert sampling["minimum_uncensored_replicates_per_primary_time"] == 3
    assert sampling["minimum_uncensored_replicates_is_not_planned_replicates"] is True


def test_manual_mapping_counts_are_stable() -> None:
    expected = {
        "MANUAL_EXPLICIT": 36,
        "MANUAL_DERIVED": 10,
        "D3_DESIGN_SPECIFIC": 34,
        "MODERN_QA_REQUIRED": 17,
        "NOT_APPLICABLE_CONTROLLED_CHAMBER": 7,
        "UNRESOLVED_NO_SOURCE": 3,
    }
    assert {
        category: sum(category in field["category"] for field in FIELDS)
        for category in expected
    } == expected


def test_requested_file_contract_keeps_unresolved_fields_explicit() -> None:
    request = yaml.safe_load(
        (ACQUISITION / "requested_file_contract.yaml").read_text(encoding="utf-8")
    )
    assert request["request_status"] == "DRAFT_READY_NOT_SENT"
    assert request["intake_boundary"]["trusted_registry_change_authorized"] is False
    unresolved_ids = {
        item["field_id"] for item in request["unresolved_manual_fields"]
    }
    assert unresolved_ids == {
        "cultivar_specific_resistance_parameter",
        "chamber_mixing_to_outdoor_wind_transform",
        "root_zone_hto_transfer_function",
    }


def test_quality_control_contract_preserves_primary_endpoint_and_replicates() -> None:
    qc = yaml.safe_load(
        (ACQUISITION / "templates" / "quality_control_checklist.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert qc["sampling"]["planned_biological_replicates_per_primary_time"] == 5
    assert qc["sampling"]["minimum_uncensored_replicates_per_primary_time"] == 3
    assert qc["sampling"]["primary_endpoint"] == (
        "COMBINED_STEM_AND_LEAF_TFWT_BQ_PER_L_TISSUE_WATER"
    )
    assert qc["primary_endpoint_excludes"] == ["ROOTS", "PODS", "SEEDS"]
    assert qc["forcing"]["post_exposure_background_maximum_fraction_of_setpoint"][
        "maximum_allowed"
    ] == 0.005


def test_manifest_and_request_contract_include_traceability_and_rights() -> None:
    manifest = yaml.safe_load(
        (ACQUISITION / "templates" / "raw_manifest_template.yaml").read_text(
            encoding="utf-8"
        )
    )
    file_contract = manifest["files"][0]
    assert {
        "creation_time_utc",
        "received_time_utc",
        "sha256",
        "immutable_read_only_copy",
        "licence",
        "redistribution_allowed",
        "publication_review_required",
        "retention_policy",
    } <= set(file_contract)
    request = yaml.safe_load(
        (ACQUISITION / "requested_file_contract.yaml").read_text(encoding="utf-8")
    )
    assert request["request_status"] == "DRAFT_READY_NOT_SENT"
    assert request["intake_boundary"]["trusted_registry_change_authorized"] is False
    assert "plant_material" in request["required_data_groups"]
    assert "root_pathway_and_controls" in request["required_data_groups"]


def test_protected_model_and_registry_paths_are_unchanged_from_main() -> None:
    protected = (
        "src",
        "configs",
        "validation/v3/policy/trusted_external_evidence_registry.yaml",
    )
    assert all(_git_diff_is_empty(path) for path in protected)
