from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOV_PATH = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r3.yaml"
MANIFEST_PATH = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
ATMOS_PATH = ROOT / "docs/v4/contracts/v4_system_atmos_exchange_contract.yaml"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _manifest_input(manifest: dict, quantity_id: str) -> dict:
    return next(item for item in manifest["inputs"] if item["quantity_id"] == quantity_id)


def test_r3_scope_is_contract_only_and_no_activation():
    gov = _load(GOV_PATH)
    assert gov["stage"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R3"
    assert gov["scope"]["kind"] == "EQ39_CASE_PRESSURE_AND_SITE_ELEVATION_SOURCE_CONTRACT_ONLY"
    for key in (
        "manifest_changed",
        "src_changed",
        "solver_equations_changed",
        "numerical_coupling_changed",
        "workflow_changed",
        "runtime_parameter_import_changed",
        "production_case_value_bound",
        "calibration_changed",
    ):
        assert gov["scope"][key] is False
    selected = gov["selected_contract"]
    assert selected["contract_id"] == "EQ39_PRESSURE_SITE_ELEVATION_PROVENANCE_CONTRACT_R1"
    assert selected["psychrometric_policy"] == "FAO56_CASE_PRESSURE_DERIVED"
    assert selected["production_case_identity_bound"] is False
    assert selected["production_pressure_bound"] is False
    assert selected["production_elevation_bound"] is False
    assert selected["production_gamma_bound"] is False
    assert selected["production_use_authorized"] is False
    assert selected["runtime_activation_authorized"] is False


def test_r3_explicit_pressure_precedence_and_fail_closed_defaults():
    gov = _load(GOV_PATH)
    assert gov["source_precedence"] == [
        "EXPLICIT_CASE_MEAN_ATMOSPHERIC_PRESSURE_WITH_PROVENANCE",
        "FAO56_PRESSURE_DERIVED_FROM_EXPLICIT_SITE_ELEVATION_WITH_PROVENANCE",
    ]
    pressure = gov["explicit_pressure_contract"]
    assert pressure["field_id"] == "case_mean_atmospheric_pressure_kpa"
    assert pressure["canonical_unit"] == "kPa"
    assert pressure["case_mean_rule"]["aggregation_must_be_explicit"] is True
    assert pressure["case_mean_rule"]["production_case_temporal_support_required"] is True
    assert pressure["case_mean_rule"]["silent_resampling_allowed"] is False
    assert pressure["case_mean_rule"]["silent_fill_allowed"] is False
    assert pressure["case_mean_rule"]["silent_unit_conversion_allowed"] is False
    assert pressure["forbidden_defaults"]["sea_level_pressure_101_3_kpa"] is True
    assert pressure["forbidden_defaults"]["fixed_gamma_66_pa_k"] is True
    assert "SEA_LEVEL_PRESSURE" in pressure["accepted_source_identity_must_not_be"]
    assert "SYNTHETIC_TEST_CONSTANT" in pressure["accepted_source_identity_must_not_be"]


def test_r3_site_elevation_is_not_receptor_or_sampling_height():
    gov = _load(GOV_PATH)
    elevation = gov["site_elevation_contract"]
    assert elevation["field_id"] == "site_elevation_m_msl"
    assert elevation["canonical_unit"] == "m"
    forbidden = set(elevation["forbidden_substitutes"])
    assert "ATMOS_AIR_SAMPLING_HEIGHT" in forbidden
    assert "RECEPTOR_HEIGHT_ABOVE_LOCAL_GROUND" in forbidden
    assert "STACK_HEIGHT" in forbidden
    assert "TERRAIN_FOLLOWING_MODEL_LEVEL" in forbidden
    assert "PRESSURE_LEVEL_ALTITUDE" in forbidden
    assert "ELLIPSOIDAL_HEIGHT_WITHOUT_GEOID_TRANSFORMATION" in forbidden
    assert elevation["ellipsoidal_height_rule"]["direct_relabel_to_msl_allowed"] is False
    assert elevation["ellipsoidal_height_rule"]["explicit_geoid_or_vertical_datum_transformation_required"] is True
    assert gov["identity_separation"]["atmos_air_sampling_height_is_site_elevation"] is False
    assert gov["identity_separation"]["atmos_vertical_reference_is_site_vertical_datum"] is False
    assert gov["identity_separation"]["explicit_reconciliation_required"] is True


def test_r3_preserves_r2_fao56_derivation_without_fixed_gamma():
    gov = _load(GOV_PATH)
    deriv = gov["fao56_derivation"]
    assert deriv["pressure_from_elevation"]["formula"] == "P_kPa = 101.3 * ((293 - 0.0065*z_m)/293)^5.26"
    assert deriv["pressure_from_elevation"]["z_semantics"] == "site_elevation_m_msl"
    assert deriv["pressure_from_elevation"]["missing_z_default_allowed"] is False
    assert deriv["psychrometric_constant"]["formula"] == "gamma_Pa_per_K = 0.665 * P_kPa"
    assert deriv["psychrometric_constant"]["fixed_66_pa_k_allowed"] is False
    assert gov["dual_source_rule"]["explicit_pressure_has_precedence"] is True
    assert gov["dual_source_rule"]["automatic_blending_allowed"] is False
    assert gov["dual_source_rule"]["automatic_averaging_allowed"] is False


def test_r3_does_not_mutate_template_manifest_or_atmos_height_contract():
    manifest = _load(MANIFEST_PATH)
    atmos = _load(ATMOS_PATH)
    assert manifest["case_identity"]["case_id"] == "TEMPLATE_NOT_PRODUCTION"
    assert manifest["case_identity"]["scenario_id"] == "UNSET"
    for quantity_id in (
        "root_eq39.latent_heat",
        "root_eq39.water_density",
        "root_eq39.psychrometric_constant",
    ):
        item = _manifest_input(manifest, quantity_id)
        assert item["readiness"] == "SOURCE_REQUIRED"
        assert item["source"] is None
        assert item["production_use_authorized"] is False
    spatial = atmos["record_contract"]["spatial_support"]
    assert spatial["air_sampling_height_required"] is True
    assert spatial["vertical_reference_required"] is True
    assert spatial["hidden_height_assumption"] == "FORBIDDEN"


def test_r3_hard_boundaries_and_next_stage_remain_fail_closed():
    gov = _load(GOV_PATH)
    hard = gov["hard_boundaries"]
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
    blocker = gov["atmos_surface_flux_blocker"]
    assert blocker["token"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert blocker["surrogate_or_zero_substitution_authorized"] is False
    nxt = gov["next_stage_if_clean_merge"]
    assert nxt["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4"
    assert nxt["focus"] == "PRODUCTION_CASE_IDENTITY_AND_EQ39_PRESSURE_SOURCE_SELECTION_ONLY"
    assert nxt["manifest_projection_authorized"] is False
    assert nxt["solver_change_authorized"] is False
    assert nxt["runtime_activation_authorized"] is False
    assert nxt["production_activation_authorized"] is False
