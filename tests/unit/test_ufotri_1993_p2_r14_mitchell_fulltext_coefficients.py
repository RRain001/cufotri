"""R14: Mitchell (1991) primary-source coefficients and discrepancy audit.

Source-derived arithmetic must not be conflated with KfK5194 executable parity.
No copyrighted primary PDF is checked into this repository.
"""

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"
PDF_SHA256 = "d9f6f74b5268c6166407e02e98208dc452f9614002ccdb87a4d045cd4e0229e4"


@pytest.fixture(scope="module")
def registry_gate():
    registry = yaml.safe_load((DOC / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    rows = [r for r in registry["rows"] if r["id"] == "UF93-13"]
    assert len(rows) == 1
    row = rows[0]
    return registry, row, row["p2_r14_mitchell_fulltext_eq30_primary_evidence"]


def test_primary_fulltext_supersedes_access_block_but_does_not_falsify_r12(registry_gate):
    _, row, gate = registry_gate
    assert gate["evidence_level"] == "USER_SUPPLIED_FULL_PDF_VISUALLY_CHECKED"
    assert gate["source_doi"] == "10.1093/oxfordjournals.aob.a088102"
    assert gate["source_pdf_sha256"] == PDF_SHA256
    assert gate["source_pdf_pages"] == 10
    assert gate["reviewed_printed_pages"] == [7, 9, 12, 13, 14, 15]
    assert gate["reviewed_pdf_page_indices_zero_based"] == [0, 2, 5, 6, 7, 8]
    assert row["p2_r12_mitchell_archive_access_gate"]["archive_pdf_http_status_observed"] == 401
    assert row["p2_r12_mitchell_archive_access_gate"]["mitchell_full_text_equation_review"] == "NOT_RUN"
    assert not (ROOT / "mitchell1991.pdf").exists()


def test_table7_shoot_coefficient_and_day_to_hour_conversion_match_manual(registry_gate):
    _, _, gate = registry_gate
    assert gate["paper_shoot_table7_alpha"] == gate["manual_eq30_growth_coefficient"] == 0.36
    assert gate["paper_shoot_table7_reference_temperature_c"] == 10
    day_rate = gate["paper_shoot_table7_b_per_day"]
    hour_rate = day_rate / 24
    manual_rate = gate["manual_eq30_maintenance_coefficient_per_hour"]
    assert day_rate == 0.004
    assert hour_rate == pytest.approx(1.6666666666666667e-4, rel=1e-13)
    assert manual_rate == 1.67e-4
    assert manual_rate == pytest.approx(hour_rate, abs=3.4e-7, rel=0)
    assert gate["table7_to_manual_eq30_coefficient_match"] == "SHOOT_MATCH_WITH_REPORTED_PRECISION"


def test_eq3_co2_equivalent_and_dry_matter_bridge_is_a_unit_identity(registry_gate):
    _, _, gate = registry_gate
    k = gate["paper_eq3_conversion_k_dry_mass_per_co2_equivalent"]
    assert k == pytest.approx(30 / 44, abs=1e-15)
    for dry_mass in (0.0, 1.0, 250.0, 1500.0):
        co2_equivalent = dry_mass / k
        assert co2_equivalent == pytest.approx(dry_mass * 44 / 30)
        assert co2_equivalent * k == pytest.approx(dry_mass)
    assert gate["paper_eq1_biomass"] == "DRY_MASS_AS_CO2_EQUIVALENT"
    assert gate["eq30_w_dry_matter_to_co2_equivalent"] == "SOURCE_EQUIVALENCE_44_DIV_30_CONDITIONAL"


def test_table3_central_coefficients_do_not_reconstruct_table7_b(registry_gate):
    _, _, gate = registry_gate
    beta = (
        gate["table3_eq2_shoot_beta0_ug_co2_per_g_dry_s"]
        + gate["table3_eq2_shoot_beta1_ug_co2_per_g_dry_deg_c_s"]
        * gate["paper_shoot_table7_reference_temperature_c"]
    )
    actual_from_printed_table3 = beta * (30 / 44) * 1e-6 * 86400
    assert beta == pytest.approx(0.129)
    assert actual_from_printed_table3 == pytest.approx(0.007599272727272727, rel=1e-13)
    assert actual_from_printed_table3 == pytest.approx(gate["table3_recomputed_b_per_day_at_10c"], rel=1e-13)
    assert abs(actual_from_printed_table3 - gate["paper_shoot_table7_b_per_day"]) > 0.003
    assert gate["table3_to_table7_b_reconciliation"] == (
        "NOT_ESTABLISHED_PRINTED_CENTRAL_VALUES_DIFFER"
    )
    # Also preserve the distinct printed Eq.(2), alternative Eq.(5) and Table 7 values.
    assert gate["table3_eq2_shoot_alpha"] == 0.35
    assert gate["table3_eq2_shoot_alpha"] != gate["paper_shoot_table7_alpha"]
    assert gate["table3_to_table7_growth_reconciliation"] == (
        "NOT_ESTABLISHED_PRINTED_ALPHA_0_35_VS_0_36"
    )


def test_shoot_ear_and_time_bases_remain_distinct(registry_gate):
    _, _, gate = registry_gate
    assert (gate["paper_shoot_table7_alpha"], gate["paper_shoot_table7_b_per_day"]) == (0.36, 0.004)
    assert (gate["paper_ear_table7_alpha"], gate["paper_ear_table7_b_per_day"]) == (0.42, 0.006)
    assert gate["paper_ear_table7_reference_temperature_c"] == 13
    assert gate["photosynthesis_two_day_average"] == "MITCHELL_FITTING_INPUT_ONLY"
    assert gate["kfk_eq30_temperature_handling"] == "NOT_ESTABLISHED"
    assert gate["kfk_eq30_ground_leaf_area_mapping"] == "NOT_ESTABLISHED"
    assert gate["kfk_eq28_eq30_original_solve_order"] == "NOT_ESTABLISHED"


def test_frozen_1990_baseline_and_historical_parity_fail_closed(registry_gate):
    registry, row, gate = registry_gate
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["runtime_1993_profile_activated"] is False
    assert registry["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert gate["original_executable_parity"] == "NOT_RUN"
    assert gate["independent_scientific_review"] == "NOT_RUN"
    assert gate["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False
    audit = ROOT / gate["audit_packet"]
    assert audit.is_file()
    text = audit.read_text(encoding="utf-8")
    for token in (PDF_SHA256, "TABLE7_EQ30_COEFFICIENT_MATCH",
                  "TABLE3_TABLE7_INTERNAL_NUMERIC_UNRESOLVED",
                  "PRODUCTION_COUPLING_BLOCKED", "NOT_RUN"):
        assert token in text
    assert audit.name in (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
