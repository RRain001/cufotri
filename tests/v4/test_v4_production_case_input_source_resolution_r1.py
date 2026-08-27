from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
GOVERNANCE = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r1.yaml"
PHYSICAL_REGISTRY = ROOT / "docs/v3/parameter_evidence/physical_constant_validation_registry.yaml"
REPORT = ROOT / "docs/v4/reports/v4_production_case_input_source_resolution_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-050-v4-production-case-input-source-resolution-r1.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def manifest_ids() -> set[str]:
    manifest = load_yaml(MANIFEST)
    return {entry["quantity_id"] for entry in manifest["inputs"]}


def resolution_ids(data: dict) -> list[str]:
    registry = data["resolution_registry"]
    result: list[str] = []
    for disposition, block in registry.items():
        if disposition in {
            "SOURCE_RESOLVED_NOT_ACTIVATED",
            "CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED",
        }:
            result.extend(block.keys())
        else:
            result.extend(block)
    return result


def test_r1_resolution_partition_exactly_covers_manifest_inventory_once() -> None:
    data = load_yaml(GOVERNANCE)
    manifest = load_yaml(MANIFEST)
    ids = resolution_ids(data)
    expected = manifest_ids()
    assert len(manifest["inputs"]) == 49
    assert sum(bool(entry["required"]) for entry in manifest["inputs"]) == 48
    assert sum(not bool(entry["required"]) for entry in manifest["inputs"]) == 1
    assert len(ids) == 49
    assert len(set(ids)) == 49
    assert set(ids) == expected
    assert sum(data["resolution_summary"][key] for key in data["resolution_summary"] if key != "total") == 49
    assert data["resolution_summary"]["total"] == 49


def test_h3_half_life_source_resolution_matches_independently_reviewed_registry() -> None:
    data = load_yaml(GOVERNANCE)
    physical = load_yaml(PHYSICAL_REGISTRY)
    resolved = data["resolution_registry"]["SOURCE_RESOLVED_NOT_ACTIVATED"][
        "soil_three_layer.tritium_half_life"
    ]
    assert physical["stage_status"] == "PASS_PHYSICAL_CONSTANT_VALIDATION"
    assert physical["validated_parameter_count"] == 1
    assert physical["active_parameter_count"] == 0
    parameter = physical["parameters"][0]
    assert parameter["parameter_id"] == "soil.tritium_half_life"
    assert parameter["validation_status"] == "PASS"
    assert parameter["review_status"] == "INDEPENDENT_REVIEWED"
    assert parameter["selected_source_evidence_id"] == "evidence.ddep.tritium_half_life.2006"
    assert parameter["selected_value"] == resolved["validated_value_s"] == 388540800.0
    assert parameter["selected_uncertainty"] == resolved["validated_uncertainty_s"] == 777600.0
    assert resolved["semantic_evidence_parameter_id"] == parameter["parameter_id"]
    assert resolved["source_revision"] == "2d6a0d1174795980406355055c4855df46ba583f"
    assert resolved["production_use_authorized"] is False
    assert resolved["runtime_import_authorized"] is False
    assert resolved["active_parameter"] is False


def test_source_resolution_does_not_mutate_h3_manifest_into_runtime_readiness() -> None:
    manifest = load_yaml(MANIFEST)
    record = next(
        entry for entry in manifest["inputs"]
        if entry["quantity_id"] == "soil_three_layer.tritium_half_life"
    )
    assert record["readiness"] == "SOURCE_REQUIRED"
    assert record["source"] is None
    assert record["production_use_authorized"] is False


def test_eq39_physical_properties_are_not_promoted_from_test_approximations() -> None:
    data = load_yaml(GOVERNANCE)
    properties = data["resolution_registry"][
        "CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED"
    ]
    assert set(properties) == {
        "root_eq39.latent_heat",
        "root_eq39.water_density",
        "root_eq39.psychrometric_constant",
    }
    for record in properties.values():
        assert record["selected_value"] is None
        assert record["test_value_promoted"] is False
        assert record["authority_url"].startswith("https://")


def test_real_surface_deposition_flux_remains_externally_blocked() -> None:
    data = load_yaml(GOVERNANCE)
    blocked = set(data["resolution_registry"]["BLOCKED_EXTERNAL"])
    assert blocked == {
        "atmosphere.surface_deposition_flux",
        "soil_three_layer.surface_deposition_flux",
    }
    gate = data["atmos_surface_flux_blocker"]
    assert gate["token"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert gate["atmosphere_surface_deposition_flux_ready"] is False
    assert gate["soil_surface_deposition_flux_ready"] is False
    assert gate["surrogate_or_zero_substitution_authorized"] is False


def test_r1_is_control_plane_only_and_preserves_all_hard_boundaries() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1"
    assert data["status"] == "SOURCE_RESOLUTION_AUDIT_COMPLETE_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "69cfebcdfa9e13bd63143321c1534a74e009bcc4"
    scope = data["scope"]
    assert scope["kind"] == "SOURCE_EVIDENCE_RESOLUTION_CONTROL_PLANE_ONLY"
    assert scope["production_source_binding_changed"] is False
    assert scope["runtime_import_changed"] is False
    assert scope["src_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["workflow_changed"] is False
    assert scope["calibration_changed"] is False
    contract = data["source_resolution_contract"]
    assert contract["source_resolution_is_production_authorization"] is False
    assert contract["source_resolution_is_parameter_activation"] is False
    assert contract["test_or_api_default_is_source_evidence"] is False
    assert contract["convenient_constant_approximation_is_universal_evidence"] is False
    assert contract["silent_zero_allowed"] is False
    hard = data["hard_boundaries"]
    assert hard["production_input_packet_ready"] is False
    assert hard["full_model_production_ready"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["obt_multi_pool_implementation_authorized"] is False
    assert hard["obt_parameter_activation_authorized"] is False
    assert hard["current_kf_kr_calibration_authorized"] is False
    assert hard["leaf_r5_authorized"] is False
    assert hard["root_q_w_production_input_resolved"] is False
    assert hard["full_hydrology_authorized"] is False
    assert hard["real_cteas_atmos_binding"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False


def test_report_and_adr_freeze_next_stage_without_overclaiming() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["next_stage_if_clean_merge"]["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2"
    assert data["next_stage_if_clean_merge"]["focus"] == "EQ39_PHYSICAL_PROPERTY_SOURCE_DECISION_ONLY"
    assert data["next_stage_if_clean_merge"]["production_activation_authorized"] is False
    for path in (REPORT, ADR):
        text = path.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        assert "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2" in text
        assert "PRODUCTION_INPUT_PACKET_READY=FALSE" in compact
        assert "FULL_MODEL_PRODUCTION_READY=FALSE" in compact
        assert "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in text
        assert "ACTIVE_PARAMETERS=0" in compact
