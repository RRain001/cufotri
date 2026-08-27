from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r1.yaml"
R2 = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r2.yaml"
MANIFEST = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-051-v4-production-case-input-source-resolution-r2.md"
REPORT = ROOT / "docs/v4/reports/v4_production_case_input_source_resolution_r2.md"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def manifest_record(quantity_id: str) -> dict:
    manifest = load_yaml(MANIFEST)
    return next(item for item in manifest["inputs"] if item["quantity_id"] == quantity_id)


def test_r2_scope_is_eq39_source_policy_only() -> None:
    data = load_yaml(R2)
    assert data["stage"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R2"
    assert data["status"] == "PASS_EQ39_PHYSICAL_PROPERTY_SOURCE_POLICY_DECISION_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "62ee5f4e83ae251fc869cb688d3d63096e9641cb"
    scope = data["scope"]
    assert scope["kind"] == "EQ39_PHYSICAL_PROPERTY_SOURCE_POLICY_DECISION_ONLY"
    assert scope["manifest_changed"] is False
    assert scope["src_changed"] is False
    assert scope["solver_equations_changed"] is False
    assert scope["numerical_coupling_changed"] is False
    assert scope["workflow_changed"] is False
    assert scope["runtime_parameter_import_changed"] is False
    assert scope["calibration_changed"] is False


def test_r2_only_resolves_the_three_r1_condition_dependent_properties() -> None:
    r1 = load_yaml(R1)
    r2 = load_yaml(R2)
    r1_props = set(
        r1["resolution_registry"]["CONDITION_DEPENDENT_PHYSICAL_PROPERTY_SOURCE_REQUIRED"]
    )
    r2_props = set(r2["properties"])
    assert r1_props == r2_props == {
        "root_eq39.latent_heat",
        "root_eq39.water_density",
        "root_eq39.psychrometric_constant",
    }


def test_latent_heat_is_fao56_model_convention_not_universal_constant() -> None:
    data = load_yaml(R2)["properties"]["root_eq39.latent_heat"]
    assert data["disposition"] == "SOURCE_POLICY_RESOLVED_MODEL_CONVENTION_NOT_ACTIVATED"
    assert data["source_role"] == "MODEL_CONVENTION_NOT_UNIVERSAL_CONSTANT"
    assert data["selected_policy"] == "FAO56_REFERENCE_ET_FIXED_CONVENTION"
    assert data["selected_value"] == 2450000.0
    assert data["unit"] == "J kg^-1"
    assert data["authority"]["organization"] == "FAO"
    assert data["authority"]["url"].startswith("https://www.fao.org/")
    applicability = data["applicability"]
    assert applicability["selected_eq39_reference_policy_only"] is True
    assert applicability["fao_reference_air_temperature_approx_c"] == 20.0
    assert applicability["temperature_dependence_acknowledged"] is True
    assert applicability["universal_exact_property_claim"] is False
    assert data["implementation"]["temperature_dependent_lambda_authorized"] is False
    assert data["implementation"]["production_use_authorized"] is False
    assert data["implementation"]["runtime_activation_authorized"] is False


def test_water_density_is_reference_conversion_convention_not_exact_density_claim() -> None:
    data = load_yaml(R2)["properties"]["root_eq39.water_density"]
    assert data["disposition"] == "SOURCE_POLICY_RESOLVED_MODEL_CONVENTION_NOT_ACTIVATED"
    assert data["source_role"] == "WATER_DEPTH_CONVERSION_MODEL_CONVENTION_NOT_UNIVERSAL_CONSTANT"
    assert data["selected_policy"] == "REFERENCE_WATER_DEPTH_CONVERSION_CONVENTION"
    assert data["selected_value"] == 1000.0
    assert data["unit"] == "kg m^-3"
    boundary = data["physical_property_boundary_authority"]
    assert boundary["organization"] == "IAPWS"
    assert "IAPWS-95" in boundary["work"]
    assert boundary["url"].startswith("https://www.iapws.org/")
    implementation = data["implementation"]
    assert implementation["iapws_runtime_solver_authorized"] is False
    assert implementation["state_dependent_density_authorized"] is False
    assert implementation["production_use_authorized"] is False
    assert implementation["runtime_activation_authorized"] is False


def test_psychrometric_constant_is_case_pressure_derived_and_fail_closed() -> None:
    data = load_yaml(R2)["properties"]["root_eq39.psychrometric_constant"]
    assert data["disposition"] == "DERIVATION_POLICY_RESOLVED_CASE_VALUE_NOT_BOUND"
    assert data["source_role"] == "CASE_PRESSURE_DERIVED_PROPERTY"
    assert data["selected_policy"] == "FAO56_CASE_PRESSURE_DERIVED"
    assert data["selected_value"] is None
    assert data["unit"] == "Pa K^-1"
    assert data["authority"]["organization"] == "FAO"
    derivation = data["derivation"]
    assert derivation["gamma_kpa_per_k_from_pressure_kpa"]["coefficient"] == 0.000665
    assert derivation["gamma_pa_per_k_from_pressure_kpa"]["coefficient"] == 0.665
    assert derivation["pressure_source_precedence"] == [
        "EXPLICIT_CASE_MEAN_ATMOSPHERIC_PRESSURE_WITH_PROVENANCE",
        "FAO56_PRESSURE_DERIVED_FROM_EXPLICIT_SITE_ELEVATION_WITH_PROVENANCE",
    ]
    assert derivation["elevation_fallback_formula"]["source_elevation_required"] is True
    assert derivation["elevation_fallback_formula"]["z_semantics"] == "site elevation above mean sea level"
    assert derivation["explicit_case_pressure_required_if_no_elevation_source"] is True
    assert derivation["sea_level_pressure_default_allowed"] is False
    assert derivation["zero_elevation_default_allowed"] is False
    assert derivation["fixed_gamma_66_pa_k_allowed"] is False
    assert data["implementation"]["pressure_or_elevation_source_bound"] is False
    assert data["implementation"]["production_use_authorized"] is False


def test_r2_does_not_silently_promote_manifest_records_to_ready() -> None:
    for quantity_id in (
        "root_eq39.latent_heat",
        "root_eq39.water_density",
        "root_eq39.psychrometric_constant",
    ):
        record = manifest_record(quantity_id)
        assert record["readiness"] == "SOURCE_REQUIRED"
        assert record["source"] is None
        assert record["production_use_authorized"] is False


def test_r2_rejects_test_value_and_silent_pressure_fallback_paths() -> None:
    data = load_yaml(R2)
    rejected = data["rejected_alternatives"]
    assert rejected["FIX_ALL_THREE_TO_SYNTHETIC_TEST_VALUES"]["selected"] is False
    assert rejected["IAPWS_RUNTIME_PROPERTY_SOLVER"]["selected"] is False
    assert rejected["FIX_GAMMA_66_PA_K"]["selected"] is False
    assert rejected["SEA_LEVEL_PRESSURE_FALLBACK"]["selected"] is False
    after = data["source_resolution_after_r2"]
    assert after["latent_heat_source_policy_resolved"] is True
    assert after["water_density_source_policy_resolved"] is True
    assert after["psychrometric_source_policy_resolved"] is True
    assert after["psychrometric_case_value_available"] is False
    assert after["all_three_runtime_ready"] is False
    assert after["eq39_production_input_ready"] is False


def test_atmos_blocker_and_hard_boundaries_remain_frozen() -> None:
    data = load_yaml(R2)
    blocker = data["atmos_surface_flux_blocker"]
    assert blocker["token"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert blocker["atmosphere_surface_deposition_flux_ready"] is False
    assert blocker["soil_surface_deposition_flux_ready"] is False
    assert blocker["surrogate_or_zero_substitution_authorized"] is False
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


def test_r2_freezes_only_pressure_source_contract_as_next_stage() -> None:
    data = load_yaml(R2)
    next_stage = data["next_stage_if_clean_merge"]
    assert next_stage["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3"
    assert next_stage["focus"] == "EQ39_CASE_PRESSURE_AND_SITE_ELEVATION_SOURCE_CONTRACT_ONLY"
    assert next_stage["manifest_projection_authorized"] is False
    assert next_stage["solver_change_authorized"] is False
    assert next_stage["production_activation_authorized"] is False
    for path in (ADR, REPORT):
        text = path.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        assert "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3" in text
        assert "PRODUCTION_INPUT_PACKET_READY=FALSE" in compact
        assert "FULL_MODEL_PRODUCTION_READY=FALSE" in compact
        assert "ACTIVE_PARAMETERS=0" in compact
        assert "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED" in text
