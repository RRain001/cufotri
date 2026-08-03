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


def _git_diff_is_empty(path: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--quiet", "main", "--", path],
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
        assert set(field["category"]) <= ALLOWED_CATEGORIES
        assert field["action"] in ALLOWED_ACTIONS
        assert field["requirement"] in ALLOWED_REQUIREMENTS


def test_manual_explicit_fields_have_a_manual_section_or_table_anchor() -> None:
    for field in FIELDS:
        if "MANUAL_EXPLICIT" in field["category"]:
            reference = str(field["manual_reference"])
            assert reference not in {"NO_MANUAL_AUTHORITY", "None"}
            assert (
                reference[:1].isdigit()
                or "§" in reference
                or "Table" in reference
                or "Eq." in reference
                or "Figure" in reference
                or "Equation" in reference
            )


def test_non_manual_design_and_qa_requirements_do_not_claim_manual_authority() -> None:
    for field in FIELDS:
        if "D3_DESIGN_SPECIFIC" in field["category"]:
            assert field["manual_reference"] == "NO_MANUAL_AUTHORITY"
        if field["field_id"].startswith("d3_"):
            assert field["manual_reference"] == "NO_MANUAL_AUTHORITY"


def test_not_applicable_fields_explain_the_controlled_chamber_boundary() -> None:
    for field in FIELDS:
        if "NOT_APPLICABLE_CONTROLLED_CHAMBER" in field["category"]:
            assert field["requirement"] == "not_applicable"
            assert field["controlled_chamber_mapping"] == "not_applicable"
            assert field["action"] in {"NOT_APPLICABLE", "CLARIFY"}
            assert field["notes"]


def test_unresolved_fields_are_fail_closed() -> None:
    unresolved = [
        field for field in FIELDS if "UNRESOLVED_NO_SOURCE" in field["category"]
    ]
    assert len(unresolved) == 3
    for field in unresolved:
        assert field["requirement"] == "defer_unresolved"
        assert field["action"] == "DEFER_UNRESOLVED"
        assert field["controlled_chamber_mapping"] == "unresolved"


def test_manual_example_values_are_not_d3_defaults() -> None:
    examples = {
        "leaf_area_index",
        "daytime_stomatal_resistance",
        "nighttime_epidermal_resistance",
        "volumetric_soil_water_content",
    }
    for field_id in examples:
        field = FIELD_BY_ID[field_id]
        assert field["value_status"] == "MANUAL_EXAMPLE_OR_CASE_PARAMETER"
        assert field["action"] in {"CLARIFY", "ADD"}
        note = field["notes"].lower()
        assert (
            "not" in note
            or "不能" in note
            or "case/example" in note
            or "example value" in note
        )


def test_d3_primary_endpoint_is_explicitly_combined_stem_and_leaf() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["primary_endpoint"] == "COMBINED_STEM_AND_LEAF_TFWT"
    assert boundary["primary_endpoint_unit"] == "Bq/L tissue water"
    endpoint = FIELD_BY_ID["d3_primary_endpoint_definition"]
    assert endpoint["d3_field"] == "combined_stem_and_leaf_tfwt"
    assert FIELD_BY_ID["d3_primary_endpoint_exclusions"]["d3_field"]


def test_roots_pods_and_seeds_are_excluded_from_primary_endpoint() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["roots_in_primary_endpoint"] is False
    assert boundary["pods_in_primary_endpoint"] is False
    assert boundary["seeds_in_primary_endpoint"] is False
    assert MAPPING["summary_contract"]["excluded_from_primary_endpoint"] == [
        "roots",
        "pods",
        "seeds",
    ]


def test_air_moisture_basis_and_background_bound_are_distinct() -> None:
    assert (
        MAPPING["frozen_d3_boundary"][
            "exposure_setpoint_bq_per_ml_air_moisture_water"
        ]
        == 5270
    )
    setpoint = FIELD_BY_ID["d3_air_moisture_hto_setpoint"]
    assert "air-moisture water" in setpoint["d3_unit"]
    background = FIELD_BY_ID["d3_background_maximum_fraction"]
    assert "0.5%" in background["notes"]
    assert "not" in background["notes"].lower()


def test_planning_lod_is_not_a_confirmed_laboratory_capability() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["planning_lod_bq_per_l_tissue_water"] == 250
    assert (
        boundary["planning_lod_status"]
        == "PROJECT_PLANNING_TARGET_NOT_CONFIRMED_CAPABILITY"
    )
    field = FIELD_BY_ID["d3_planning_lod"]
    assert "planning target" in field["notes"].lower()
    assert "actual LOD" in field["notes"]


def test_frozen_d3_schedule_replicates_and_thresholds_are_not_changed() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["exposure_duration_h"] == 24
    assert boundary["post_exposure_followup_h"] == 120
    assert boundary["primary_sampling_times_h"] == [0.2, 48, 120]
    assert boundary["biological_replicates_per_primary_time"] == 5
    assert "0.15 dex" in FIELD_BY_ID["d3_classifier_thresholds"]["d3_unit"]
    assert "0.50 dex" in FIELD_BY_ID["d3_classifier_thresholds"]["d3_unit"]


def test_lab_and_external_evidence_gate_remain_closed() -> None:
    boundary = MAPPING["frozen_d3_boundary"]
    assert boundary["lab_feasibility_status"] == "AWAITING_LAB_CONFIRMATION"
    assert boundary["real_experiment"] == "NOT_EXECUTED"
    assert boundary["real_external_evidence"] is False
    assert boundary["formal_v3_physics"] == "NOT_STARTED"
    assert (
        boundary["v3_physics_start_gate"]
        == "BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA"
    )


def test_mapping_does_not_authorize_registry_or_model_changes() -> None:
    boundary = MAPPING["authorization_boundary"]
    assert boundary["model_code_change_authorized"] is False
    assert boundary["formal_root_config_change_authorized"] is False
    assert boundary["h2_h3_parameter_change_authorized"] is False
    assert boundary["classifier_threshold_change_authorized"] is False
    assert boundary["primary_sampling_time_change_authorized"] is False
    assert boundary["replicate_count_change_authorized"] is False
    assert boundary["trusted_registry_change_authorized"] is False
    assert boundary["formal_h2_h3_selection_authorized"] is False


def test_csv_templates_have_equal_header_and_example_row_width() -> None:
    template_dir = ACQUISITION / "templates"
    for path in sorted(template_dir.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        assert len(rows) == 2, path.name
        assert len(rows[0]) == len(rows[1]), path.name


def test_chamber_template_uses_air_moisture_and_controlled_analogues() -> None:
    path = ACQUISITION / "templates" / "chamber_forcing_template.csv"
    header = next(csv.reader(path.open(encoding="utf-8", newline="")))
    required = {
        "experiment_phase",
        "exposure_medium",
        "air_moisture_hto_bq_per_ml_water",
        "mixing_velocity_m_s",
        "par_or_radiation_value",
        "par_or_radiation_unit",
        "measurement_height_m",
        "measurement_location",
        "quality_flag",
    }
    assert required <= set(header)
    assert "wind_direction" not in header
    assert "stability_class" not in header


def test_tfwt_and_biomass_templates_preserve_primary_endpoint_boundaries() -> None:
    tfwt = next(
        csv.reader(
            (ACQUISITION / "templates" / "tfwt_sample_template.csv").open(
                encoding="utf-8", newline=""
            )
        )
    )
    biomass = next(
        csv.reader(
            (ACQUISITION / "templates" / "biomass_template.csv").open(
                encoding="utf-8", newline=""
            )
        )
    )
    assert {
        "biological_replicate_id",
        "exposure_group",
        "organ_definition",
        "hours_after_exposure",
        "tfwt_bq_per_l_tissue_water",
        "detection_limit_bq_per_l",
        "quantification_limit_bq_per_l",
        "combined_uncertainty_percent",
    } <= set(tfwt)
    assert {
        "cultivar",
        "plant_batch",
        "sowing_date",
        "substrate",
        "nutrition",
        "watering",
        "pre_exposure_acclimation",
        "uniformity_assessment",
        "leaf_area_index",
        "root_mass_g",
        "pod_mass_g",
        "seed_mass_g",
    } <= set(biomass)


def test_qc_template_separates_planned_and_uncensored_replicates() -> None:
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
