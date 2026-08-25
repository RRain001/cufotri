"""P7.8B-2 physics-selection, roadmap, validation, and isolation gates."""

from pathlib import Path
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[2]
SELECTION = ROOT / "docs/v3/physics/p7_8b2_physics_selection.yaml"
ROADMAP = ROOT / "docs/v3/physics/p7_8b2_architecture_roadmap.yaml"
COUPLING = ROOT / "docs/v3/physics/p7_8b2_coupling_decision.yaml"
VALIDATION = ROOT / "docs/v3/physics/p7_8b2_validation_dependency.yaml"
BASE_SHA = "9d3ba09abf4fd68a93ae2e5e4e80c9f2d0d76e6e"
STAGE_TIP_SHA = "5ba891ec5e2d24cffdfe197afcf9006d2e4c5280"

EXPECTED_SOURCE_ITEMS = {
    "R1_OBT_DAYLIGHT_FORMATION_STATE",
    "R2_OBT_NIGHTTIME_FORMATION_STATE",
    "R3_OBT_PHOTOSYNTHETIC_FORCING_STATE",
    "R4_OBT_PLANT_MASS_BASIS",
    "R5_OBT_TEMPERATURE_RESPONSE",
    "R6_ROOT_LAYERED_UPTAKE_STATE",
    "R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY",
    "R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY",
    "R9_LEAF_PHENOLOGY_RESISTANCE",
    "D1_TFWT_WATER_TURNOVER_GROWTH_DILUTION",
    "D2_SOIL_HYDRAULIC_TRANSPORT_EVAPORATION",
}

EXPECTED_DECISIONS = {
    "OBT_FORMATION_PACKAGE": ("option_b_two_pool_biological_extension", "V4", "SELECTED_FOR_V4"),
    "OBT_PLANT_MASS_BASIS_CONTRACT": ("explicit_typed_mass_basis_contract", "V3.1", "SELECTED_FOR_V3_1"),
    "ROOT_UPTAKE_WATER_FLUX_BOUNDARY": ("option_b_water_flux_coupled", "V4", "SELECTED_FOR_V4"),
    "SOIL_SIGNED_TRANSPORT_BASELINE": ("option_a_signed_transport_interface", "MAINTAINED", "KEEP_CURRENT"),
    "LEAF_DYNAMIC_STOMATAL_RESPONSE": ("option_b_dynamic_stomatal_response", "V4", "SELECTED_FOR_V4"),
    "TFWT_FIXED_STORAGE_BOUNDARY": ("option_a_fixed_water_storage", "MAINTAINED", "KEEP_CURRENT"),
    "FOOD_ENVIRONMENTAL_TRANSFER_BOUNDARY": ("option_a_harvest_event", "MAINTAINED", "KEEP_CURRENT"),
    "CONSUMPTION_EXTERNAL_INPUT_BOUNDARY": ("external_scenario_input", "MAINTAINED", "KEEP_CURRENT"),
    "DOSE_EXTERNAL_LAYER_BOUNDARY": ("keep_external_dose_layer", "MAINTAINED", "KEEP_CURRENT"),
}

REQUIRED_FIELDS = {
    "item_id",
    "subsystem",
    "current_model",
    "candidate_models",
    "selected_model",
    "selection_reason",
    "scientific_basis",
    "advantages",
    "limitations",
    "new_state_variables",
    "new_parameters_required",
    "validation_requirement",
    "coupling_impact",
    "implementation_stage",
    "decision_status",
}

ALLOWED_PATHS = {
    "docs/implementation_status.md",
    "docs/v3/physics/p7_8b2_physics_selection.yaml",
    "docs/v3/physics/p7_8b2_architecture_roadmap.yaml",
    "docs/v3/physics/p7_8b2_coupling_decision.yaml",
    "docs/v3/physics/p7_8b2_validation_dependency.yaml",
    "docs/v3/reports/v3_p7_8b2_physics_selection_report.md",
    "docs/v3/reports/v3_p7_8b2_architecture_roadmap.md",
    "docs/v3/reports/v3_p7_8b2_validation_dependency_report.md",
    "docs/v3/reports/v3_p7_8b2_independent_review.md",
    "docs/v3/adr/ADR-021-v3-physics-selection-policy.md",
    "tests/v3/test_p7_8b2_physics_selection.py",
}


def read_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def changed_paths() -> set[str]:
    """Return only the immutable P7.8B-2 historical stage diff."""

    return set(git("diff", "--name-only", BASE_SHA, STAGE_TIP_SHA).splitlines())


