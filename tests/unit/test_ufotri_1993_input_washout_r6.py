"""1993 KfK 5194 R6 source-input and washout contracts, without enabling runtime physics."""
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "v4" / "1993_upgrade"


def read_yaml(name: str) -> dict:
    result = yaml.safe_load((DOCS / name).read_text(encoding="utf-8"))
    assert isinstance(result, dict)
    return result


def test_1993_source_version_status_and_page_anchors() -> None:
    r = read_yaml("primary_source_input_washout_r6.yaml")
    assert r["source_identity"]["target_model"] == "UFOTRI_4_0_1993"
    assert r["source_identity"]["report"] == "KfK 5194"
    assert "KfK 4605" in r["source_identity"]["baseline"]
    assert "KfK 4853" in r["source_identity"]["comparison"]
    assert r["scope"] == "PRIMARY_SOURCE_DOCUMENTATION_ONLY_NO_ACTIVE_SOLVER_OR_INPUT_PARSER"
    assert r["executable_equivalence"] == "NOT_ESTABLISHED"
    assert r["status"].endswith("P0_OPEN")
    assert r["source_page_indexing"] == "Printed page = PDF zero-based page - 9"
    for key in ("input_structure", "meteorology", "fixed_run", "diagnostics"):
        v = r[key]
        assert v["pdf_index"] == v["source_printed_page"] + 9


def test_original_namelist_input_order_is_conditional() -> None:
    inp = read_yaml("primary_source_input_washout_r6.yaml")["input_structure"]
    assert inp["mandatory_groups"] == ["METEOZON", "SOURCE", "END"]
    assert set(inp["optional_groups"]) == {
        "PRINTOUT", "POLGRID", "ISOTOPE", "METEOROL", "TRIDAT"
    }
    assert inp["ordering_edges"] == [
        ["ISOTOPE", "SOURCE"],
        ["POLGRID", "METEOZON"],
        ["PRINTOUT", "POLGRID"],
        ["END", "TRIDAT"],
    ]
    assert inp["tridat_after_end"] is True
    assert inp["terminal_ufotri_group"] == "END"
    assert "conditional" in inp["note"].lower()


def test_default_washout_is_class_based_not_power_law() -> None:
    s = read_yaml("primary_source_input_washout_r6.yaml")["isotope"]
    assert s["nuclide_order"] == ["HT", "HTO"]
    assert s["nuclide_count_default"] == 2
    assert s["deposition_velocity_m_per_s"] == [0.0005, 0.005]
    assert s["deposition_correction_factors"] == [1.0, 1.0]
    assert s["washout_mode_default"] == 0
    classes = s["mode_zero"]
    assert classes["label"] == "THREE_PRECIPITATION_CLASSES"
    assert classes["rain_class_boundaries_source_scaled"] == [100, 300]
    assert classes["source_unit"] == "0.01 mm/h"
    assert classes["physical_boundaries_mm_per_h"] == [1, 3]
    assert classes["hto_washout_rate_per_s"] == pytest.approx([6e-5, 1e-4, 4e-4])
    assert classes["hto_relative_precipitation_duration"] == pytest.approx([0.5, 0.75, 0.72])
    assert classes["ht_washout_rate_per_s"] == [0, 0, 0]
    advanced = s["mode_one"]
    assert advanced["label"] == "POWER_LAW"
    assert advanced["AWASH_HTO"] == pytest.approx(9e-5)
    assert advanced["BWASH_HTO"] == pytest.approx(0.6)
    assert advanced["AWASH_HT"] == 0
    assert advanced["BWASH_HT"] == 0


def test_original_scaled_meteorological_values_and_stationary_limits() -> None:
    r = read_yaml("primary_source_input_washout_r6.yaml")
    m = r["meteorology"]
    assert m["metin_default"] == 0 and m["noshft_default"] == 2
    assert m["iWNDG_default_scaled"] == 500
    assert m["iWNDG_unit"] == "0.01 m/s"
    assert m["iWNDG_physical_default_m_per_s"] == 5
    assert m["iREGN_unit"] == "0.01 mm/h"
    assert m["hght_default_m"] == [50, 100, 180]
    assert m["mixlh_default_m"] == [1600, 1200, 800, 560, 320, 200]
    assert m["wpe_default_by_category"] == pytest.approx(
        [0.07, 0.13, 0.21, 0.34, 0.44, 0.44]
    )
    f = r["fixed_run"]
    assert "testing" in f["original_advice"]
    assert f["irfix_default"] == 0
    assert f["refest_default"] == 5
    assert f["itempe_default_scaled"] == 1000
    assert f["itempe_derived_celsius"] == 10
    assert f["istrbe_source_unit"] == "Watt (as printed), not assumed W/m²"
    assert f["relfa_default"] == pytest.approx(0.5)
    assert "ambiguous" in f["relfa_dimension_warning"]


def test_output_switches_remain_diagnostics_not_physics_switches() -> None:
    r = read_yaml("primary_source_input_washout_r6.yaml")
    d = r["diagnostics"]
    assert d["ifachs_default"] == 28
    assert d["ieinr_defaults"] == [6, 8, 12, 16]
    assert d["izuaus_default"] == 0
    assert d["kausdr_default"] == [0] * 12
    assert set(d["known_diagnostic_routes"]).issuperset(
        {"4", "5", "7", "8", "9", "10", "11", "12"}
    )
    assert "not physical" in d["note"]


def test_r6_matrix_1993_washout_mode_is_correctly_classified() -> None:
    matrix = read_yaml("physics_delta_matrix.yaml")
    assert matrix["target_version"] == "UFOTRI_4_0_1993"
    assert matrix["runtime_1993_profile_activated"] is False
    assert matrix["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    assert matrix["input_washout_audit_r6"].endswith("primary_source_input_washout_r6.yaml")
    rows = {x["id"]: x for x in matrix["rows"]}
    assert len(rows) == 24
    assert rows["UF93-08"]["historical_1993_default_branch"] == (
        "IWASH_0_THREE_CLASSES_NOT_POWER_LAW"
    )
    assert rows["UF93-08"]["classification"] == (
        "1993_DOCUMENTED_WASHOUT_MODES_DEFAULT_BRANCH_VERIFIED"
    )
    assert rows["UF93-24"]["safety_review_flag"] == (
        "1993_LEGACY_SCALED_METPAR_AND_ORDERED_ISOPAR"
    )
    report = (DOCS / "PRIMARY_SOURCE_INPUT_WASHOUT_R6.md").read_text(encoding="utf-8")
    assert "1993" in report and "KfK 5194" in report
    assert "IWASH=0" in report and "IWASH=1" in report
    assert "P0=OPEN" in report and "NOT_ESTABLISHED" in report
