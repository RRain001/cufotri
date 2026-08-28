from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs" / "v4" / "governance" / "ufotri_leaf_eq7_31_reconciliation_r1.yaml"
ADR = ROOT / "docs" / "v4" / "adr" / "ADR-059-ufotri-leaf-eq7-31-reconciliation-r1.md"
REPORT = ROOT / "docs" / "v4" / "reports" / "ufotri_leaf_eq7_31_reconciliation_r1.md"


def _load():
    return yaml.safe_load(GOVERNANCE.read_text())


def test_leaf_reconciliation_verdict_and_boundaries():
    data = _load()
    assert data["stage"] == "UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1"
    assert data["scope"] == "GOVERNANCE_AND_FIDELITY_DECISION_ONLY"
    assert data["verdict"]["reconciliation_complete"] is True
    assert data["verdict"]["current_v2_exactly_manual_faithful"] is False
    assert data["verdict"]["current_v4_rc1_exactly_manual_faithful"] is False
    assert data["verdict"]["source_changes_required"] is True
    assert data["verdict"]["current_empirical_leaf_r5_required_for_replication"] is False
    assert data["verdict"]["next_stage_authorized"] == "UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1"
    assert data["claim_boundary"]["v4_rc1_default_path_changed"] is False
    assert data["claim_boundary"]["source_physics_changed_in_this_stage"] is False
    assert data["claim_boundary"]["production_parameter_activation"] is False


def test_leaf_manual_matrix_covers_all_required_equation_groups():
    data = _load()
    by_id = {row["id"]: row for row in data["manual_role_matrix"]}
    expected = {
        "LEAF-07-08",
        "LEAF-09",
        "LEAF-10-11",
        "LEAF-12-14",
        "LEAF-STOMATAL-RULES",
        "LEAF-15-18",
        "LEAF-19-21",
        "LEAF-22-24",
        "LEAF-25",
        "LEAF-26",
        "LEAF-27",
        "LEAF-28-30",
        "LEAF-31",
    }
    assert expected <= set(by_id)
    assert by_id["LEAF-19-21"]["classification"] == "HISTORICAL_LITERATURE_SUBSTITUTION"
    assert by_id["LEAF-19-21"]["required_manual_relation"] == "r_b_equals_2_over_k_u_star"
    assert by_id["LEAF-25"]["classification"] == "MANUAL_FIDELITY_MISSING"
    assert by_id["LEAF-28-30"]["classification"] == "MANUAL_FIDELITY_MISSING"


def test_a2_scope_is_manual_fidelity_not_generic_leaf_r5():
    data = _load()
    required = set(data["A2_minimum_scope"])
    assert "eq21_boundary_layer_resistance" in required
    assert "eq22_to_eq25_wind_profile_and_geometry_compatibility" in required
    assert "eq27_to_eq30_analytic_interval_exchange" in required
    assert "manual_day_night_lai_soil_water_rain_canopy_resistance" in required
    forbidden = set(data["forbidden_scope"])
    assert "generic_empirical_leaf_r5_physiology" in forbidden
    assert "replace_rc1_default_path" in forbidden
    assert "production_activation" in forbidden
    assert data["selected_next_stage"] == "UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1"


def test_reconciliation_documents_state_source_changes_required():
    adr = ADR.read_text()
    report = REPORT.read_text()
    assert "SOURCE_CHANGES_REQUIRED = TRUE" in adr
    assert "UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1" in adr
    assert "PASS_RECONCILIATION_SOURCE_CHANGES_REQUIRED" in report
    assert "generic Leaf R5 formulation is not required for UFOTRI replication" in report


def test_existing_source_boundaries_remain_present():
    historical = (ROOT / "src" / "cteas_ufotri" / "plant" / "leaf_exchange.py").read_text()
    resistance = (
        ROOT
        / "src"
        / "cteas_ufotri"
        / "plant"
        / "leaf_exchange_resistance"
        / "resistance.py"
    ).read_text()
    tfwt = (ROOT / "src" / "cteas_ufotri" / "plant" / "tfwt_v3" / "tfwt_solver.py").read_text()
    assert "def bidirectional_leaf_exchange" in historical
    assert "sherwood = 0.664" in historical
    assert "def signed_leaf_exchange_flux" in resistance
    assert "aerodynamic + boundary + canopy" in resistance
    assert "leaf_transfer = leaf_flux * interval" in tfwt
