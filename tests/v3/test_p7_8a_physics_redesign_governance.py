"""P7.8A redesign registry, priority, coupling, and gate tests."""

from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/v3/physics/p7_8a_redesign_priority_registry.yaml"
MATRIX = ROOT / "docs/v3/physics/p7_8a_coupling_impact_matrix.yaml"
P7_6D = ROOT / "docs/v3/physics/p7_6d_physics_adoption_decision.yaml"
BASE_SHA = "9490c21d491754fd77f12151380a107df5409445"

REQUIRED_ITEM_FIELDS = {
    "item_id",
    "subsystem",
    "current_v3_model",
    "ufotri_gap",
    "decision_from_p7_6d",
    "scientific_importance",
    "dose_pathway_importance",
    "uncertainty_impact",
    "implementation_complexity",
    "coupling_impact",
    "priority",
    "recommended_stage",
    "decision",
    "rationale",
    "required_validation_data",
}

EXPECTED_REDESIGN_PARAMETER_IDS = {
    "food.harvest_fraction",
    "food.tfwt_harvest_fraction",
    "leaf.growth_stage",
    "obt.daylight_multiplier",
    "obt.nighttime_multiplier",
    "obt.photosynthetic_activity",
    "obt.plant_mass",
    "obt.temperature",
    "root.k_root",
}

