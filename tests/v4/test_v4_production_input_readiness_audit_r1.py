from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_production_input_readiness_audit_r1.yaml"
REPORT = ROOT / "docs/v4/reports/v4_production_input_readiness_audit_r1.md"
ADR = ROOT / "docs/v4/adr/ADR-048-v4-production-input-readiness-audit-r1.md"


def load_governance() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_audit_is_control_plane_only_and_anchored_to_clean_pr44_merge() -> None:
    data = load_governance()
    assert data["stage"] == "V4_PRODUCTION_INPUT_READINESS_AUDIT_R1"
    assert data["status"] == "AUDIT_COMPLETE_AWAITING_EXACT_HEAD_GATE"
    assert data["base_main_sha"] == "7800176751050c678ccfe24b04c5c263ec6c27bb"

    scope = data["review_scope"]
    assert scope["kind"] == "CONTROL_PLANE_AND_INPUT_INVENTORY_ONLY"
    for key in (
        "production_source_changed",
        "solver_equations_changed",
        "numerical_coupling_changed",
        "workflow_changed",
        "parameter_values_changed",
        "parameter_activation",
        "calibration",
        "empirical_validation",
        "physical_accuracy_claim",
        "real_cteas_atmos_binding",
    ):
        assert scope[key] is False

    merge = data["post_review_merge_anchor"]
    assert merge == {
        "pr": 44,
        "merge_sha": "7800176751050c678ccfe24b04c5c263ec6c27bb",
        "merge_tree": "76db5ceec943e568cd1c0be3d4ae2a2ee7808fc6",
        "parent1": "589d23a81fb27509fb8591dac8695971dc14905f",
        "parent2": "e854092cfa2e8cf696e434e2b8b86b72c89ed856",
        "head_to_merge_files_empty": True,
        "no_drift_verified": True,
    }


def test_source_snapshot_is_bound_to_actual_current_runtime_files() -> None:
    snapshot = load_governance()["source_snapshot"]
    expected = {
        "atmos_forcing": "76500c048caac1d9d1bce8a463560adc91d521a0",
        "atmos_exchange_contract": "886d454c8bc3b2ff9c1bff864dae63c76897df25",
        "soil_v4_solver": "18abf2ef1f4c71281f6c609594f736d7735177aa",
        "root_eq39": "dab83798058b635ba1d9d9ec9bbced78fa367277",
        "leaf_resistance": "57b87cf6575c44a35505e317fb8aa4a1141d4ab1",
        "tfwt_state": "aeb5fb9605b89fadf5b1ce1d1580325213b5ca3c",
        "obt_baseline": "ef62228b8b4e41de19f33c137f2e63f621d93270",
        "obt_state": "c1246492e0f9e9a1e2124e4b7392d60a509d37a5",
        "food_transfer": "2061ed157df0b59fff194ad41034b5ae7f3ee7c7",
        "intake": "1c0f6019d733183ba57265a96f41a4fcda909e04",
        "dose": "ca44d6345789b203d3577bd589467121b144bd9e",
        "sensitivity_review": "715db8e31cb69f5bffafe3bbbcd1332175381e63",
    }
    assert set(snapshot) == set(expected)
    for key, blob_sha in expected.items():
        assert snapshot[key]["blob_sha"] == blob_sha
        assert snapshot[key]["path"]


def test_classification_contract_forbids_synthetic_and_implicit_defaults_in_production() -> None:
    contract = load_governance()["classification_contract"]
    assert contract["allowed"] == [
        "CONTROLLED_UFOTRI_BASELINE_OR_PROFILE",
        "PHYSICAL_CONSTANT",
        "EXPLICIT_EXTERNAL_SCENARIO_INPUT",
        "REAL_UPSTREAM_DATA_PREREQUISITE",
        "UNRESOLVED_OR_SYNTHETIC_ONLY",
    ]
    assert "READY_CONTROLLED" in contract["production_required_readiness_states"]
    assert "READY_PROVENANCED_SOURCE" in contract["production_required_readiness_states"]
    assert "DERIVED_FROM_READY_STATE" in contract["production_required_readiness_states"]
    assert "BLOCKED_EXTERNAL" in contract["non_ready_states"]
    assert "SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED" in contract["non_ready_states"]
    assert contract["api_default_is_production_evidence"] is False
    assert contract["synthetic_fixture_is_production_evidence"] is False
    assert contract["replay_fixture_is_live_binding"] is False
    assert contract["silent_zero_allowed"] is False
    assert contract["silent_unit_conversion_allowed"] is False
    assert contract["silent_time_or_space_reconciliation_allowed"] is False