def test_selection_registry_is_complete_and_traceable() -> None:
    payload = read_yaml(SELECTION)
    items = {item["item_id"]: item for item in payload["items"]}

    assert payload["stage"] == "P7.8B-2"
    assert payload["status"] == "PASS_PHYSICS_SELECTION"
    assert payload["current_v3_model"] == "FROZEN"
    assert set(items) == set(EXPECTED_DECISIONS)

    covered_source_items = {
        source_id
        for item in items.values()
        for source_id in item["source_item_ids"]
    }
    assert covered_source_items == EXPECTED_SOURCE_ITEMS

    for item_id, item in items.items():
        assert not REQUIRED_FIELDS - set(item), item_id
        assert item["current_model"].strip()
        assert item["candidate_models"]
        assert item["selected_model"].strip()
        assert item["selection_reason"].strip()
        assert item["scientific_basis"].strip()
        assert item["advantages"]
        assert item["limitations"]
        assert item["validation_requirement"]["datasets"]
        assert item["validation_requirement"]["observables"]
        assert item["validation_requirement"]["metrics"]
        assert item["coupling_impact"] in {
            "NO_IMPACT",
            "INTERFACE_EXTENSION",
            "PIPELINE_CHANGE_REQUIRED",
            "NUMERICAL_COUPLING_CHANGE_REQUIRED",
        }
        assert item["decision_status"] in {
            "SELECTED_FOR_V3_1",
            "SELECTED_FOR_V4",
            "KEEP_CURRENT",
            "REJECTED",
            "INSUFFICIENT_EVIDENCE",
        }
        for parameter in item["new_parameters_required"]:
            assert isinstance(parameter, str)
            assert "value:" not in parameter.lower()
            assert "= 0" not in parameter
        for candidate in item["candidate_models"]:
            assert candidate["model_id"]
            assert candidate["disposition"] in {
                "SELECTED_FOR_V3_1",
                "SELECTED_FOR_V4",
                "KEEP_CURRENT",
                "REJECTED",
                "INSUFFICIENT_EVIDENCE",
            }
            assert candidate["reason"].strip()


def test_final_model_choices_and_rejections_are_frozen() -> None:
    payload = read_yaml(SELECTION)
    items = {item["item_id"]: item for item in payload["items"]}

    for item_id, (model, stage, status) in EXPECTED_DECISIONS.items():
        item = items[item_id]
        assert item["selected_model"] == model
        assert item["implementation_stage"] == stage
        assert item["decision_status"] == status

    assert items["ROOT_UPTAKE_WATER_FLUX_BOUNDARY"]["coupling_impact"] == (
        "NUMERICAL_COUPLING_CHANGE_REQUIRED"
    )
    assert items["OBT_PLANT_MASS_BASIS_CONTRACT"]["implementation_stage"] == "V3.1"
    assert items["FOOD_ENVIRONMENTAL_TRANSFER_BOUNDARY"]["decision_status"] == (
        "KEEP_CURRENT"
    )

    rejected = {item["candidate_id"] for item in payload["rejected_candidates"]}
    assert {
        "X1_IMPORT_UNREVIEWED_UFOTRI_VALUES",
        "X2_ROOT_RATE_TO_VELOCITY_SCALING",
        "X3_CONTINUOUS_FOOD_RATE_TO_HARVEST_FRACTION",
        "X4_DOSE_DRIVEN_ENVIRONMENTAL_PHYSICS_REDESIGN",
        "OBT_OPTION_C_ORGAN_SPECIFIC_GROWTH",
        "ROOT_MOISTURE_RESPONSE_AS_STANDALONE_MODEL",
        "FOOD_CONTINUOUS_ONLY_PRODUCT_MODEL",
        "TFWT_GROWTH_CORRECTION_FACTOR",
    } <= rejected

    unresolved = {item["candidate_id"] for item in payload["unresolved_candidates"]}
    assert {
        "SOIL_OPTION_B_LAYERED_TRANSPORT",
        "SOIL_OPTION_C_FULL_HYDROLOGY",
        "TFWT_OPTION_B_DYNAMIC_WATER_TURNOVER",
        "FOOD_OPTION_C_HYBRID_PRODUCT_STATE",
    } <= unresolved


