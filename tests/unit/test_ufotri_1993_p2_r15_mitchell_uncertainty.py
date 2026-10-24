"""P2 R15: independent arithmetic for Mitchell Table 3/7, not a fit or erratum."""

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/v4/1993_upgrade/physics_delta_matrix.yaml"
DAYS_PER_HOUR = 24.0
MICROGRAM_TO_GRAM = 1e-6
SECONDS_PER_DAY = 86400
DRY_PER_CO2_EQ = 30.0 / 44.0


@pytest.fixture(scope="module")
def gates():
    y = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    row = next(r for r in y["rows"] if r["id"] == "UF93-13")
    return y, row, row["p2_r15_table3_table7_uncertainty_discrimination"]


def table3_maintenance_day(beta0, beta1, temperature_celsius):
    return (beta0 + beta1 * temperature_celsius) * DRY_PER_CO2_EQ * MICROGRAM_TO_GRAM * SECONDS_PER_DAY


def test_r15_printed_central_values_differ_from_table7(gates):
    _, row, g = gates
    assert g["source_pdf_sha256"] == row["p2_r14_mitchell_fulltext_eq30_primary_evidence"]["source_pdf_sha256"]
    assert (g["original_printed_table3_page"], g["original_printed_table7_page"]) == (12, 15)
    center = table3_maintenance_day(g["shoot_beta0_table3"], g["shoot_beta1_table3"], 10)
    assert center == pytest.approx(0.007599272727272727)
    assert center == pytest.approx(g["derived_central_b_per_day_at_10c"])
    assert g["table7_shoot_b_per_day_at_10c"] == 0.004
    assert center / g["table7_shoot_b_per_day_at_10c"] == pytest.approx(1.8998181818181814)
    assert center != pytest.approx(g["table7_shoot_b_per_day_at_10c"])


def test_r15_marginal_plusminus_rectangle_bounds_contain_table7_without_statistical_claim(gates):
    _, _, g = gates
    b0lo = g["shoot_beta0_table3"] - g["shoot_beta0_table3_plusminus"]
    b0hi = g["shoot_beta0_table3"] + g["shoot_beta0_table3_plusminus"]
    b1lo = g["shoot_beta1_table3"] - g["shoot_beta1_table3_plusminus"]
    b1hi = g["shoot_beta1_table3"] + g["shoot_beta1_table3_plusminus"]
    lower = table3_maintenance_day(b0lo, b1lo, 10)
    upper = table3_maintenance_day(b0hi, b1hi, 10)
    assert lower == pytest.approx(g["derived_marginal_rectangle_b_min_per_day"])
    assert upper == pytest.approx(g["derived_marginal_rectangle_b_max_per_day"])
    assert lower == pytest.approx(0.003063272727272727)
    assert upper == pytest.approx(0.012135272727272725)
    assert lower <= g["table7_shoot_b_per_day_at_10c"] <= upper
    assert g["table7_b_within_marginal_rectangle"] is True
    assert g["rectangle_is_confidence_region"] is False
    assert g["reported_plusminus_statistical_meaning"] == "NOT_ESTABLISHED"
    assert g["covariance_and_unrounded_fit"] == "NOT_AVAILABLE"


def test_r15_conditional_in_rectangle_coefficient_pair_exists_but_is_not_authorized(gates):
    _, _, g = gates
    example_b1 = 0.008  # Within printed marginal interval; NOT a newly fitted coefficient.
    target = g["table7_shoot_b_per_day_at_10c"]
    f = DRY_PER_CO2_EQ * MICROGRAM_TO_GRAM * SECONDS_PER_DAY
    example_b0 = target / f - example_b1 * 10
    assert example_b0 == pytest.approx(-0.012098765432098757)
    assert abs(example_b0 - g["shoot_beta0_table3"]) <= g["shoot_beta0_table3_plusminus"]
    assert abs(example_b1 - g["shoot_beta1_table3"]) <= g["shoot_beta1_table3_plusminus"]
    assert table3_maintenance_day(example_b0, example_b1, 10) == pytest.approx(target)
    assert g["same_equation_statistical_reconciliation"] == "NOT_ESTABLISHED"
    assert g["erratum_or_modified_table7_coefficient"] == "NOT_ESTABLISHED"


def test_r15_inverse_temperature_is_not_evidence_for_changing_reference_t(gates):
    _, row, g = gates
    f = DRY_PER_CO2_EQ * MICROGRAM_TO_GRAM * SECONDS_PER_DAY
    temp_if_central_fixed = (
        g["table7_shoot_b_per_day_at_10c"] / f - g["shoot_beta0_table3"]
    ) / g["shoot_beta1_table3"]
    assert temp_if_central_fixed == pytest.approx(3.8901234567901244)
    assert temp_if_central_fixed != 10
    assert row["p2_r14_mitchell_fulltext_eq30_primary_evidence"]["paper_shoot_table7_reference_temperature_c"] == 10


def test_r15_alpha_difference_within_reported_marginal_magnitude_does_not_select_equation(gates):
    _, row, g = gates
    alpha3 = g["shoot_alpha_table3_eq2"]
    alpha7 = row["p2_r14_mitchell_fulltext_eq30_primary_evidence"]["paper_shoot_table7_alpha"]
    assert alpha3 == 0.35
    assert alpha7 == 0.36
    assert (alpha7 - alpha3) / g["shoot_alpha_table3_eq2_plusminus"] == pytest.approx(.25)
    assert g["same_equation_statistical_reconciliation"] == "NOT_ESTABLISHED"


def test_r15_documentary_gate_keeps_original_baseline_and_no_production(gates):
    root, row, g = gates
    assert root["baseline_version"] == "KFK4605_1990"
    assert root["runtime_1993_profile_activated"] is False
    assert g["original_executable_parity"] == "NOT_RUN"
    assert g["independent_scientific_review"] == "NOT_RUN"
    assert g["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False
    text = (ROOT / g["audit_packet"]).read_text(encoding="utf-8")
    assert "STATISTICAL_RECONCILIATION_NOT_ESTABLISHED" in text
    assert "not a confidence" in text.lower()
    assert Path(g["audit_packet"]).name in (ROOT / "docs/v4/1993_upgrade/PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
