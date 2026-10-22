"""Source-card-only checks for KfK 5194 (1993) P0 R7; not physics tests."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "docs" / "v4" / "1993_upgrade"


def _read(name: str) -> dict:
    value = yaml.safe_load((DIR / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r7_version_page_anchors_and_unactivated_mode() -> None:
    d = _read("primary_source_meteozon_source_r7.yaml")
    assert d["target_version"] == "UFOTRI_4_0_1993"
    assert d["target_report"] == "KfK 5194"
    assert d["source_url"].startswith("https://publikationen.bibliothek.kit.edu/")
    assert d["source_checked_printed_pages"] == [36, 37, 38, 39, 40, 41]
    assert d["pdf_zero_based_page_offset"] == 9
    assert d["evidence_kind"] == "PRINTED_GUIDE_CARD_SPECIFICATION_NOT_ORIGINAL_PARSER"
    assert d["status"].endswith("P0_OPEN")
    assert d["historical_1991_comparison"] == "NOT_COMPLETED"
    assert d["independent_scientific_review"] == "NOT_COMPLETED"
    assert d["original_executable_equivalence"] == "NOT_ESTABLISHED"
    assert d["runtime_1993_profile_activated"] is False


def test_historical_compile_caps_are_not_input_defaults() -> None:
    d = _read("primary_source_meteozon_source_r7.yaml")
    c = d["array_caps"]
    assert c["pdf_index"] == c["printed_page"] + 9
    assert c["values"] == {
        "NSITMX": 5, "LWMAX": 144, "NPHSMX": 17,
        "NTYPMX": 2, "NUCMAX": 2, "NRMAX": 20, "NPHIMX": 72
    }
    assert "NOT actual defaults" in c["meaning"]


def test_meteozon_sampling_branches_not_conflated() -> None:
    d = _read("primary_source_meteozon_source_r7.yaml")
    m = d["meteozon"]
    assert m["pdf_indices"] == [p + 9 for p in m["printed_pages"]]
    cards = {row["id"]: row for row in m["cards"]}
    assert cards["K1.2"]["fields"] == [
        "ZONNAM", "LMAX", "NSTMAX", "LPOPT", "LWOPT", "IRAU", "IHOM", "IBEWE"
    ]
    assert cards["K1.3"]["when"] == "LWOPT_EQ_1"
    assert cards["K1.4"]["when"] == "LPOPT_EQ_1"
    assert m["selectors"]["LPOPT"] == {
        "0": "UNIFORM_PWET_EQUALS_ONE_OVER_LMAX",
        "1": "PWET_IN_K1_4",
        "2": "PWET_FROM_NUNITS_13",
    }
    assert m["selectors"]["LWOPT"] == {
        "0": "CYCLIC_SAMPLING",
        "1": "LWET_IN_K1_3",
        "2": "LWET_FROM_NUNITS_13",
    }
    assert any("sum over L = 1" in rule for rule in m["invariants"])
    assert m["data_files"]["weather_sequence"] == "NUNITS(13)"
    assert m["weather_sequence_spacing_printed_behavior"].startswith("if LWOPT != 0")
    assert "COSYMA_RELEVANT_NOT_CONSIDERED_IN_UFOTRI" in cards["K1.5-K1.7"]["scope"]


def test_source_phases_thermal_power_is_not_activity() -> None:
    d = _read("primary_source_meteozon_source_r7.yaml")
    src = d["source_group"]
    assert src["printed_page"] == 40 and src["pdf_index"] == 49
    assert src["max_phase_count"] == d["array_caps"]["values"]["NPHSMX"] == 17
    cards = {c["id"]: c for c in src["cards"]}
    assert cards["K2.2"]["fields"] == ["UNFNAM", "NPHMAX", "IPZ"]
    assert cards["K2.3"]["fields"] == [
        "IPHASE(NP)", "IHO(NP)", "QH(NP)", "BR(NP)", "HOE(NP)"
    ]
    f = {v["name"]: v for v in src["source_fields"]}
    assert f["IPHASE(NP)"]["units"] == "whole hour"
    assert f["IPZ"]["units"].startswith("time unit NOT_EXPLICIT")
    assert f["QH(NP)"]["units"] == "cal/s"
    assert "Q1(J)" in f["QH(NP)"]["not_equivalent_to"]
    assert "REFERENCED_BUT_NOT_SHOWN" in src["additional_phase_card_K2_4"]
    assert src["full_parser_equivalence"] == "NOT_ESTABLISHED"


def test_end_input_is_not_physical_acceptance() -> None:
    d = _read("primary_source_meteozon_source_r7.yaml")
    end = d["end_group"]
    assert end["printed_page"] == 41 and end["pdf_index"] == 50
    assert end["fields"] == ["END"]
    assert end["original_parser_success_message"] == "END OF INPUT WITHOUT ERRORS"
    assert end["not_a_scientific_validation_marker"] is True
    assert any("Do not convert QH" in note for note in d["safety_boundaries"])
    master = _read("physics_delta_matrix.yaml")
    assert master["target_version"] == "UFOTRI_4_0_1993"
    assert master["runtime_1993_profile_activated"] is False
    assert master["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    assert master["historical_source_cards_audit_r7"].endswith("primary_source_meteozon_source_r7.yaml")
    assert len(master["rows"]) == 24


def test_r7_human_report_states_scientific_limitations() -> None:
    text = (DIR / "PRIMARY_SOURCE_METEOZON_SOURCE_R7.md").read_text(encoding="utf-8")
    for name in ("KfK 5194", "METEOZON", "SOURCE", "END", "QH(NP)",
                 "cal/s", "Q1(J)", "PWET", "NPHSMX", "K2.4"):
        assert name in text
    assert "P0=OPEN" in text
    assert "ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED" in text
