"""P2 R12: a located but inaccessible primary paper is not validated physics."""

from collections import Counter
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
    return registry, rows[0], rows[0]["p2_r12_mitchell_archive_access_gate"]


def test_archived_paper_location_has_exact_identity_without_access_claim(evidence):
    _, _, r = evidence
    assert r["doi"] == "10.1093/oxfordjournals.aob.a088102"
    assert r["openalex_work_id"] == "W2401308966"
    assert r["archive_item_url"].endswith("/dark-respiration-of-winter-wheat-crops-in-relation-to-temperature-and-simulated-photosynthesis")
    assert r["archive_pdf_url"].endswith("/id/eprint/5335/1/42758396.pdf")
    assert r["archive_item_http_status_observed"] == 200
    assert r["archive_pdf_http_status_observed"] == 401
    assert r["openalex_oa_status"] == "closed"
    assert r["evidence_level"] == "PRIMARY_ASSET_LOCATED_BUT_UNAUTHORIZED"


def test_no_original_fulltext_or_fake_pdf_checksum_is_asserted(evidence):
    _, _, r = evidence
    assert r["asset_pdf_sha256"] == "NOT_AVAILABLE"
    assert r["mitchell_full_text_equation_review"] == "NOT_RUN"
    packet = ROOT / r["audit_packet"]
    assert packet.is_file()
    text = packet.read_text(encoding="utf-8")
    for token in ("401 Unauthorized", "No PDF bytes were acquired",
                  "NOT_RUN", "NOT_ESTABLISHED", "COUPLING_BLOCKED"):
        assert token in text


def test_publisher_abstract_is_not_1993_coefficient_or_time_lag(evidence):
    _, row, r = evidence
    assert r["abstract_rate_normalization"] == "PER_UNIT_DRY_MASS_ABSTRACT_ONLY"
    assert r["abstract_shoot_ear_partition"] == "STAGE_DEPENDENT_ABSTRACT_ONLY"
    assert r["abstract_photosynthesis_lag"] == "PRECEDING_TWO_DAYS_CORRELATION_ONLY"
    assert r["kfk_eq30_growth_coefficient_source"] == "NOT_ESTABLISHED"
    assert r["kfk_eq30_maintenance_coefficient_source"] == "NOT_ESTABLISHED"
    assert row["p2_r9_source_gate"]["eq28_eq30_original_solve_order"] == "NOT_ESTABLISHED"


def test_conditional_mass_area_dimensional_identity_not_a_calibration(evidence):
    _, _, r = evidence
    # r_m [CO2 / (dry mass*time)] * M [dry mass/ground area].
    rate = Counter({"CO2_mass": 1, "dry_mass": -1, "time": -1})
    area_mass = Counter({"dry_mass": 1, "ground_area": -1})
    result = {name: rate[name] + area_mass[name] for name in set(rate) | set(area_mass)}
    assert {k: v for k, v in result.items() if v} == {
        "CO2_mass": 1, "time": -1, "ground_area": -1
    }
    assert r["eq30_co2_equivalent_per_dry_mass_conversion"] == "NOT_ESTABLISHED"
    assert r["eq30_dry_matter_to_w_bridge"] == "NOT_ESTABLISHED"
    assert r["eq30_respiration_area_basis"] == "NOT_ESTABLISHED"


def test_1990_baseline_production_gate_and_document_index_fail_closed(evidence):
    registry, row, r = evidence
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["runtime_1993_profile_activated"] is False
    assert r["eq28_eq30_original_solve_order"] == "NOT_ESTABLISHED"
    assert r["original_executable_parity"] == "NOT_RUN"
    assert r["independent_scientific_review"] == "NOT_RUN"
    assert r["production_coupling_allowed"] is False
    assert row["p2_r9_source_gate"]["production_coupling_allowed"] is False
    index = (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
    assert Path(r["audit_packet"]).name in index
