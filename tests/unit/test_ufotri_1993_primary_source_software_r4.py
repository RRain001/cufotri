"""R4 primary-document contracts: KfK5194 1993 software tables and earlier guides.

Only checks documentary evidence, not implementation of any original executable.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/v4/1993_upgrade"


def load(path: str) -> dict:
    result = yaml.safe_load((DOCS / path).read_text(encoding="utf-8"))
    assert isinstance(result, dict)
    return result


def test_1993_table2_to8_reclassified_as_software_not_physics() -> None:
    r = load("primary_source_software_and_crossedition_r4.yaml")
    assert r["edition"] == "UFOTRI_4_0_1993"
    assert r["source_1993"]["report"] == "KfK 5194"
    assert r["comparison_1991"]["report"] == "KfK 4853"
    assert r["comparison_1990"]["report"] == "KfK 4605"
    assert r["comparison_1990"]["per_parameter_reconciliation"] == "PENDING"
    assert r["runtime_physics_changed"] is False
    assert r["independent_scientific_review"] == "NOT_COMPLETED"
    assert r["original_executable_numeric_equivalence"] == "NOT_ESTABLISHED"
    tables = {t["number"]: t for t in r["table_2_to_8"]}
    assert set(tables) == set(range(2, 9))
    assert tables[2]["kind"] == tables[3]["kind"] == "NUMERICAL_LIBRARY"
    assert tables[4]["kind"] == "IO_CONTRACT"
    assert tables[5]["kind"] == "EXAMPLE_INPUT_NOT_DEFAULTS"
    assert tables[6]["kind"] == tables[7]["kind"] == "SOFTWARE_CALL_GRAPH"
    assert tables[8]["kind"] == "NUMERICAL_SOLVER_CALL_GRAPH"
    for number, p in {2: 80, 3: 80, 4: 81, 6: 84, 7: 85, 8: 85}.items():
        assert tables[number]["printed_page"] == p
        assert tables[number]["pdf_index"] == p + 9
    assert tables[5]["printed_page_start"] == 82
    assert tables[5]["printed_page_end"] == 83
    assert "95" in tables[4]["entries"]
    assert {"COMA1", "COMA1-EIGENS", "COMA2", "COMA2-CMACMP"}.issubset(set(tables[8]["entries"]))
    assert "BODENR-WATER" in tables[7]["entries"]
    assert "FOOBAN" in tables[6]["entries"]
    assert len(tables[6]["entries"]) == 25
    assert len(tables[7]["entries"]) == 11
    assert len(tables[8]["entries"]) == 6


@pytest.mark.parametrize(
    ("name", "old", "new"),
    [
        ("ISTRGR", 1000, 200),
        ("RCMIN", 4, 2),
        ("BEWG", 400, 1440),
        ("BEWGZ", 100, 160),
        ("LEAF", 3, 3),
        ("IMODEL", 1, 1),
        ("IMEAT", 300, 206),
        ("IVEGE", 500, 165),
        ("IMILK", 300, 315),
        ("DOSF", 1.7e-11, 1.7e-11),
        ("DOSHT", 1.7e-15, 1.7e-15),
        ("DOSFOB", 4.5e-11, 4.0e-11),
    ],
)
def test_1991_vs_1993_guide_default_provenance(
    name: str, old: float, new: float
) -> None:
    r = load("primary_source_software_and_crossedition_r4.yaml")
    by_name = {x["name"]: x for x in r["documented_1991_to_1993_defaults"]}
    assert len(by_name) == 16
    d = by_name[name]
    assert d["source_1991"]["documented_default"] == pytest.approx(old)
    assert d["target_1993"]["documented_default"] == pytest.approx(new)
    assert d["source_1990_exact_parameter_comparison"] == "NOT_YET_COMPLETED"


def test_1993_long_term_inputs_are_not_1991_legacy_configs() -> None:
    r = load("primary_source_software_and_crossedition_r4.yaml")
    controls = {x["parameter"]: x for x in r["long_term_ingestion_control"]}
    assert "6" in controls["NBOX/NINI/NINT/NOUT"]["old_rule"]
    assert "untested" in controls["NBOX/NINI/NINT/NOUT"]["new_rule"]
    assert controls["NTIM/TIMC"]["decision"] == "VERSIONED_INPUT_MIGRATION_REQUIRED"
    assert controls["NTFX"]["decision"] == "NO_INFERENCE_FROM_NUMBER_27_TO_GRAPH_EDGE_COUNT"


def test_1993_jcl_example_does_not_define_guide_defaults() -> None:
    r = load("primary_source_software_and_crossedition_r4.yaml")
    x = {d["name"]: d for d in r["example_not_default"]}
    assert set(x) == {"FAKC1", "FAKC2", "BRRATE", "DOSHT", "BEWGP"}
    assert x["FAKC1"]["guide_1993_default"] == pytest.approx(0.4)
    assert x["FAKC1"]["table_5_example_value"] == pytest.approx(0.2)
    assert x["DOSHT"]["guide_1993_default"] == pytest.approx(1.7e-15)
    assert x["DOSHT"]["table_5_example_value"] == pytest.approx(6.8e-16)
    assert x["BEWGP"]["guide_1993_default"] == 2400
    assert x["BEWGP"]["table_5_example_value"] == 2700


def test_table1_printed_g_vs_area_based_plant_input_g_per_m2() -> None:
    source = load("primary_source_transfer_tables_r3.yaml")
    table = source["table_1"]
    assert table["table_units_as_printed"] == "g"
    assert table["associated_1993_namelist_plant_mass_units"] == "g/m^2"
    assert "not interpret" in table["mass_basis"]
    assert table["normalization_audit"] == (
        "TABLE1_BARE_G_VS_TRIDAT_G_PER_M2_SOURCE_MAPPING_REQUIRES_VALIDATION"
    )


def test_matrix_reclassifies_dose_claim_without_1993_invention() -> None:
    m = load("physics_delta_matrix.yaml")
    row = next(x for x in m["rows"] if x["id"] == "UF93-22")
    assert row["classification"] == (
        "1993_DOSFOB_DEFAULT_CHANGED_VS_1991_1990_PHYSICS_REVIEW_PENDING"
    )
    assert "1991" in row["kfk5194_target_fact"]
    assert m["source_audit_r4_status"].endswith("P0_STILL_OPEN")
    assert m["runtime_1993_profile_activated"] is False
    report = (DOCS / "PRIMARY_SOURCE_SOFTWARE_AND_CROSSEDITION_R4.md").read_text(encoding="utf-8")
    assert "1993 KfK 5194" in report
    assert "g/m²" in report
    assert "NOT_ESTABLISHED" in report
    assert "P0" in report
