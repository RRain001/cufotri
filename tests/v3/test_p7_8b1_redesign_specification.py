"""P7.8B-1 redesign specification, dimensional, gate, and isolation tests."""

from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/v3/physics/p7_8b1_redesign_specification.yaml"
P7_8A = ROOT / "docs/v3/physics/p7_8a_redesign_priority_registry.yaml"
BASE_SHA = "986e375ce586a1ba1b3a707e07f5f5dd80e5617e"

EXPECTED_REDESIGNS = {
    "R1_OBT_DAYLIGHT_FORMATION_STATE",
    "R2_OBT_NIGHTTIME_FORMATION_STATE",
    "R3_OBT_PHOTOSYNTHETIC_FORCING_STATE",
    "R4_OBT_PLANT_MASS_BASIS",
    "R5_OBT_TEMPERATURE_RESPONSE",
    "R6_ROOT_LAYERED_UPTAKE_STATE",
    "R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY",
    "R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY",
    "R9_LEAF_PHENOLOGY_RESISTANCE",
}
EXPECTED_DEFERRED = {
    "D1_TFWT_WATER_TURNOVER_GROWTH_DILUTION",
    "D2_SOIL_HYDRAULIC_TRANSPORT_EVAPORATION",
}
EXPECTED_REJECTED = {
    "X1_IMPORT_UNREVIEWED_UFOTRI_VALUES",
    "X2_ROOT_RATE_TO_VELOCITY_SCALING",
    "X3_CONTINUOUS_FOOD_RATE_TO_HARVEST_FRACTION",
    "X4_DOSE_DRIVEN_ENVIRONMENTAL_PHYSICS_REDESIGN",
}
REQUIRED_FIELDS = {
    "item_id",
    "subsystem",
    "current_model",
    "current_equation",
    "identified_gap",
    "scientific_requirement",
    "candidate_model",
    "new_state_variables",
    "new_parameters",
    "interface_changes",
    "coupling_impact",
    "validation_dataset_requirement",
    "implementation_complexity",
    "priority",
    "decision",
}
DECISIONS = {
    "APPROVED_FOR_FUTURE_IMPLEMENTATION",
    "REQUIRES_MORE_RESEARCH",
    "KEEP_CURRENT_MODEL",
    "REJECT_REDESIGN",
}
COUPLING_IMPACTS = {
    "NO_INTERFACE_CHANGE",
    "INTERFACE_EXTENSION",
    "PIPELINE_CHANGE",
    "NUMERICAL_COUPLING_CHANGE",
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
    return set(git("diff", "--name-only", BASE_SHA).splitlines()) | set(
        git("ls-files", "--others", "--exclude-standard").splitlines()
    )


def test_specification_covers_all_p7_8a_redesign_and_deferred_items() -> None:
    payload = read_yaml(SPEC)
    p7_8a = read_yaml(P7_8A)
    specs = {item["item_id"]: item for item in payload["specifications"]}
    p7_8a_items = {item["item_id"]: item for item in p7_8a["items"]}

    assert payload["stage"] == "P7.8B-1"
    assert payload["status"] == "PASS_REDESIGN_SPECIFICATION"
    assert payload["current_v3_model"] == "FROZEN"
    assert set(specs) == EXPECTED_REDESIGNS | EXPECTED_DEFERRED
    assert payload["specification_scope"]["p7_8a_redesign_items_specified"] == 9
    assert payload["specification_scope"]["p7_8a_deferred_extensions_specified"] == 2
    assert payload["specification_scope"]["high_priority_items_specified"] is True

    expected_high_priority = {
        item_id
        for item_id in EXPECTED_REDESIGNS
        if p7_8a_items[item_id]["priority"] in {"CRITICAL", "HIGH"}
    }
    assert expected_high_priority <= set(specs)

    for item_id, item in specs.items():
        missing = REQUIRED_FIELDS - set(item)
        assert not missing, f"{item_id} missing {sorted(missing)}"
        assert item["current_model"].strip()
        assert item["current_equation"].strip()
        assert item["identified_gap"].strip()
        assert item["candidate_model"].strip()
        assert item["validation_dataset_requirement"].strip()
        assert item["new_state_variables"]
        assert item["new_parameters"]
        assert item["decision"] in DECISIONS
        assert item["coupling_impact"] in COUPLING_IMPACTS
        assert item["priority"] == p7_8a_items[item_id]["priority"]
        assert item["parameter_admission"] == "FORBIDDEN_IN_P7_8B1"
        assert item["equation_status"] in {
            "CANDIDATE_NOT_IMPLEMENTED",
            "SPECIFICATION_ONLY",
        }


def test_option_sets_and_required_subsystem_candidates_are_explicit() -> None:
    payload = read_yaml(SPEC)
    options = payload["model_options"]

    assert set(options) == {
        "obt",
        "root",
        "soil",
        "leaf_exchange",
        "tfwt",
        "food_transfer",
    }
    assert options["obt"]["option_a_reduced_first_order"]["decision"] == (
        "KEEP_CURRENT_MODEL"
    )
    assert options["obt"]["option_b_two_pool_biological_extension"]["decision"] == (
        "REQUIRES_MORE_RESEARCH"
    )
    assert {key for key in options["root"]} == {
        "option_a_effective_velocity",
        "option_b_water_flux_coupled",
        "option_c_moisture_dependent",
    }
    assert options["soil"]["option_b_layered_conservative_transport"]["decision"] == (
        "REQUIRES_MORE_RESEARCH"
    )
    assert options["leaf_exchange"]["option_b_dynamic_stomatal_response"]["decision"] == (
        "REQUIRES_MORE_RESEARCH"
    )
    assert options["tfwt"]["option_b_dynamic_water_turnover"]["decision"] == (
        "REQUIRES_MORE_RESEARCH"
    )
    assert options["food_transfer"]["option_b_continuous_or_hybrid_product_state"]["decision"] == (
        "REQUIRES_MORE_RESEARCH"
    )


def test_candidate_equations_have_dimensional_and_boundary_markers() -> None:
    payload = read_yaml(SPEC)
    specs = {item["item_id"]: item for item in payload["specifications"]}

    assert "Bq m^-2" in specs["R1_OBT_DAYLIGHT_FORMATION_STATE"]["current_equation"]
    assert "s^-1" in specs["R1_OBT_DAYLIGHT_FORMATION_STATE"]["current_equation"]
    assert "m s^-1" in specs["R6_ROOT_LAYERED_UPTAKE_STATE"]["current_equation"]
    assert "Bq m^-3" in specs["R6_ROOT_LAYERED_UPTAKE_STATE"]["current_equation"]
    assert "lambda" in specs["D2_SOIL_HYDRAULIC_TRANSPORT_EVAPORATION"]["current_equation"]
    assert "r_a" in specs["R9_LEAF_PHENOLOGY_RESISTANCE"]["current_equation"]
    assert "dW/dt" in specs["D1_TFWT_WATER_TURNOVER_GROWTH_DILUTION"]["candidate_model"]
    assert "M_food,O" in specs["R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY"]["candidate_model"]
    assert "M_food,T" in specs["R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY"]["candidate_model"]

    numerical = {
        item_id
        for item_id, item in specs.items()
        if item["coupling_impact"] == "NUMERICAL_COUPLING_CHANGE"
    }
    assert numerical == {
        "R6_ROOT_LAYERED_UPTAKE_STATE",
        "R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY",
        "R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY",
        "D2_SOIL_HYDRAULIC_TRANSPORT_EVAPORATION",
    }


def test_governance_blocks_activation_and_preserves_rejected_redesigns() -> None:
    payload = read_yaml(SPEC)
    governance = payload["governance"]

    assert governance["specification_is_control_plane_only"] is True
    assert governance["candidate_equations_are_implemented"] is False
    assert governance["candidate_parameters_have_values"] is False
    assert governance["candidate_parameters_are_runtime_admissible"] is False
    assert governance["implementation_authorized"] is False
    assert governance["direct_activation_forbidden"] is True
    assert ["SPECIFICATION_ONLY", "ACTIVE_PARAMETER"] in governance[
        "forbidden_transitions"
    ]
    assert ["REQUIRES_MORE_RESEARCH", "ACTIVE_PARAMETER"] in governance[
        "forbidden_transitions"
    ]
    assert payload["specification_scope"]["active_parameters"] == 0
    assert payload["specification_scope"]["calibration_started"] is False
    assert payload["specification_scope"]["v3_physics_ready"] is False

    rejected = {
        item["item_id"]: item for item in payload["rejected_redesigns"]
    }
    assert set(rejected) == EXPECTED_REJECTED
    assert all(item["decision"] == "REJECT_REDESIGN" for item in rejected.values())


def test_baseline_profile_is_unchanged_and_all_future_migrations_are_explicit() -> None:
    payload = read_yaml(SPEC)
    baseline = payload["baseline_compatibility"]

    assert baseline["profile_id"] == "v3_frozen_baseline"
    assert baseline["status"] == "RUNNABLE_UNCHANGED"
    assert baseline["existing_cases_continue_running"] is True
    assert baseline["existing_solver_equations_changed"] is False
    assert baseline["existing_state_serialization_changed"] is False
    assert baseline["existing_parameter_defaults_changed"] is False
    assert baseline["new_parameters_required"] is False
    assert "fail closed" in baseline["migration_strategy"]
    assert {
        item["decision"] for item in payload["baseline_preservation"]
    } == {"KEEP_CURRENT_MODEL"}


def test_p7_8b1_artifacts_are_isolated_from_runtime_and_parameters() -> None:
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

    allowed_paths = {
        "docs/implementation_status.md",
        "docs/v3/adr/ADR-020-v3-redesign-specification-policy.md",
        "docs/v3/physics/p7_8b1_redesign_specification.yaml",
        "docs/v3/reports/v3_p7_8b1_coupling_impact_report.md",
        "docs/v3/reports/v3_p7_8b1_equation_gap_analysis.md",
        "docs/v3/reports/v3_p7_8b1_independent_review.md",
        "docs/v3/reports/v3_p7_8b1_redesign_specification_report.md",
        "tests/v3/test_p7_8b1_redesign_specification.py",
    }
    assert changed <= allowed_paths


@pytest.mark.parametrize(
    "path",
    [
        SPEC,
        ROOT / "docs/v3/adr/ADR-020-v3-redesign-specification-policy.md",
        ROOT / "docs/v3/reports/v3_p7_8b1_redesign_specification_report.md",
        ROOT / "docs/v3/reports/v3_p7_8b1_equation_gap_analysis.md",
        ROOT / "docs/v3/reports/v3_p7_8b1_coupling_impact_report.md",
        ROOT / "docs/v3/reports/v3_p7_8b1_independent_review.md",
    ],
)
def test_required_p7_8b1_artifact_exists(path: Path) -> None:
    assert path.is_file()