def test_governance_and_roadmap_preserve_current_v3() -> None:
    selection = read_yaml(SELECTION)
    roadmap = read_yaml(ROADMAP)

    scope = selection["selection_scope"]
    assert scope["implementation_started"] is False
    assert scope["solver_changes"] is False
    assert scope["numerical_coupling_changes"] is False
    assert scope["active_parameters"] == 0
    assert scope["calibration_started"] is False
    assert scope["ufotri_active_database"] is False
    assert scope["v3_physics_ready"] is False

    governance = selection["governance"]
    assert governance["selection_registry_is_control_plane_only"] is True
    assert governance["selected_equations_are_implemented"] is False
    assert governance["selected_parameters_have_values"] is False
    assert governance["selected_models_are_runtime_admissible"] is False
    assert governance["implementation_authorized"] is False
    assert ["SELECTED_FOR_V4", "ACTIVE_PARAMETER"] in governance[
        "forbidden_transitions"
    ]

    assert roadmap["current_profile"] == "v3_frozen_baseline"
    assert roadmap["roadmap_invariants"]["v3_1_is_not_a_new_solver"] is True
    assert roadmap["roadmap_invariants"]["v4_is_opt_in"] is True
    assert roadmap["roadmap_invariants"]["missing_future_fields_fail_closed"] is True
    assert [item["order"] for item in roadmap["V4"]["implementation_order"]] == [
        1,
        2,
        3,
        4,
    ]
    assert [
        item["item_id"] for item in roadmap["V4"]["implementation_order"]
    ] == [
        "V4_DATA_AND_STATE_CONTRACTS",
        "V4_LEAF_DYNAMIC_STOMATAL_RESPONSE",
        "V4_OBT_FORMATION_PACKAGE",
        "V4_ROOT_UPTAKE_WATER_FLUX_BOUNDARY",
    ]
    assert roadmap["V4"]["not_in_v4_until_reopened"]


def test_coupling_decision_and_validation_cover_every_selection() -> None:
    selection = read_yaml(SELECTION)
    coupling = read_yaml(COUPLING)
    validation = read_yaml(VALIDATION)
    selection_items = {item["item_id"]: item for item in selection["items"]}
    selected_ids = set(selection_items)

    coupling_items = {item["item_id"]: item for item in coupling["decisions"]}
    validation_items = {
        item["item_id"]: item for item in validation["validation_dependencies"]
    }
    assert set(coupling_items) == selected_ids
    assert set(validation_items) == selected_ids
    assert set(coupling["coupling_states"]) == {
        "NO_IMPACT",
        "INTERFACE_EXTENSION",
        "PIPELINE_CHANGE_REQUIRED",
        "NUMERICAL_COUPLING_CHANGE_REQUIRED",
    }
    assert coupling["coupling_invariants"]["current_coupling_changed"] is False
    assert coupling["coupling_invariants"]["p7_5_semantics_changed"] is False
    assert coupling["coupling_invariants"]["p7_5b_semantics_changed"] is False
    assert coupling["coupling_invariants"]["active_parameters"] == 0
    assert coupling["coupling_invariants"]["v3_physics_ready"] is False

    for item_id in selected_ids:
        coupling_item = coupling_items[item_id]
        validation_item = validation_items[item_id]
        assert coupling_item["selected_model"] == selection_items[item_id][
            "selected_model"
        ]
        assert coupling_item["affected_modules"]
        assert coupling_item["migration_strategy"].strip()
        assert coupling_item["compatibility_plan"].strip()
        assert validation_item["selected_model"].strip()
        assert validation_item["required_datasets"]
        assert validation_item["observable_variables"]
        assert validation_item["validation_metrics"]
        assert validation_item["minimum_case_contract"]

    root = coupling_items["ROOT_UPTAKE_WATER_FLUX_BOUNDARY"]
    assert root["coupling_impact"] == "NUMERICAL_COUPLING_CHANGE_REQUIRED"
    assert "P7.5/P7.5B" in root["required_review"]
    assert validation["validation_invariants"]["synthetic_benchmarks_are_not_empirical_validation"] is True


def test_p7_8b2_artifacts_are_isolated_from_runtime_and_parameters() -> None:
    changed = changed_paths()
    forbidden_prefixes = (
        "parameters/",
        "runtime/",
        "pipeline/",
        "src/cteas_ufotri/plant/",
        "src/cteas_ufotri/soil/",
        "src/cteas_ufotri/exposure/",
        "src/cteas_ufotri/coupling/",
        "src/cteas_ufotri/v3_pipeline/",
        "src/cteas_ufotri/parameters_v3/",
    )
    assert not sorted(
        path for path in changed if path.startswith(forbidden_prefixes)
    )
    assert changed <= ALLOWED_PATHS


def test_required_p7_8b2_artifacts_exist() -> None:
    for path in (
        SELECTION,
        ROADMAP,
        COUPLING,
        VALIDATION,
        ROOT / "docs/v3/reports/v3_p7_8b2_physics_selection_report.md",
        ROOT / "docs/v3/reports/v3_p7_8b2_architecture_roadmap.md",
        ROOT / "docs/v3/reports/v3_p7_8b2_validation_dependency_report.md",
        ROOT / "docs/v3/reports/v3_p7_8b2_independent_review.md",
        ROOT / "docs/v3/adr/ADR-021-v3-physics-selection-policy.md",
    ):
        assert path.is_file(), path