ALLOWED_PRIORITIES = {
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "DEFERRED",
    "REJECTED",
}
ALLOWED_COUPLING_IMPACTS = {
    "NO_IMPACT",
    "INTERFACE_CHANGE_ONLY",
    "PIPELINE_CHANGE_REQUIRED",
    "NUMERICAL_COUPLING_REDESIGN_REQUIRED",
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


def test_registry_covers_p7_6d_redesigns_and_required_schema() -> None:
    registry = read_yaml(REGISTRY)
    p7_6d = read_yaml(P7_6D)
    items = registry["items"]
    redesigns = [item for item in items if item["item_class"] == "REDESIGN"]

    assert registry["stage"] == "P7.8A"
    assert registry["status"] == "PASS_PHYSICS_REDESIGN_PRIORITIZATION"
    assert registry["current_v3_model"] == "FROZEN"
    assert len(redesigns) == 9
    assert registry["redesign_item_count"] == len(redesigns)
    assert registry["implementation_started"] is False
    assert registry["solver_changes"] is False
    assert registry["coupling_changes"] is False
    assert registry["active_parameters"] == 0
    assert registry["calibration_started"] is False
    assert registry["ufotri_active_database"] is False
    assert registry["v3_physics_ready"] is False

    mapped_ids = {
        parameter_id
        for item in redesigns
        for parameter_id in item["p7_6d_parameter_ids"]
    }
    assert mapped_ids == set(p7_6d["required_redesign_parameter_ids"])
    assert mapped_ids == EXPECTED_REDESIGN_PARAMETER_IDS

    for item in items:
        missing = REQUIRED_ITEM_FIELDS - set(item)
        assert not missing, f"{item.get('item_id')} missing {sorted(missing)}"
        assert item["required_validation_data"]
        assert item["rationale"].strip()
        assert item["priority"] in ALLOWED_PRIORITIES
        assert item["coupling_impact"] in ALLOWED_COUPLING_IMPACTS
        assert item["activation_allowed_in_p7_8a"] is False


def test_priority_and_subsystem_decisions_are_complete() -> None:
    registry = read_yaml(REGISTRY)
    items = registry["items"]

    assert registry["priority_states"] == [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
        "DEFERRED",
        "REJECTED",
    ]
    assert registry["decision_counts"] == {
        "REDESIGN_REQUIRED": 9,
        "DEFERRED": 2,
        "REJECTED": 4,
    }
    assert {
        item["decision"] for item in items
    } <= {"REDESIGN_REQUIRED", "DEFERRED", "REJECTED"}
    assert {item["recommended_stage"] for item in items} >= {
        "V3.1",
        "V3.2",
        "V4",
        "NEVER",
    }

    expected_subsystems = {
        "leaf_exchange",
        "tfwt",
        "obt",
        "soil",
        "root_uptake",
        "food_transfer",
        "consumption",
        "dose",
    }
    assert set(registry["subsystem_reviews"]) == expected_subsystems
    assert registry["subsystem_reviews"]["leaf_exchange"]["decision"] == (
        "KEEP_CURRENT_V3"
    )
    assert registry["subsystem_reviews"]["obt"]["decision"] == (
        "REDESIGN_REQUIRED"
    )
    assert registry["subsystem_reviews"]["root_uptake"]["decision"] == (
        "REDESIGN_REQUIRED"
    )
    assert registry["subsystem_reviews"]["food_transfer"]["decision"] == (
        "REDESIGN_REQUIRED"
    )
    assert registry["subsystem_reviews"]["dose"]["decision"] == (
        "KEEP_EXTERNAL_LAYER"
    )


def test_coupling_matrix_covers_every_registry_item() -> None:
    registry = read_yaml(REGISTRY)
    matrix = read_yaml(MATRIX)
    registry_items = {item["item_id"]: item for item in registry["items"]}
    matrix_items = {item["item_id"]: item for item in matrix["matrix_records"]}

    assert matrix["stage"] == "P7.8A"
    assert matrix["current_v3_model"] == "FROZEN"
    assert matrix["current_numerical_coupling_changed"] is False
    assert matrix["p7_5_reopened"] is False
    assert matrix["p7_5b_reopened"] is False
    assert set(matrix_items) == set(registry_items)
    assert set(matrix["impact_states"]) == ALLOWED_COUPLING_IMPACTS

    for item_id, item in registry_items.items():
        assert matrix_items[item_id]["coupling_impact"] == item[
            "coupling_impact"
        ]
        assert matrix_items[item_id]["current_action"] in {
            "NO_CHANGE",
            "HOLD_UNTIL_COUPLING_REVIEW",
            "DEFER",
            "REJECT_PERMANENTLY",
        }


def test_redesign_required_cannot_directly_become_active() -> None:
    registry = read_yaml(REGISTRY)
    gate = registry["admission_gate"]
    forbidden = {tuple(pair) for pair in gate["forbidden_direct_transitions"]}

    assert gate["implementation_authorized"] is False
    assert gate["redesign_required_can_enter_validation"] is False
    assert gate["redesign_required_can_activate"] is False
    assert gate["direct_transition_to_active"] is False
    assert ("REDESIGN_REQUIRED", "ACTIVE") in forbidden
    assert ("REDESIGN_REQUIRED", "VALIDATED") in forbidden
    assert ("DEFERRED", "ACTIVE") in forbidden
    assert ("DEFERRED", "VALIDATED") in forbidden

    for item in registry["items"]:
        if item["decision"] in {"REDESIGN_REQUIRED", "DEFERRED"}:
            assert item["activation_allowed_in_p7_8a"] is False
            assert item["decision"] != "ACTIVE"
            assert item["decision"] != "VALIDATED"


def test_p7_8a_artifacts_are_isolated_from_runtime_and_parameters() -> None:
    changed = changed_paths()
    forbidden_prefixes = (
        "parameters/",
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
        "docs/v3/adr/ADR-019-v3-physics-redesign-governance.md",
        "docs/v3/physics/p7_8a_coupling_impact_matrix.yaml",
        "docs/v3/physics/p7_8a_redesign_priority_registry.yaml",
        "docs/v3/reports/v3_p7_8a_coupling_impact_report.md",
        "docs/v3/reports/v3_p7_8a_independent_review.md",
        "docs/v3/reports/v3_p7_8a_physics_evolution_roadmap.md",
        "docs/v3/reports/v3_p7_8a_redesign_prioritization_report.md",
        "tests/architecture/test_p7_8a_physics_redesign_boundary.py",
        "tests/v3/test_p7_8a_physics_redesign_governance.py",
    }
    assert changed <= allowed_paths


@pytest.mark.parametrize(
    "path",
    [
        REGISTRY,
        MATRIX,
        ROOT / "docs/v3/adr/ADR-019-v3-physics-redesign-governance.md",
        ROOT / "docs/v3/reports/v3_p7_8a_redesign_prioritization_report.md",
        ROOT / "docs/v3/reports/v3_p7_8a_physics_evolution_roadmap.md",
        ROOT / "docs/v3/reports/v3_p7_8a_coupling_impact_report.md",
        ROOT / "docs/v3/reports/v3_p7_8a_independent_review.md",
    ],
)
def test_required_p7_8a_artifact_exists(path: Path) -> None:
    assert path.is_file()
