from __future__ import annotations

import importlib.util
from pathlib import Path


STAGE = "UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1"


def _load_gate_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "v4"
        / "check_ufotri_ht_derived_hto_reemission_secondary_feedback_reconciliation_r1.py"
    )
    spec = importlib.util.spec_from_file_location("e3_reconciliation_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result():
    return _load_gate_module().build_result()


def test_e3_machine_reconciliation_gate_passes() -> None:
    result = _result()
    assert result["stage"] == STAGE
    assert (
        result["status"]
        == "PASS_UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION"
    )
    assert all(result["contract_gates"].values())


def test_manual_roles_and_eq44_source_limit_are_machine_visible() -> None:
    result = _result()
    assert all(result["manual_gates"].values())
    assert all(result["source_ambiguity_gates"].values())
    assert result["manual_gates"]["manual_topsoil_only_direct_reemission"]
    assert result["manual_gates"]["manual_plant_reemission_rate_exists"]
    assert result["manual_gates"]["eq44_inventory_is_provisional"]
    assert result["source_ambiguity_gates"]["rain_start_rule_remains_partial"]
    assert result["source_ambiguity_gates"][
        "concentration_dependent_diff_remains_partial"
    ]


def test_historical_feedback_topology_is_reconciled_but_not_promoted() -> None:
    result = _result()
    historical = result["historical_gates"]
    decision = result["reconciliation_decision"]
    assert all(historical.values())
    assert historical["historical_feedback_delay_exists"]
    assert historical["historical_area_source_feedback_exists"]
    assert historical["historical_point_equivalent_feedback_exists"]
    assert historical["historical_feedback_uses_total_reemission"]
    assert historical["historical_air_is_primary_plus_secondary"]
    assert not decision["historical_eq44_promoted_to_manual_exact"]
    assert not decision["historical_area_source_promoted_to_phase_e_default"]


def test_current_v4_reuses_roles_without_adding_e3_solver() -> None:
    result = _result()
    current = result["current_v4_gates"]
    decision = result["reconciliation_decision"]
    assert all(current.values())
    assert current["soil_v4_has_explicit_surface_reemission_sink"]
    assert current["soil_reemission_is_l1_only"]
    assert current["soil_global_balance_counts_reemission_as_external_loss"]
    assert current["leaf_eq31_diagnostic_exists"]
    assert current["leaf_operator_is_signed"]
    assert decision["plant_reemission_role_reusable_from_phase_a"]
    assert decision["soil_reemission_sink_role_reusable_from_soil_v4"]
    assert not decision["soil_reemission_rate_generation_recovered"]
    assert not decision["e3_new_reemission_solver_authorized"]
    assert not decision["e3_existing_source_change_required"]


def test_ht_derived_label_fails_closed_after_aggregate_soil_mixing() -> None:
    result = _result()
    e2 = result["e2_provenance_gates"]
    decision = result["reconciliation_decision"]
    assert all(e2.values())
    assert e2["e2_keeps_primary_and_ht_derived_fluxes_separate"]
    assert e2["e2_projects_only_combined_flux_to_soil"]
    assert not decision["aggregate_soil_inventory_retains_origin_partition"]
    assert not decision["aggregate_total_reemission_may_be_called_ht_derived"]
    assert decision["explicit_origin_proof_required_for_ht_derived_label"]
    assert decision["mixed_origin_feedback_must_remain_mixed_origin"]
    assert result["contract_gates"]["no_false_ht_derived_attribution"]


def test_phase_f_and_real_atmos_boundaries_remain_isolated() -> None:
    result = _result()
    decision = result["reconciliation_decision"]
    assert decision["phase_f_owns_area_source_numerical_compatibility"]
    assert not decision["real_cteas_atmos_required_for_e3"]
    assert result["contract_gates"]["phase_f_boundary_preserved"]
    assert result["next_scope"] == "PHASE_F_REEMISSION_AREA_SOURCE_COMPATIBILITY"


def test_e3_claims_remain_software_reconciliation_only() -> None:
    result = _result()
    assert result["scope_claim"] == "RECONCILIATION_ONLY_NO_EXISTING_SOURCE_CHANGE"
    assert not result["empirical_validation"]
    assert not result["physical_accuracy_claim"]
    assert not result["production_readiness_claim"]
    assert not result["original_executable_equivalence"]
