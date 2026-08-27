from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
SCHEMA = ROOT / "schemas/v4/v4_production_case_input_manifest.schema.json"
AUDIT = ROOT / "docs/v4/governance/v4_production_input_readiness_audit_r1.yaml"
GOVERNANCE = ROOT / "docs/v4/governance/v4_production_case_input_manifest_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_production_case_input_manifest_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-049-v4-production-case-input-manifest-r1.md"
VALIDATOR = ROOT / "scripts/v4/validate_production_case_input_manifest_r1.py"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_validator_module():
    spec = importlib.util.spec_from_file_location("v4_manifest_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_records() -> dict[str, dict]:
    audit = load_yaml(AUDIT)
    result = {}
    for domain, block in audit["input_registry"].items():
        for name, record in block.items():
            if isinstance(record, dict) and "classification" in record and "readiness" in record:
                result[f"{domain}.{name}"] = record
    return result


def test_manifest_schema_is_valid_but_does_not_claim_production_readiness() -> None:
    manifest = load_yaml(MANIFEST)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(manifest)
    assert manifest["stage"] == "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1"
    assert manifest["case_identity"]["mode"] == "TEMPLATE_FAIL_CLOSED"
    assert manifest["production_claim"] is False


def test_manifest_inventory_exactly_covers_the_frozen_audit_registry() -> None:
    manifest = load_yaml(MANIFEST)
    authority = audit_records()
    entries = manifest["inputs"]
    ids = [entry["quantity_id"] for entry in entries]
    assert len(ids) == 49
    assert len(set(ids)) == 49
    assert set(ids) == set(authority)
    assert sum(entry["required"] for entry in entries) == 48
    assert sum(not entry["required"] for entry in entries) == 1
    by_id = {entry["quantity_id"]: entry for entry in entries}
    for qid, frozen in authority.items():
        entry = by_id[qid]
        assert entry["required"] is bool(frozen.get("required", False))
        assert entry["classification"] == frozen["classification"]
        if frozen.get("canonical_unit") is not None:
            assert entry["canonical_unit"] == frozen["canonical_unit"]


def test_checked_in_template_fails_closed_for_real_production() -> None:
    validator = load_validator_module()
    result = validator.evaluate(load_yaml(MANIFEST))
    assert result["schema_valid"] is True
    assert result["inventory_complete"] is True
    assert result["production_complete"] is False
    assert result["status"] == "FAIL_CLOSED_INCOMPLETE"
    assert result["required_input_count"] == 48
    assert result["manifest_input_count"] == 49
    issues = result["issues"]
    assert any(issue == "non_ready_state:atmosphere.surface_deposition_flux:BLOCKED_EXTERNAL" for issue in issues)
    assert "case_mode_not_production_candidate" in issues
    assert "production_claim_false" in issues


def test_surface_deposition_and_silent_zero_remain_fail_closed() -> None:
    manifest = load_yaml(MANIFEST)
    by_id = {entry["quantity_id"]: entry for entry in manifest["inputs"]}
    deposition = by_id["atmosphere.surface_deposition_flux"]
    assert deposition["readiness"] == "BLOCKED_EXTERNAL"
    assert deposition["source"] is None
    assert deposition["production_use_authorized"] is False
    assert deposition["explicit_zero"]["declared"] is False

    audit = load_yaml(AUDIT)
    contract = audit["classification_contract"]
    assert contract["api_default_is_production_evidence"] is False
    assert contract["silent_zero_allowed"] is False
    assert contract["silent_unit_conversion_allowed"] is False
    assert contract["silent_time_or_space_reconciliation_allowed"] is False


def test_controlled_profiles_are_preserved_without_activating_new_physics() -> None:
    manifest = load_yaml(MANIFEST)
    profiles = {item["profile_id"] for item in manifest["controlled_profiles"]}
    assert profiles == {
        "obt_reduced_ufotri_kf_kr_daily_average",
        "root_total_uptake_eq39_equilibrium_radiation",
        "root_layer_distribution_20_40_40",
        "operator_split_preserve_v3_post_obt_root_gain",
        "harvest_boundary_keep_harvest_event",
    }
    controlled_obt = next(
        entry for entry in manifest["inputs"]
        if entry["quantity_id"] == "plant_state_and_obt.obt_kf_kr_and_daily_average_multipliers"
    )
    assert controlled_obt["readiness"] == "READY_CONTROLLED"
    assert controlled_obt["production_use_authorized"] is True


def test_missing_required_input_cannot_be_schema_validated_into_production_completeness() -> None:
    validator = load_validator_module()
    manifest = load_yaml(MANIFEST)
    manifest["inputs"] = [
        entry for entry in manifest["inputs"]
        if entry["quantity_id"] != "root_eq39.net_radiation"
    ]
    result = validator.evaluate(manifest)
    assert result["schema_valid"] is True
    assert result["inventory_complete"] is False
    assert result["production_complete"] is False
    assert "missing_inventory:root_eq39.net_radiation" in result["issues"]


def test_declared_zero_without_evidence_is_rejected() -> None:
    validator = load_validator_module()
    manifest = load_yaml(MANIFEST)
    manifest["case_identity"]["mode"] = "PRODUCTION_CANDIDATE"
    manifest["production_claim"] = True
    target = next(
        entry for entry in manifest["inputs"]
        if entry["quantity_id"] == "soil_three_layer.surface_water_input"
    )
    target["readiness"] = "READY_PROVENANCED_SOURCE"
    target["production_use_authorized"] = True
    target["source"] = {"artifact": "case/source.yaml", "revision": "r1", "dataset_id": "ZERO_POLICY"}
    target["missing_data_policy"] = "FAIL_CLOSED"
    target["explicit_zero"] = {
        "declared": True,
        "evidence_artifact": None,
        "evidence_revision": None,
        "rationale": None,
    }
    result = validator.evaluate(manifest)
    assert result["production_complete"] is False
    assert "unevidenced_explicit_zero:soil_three_layer.surface_water_input" in result["issues"]


def test_governance_keeps_manifest_stage_control_plane_only() -> None:
    data = load_yaml(GOVERNANCE)
    assert data["stage"] == "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1"
    assert data["status"] == "MANIFEST_CONTRACT_COMPLETE_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "211cfe6799e8a4285466c6836fc849a701eff8bb"
    scope = data["scope"]
    assert scope["kind"] == "CASE_MANIFEST_SCHEMA_AND_COMPLETENESS_GATE_ONLY"
    assert scope["production_source_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["workflow_changed"] is False
    assert scope["production_values_added"] is False
    hard = data["hard_boundaries"]
    assert hard["production_input_packet_ready"] is False
    assert hard["full_model_production_ready"] is False
    assert hard["active_parameters"] == 0
    assert hard["calibration_started"] is False
    assert hard["empirical_validation"] is False
    assert hard["physical_accuracy_claim"] is False
    assert hard["real_cteas_atmos_binding"] is False
    assert hard["leaf_r5"] is False
    assert hard["full_hydrology"] is False
    assert hard["multi_pool_obt"] is False
    assert data["next_stage_if_clean_merge"]["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1"


def test_report_and_adr_do_not_overclaim_readiness() -> None:
    for path in (REPORT, ADR):
        text = path.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        assert "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1" in text
        assert "PRODUCTION_INPUT_PACKET_READY=FALSE" in compact
        assert "FULL_MODEL_PRODUCTION_READY=FALSE" in compact
        assert "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in text