def test_controlled_ufotri_items_stay_selected_without_claiming_caller_inputs_are_ready() -> None:
    data = load_governance()
    controlled = data["controlled_runtime_items"]
    assert controlled["obt_reduced_baseline"]["readiness"] == "READY_CONTROLLED"
    assert controlled["obt_reduced_baseline"]["values"] == {
        "formation_per_hour": 0.0006,
        "loss_per_hour": 0.003,
        "daylight_multiplier": 1.0,
        "nighttime_multiplier": 1.0,
    }
    assert controlled["root_total_uptake_equation"]["mode"] == "EQUILIBRIUM_RADIATION_EQ39"
    assert controlled["root_total_uptake_equation"]["eq38_aerodynamic_term_active"] is False
    assert controlled["root_layer_profile"]["fractions"] == [0.2, 0.4, 0.4]
    assert controlled["operator_split"]["value"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert controlled["harvest_boundary"]["value"] == "KEEP_HARVEST_EVENT"

    root = data["input_registry"]["root_eq39"]
    assert root["net_radiation"]["readiness"] == "SOURCE_REQUIRED"
    assert root["net_radiation"]["inferred_from_cteas_atmos"] is False
    assert root["lai"]["readiness"] == "SOURCE_REQUIRED"
    assert root["maximum_water"]["readiness"] == "SOURCE_REQUIRED"
    assert root["wilting_water"]["readiness"] == "SOURCE_REQUIRED"


def test_real_atmos_packet_remains_fail_closed_on_surface_flux() -> None:
    atmosphere = load_governance()["input_registry"]["atmosphere"]
    assert atmosphere["air_hto_concentration"]["readiness"] == "CONTRACT_READY_SOURCE_NOT_BOUND"
    deposition = atmosphere["surface_deposition_flux"]
    assert deposition["classification"] == "REAL_UPSTREAM_DATA_PREREQUISITE"
    assert deposition["readiness"] == "BLOCKED_EXTERNAL"
    assert deposition["blocker"] == "BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED"
    assert "silent_zero" in deposition["forbidden_substitutes"]
    for field in ("temperature", "relative_humidity", "wind_speed", "precipitation"):
        assert atmosphere[field]["readiness"] == "CONTRACT_READY_SOURCE_NOT_BOUND"


def test_soil_api_zero_defaults_do_not_close_production_forcing_gap() -> None:
    soil = load_governance()["input_registry"]["soil_three_layer"]
    assert soil["initial_layer_water_inventories"]["readiness"] == "SOURCE_REQUIRED"
    assert soil["initial_layer_hto_inventories"]["readiness"] == "SOURCE_REQUIRED"
    unresolved = (
        "surface_water_input",
        "surface_water_loss",
        "l1_l2_water_flux",
        "l1_l2_hto_flux",
        "l2_l3_water_flux",
        "l2_l3_hto_flux",
        "lower_boundary_water_loss",
        "lower_boundary_hto_loss",
        "surface_reemission_hto_loss",
    )
    for field in unresolved:
        assert soil[field]["classification"] == "UNRESOLVED_OR_SYNTHETIC_ONLY"
        assert soil[field]["readiness"] == "SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED"
    assert soil["surface_deposition_flux"]["readiness"] == "BLOCKED_EXTERNAL"
    assert soil["root_water_and_hto_extraction"]["owner"] == "root_v4"
    assert soil["root_water_and_hto_extraction"]["base_soil_root_slots_must_be_zero"] is True


def test_leaf_path_is_connected_but_production_resistance_source_is_not_ready() -> None:
    leaf = load_governance()["input_registry"]["leaf_exchange"]
    for field in ("aerodynamic_resistance", "boundary_layer_resistance", "canopy_resistance"):
        assert leaf[field]["classification"] == "UNRESOLVED_OR_SYNTHETIC_ONLY"
        assert leaf[field]["readiness"] == "PROVISIONAL_SOURCE_REQUIRED"
        assert leaf[field]["canonical_unit"] == "s m^-1"
    assert leaf["production_parameter_database_path_ready"] is False
    assert leaf["current_database_lookup_mode"] == "production_false_only"
    assert leaf["active_parameter_provenance_rejected"] is True
    assert leaf["leaf_r5_required_to_complete_manifest"] is False
    assert leaf["leaf_r5_authorized"] is False


def test_plant_and_endpoint_inputs_remain_provisional_or_source_required() -> None:
    registry = load_governance()["input_registry"]
    plant = registry["plant_state_and_obt"]
    assert plant["initial_tfwt_inventory"]["readiness"] == "SOURCE_REQUIRED"
    assert plant["tfwt_water_content"]["readiness"] == "PROVISIONAL_SOURCE_REQUIRED"
    assert plant["tfwt_water_loss_flux"]["readiness"] == "SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED"
    assert plant["tfwt_transformation_flux"]["readiness"] == "SOURCE_OR_EXPLICIT_ZERO_POLICY_REQUIRED"
    assert plant["initial_obt_inventory"]["readiness"] == "SOURCE_REQUIRED"
    assert plant["obt_plant_mass"]["readiness"] == "PROVISIONAL_SOURCE_REQUIRED"
    assert plant["obt_kf_kr_and_daily_average_multipliers"]["readiness"] == "READY_CONTROLLED"

    endpoint = registry["endpoint"]
    for field in ("harvest_fraction", "harvest_area", "food_product_mass", "annual_consumption_amount", "dose_coefficient"):
        assert endpoint[field]["readiness"] == "PROVISIONAL_SOURCE_REQUIRED"
    assert endpoint["harvest_fraction"]["current_default_parameter_status"] == "provisional"
    assert endpoint["tfwt_harvest_fraction"]["required"] is False
    assert endpoint["tfwt_harvest_fraction"]["if_omitted_semantics"] == "TFWT_TRANSFER_ZERO_BY_EXPLICIT_ENDPOINT_MODEL"


def test_sensitivity_is_used_only_as_software_propagation_context() -> None:
    sensitivity = load_governance()["prior_sensitivity_context"]
    assert sensitivity["status"] == "PASS_SOFTWARE_SCREENING"
    assert sensitivity["physical_importance_ranking"] == "NOT_AVAILABLE"
    assert sensitivity["selected_local_computational_elasticities"] == {
        "food_tfwt_harvest_fraction": 0.844289,
        "atmos_air_hto_concentration": 0.670850,
        "leaf_total_resistance": -0.559056,
        "atmos_surface_deposition_flux": 0.139315,
    }
    assert sensitivity["interpretation"] == "SOFTWARE_PROPAGATION_ONLY_DO_NOT_USE_AS_EMPIRICAL_OR_PHYSICAL_RANKING"


def test_next_stage_is_fail_closed_case_manifest_not_new_physics() -> None:
    data = load_governance()
    summary = data["readiness_summary"]
    assert summary["software_chain_connected_with_controlled_ufotri_profiles"] is True
    assert summary["root_q_w_controlled_equation_and_profile_resolved"] is True
    assert summary["production_input_packet_ready"] is False
    assert summary["complete_real_atmos_packet_ready"] is False
    assert summary["soil_dynamic_forcing_source_ready"] is False
    assert summary["leaf_resistance_production_source_ready"] is False
    assert summary["plant_state_source_packet_ready"] is False
    assert summary["endpoint_parameter_source_packet_ready"] is False
    assert summary["full_model_production_ready"] is False

    ranking = data["blocker_ranking"]
    assert ranking[0]["candidate"] == "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1"
    assert ranking[0]["disposition"] == "SELECT_NEXT_CONTROL_PLANE_STAGE"
    assert ranking[1]["candidate"] == "REAL_CTEAS_ATMOS_BINDING"
    assert ranking[1]["disposition"] == "HOLD_EXTERNAL_PREREQUISITE_SURFACE_FLUX_UNCONFIRMED"

    next_stage = data["next_stage"]
    assert next_stage["selected"] == "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1"
    assert next_stage["scope"] == "CONTROL_PLANE_SCHEMA_AND_FAIL_CLOSED_COMPLETENESS_GATE_ONLY"
    for key in (
        "production_values_may_be_activated",
        "parameter_fitting_authorized",
        "solver_changes_authorized",
        "numerical_coupling_changes_authorized",
        "real_cteas_atmos_binding_authorized",
        "leaf_r5_authorized",
        "full_hydrology_authorized",
        "multi_pool_obt_authorized",
    ):
        assert next_stage[key] is False

    fail = data["manifest_fail_closed_rules"]
    assert set(fail.values()) == {"FAIL"}
    assert fail["implicit_default_zero"] == "FAIL"
    assert fail["required_real_upstream_product_unbound"] == "FAIL"


def test_hard_boundaries_and_artifact_messages_remain_fail_closed() -> None:
    data = load_governance()
    hard = data["hard_boundaries"]
    assert hard["v3_default_path_changed"] is False
    assert hard["active_parameters"] == 0
    for key in (
        "calibration_started",
        "empirical_validation",
        "physical_accuracy_claim",
        "full_model_production_ready",
        "real_cteas_atmos_binding",
        "leaf_r5",
        "full_hydrology",
        "full_penman_eq38_production_active",
        "ufotri_reference_layer_rates_active",
        "short_term_3h_delay_active",
        "multi_pool_obt",
    ):
        assert hard[key] is False

    exit_state = data["exit_state_if_exact_head_and_merge_clean"]
    assert exit_state == {
        "audit_complete": True,
        "production_input_packet_ready": False,
        "software_chain_connected_with_controlled_ufotri_profiles": True,
        "full_model_production_ready": False,
        "next_stage": "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1",
    }

    for artifact in (REPORT, ADR):
        text = artifact.read_text(encoding="utf-8")
        compact = text.replace(" ", "")
        assert "V4_PRODUCTION_CASE_INPUT_MANIFEST_R1" in text
        assert "PRODUCTION_INPUT_PACKET_READY=FALSE" in compact
        assert "FULL_MODEL_PRODUCTION_READY=FALSE" in compact
        assert "REAL_CTEAS_ATMOS_BINDING=FALSE" in compact
        assert "Leaf R5" in text or "LEAF_R5" in text
        assert "full hydrology" in text.lower() or "FULL_HYDROLOGY" in text
