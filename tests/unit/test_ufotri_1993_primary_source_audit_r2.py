"""KfK5194 (1993) original-source audit contracts, not solver verification."""
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = ROOT / "docs" / "v4" / "1993_upgrade"


def _yaml(filename: str) -> dict:
    doc = yaml.safe_load((AUDIT_DIR / filename).read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def test_kfk5194_r2_primary_source_and_scope_are_explicit() -> None:
    doc = _yaml("primary_source_formula_audit_r2.yaml")
    assert doc["target_version"] == "UFOTRI_4_0_1993"
    assert doc["original_report"] == "KfK 5194"
    assert doc["baseline_version"] == "KFK4605_1990"
    assert doc["status"] == "PARTIAL_PRIMARY_SOURCE_AUDIT"
    assert doc["scope"] == "SOURCE_VERIFICATION_ONLY_NOT_IMPLEMENTATION"
    assert doc["pdf_url"].endswith("/270034158/3813483")
    assert doc["baseline_pdf_url"].endswith("/270029395/3813413")


def test_1993_selected_equations_are_anchored_to_printed_pages() -> None:
    doc = _yaml("primary_source_formula_audit_r2.yaml")
    eqs = doc["verified_equations"]
    assert len(eqs) == 22
    assert len({q["id"] for q in eqs}) == len(eqs)
    assert all(q["source_review"] == "PRINTED_PDF_VISUALLY_CHECKED" for q in eqs)
    for eq in eqs:
        assert eq["print_page"] + 9 == eq["pdf_page_index"]
        assert eq["expression"]
        assert eq["units"] and eq["notes"]
    by_id = {q["id"]: q for q in eqs}
    assert by_id["E23"]["units"] == "mm/day"
    assert "mm/hour" in by_id["E24"]["units"]
    assert "P_m" in by_id["E26"]["notes"]
    assert "NOT Eq.(26)" in by_id["E33"]["notes"]


def test_1993_historical_defaults_are_version_scoped_not_active() -> None:
    doc = _yaml("primary_source_formula_audit_r2.yaml")
    items = doc["documented_defaults"]
    assert len(items) == 21
    assert len({q["name"] for q in items}) == len(items)
    assert all(q["source_review"] == "PRINTED_PDF_VISUALLY_CHECKED" for q in items)
    assert all(q["print_page"] + 9 == q["pdf_page_index"] for q in items)
    defaults = {q["name"]: q["value"] for q in items}
    for switch in (
        "IMODEL", "ICOVER", "IPHOTO", "IMONT", "IFLAGS",
        "IFLAGR", "IDEPHT", "IBODEX",
    ):
        assert defaults[switch] == 1
    assert defaults["SOILAP"] == 1.65
    assert defaults["SOILBP"] == 7.3
    assert defaults["SOILCP"] == -3.1
    assert defaults["SOILNP"] == 7.5
    assert defaults["SOIAKP"] == 1000
    assert defaults["SOIBKP"] == 60
    assert defaults["SOIMKP"] == 1.41
    assert defaults["RSOIL"] == 150
    assert defaults["RSSMIN"] == 50
    assert defaults["ZSOILA"] == 0.004
    assert defaults["REMRE"] == 0.3
    assert defaults["REMNI"] == 1
    assert defaults["REDREM"] == 1


def test_original_pdf_uncertainty_cannot_be_dropped() -> None:
    doc = _yaml("primary_source_formula_audit_r2.yaml")
    conflicts = doc["unresolved_source_conflicts"]
    assert {q["kind"] for q in conflicts} == {
        "UNIT_MISMATCH", "SYMBOL_REUSE", "DIMENSION_CONVENTION", "EDITION_DIFFERENCE"
    }
    assert all(q["disposition"] and q["summary"] for q in conflicts)
    matrix = _yaml("physics_delta_matrix.yaml")
    assert matrix["target_version"] == "UFOTRI_4_0_1993"
    assert matrix["runtime_1993_profile_activated"] is False
    assert matrix["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    assert len(matrix["rows"]) == 24
    by_id = {q["id"]: q for q in matrix["rows"]}
    assert all(q["independent_scientific_review"] == "NOT_COMPLETED" for q in by_id.values())
    assert by_id["UF93-03"]["classification"] == "1993_FORMULA_VERIFIED_1990_DELTA_PENDING"
    assert by_id["UF93-09"]["classification"] == "1993_FORMULA_VERIFIED_1990_DELTA_PENDING"
    assert by_id["UF93-09"]["safety_review_flag"] == "K_MM_PER_DAY_V_MM_PER_HOUR_SOURCE_CONFLICT"
    assert by_id["UF93-11"]["dual_edition_exact_formula_review"] == (
        "PRINTED_1990_EQ44_AND_1993_EQ25_COMPARED"
    )
    page = (AUDIT_DIR / "PRIMARY_SOURCE_AUDIT_R2.md").read_text(encoding="utf-8")
    assert "KfK 5194" in page and "1993" in page
    assert "1990" in page and "mm/day" in page and "mm/hour" in page
    assert "NOT_ESTABLISHED" in page
