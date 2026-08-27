from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOV_PATH = ROOT / "docs/v4/governance/v4_production_case_input_source_resolution_r5.yaml"
MANIFEST_PATH = ROOT / "docs/v4/contracts/v4_production_case_input_manifest_r1.yaml"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_r5_is_independent_declaration_intake_only():
    gov = _load(GOV_PATH)
    assert gov["stage"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R5"
    assert gov["scope"]["kind"] == "INDEPENDENT_PRODUCTION_CASE_DECLARATION_INTAKE_ONLY"
    assert gov["status"] == "DECLARATION_NOT_RECEIVED_FAIL_CLOSED_AWAITING_EXACT_HEAD_GATE"
    for key in (
        "manifest_changed",
        "src_changed",
        "solver_equations_changed",
        "numerical_coupling_changed",
        "workflow_changed",
        "runtime_parameter_import_changed",
        "calibration_changed",
        "pressure_source_selected",
        "site_elevation_source_selected",
        "gamma_computed",
    ):
        assert gov["scope"][key] is False


def test_r5_preserves_r4_thirteen_field_binding_packet():
    gov = _load(GOV_PATH)
    intake = gov["declaration_intake"]
    expected = [
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
    assert intake["contract_id"] == "PRODUCTION_CASE_IDENTITY_DECLARATION_INTAKE_R1"
    assert intake["required_fields"] == expected
    assert list(intake["declared_fields"].keys()) == expected
    assert all(value is None for value in intake["declared_fields"].values())


def test_r5_current_state_is_not_received_and_unvalidated():
    gov = _load(GOV_PATH)
    intake = gov["declaration_intake"]
    validation = gov["validation"]
    assert intake["receipt_state"] == "NOT_RECEIVED"
    assert intake["artifact_identity"] is None
    assert intake["artifact_revision"] is None
    assert intake["artifact_sha256"] is None
    assert validation["performed"] is False
    assert validation["declaration_complete"] is False
    assert validation["declaration_accepted"] is False
    assert validation["blocking_reason"] == "DECLARATION_NOT_RECEIVED"
    assert validation["missing_fields"] == intake["required_fields"]
    assert validation["inference_from_test_context_used"] is False


def test_r5_forbids_historical_or_implicit_field_filling():
    gov = _load(GOV_PATH)
    rules = gov["intake_rules"]
    assert rules["independent_declaration_required"] is True
    assert rules["all_required_fields_must_be_explicit"] is True
    assert rules["positive_time_interval_required"] is True
    assert rules["horizontal_crs_or_datum_must_be_explicit"] is True
    assert rules["declaration_source_revision_required"] is True
    assert rules["declaration_provenance_note_required"] is True
    for key in (
        "historical_test_coordinate_may_fill_missing_field",
        "era5_nearest_grid_may_fill_missing_field",
        "software_label_may_fill_missing_field",
        "synthetic_configuration_may_fill_missing_field",
        "conversational_background_without_controlled_declaration_may_fill_missing_field",
        "missing_field_inference_allowed",
    ):
        assert rules[key] is False


def test_r5_state_machine_does_not_activate_production():
    gov = _load(GOV_PATH)
    state = gov["state_machine"]
    assert state["current_token"] == "DECLARATION_NOT_RECEIVED"
    assert state["on_independent_artifact_receipt"] == "DECLARATION_RECEIVED_UNVALIDATED"
    assert state["on_complete_valid_declaration"] == "DECLARATION_ACCEPTED_FOR_SOURCE_RESOLUTION"
    assert state["on_missing_required_field"] == "DECLARATION_REJECTED_INCOMPLETE"
    assert state["on_identity_time_or_datum_ambiguity"] == "DECLARATION_REJECTED_AMBIGUOUS"
    for key in (
        "acceptance_binds_production_manifest",
        "acceptance_selects_pressure_source",
        "acceptance_selects_site_elevation_source",
        "acceptance_computes_gamma",
        "acceptance_authorizes_runtime_activation",
        "acceptance_authorizes_production_activation",
    ):
        assert state[key] is False


def test_r5_keeps_manifest_template_and_eq39_sources_unbound():
    gov = _load(GOV_PATH)
    manifest = _load(MANIFEST_PATH)
    assert manifest["case_identity"]["case_id"] == "TEMPLATE_NOT_PRODUCTION"
    assert manifest["case_identity"]["scenario_id"] == "UNSET"
    assert gov["manifest_snapshot"]["projection_performed"] is False
    current = gov["current_outcome"]
    assert current["token"] == "DECLARATION_NOT_RECEIVED_FAIL_CLOSED"
    assert current["production_case_identity_bound"] is False
    assert current["production_pressure_source_selected"] is False
    assert current["production_site_elevation_source_selected"] is False
    assert current["production_psychrometric_constant_available"] is False
    assert current["eq39_production_input_ready"] is False
    pressure = gov["pressure_elevation_snapshot"]
    assert pressure["r3_contract_id"] == "EQ39_PRESSURE_SITE_ELEVATION_PROVENANCE_CONTRACT_R1"
    assert pressure["selected_pressure_source_kind"] is None
    assert pressure["selected_pressure_kpa"] is None
    assert pressure["selected_site_elevation_m_msl_source"] is None
    assert pressure["selected_site_elevation_m_msl"] is None
    assert pressure["selected_gamma_pa_k"] is None


def test_r5_preserves_all_hard_boundaries():
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
    atmos = gov["atmos_surface_flux_blocker"]
    assert atmos["token"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert atmos["surrogate_or_zero_substitution_authorized"] is False


def test_r5_r6_handoff_is_conditional_on_accepted_declaration():
    gov = _load(GOV_PATH)
    nxt = gov["conditional_next_stage"]
    assert nxt["prerequisite"] == "DECLARATION_ACCEPTED_FOR_SOURCE_RESOLUTION"
    assert nxt["selected"] == "V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R6"
    assert nxt["focus"] == "PRODUCTION_CASE_IDENTITY_BINDING_AND_EQ39_CASE_SOURCE_RESOLUTION_ONLY"
    assert nxt["manifest_projection_authorized_by_r5"] is False
    assert nxt["solver_change_authorized"] is False
    assert nxt["runtime_activation_authorized"] is False
    assert nxt["production_activation_authorized"] is False
    assert gov["current_next_action"]["token"] == "AWAIT_INDEPENDENT_PRODUCTION_CASE_DECLARATION"
    assert gov["current_next_action"]["create_r6_before_accepted_declaration"] is False
