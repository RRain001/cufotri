from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOV_PATH = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r4.yaml"
MANIFEST_PATH = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"
ASSUMPTIONS_PATH = ROOT / "docs/assumptions.md"
ERA5_AUDIT_PATH = ROOT / "docs/era5_data_audit.md"
ERA5_CATALOGUE_PATH = ROOT / "era5/era5_catalogue.py"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_r4_selection_fails_closed_without_independent_production_case():
    gov = _load(GOV_PATH)
    assert gov["stage"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R4"
    assert gov["scope"]["kind"] == "PRODUCTION_CASE_IDENTITY_AND_EQ39_PRESSURE_SOURCE_SELECTION_ONLY"
    outcome = gov["selection_outcome"]
    assert outcome["token"] == "BLOCKED_PRODUCTION_CASE_IDENTITY_NOT_INDEPENDENTLY_DECLARED"
    assert outcome["production_case_identity_bound"] is False
    assert outcome["production_pressure_source_selected"] is False
    assert outcome["production_site_elevation_source_selected"] is False
    assert outcome["production_psychrometric_constant_available"] is False
    assert outcome["eq39_production_input_ready"] is False


def test_r4_historical_hefei_coordinate_is_test_context_not_production_binding():
    gov = _load(GOV_PATH)
    evidence = gov["historical_repository_evidence"]
    requested = evidence["era5_requested_test_point"]
    assert requested["longitude_deg_e"] == 117.141610855
    assert requested["latitude_deg_n"] == 31.939774444
    assert requested["disposition"] == "HISTORICAL_TEST_CONTEXT_NOT_PRODUCTION_BINDING"
    nearest = evidence["era5_returned_nearest_grid_point"]
    assert nearest["longitude_deg_e"] == 117.25
    assert nearest["latitude_deg_n"] == 32.0
    assert nearest["disposition"] == "METEOROLOGICAL_TEST_GRID_POINT_NOT_SITE_IDENTITY"
    assert evidence["software_label"]["disposition"] == "SOFTWARE_REQUEST_LABEL_NOT_PRODUCTION_DECLARATION"

    assumptions = ASSUMPTIONS_PATH.read_text(encoding="utf-8")
    assumptions_one_line = " ".join(assumptions.split())
    audit = ERA5_AUDIT_PATH.read_text(encoding="utf-8")
    catalogue = ERA5_CATALOGUE_PATH.read_text(encoding="utf-8")
    assert "not site claims" in assumptions
    assert "rather than claims about the Hefei receptor or a specific agricultural survey." in assumptions_one_line
    assert "117.141610855 E, 31.939774444 N" in audit
    assert "117.25 E, 32.00 N" in audit
    assert "Hefei-H3-ERA5/1.0" in catalogue


def test_r4_historical_era5_audit_does_not_supply_surface_pressure():
    gov = _load(GOV_PATH)
    pressure = gov["pressure_source_audit"]
    assert pressure["historical_era5_mapped_variables"] == [
        "t2m", "d2m", "u10", "v10", "tp", "ssrd", "strd"
    ]
    assert pressure["surface_pressure_documented_in_historical_audit"] is False
    assert pressure["selected_case_mean_atmospheric_pressure_source"] is None
    assert pressure["explicit_pressure_path_ready"] is False
    audit = ERA5_AUDIT_PATH.read_text(encoding="utf-8")
    for field in ("`t2m`", "`d2m`", "`u10`,`v10`", "`tp`", "`ssrd`", "`strd`"):
        assert field in audit


def test_r4_no_site_elevation_or_gamma_is_selected():
    gov = _load(GOV_PATH)
    elevation = gov["site_elevation_source_audit"]
    assert elevation["independently_sourced_site_elevation_m_msl_found"] is False
    assert elevation["selected_site_elevation_m_msl_source"] is None
    assert elevation["elevation_derived_pressure_path_ready"] is False
    selection = gov["psychrometric_selection"]
    assert selection["r3_policy"] == "FAO56_CASE_PRESSURE_DERIVED"
    assert selection["selected_pressure_source_kind"] is None
    assert selection["selected_pressure_kpa"] is None
    assert selection["selected_site_elevation_m_msl"] is None
    assert selection["selected_gamma_pa_k"] is None
    assert selection["source_selection_authorized_without_case_declaration"] is False


def test_r4_freezes_minimum_case_identity_binding_packet():
    gov = _load(GOV_PATH)
    packet = gov["production_case_identity_binding_packet"]
    assert packet["contract_id"] == "PRODUCTION_CASE_IDENTITY_BINDING_PACKET_R1"
    assert packet["required_fields"] == [
        "case_id",
        "scenario_id",
        "facility_or_site_id",
        "site_location_id",
        "site_latitude_deg",
        "site_longitude_deg",
        "horizontal_crs_or_datum",
        "production_time_start_utc",
        "production_time_end_utc",
        "operational_mode_or_release_case",
        "declaration_source_id",
        "declaration_source_revision",
        "declaration_provenance_note",
    ]
    rules = packet["rules"]
    assert rules["positive_time_interval_required"] is True
    assert rules["historical_test_coordinate_may_be_silently_promoted"] is False
    assert rules["era5_nearest_grid_may_be_silently_promoted"] is False
    assert rules["receptor_coordinate_may_be_silently_promoted"] is False
    assert rules["explicit_spatial_reconciliation_required_when_different"] is True
    assert rules["missing_declaration_fields_may_be_inferred_from_test_artifacts"] is False


def test_r4_does_not_mutate_template_manifest_or_hard_boundaries():
    gov = _load(GOV_PATH)
    manifest = _load(MANIFEST_PATH)
    assert manifest["case_identity"]["case_id"] == "TEMPLATE_NOT_PRODUCTION"
    assert manifest["case_identity"]["scenario_id"] == "UNSET"
    for key in (
        "manifest_changed",
        "src_changed",
        "solver_equations_changed",
        "numerical_coupling_changed",
        "workflow_changed",
        "runtime_parameter_import_changed",
        "calibration_changed",
    ):
        assert gov["scope"][key] is False
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


def test_r4_next_stage_is_declaration_intake_only():
    gov = _load(GOV_PATH)
    nxt = gov["next_stage_if_clean_merge"]
    assert nxt["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R5"
    assert nxt["focus"] == "INDEPENDENT_PRODUCTION_CASE_DECLARATION_INTAKE_ONLY"
    assert nxt["historical_test_inference_authorized"] is False
    assert nxt["manifest_projection_authorized"] is False
    assert nxt["solver_change_authorized"] is False
    assert nxt["runtime_activation_authorized"] is False
    assert nxt["production_activation_authorized"] is False
