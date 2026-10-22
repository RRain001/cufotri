"""Source-identity contracts for selected 1990/1991/1993 UFOTRI R5 evidence.

These tests guard historical statements, not numerical equivalence to UFOTRI 4.0.
"""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "docs/v4/1993_upgrade"


def _read(name: str) -> dict:
    value = yaml.safe_load((DIR / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r5_is_1993_target_with_three_edition_citations_and_no_solver_claim() -> None:
    d = _read("primary_source_triedition_physics_r5.yaml")
    assert d["target_version"] == "UFOTRI_4_0_1993"
    assert d["target_report"] == "KfK 5194"
    assert {x["report"] for x in d["source_documents"]} == {
        "KfK 4605", "KfK 4853", "KfK 5194"
    }
    assert all(x["url"].startswith("https://publikationen.bibliothek.kit.edu/") for x in d["source_documents"])
    assert d["original_executable_equivalence"] == "NOT_ESTABLISHED"
    assert d["independent_scientific_review"] == "NOT_COMPLETED"
    assert d["runtime_1993_profile_activated"] is False
    assert d["audit_status"] == "SELECTED_PRINTED_PDF_PAGES_CHECKED_FULL_P0_OPEN"


def test_r5_six_focused_comparisons_have_source_page_anchors() -> None:
    d = _read("primary_source_triedition_physics_r5.yaml")
    rows = d["rows"]
    assert len(rows) == 6
    assert {x["id"] for x in rows} == {f"R5-{i:02d}" for i in range(1, 7)}
    for row in rows:
        assert row["topic"] and row["conclusion"]
        assert row["cannot_claim"] and row["remaining"]
        assert row["link_to_delta"].startswith("UF93-")
        assert row["printed_evidence"]
        for ev in row["printed_evidence"]:
            assert ev["report"] in {"KfK 4605", "KfK 4853", "KfK 5194"}
            assert isinstance(ev["printed_page"], int)
            expected_shift = 9 if ev["report"] == "KfK 5194" else (
                7 if ev["report"] == "KfK 4853" else 11
            )
            assert ev["pdf_index"] == ev["printed_page"] + expected_shift
            assert ev["anchor"] and ev["finding"]


def test_stomatal_and_soil_relations_not_falsely_claimed_new_in_1993() -> None:
    rows = {x["id"]: x for x in _read("primary_source_triedition_physics_r5.yaml")["rows"]}
    assert "PRESENT_BY_1991" in rows["R5-01"]["conclusion"]
    assert rows["R5-02"]["conclusion"] == "SOIL_HYDRAULIC_CLOSURE_FORM_PRESENT_BY_1991"
    assert "IBODEX" in " ".join(x["finding"] for x in rows["R5-02"]["printed_evidence"])
    assert "0.06%/h" in " ".join(x["finding"] for x in rows["R5-03"]["printed_evidence"])
    assert "1993" in rows["R5-03"]["conclusion"]


def test_reemission_and_hydraulic_time_basis_remain_unresolved() -> None:
    rows = {x["id"]: x for x in _read("primary_source_triedition_physics_r5.yaml")["rows"]}
    re = rows["R5-04"]
    assertions = " ".join(x["finding"] for x in re["printed_evidence"])
    assert "ABFLR" in assertions
    assert "s^-1" in assertions and "h^-1" in assertions
    assert "3600" in re["remaining"]
    assert "mm/day" in rows["R5-06"]["remaining"]
    assert rows["R5-06"]["conclusion"] == "SOURCE_LIMITED_UNIT_AMBIGUITY_OPEN"


def test_original_1990_and_1991_dose_distinctions_not_overstated() -> None:
    rows = {x["id"]: x for x in _read("primary_source_triedition_physics_r5.yaml")["rows"]}
    dose = rows["R5-05"]
    assert "PREEXISTS_1993" in dose["conclusion"]
    assert "4.5e-11" in dose["printed_evidence"][0]["finding"]
    assert "4.0e-11" in dose["printed_evidence"][1]["finding"]
    main = _read("physics_delta_matrix.yaml")
    assert main["target_version"] == "UFOTRI_4_0_1993"
    assert main["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    assert main["runtime_1993_profile_activated"] is False
    assert "1990_1991_1993" in main["source_audit_r5_status"]
    items = {x["id"]: x for x in main["rows"]}
    assert len(items) == 24
    assert items["UF93-03"]["comparison_1991_status"] == "EXTENDED_STOMATAL_AND_LAI_PRESENT_BY_1991"
    assert items["UF93-09"]["comparison_1991_status"] == "SUCTION_CONDUCTIVITY_CLOSURE_AND_IBODEX_PRESENT_BY_1991"
    assert items["UF93-11"]["cross_edition_r5"].startswith("CONFIRMED_PRINTED")
    assert items["UF93-22"]["cross_edition_r5"].startswith("OBT_DOSFOB")


def test_r5_research_text_preserves_original_source_scope() -> None:
    md = (DIR / "PRIMARY_SOURCE_TRIEDITION_PHYSICS_R5.md").read_text(encoding="utf-8")
    assert "1993" in md and "1991" in md and "1990" in md
    assert "KfK 5194" in md and "KfK 4853" in md and "KfK 4605" in md
    assert "K" in md and "mm/hour" in md
    assert "NOT_ESTABLISHED" in md
    assert "P0 #126" in md
