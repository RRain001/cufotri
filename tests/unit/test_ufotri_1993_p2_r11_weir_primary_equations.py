"""R11 Weir 1984 primary-source unit provenance; NO Eq29 runtime bridge."""

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"


@pytest.fixture(scope="module")
def evidence():
    registry = yaml.safe_load((DOC / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    rows = [r for r in registry["rows"] if r["id"] == "UF93-13"]
    assert len(rows) == 1
    return registry, rows[0], rows[0]["p2_r11_weir_primary_equation_evidence"]


def test_primary_weir_pdf_equations_have_page_and_hash_provenance(evidence):
    _, _, record = evidence
    assert record["evidence_level"] == "WEIR_1984_PRIMARY_PDF_EQUATIONS_VISUALLY_CHECKED"
    assert record["source_doi"] == "10.1017/S0021859600042702"
    assert record["source_pdf_sha256"] == "0558e6c38f9efb2d7fe9f3af1b862c096cfcd6c1e35619b233a09d39609d17e4"
    assert record["weir_original_printed_pages"] == [374, 375]
    assert record["weir_pdf_pages_zero_based"] == [4, 5]


def test_weir_dimensional_rate_resistance_and_daily_ledger_are_separate(evidence):
    _, _, record = evidence
    assert record["weir_eq20_pmax_unit"] == "MG_CO2_PER_M2_PER_SECOND"
    assert record["weir_eq20_ca_unit"] == "MG_CO2_PER_M3"
    assert record["weir_eq20_rp_unit"] == "SECOND_PER_M"
    assert record["weir_eq25_respiration_unit"] == "G_PER_M2_PER_DAY"
    assert record["weir_eq25_biomass_unit"] == "G_PER_M2"
    assert record["weir_eq25_ch2o_co2_factor"] == pytest.approx(0.65)


def test_dimensional_identity_is_not_a_1993_coefficient_calibration(evidence):
    _, row, record = evidence
    factor = (3600.0 / 1000.0)
    assert record["unit_identity_mg_per_second_to_g_per_hour"] == pytest.approx(factor)
    assert row["p2_r9_source_gate"]["eq29_co_to_pm_bridge"] == "NOT_ESTABLISHED"
    assert record["eq29_empirical_coefficient_calibration"] == "NOT_ESTABLISHED"
    assert record["eq29_co_to_pm_bridge"] == "NOT_ESTABLISHED"
    assert record["weir_to_1993_area_aggregation"] == "NOT_ESTABLISHED"


def test_unverified_science_and_1990_baseline_stay_fail_closed(evidence):
    registry, row, record = evidence
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["runtime_1993_profile_activated"] is False
    assert record["mitchell_1991_primary_equation_review"] == "NOT_RUN"
    assert record["original_executable_parity"] == "NOT_RUN"
    assert record["independent_scientific_review"] == "NOT_RUN"
    assert record["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False


def test_audit_packet_is_traceable_and_does_not_claim_equivalence(evidence):
    _, _, record = evidence
    p = ROOT / record["audit_packet"]
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    index = (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
    for token in ("10.1017/S0021859600042702", record["source_pdf_sha256"],
                  "NOT_ESTABLISHED", "NOT_RUN", "PRODUCTION_COUPLING_BLOCKED",
                  "KfK 4605", "Mitchell"):
        assert token in text
    assert p.name in index
