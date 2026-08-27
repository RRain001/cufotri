from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/v4_soil_root_tfwt_obt_integration_r1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-031-v4-soil-root-tfwt-obt-integration.md"
REPORT = ROOT / "docs/v4/reports/v4_soil_root_tfwt_obt_integration_r1.md"


def test_governance_keeps_new_integration_opt_in_and_next_stage_closed() -> None:
    data = yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))
    assert data["stage"] == "V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1"
    assert data["status"] == "INTEGRATION_IMPLEMENTED_AWAITING_MACHINE_GATE"
    assert data["scope"]["opt_in_only"] is True
    assert data["scope"]["v3_default_path_changed"] is False
    assert data["scope"]["v3_pipeline_changed"] is False
    assert data["selected_numerical_semantics"]["operator_split"] == "PRESERVE_V3_POST_OBT_ROOT_GAIN"
    assert data["area_basis_contract"]["identical_declared_basis_required"] is True
    assert data["area_basis_contract"]["silent_soil_area_to_plant_area_conversion"] == "forbidden"
    assert data["water_contract"]["plant_water_storage_added"] is False
    assert data["water_contract"]["coupled_plant_water_conservation_claim"] is False
    assert data["parameter_boundary"]["active_parameters"] == 0
    assert data["parameter_boundary"]["ufotri_20_40_40_active"] is False
    assert data["parameter_boundary"]["short_term_3h_delay_active"] is False
    assert data["next_stage"]["authorized_now"] is False
    assert data["next_stage"]["leaf_r5"] == "not_authorized"
    assert data["hard_invariants"]["physical_validation_complete"] is False
    assert data["hard_invariants"]["real_cteas_atmos_coupling_active"] is False


def test_adr_and_report_do_not_promote_synthetic_integration_to_physical_validation() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    assert "Status: Proposed pending exact-head machine gate" in adr
    assert "software integration evidence only" in adr
    assert "`INTEGRATION_IMPLEMENTED_AWAITING_MACHINE_GATE`" in report
    assert "no empirical or physical validation claim" in report
    assert "no real CTEAS-Atmos binding" in report
