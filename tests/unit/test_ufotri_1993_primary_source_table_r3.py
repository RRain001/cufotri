"""Documentation-only guard for KfK 5194 (1993) Table 1/9–12 and inputs.

No runtime/physics-default implications and no original FORTRAN equivalence claim.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs" / "v4" / "1993_upgrade"


def load(name: str) -> dict:
    doc = yaml.safe_load((AUDIT / name).read_text(encoding="utf-8"))
    assert isinstance(doc, dict)
    return doc


def test_1993_document_identity_and_printed_table_page_images() -> None:
    doc = load("primary_source_transfer_tables_r3.yaml")
    assert doc["target_version"] == "UFOTRI_4_0_1993"
    assert doc["report"] == "KfK 5194"
    assert doc["scope"] == "LITERATURE_TABLE_TRANSCRIPTION_NOT_SOLVER_COEFFICIENTS"
    assert doc["validation"] == "NOT_EQUIVALENT_TO_ORIGINAL_EXECUTABLE"
    t1 = doc["table_1"]
    assert t1["printed_page"] == 17 and t1["pdf_page_index_zero_based"] == 26
    for key, page in ((9, 86), (10, 87), (11, 88), (12, 89)):
        table = doc["tables"][key]
        assert table["printed_page"] == page
        assert table["pdf_page_index_zero_based"] == page + 9
        assert table["units"] == "d^-1"
        assert "standard input values" in table["context"]


def test_table1_plant_and_edible_dry_water_mass_budget() -> None:
    values = load("primary_source_transfer_tables_r3.yaml")["table_1"]["values"]
    for crop in ("leafy_vegetables", "grass", "potatoes", "winter_wheat"):
        total = values["plant_total_mass_g"][crop]
        dry = values["plant_dry_mass_g"][crop]
        water = values["plant_water_mass_g"][crop]
        assert dry + water == total, crop
    for crop in ("potatoes", "winter_wheat"):
        assert (
            values["edible_dry_mass_g"][crop] + values["edible_water_mass_g"][crop]
            == values["edible_total_mass_g"][crop]
        )
    assert "grass" not in values["edible_dry_mass_g"]
    assert values["edible_dry_mass_g"]["winter_wheat"] == 519
    assert values["edible_water_mass_g"]["winter_wheat"] == 81


def test_all_four_coma_transfer_rate_tables_are_preserved_without_guessing() -> None:
    doc = load("primary_source_transfer_tables_r3.yaml")
    t = doc["tables"]
    counts = {9: 15, 10: 26, 11: 21, 12: 18}
    assert {i: len(t[i]["rows"]) for i in counts} == counts
    assert sum(counts.values()) == 80
    for table in t.values():
        for row in table["rows"]:
            assert row["source_symbol_as_printed"]
            assert row["from_as_printed"] and row["to_as_printed"]
            assert math.isfinite(row["rate_per_day"]) and row["rate_per_day"] > 0

    # These apparent source-label problems must be recorded as-is.
    assert any(
        x["source_symbol_as_printed"] == "t13,13"
        and x["to_as_printed"] == "ground water"
        for x in t[9]["rows"]
    )
    assert t[12]["rows"][2]["to_as_printed"] == "potato HTO"
    assert t[12]["rows"][2]["rate_per_day"] == 0.304
    assert any(a["table"] == 12 and a["symbol"] == "tp1,p5"
               for a in doc["source_ambiguities"])


def test_grass_obt_half_life_uses_all_four_outgoing_paths() -> None:
    doc = load("primary_source_transfer_tables_r3.yaml")
    grass = doc["tables"][10]["rows"]
    outflow = [x for x in grass if x["from_as_printed"] == "grass OBT"]
    assert len(outflow) == 4
    destination = {r["to_as_printed"]: r["rate_per_day"] for r in outflow}
    assert destination == {
        "grass HTO": 0.024,
        "cow HTO": 0.018,
        "cow OBT": 0.0029,
        "milk OBT": 0.0015,
    }
    total = math.fsum(destination.values())
    assert total == pytest.approx(0.0464)
    assert math.log(2) / total == pytest.approx(14.938516822412614)
    assert doc["derived_non_source_diagnostics"]["grass_obt_total_outflow_per_day"]["value"] == pytest.approx(total)
    leafy = doc["tables"][9]["rows"]
    o = [r for r in leafy if r["from_as_printed"] == "plant OBT"]
    assert len(o) == 1 and o[0]["rate_per_day"] == 0.032
    assert math.log(2) / o[0]["rate_per_day"] == pytest.approx(21.66084939249829)


def test_input_defaults_do_not_activate_runtime_switches() -> None:
    doc = load("primary_source_input_defaults_r3.yaml")
    assert doc["target"] == "UFOTRI_4_0_1993"
    assert doc["scope"] == "HISTORICAL_INPUT_DOCUMENTATION_ONLY"
    d = {x["name"]: x["value"] for x in doc["scalar_defaults"]}
    assert len(d) == 19
    assert d["IBODFX"] == 0 and d["BODEIN"] == pytest.approx(0.2)
    assert d["IARTBO"] == 1
    assert sum(d[x] for x in ("FAKC1", "FAKC2", "FAKCP", "FAKCW")) == pytest.approx(1.0)
    assert (d["IHARP"], d["IHARW"], d["IRELIN"]) == (258, 225, 181)
    a = {x["name"]: x for x in doc["array_defaults"]}
    assert a["COGRF"]["count"] == 5
    assert a["COGRF"]["numerical_repeated_value"] == 1250
    assert a["TIMEDO"]["count"] == 12
    assert a["TIMEDO"]["raw_default"] == "1,3,7,14,21,30,90,180,200,360,2*3600"
    assert d["IBANWR"] == 0
    assert "NOT" in next(x["warning"] for x in doc["model_semantics"]
                         if x["name"] == "FOOD_RESTRICTION")
    main = load("physics_delta_matrix.yaml")
    assert main["runtime_1993_profile_activated"] is False
    assert main["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"


def test_r3_human_report_preserves_cautious_claims() -> None:
    s = (AUDIT / "PRIMARY_SOURCE_TABLE_AUDIT_R3.md").read_text(encoding="utf-8")
    assert "UFOTRI 4.0" in s and "KfK 5194" in s
    assert "80" in s and "d⁻¹" in s
    assert "0.0464/d" in s and "14.94 d" in s
    assert "potato HTO" in s and "Table 12" in s
    assert "P0=OPEN" in s and "NOT_ESTABLISHED" in s
