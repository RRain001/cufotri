"""V4-2 R4 prospective soybean experiment-design governance invariants."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs/v4/leaf/v4_2_leaf_prospective_experiment_design_r4.yaml"
DATA = ROOT / "docs/v4/leaf/v4_2_leaf_prospective_data_contract_r4.yaml"
REVIEW = ROOT / "docs/v4/reports/v4_2_leaf_prospective_experiment_design_r4_review.md"


def _design() -> dict:
    return yaml.safe_load(DESIGN.read_text(encoding="utf-8"))


def _data() -> dict:
    return yaml.safe_load(DATA.read_text(encoding="utf-8"))


def test_r4_is_design_only_and_not_executed() -> None:
    d = _design()
    assert d["base_main_sha"] == "d6a4bcb7bcdbe6634235cea016b76c39dd9ca664"
    assert d["status"] == "READY_FOR_FEASIBILITY_REVIEW_NOT_EXECUTED"
    inv = d["hard_invariants"]
    assert inv["experiment_executed"] is False
    assert inv["empirical_packet_collected"] is False
    assert inv["leaf_implementation_authorized"] is False
    assert inv["solver_implementation_started"] is False
    assert inv["candidate_parameter_values_admitted"] is False
    assert inv["calibration_started"] is False
    assert inv["active_parameters"] == 0
    assert inv["ufotri_active_database"] is False
    assert inv["v3_physics_ready"] is False
    assert inv["physical_validation_complete"] is False


def test_candidate_model_remains_symbolic_and_unfitted() -> None:
    c = _design()["candidate_response_contract"]
    assert "F_light" in c["symbolic_form"]
    assert "F_vpd" in c["symbolic_form"]
    assert "F_temp" in c["symbolic_form"]
    assert "F_stage" in c["symbolic_form"]
    assert c["numerical_parameter_values_selected"] is False
    assert c["functional_forms_selected"] is False
    assert c["kinetic_model_added"] is False


def test_same_record_packet_contains_target_drivers_time_identity_and_provenance() -> None:
    fields = _design()["mandatory_same_record_fields"]
    assert "gsw_or_compatible_rc" in fields["target"]
    assert {"PAR_or_PPFD", "VPDleaf_or_equivalent_direct_leaf_VPD", "Tleaf"}.issubset(fields["drivers"])
    assert {"timestamp_or_elapsed_time", "sampling_interval_semantics"}.issubset(fields["timing"])
    assert {"plant_id", "run_id", "developmental_stage_id", "condition_id"}.issubset(fields["identity"])
    assert {"instrument_model", "source_file_name", "variable_definitions_and_units"}.issubset(fields["provenance"])


def test_independent_unit_is_plant_and_row_pseudoreplication_is_forbidden() -> None:
    r = _design()["experimental_unit_and_replication"]
    assert r["independent_biological_unit"] == "plant"
    assert r["repeated_measurement_unit"] == "time_record_nested_within_plant"
    assert "must never be counted as" in r["pseudoreplication_rule"]
    assert r["biological_replicates_per_condition"] == "TBD_FEASIBILITY_AND_PRECISION_REVIEW"


def test_continuous_driver_support_and_stage_support_are_structurally_non_degenerate() -> None:
    factors = _design()["factor_coverage"]
    for key in ("light", "vpd", "leaf_temperature"):
        assert factors[key]["minimum_distinct_support_levels_for_candidate_shape_review"] >= 3
        assert factors[key]["exact_levels"] == "TBD_FEASIBILITY_REVIEW"
    assert factors["developmental_stage"]["minimum_distinct_stage_categories_for_stage_effect_review"] >= 2
    assert "Do not infer stage" in factors["developmental_stage"]["ontology_rule"]


def test_design_prevents_perfect_driver_confounding_and_order_bias() -> None:
    d = _design()
    assert "must not be perfectly confounded" in d["factor_design_rule"]
    p = d["condition_order_and_randomization"]["prohibition"]
    assert "do_not_assign_all_high_VPD_records_to_one_batch_only" in p
    assert "do_not_assign_all_low_light_records_to_one_growth_stage_only" in p
    assert "do_not_treat_run_order_as_biology" in p


def test_holdout_is_plant_level_and_not_used_for_domain_or_tuning() -> None:
    s = _design()["split_and_holdout_contract"]
    assert s["split_unit"] == "plant"
    assert s["calibration_groups_and_final_validation_groups_must_be_disjoint"] is True
    assert s["row_random_split_within_same_plant_for_final_validation"] == "forbidden"
    assert s["final_validation_used_for_response_domain_estimation"] is False
    assert s["final_validation_used_for_model_selection"] is False
    assert s["final_validation_used_for_threshold_tuning"] is False
    assert s["final_validation_used_for_preprocessing_tuning"] is False


def test_setpoints_are_not_measured_values_and_vpd_fallback_is_fail_closed() -> None:
    d = _design()
    m = d["measurement_protocol"]
    assert m["direct_Tleaf_required"] is True
    assert m["direct_PAR_or_PPFD_required"] is True
    assert m["setpoint_and_measured_value_must_be_distinguished"] is True
    fallback = d["vpd_fallback_if_direct_vpd_absent"]
    assert "pressure" in fallback["required_row_aligned_inputs"]
    assert "Tleaf" in fallback["required_row_aligned_inputs"]
    assert "midpoint substitution" in fallback["rule"]


def test_data_contract_has_unique_record_key_and_raw_hash_chain() -> None:
    data = _data()
    assert data["status"] == "DESIGN_ONLY_NOT_COLLECTED"
    key = set(data["record_key"]["required_components"])
    assert {"experiment_id", "run_id", "plant_id", "developmental_stage_id", "condition_id"}.issubset(key)
    raw = set(data["raw_file_manifest_required_fields"])
    assert {"original_filename", "byte_size", "sha256", "instrument_id", "experiment_id"}.issubset(raw)
    clean = set(data["clean_table_manifest_required_fields"])
    assert {"source_raw_sha256_values", "unit_conversion_log", "row_exclusion_log", "output_sha256"}.issubset(clean)


def test_quality_contract_forbids_silent_data_repair() -> None:
    q = _data()["quality_rules"]
    assert q["silent_imputation"] == "forbidden"
    assert q["silent_row_drop"] == "forbidden"
    assert q["silent_unit_conversion"] == "forbidden"
    assert q["silent_clipping"] == "forbidden"
    assert q["duplicate_record_key"] == "FAIL_CLOSED"
    assert q["target_driver_alignment_ambiguous"] == "FAIL_CLOSED"


def test_feasibility_gate_does_not_authorize_experiment_or_solver() -> None:
    gate = _design()["execution_gate"]
    assert gate["current_decision"] == "HOLD_EXPERIMENT_EXECUTION_PENDING_FEASIBILITY_REVIEW"
    assert gate["pass_does_not_authorize_solver"] is True
    assert "metrics_and_thresholds_preregistered" in gate["pass_requires"]
    assert "data_file_schema_frozen" in gate["pass_requires"]


def test_review_has_frozen_nonimplementation_boundary() -> None:
    text = REVIEW.read_text(encoding="utf-8")
    assert "READY_FOR_FEASIBILITY_REVIEW_NOT_EXECUTED" in text
    for line in (
        "EXPERIMENT_EXECUTED = FALSE",
        "EMPIRICAL_PACKET_COLLECTED = FALSE",
        "LEAF_IMPLEMENTATION_AUTHORIZED = FALSE",
        "SOLVER_IMPLEMENTATION_STARTED = FALSE",
        "CANDIDATE_PARAMETER_VALUES_ADMITTED = FALSE",
        "CALIBRATION_STARTED = FALSE",
        "ACTIVE_PARAMETERS = 0",
        "V3_PHYSICS_READY = FALSE",
    ):
        assert line in text
