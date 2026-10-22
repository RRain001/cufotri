"""UFOTRI 1991/1993 primary manual card comparison (R8), not a runtime parser."""
from pathlib import Path

import yaml


DOCS = Path(__file__).resolve().parents[2] / "docs" / "v4" / "1993_upgrade"


def load(name: str) -> dict:
    data = yaml.safe_load((DOCS / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def rows() -> dict:
    return {x["id"]: x for x in load("primary_source_input_cards_crossedition_r8.yaml")["comparison_rows"]}


def test_version_scoped_sources_and_unactivated_acceptance() -> None:
    source = load("primary_source_input_cards_crossedition_r8.yaml")
    sources = source["sources"]
    assert sources["legacy_1991"]["report"] == "KfK 4853"
    assert sources["target_1993"]["report"] == "KfK 5194"
    assert sources["legacy_1991"]["printed_pages"] == [10, 11, 12, 13, 14, 15]
    assert sources["target_1993"]["printed_pages"] == [36, 37, 38, 39, 40, 41]
    assert sources["legacy_1991"]["pdf_zero_based_page_offset"] == 7
    assert sources["target_1993"]["pdf_zero_based_page_offset"] == 9
    assert source["status"].endswith("P0_OPEN")
    assert source["scope"].endswith("NOT_A_PARSER")
    limits = source["crossedition_findings"]
    assert limits["runtime_1993_profile_activated"] is False
    assert limits["parser_equivalence"] == "NOT_ESTABLISHED"
    assert limits["source_1990_full_input_comparison"] == "NOT_COMPLETED"
    assert limits["full_1991_to_1993_card_comparison"] == "NOT_COMPLETED"
    assert limits["independent_scientific_review"] == "NOT_COMPLETED"
    assert limits["original_executable_numeric_equivalence"] == "NOT_ESTABLISHED"
    assert limits["empirical_validation"] == "NOT_ESTABLISHED"


def test_meteozon_k1_2_printed_order_difference_not_assumed_parser_change() -> None:
    c = rows()["R8-02"]
    assert c["printed_format_both"] == "1X,A8,1X,2I10,5I5"
    shared = ["ZONNAM", "LMAX", "NSTMAX", "LPOPT", "LWOPT"]
    assert c["legacy_field_order"][:5] == c["target_field_order"][:5] == shared
    assert c["differing_last_three_legacy"] == ["IBEWE", "IRAU", "IHOM"]
    assert c["differing_last_three_target"] == ["IRAU", "IHOM", "IBEWE"]
    assert c["legacy_field_order"][5:] == c["differing_last_three_legacy"]
    assert c["target_field_order"][5:] == c["differing_last_three_target"]
    assert set(c["legacy_field_order"]) == set(c["target_field_order"])
    assert "SOURCE_LIMITED" in c["status"]
    assert "NOT VERIFIED" in c["interpretation"]


def test_source_k2_2_format_has_only_two_named_numeric_fields_in_both_versions() -> None:
    c = rows()["R8-05"]
    assert c["legacy_printed_format"] == "A8,2X,3I10,F10.2"
    assert c["target_printed_format"] == "A8,2X,2I10"
    assert c["shared_named_fields"] == ["UNFNAM", "NPHMAX", "IPZ"]
    assert "3I10 and F10.2" in c["legacy_printed_descriptor_count"]
    assert "two named integers" in c["target_printed_descriptor_count"]
    assert "SOURCE_LIMITED" in c["status"]
    assert "do not infer" in c["interpretation"]


def test_inherited_caps_branches_phases_and_end_card() -> None:
    r = rows()
    assert set(r) == {f"R8-{i:02d}" for i in range(1, 8)}
    assert r["R8-01"]["shared_values"] == {
        "NSITMX": 5, "LWMAX": 144, "NPHSMX": 17, "NTYPMX": 2,
        "NUCMAX": 2, "NRMAX": 20, "NPHIMX": 72
    }
    assert r["R8-03"]["shared_switches"]["LPOPT"] == {
        "0": "equal_probabilities", "1": "K1.4_PWET", "2": "NUNITS_13"
    }
    assert r["R8-03"]["shared_switches"]["LWOPT"] == {
        "0": "cyclic", "1": "K1.3_LWET_hours", "2": "NUNITS_13"
    }
    assert r["R8-03"]["shared_ibewe_rule"] == "IBEWE set to zero if LWOPT != 0"
    assert r["R8-04"]["status"].startswith("DIFFERENT_PRINTED_SCOPE")
    assert r["R8-04"]["legacy_pages"] == [12, 13]
    assert r["R8-04"]["target_pages"] == [38, 39]
    assert r["R8-06"]["shared_phase_fields"] == [
        "IPHASE(NP)", "IHO(NP)", "QH(NP)", "BR(NP)", "HOE(NP)"
    ]
    assert r["R8-06"]["shared_printed_format"] == "2I10,3E10.3"
    assert r["R8-06"]["shared_qh_units"] == "cal/s"
    assert "K2.4 referenced in both" in r["R8-06"]["shared_k2_4_reference"]
    assert r["R8-07"]["shared_format"] == "A8"
    assert r["R8-07"]["shared_field"] == "END"


def test_risk_ledger_guards_and_project_registry_links() -> None:
    data = load("primary_source_input_cards_crossedition_r8.yaml")
    risk = {x["id"]: x for x in data["risk_ledger"]}
    assert len(risk) == 5
    assert risk["SRC-R8-01"]["severity"] == "HIGH"
    assert "DO_NOT_IMPLEMENT" in risk["SRC-R8-01"]["disposition"]
    assert risk["SRC-R8-02"]["disposition"] == "SOURCE_LIMITED_NO_INFERRED_HIDDEN_FIELDS"
    assert "SRC-R8-04" in risk and "SRC-R8-05" in risk
    root = load("physics_delta_matrix.yaml")
    assert root["source_cards_crossedition_audit_r8"].endswith("primary_source_input_cards_crossedition_r8.yaml")
    assert root["target_version"] == "UFOTRI_4_0_1993"
    assert root["runtime_1993_profile_activated"] is False
    assert root["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert len(root["rows"]) == 24
    r7 = load("primary_source_meteozon_source_r7.yaml")
    assert r7["historical_1991_comparison"] == "NOT_COMPLETED"
    assert r7["meteozon"]["cards"][1]["fields"][-3:] == ["IRAU", "IHOM", "IBEWE"]


def test_report_preserves_discrepancies_and_unresolved_limits() -> None:
    report = (DOCS / "PRIMARY_SOURCE_INPUT_CARDS_CROSSEDITION_R8.md").read_text(encoding="utf-8")
    for needle in (
        "KfK 4853", "KfK 5194", "K1.2", "K2.2", "3I10,F10.2",
        "IBEWE", "IRAU", "IHOM", "K2.4", "cal/s", "SOURCE_LIMITED",
        "P0=OPEN", "ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED",
    ):
        assert needle in report
