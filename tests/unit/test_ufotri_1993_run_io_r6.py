"""Source-only guard for KfK 5194 (1993) run and input contracts.

The source registry is not an activated solver or a numeric parity test.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "v4" / "1993_upgrade"


def _read(filename: str) -> dict:
    value = yaml.safe_load((BASE / filename).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_target_edition_and_explicit_non_activation() -> None:
    doc = _read("primary_source_run_io_contract_r6.yaml")
    assert doc["document_kind"] == "UFOTRI_1993_V4_PRIMARY_INPUT_AUDIT_R6"
    assert doc["target_version"] == "UFOTRI_4_0_1993"
    assert doc["report"] == "KfK 5194"
    assert doc["comparison_1991"]["report"] == "KfK 4853"
    assert doc["status"] == "SELECTED_PRINTED_INPUT_PAGES_CHECKED_FULL_P0_OPEN"
    assert doc["runtime_1993_profile_activated"] is False
    assert doc["numerical_equivalence_to_original"] == "NOT_ESTABLISHED"
    assert doc["independent_scientific_review"] == "NOT_COMPLETED"
    for section in doc["source_sections"]:
        assert len(section["print_pages"]) == len(section["pdf_indices"])
        assert all(i == p + 9 for p, i in zip(section["print_pages"], section["pdf_indices"]))


def test_1993_source_truncation_reemission_and_hourly_input_controls() -> None:
    doc = _read("primary_source_run_io_contract_r6.yaml")
    inputs = {row["name"]: row for row in doc["control_parameters"]}
    assert len(inputs) == 28
    assert inputs["BODFAK"]["default"] == 100
    assert inputs["BODFAK"]["impact"] == "CHANGES_AREA_SOURCE_CUTOFF_AND_COMPUTATIONAL_COST"
    assert inputs["NSTOP"]["default"] == 70
    assert inputs["IFLENG"]["default"] == 0
    assert "14 grid points" in inputs["IFLENG"]["meaning"]
    assert "6 points" in inputs["IFLENG"]["meaning"]
    assert inputs["ZEIT"]["default"] == 3600
    assert float(inputs["CHIMAX"]["default"]) == pytest.approx(1.0e-15)
    assert inputs["LT1"]["default"] == 90
    assert inputs["LT4"]["default"] == 670
    assert inputs["Q(NN,J)"]["default_raw"] == "17*0.,17*1."
    assert inputs["Q1(J)"]["default_raw"] == "17*1."
    rec = doc["recommended_not_default"][0]
    assert rec["parameter"] == "BODFAK"
    assert [v["value"] for v in rec["conditions"]] == [1,100,10,0.1]


def test_1993_primary_source_contradictions_not_automatically_corrected() -> None:
    doc = _read("primary_source_run_io_contract_r6.yaml")
    conflicts = {x["parameter"]: x for x in doc["source_conflicts"]}
    assert set(conflicts) == {"IZFREI", "RELFA", "NSTOP", "METEO_FILE", "BODFAK"}
    assert conflicts["IZFREI"]["printed_condition"] == "0 < IZFREI < 3600"
    assert conflicts["IZFREI"]["printed_default"] == "3600"
    assert "UNRESOLVED" in conflicts["IZFREI"]["resolution"]
    assert conflicts["RELFA"]["printed_default"] == "0.5"
    # KfK5194 printed p51 uses two descriptions for the reference
    # concentration; a matching numerical source-threshold rule is unproven.
    assert "soil concentration" in conflicts["BODFAK"]["printed_prose_label"]
    assert "air concentration" in conflicts["BODFAK"]["printed_parameter_label"]
    assert "UNRESOLVED" in conflicts["BODFAK"]["resolution"]
    inputs = {x["name"]: x for x in doc["control_parameters"]}
    assert inputs["IRFIX"]["default"] == 0
    assert "testing" in inputs["IRFIX"]["meaning"]
    assert inputs["REFEST"]["default"] == 5.0
    assert inputs["IWRITE"]["default"] == 0
    assert "unit 9" in inputs["IWRITE"]["meaning"]


def test_1991_to_1993_fixed_mode_defaults_remained_equal() -> None:
    doc = _read("primary_source_run_io_contract_r6.yaml")
    names = doc["historical_1991_comparison"]["fields"]
    assert names == ["IRFIX", "REFEST", "ITEMPE", "ISTRBE", "RELFA"]
    assert "UNCHANGED" in doc["historical_1991_comparison"]["verdict"]
    # Some historical controls are Fortran repeat initializers, recorded as
    # default_raw rather than a scalar default. Restrict this comparison to
    # the five source-matched stationary controls with numeric defaults.
    vals = {
        x["name"]: x["default"]
        for x in doc["control_parameters"]
        if x["name"] in names
    }
    assert [vals[x] for x in names] == [0,5.0,1000,100,0.5]


def test_fortran_daily_met_record_schema_kept_separate_from_modern_forcing() -> None:
    m = _read("primary_source_run_io_contract_r6.yaml")["meteorology_direct_access"]
    assert m["print_page"] == 69
    assert m["pdf_index"] == 78
    assert m["interval_s"] == 3600
    assert m["subrecord_index"] == "J=1..24"
    assert m["fields"] == [
        "WR", "IDIFF", "IRAIN", "WG", "ITEMP", "ISTRB",
        "RELF", "ISOIL1", "ISOIL2", "ISOIL3"
    ]
    assert "not" in m["evidence_status"].lower()
    assert "endianness" in m["software_format"]
    matrix = _read("physics_delta_matrix.yaml")
    assert matrix["target_version"] == "UFOTRI_4_0_1993"
    assert matrix["runtime_1993_profile_activated"] is False
    assert matrix["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"


def test_1993_r6_human_readme_is_source_limited() -> None:
    text = (BASE / "PRIMARY_SOURCE_RUN_IO_AUDIT_R6.md").read_text(encoding="utf-8")
    assert "KfK 5194" in text and "1993" in text
    for label in ("BODFAK", "NSTOP", "IFLENG", "CHIMAX", "IZFREI", "RELFA",
                  "KAUSDR", "IWRITE", "ISOIL3", "IBODFX"):
        assert label in text
    assert "P0=OPEN" in text
    assert "ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED" in text
