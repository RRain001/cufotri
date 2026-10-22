"""KfK 4853/5194 printed JCL sample consistency: source-only R9, no parser."""
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "v4" / "1993_upgrade"


def read(name: str) -> dict:
    d = yaml.safe_load((DOC / name).read_text(encoding="utf-8"))
    assert isinstance(d, dict)
    return d


def samples() -> dict:
    return {r["id"]: r for r in read("primary_source_job_card_samples_r9.yaml")["compared_cards"]}


def test_r9_sources_are_printed_examples_not_runtime_evidence() -> None:
    x = read("primary_source_job_card_samples_r9.yaml")
    assert x["source_only"] is True
    assert x["source_status"].endswith("P0_OPEN")
    assert x["source_documents"]["1991"]["report"] == "KfK 4853"
    assert x["source_documents"]["1991"]["job_example"] == "Table 3"
    assert x["source_documents"]["1991"]["job_example_printed_page"] == 43
    assert x["source_documents"]["1991"]["job_example_pdf0_index"] == 50
    assert x["source_documents"]["1993"]["report"] == "KfK 5194"
    assert x["source_documents"]["1993"]["job_example"] == "Table 5"
    assert x["source_documents"]["1993"]["job_example_printed_page"] == 82
    assert x["source_documents"]["1993"]["job_example_pdf0_index"] == 91
    assert x["examples_kind"] == "SCANNED_PRINTED_JCL_USER_INPUT_NOT_ORIGINAL_FORTRAN_READ_OR_SUCCESSFUL_EXECUTION"
    assert set(samples()) == {f"R9-SAMPLE-{i:02}" for i in range(1, 6)}


def test_k2_2_three_printed_numbers_do_not_become_hidden_fields() -> None:
    r = samples()["R9-SAMPLE-01"]
    assert r["observed_source_name"] == "FKxy"
    assert r["following_numeric_tokens"] == ["1", "0", "0"]
    assert r["printed_manual_named_fields"] == ["UNFNAM", "NPHMAX", "IPZ"]
    assert r["printed_manual_formats"]["1991"] == "A8,2X,3I10,F10.2"
    assert r["printed_manual_formats"]["1993"] == "A8,2X,2I10"
    assert r["epistemic_status"] == "PRINTED_SAMPLE_FIELD_FORMAT_COUNT_CONFLICT_NO_PARSER_CLAIM"
    assert "original card bytes" in r["required_evidence"]
    assert "TWO integer fields" in r["mismatch"]


def test_k1_2_both_printed_examples_inadequate_for_column_exact_decode() -> None:
    r = samples()["R9-SAMPLE-03"]
    assert r["observed_zone_name"] == "KARLSRHE"
    assert r["visible_numeric_tokens"] == ["1", "1", "0", "1", "2", "10"]
    assert r["both_printed_format"] == "1X,A8,1X,2I10,5I5"
    assert r["named_field_order"]["1991"][-3:] == ["IBEWE", "IRAU", "IHOM"]
    assert r["named_field_order"]["1993"][-3:] == ["IRAU", "IHOM", "IBEWE"]
    assert "seven numeric positions" in r["count_risk"]
    assert r["epistemic_status"] == "PRINTED_EXAMPLE_VISUAL_TOKENS_NOT_COLUMN_EXACT_BYTES"
    assert "byte-preserving data" in r["required_evidence"]


def test_k2_3_thermal_source_and_4020_not_overinterpreted() -> None:
    p = samples()
    k23 = p["R9-SAMPLE-02"]
    assert k23["visible_phase_tokens"] == ["1", "20", "0.000E0", "0.000E0", "0.000E0"]
    assert k23["named_fields"] == [
        "IPHASE(NP)", "IHO(NP)", "QH(NP)", "BR(NP)", "HOE(NP)"
    ]
    assert k23["both_printed_format"] == "2I10,3E10.3"
    assert "cal/s" in k23["qh_meaning"]
    assert "not radiological" in k23["qh_meaning"]
    k13 = p["R9-SAMPLE-04"]
    assert k13["visible_tokens"] == ["4020"]
    assert k13["epistemic_status"] == "SAMPLE_CONTEXT_ONLY_DO_NOT_TREAT_4020_AS_VALIDATED_METEOROLOGY_DATA"


def test_source_risk_ledger_and_original_validation_boundaries() -> None:
    x = read("primary_source_job_card_samples_r9.yaml")
    risks = {v["id"]: v for v in x["discrepancy_registry"]}
    assert set(risks) == {f"SRC-R9-{i:02}" for i in range(1, 6)}
    assert risks["SRC-R9-01"]["status"] == "SOURCE_LIMITED"
    assert risks["SRC-R9-02"]["priority"] == "P0_HIGH"
    assert risks["SRC-R9-03"]["status"] == "SOURCE_LIMITED"
    assert "Do not map thermal QH" in risks["SRC-R9-05"]["action"]
    assert x["no_activation"] == {
        "P0": "OPEN",
        "original_1993_executable_equivalence": "NOT_ESTABLISHED",
        "1993_runtime_mode": "NOT_ACTIVATED",
        "empirical_validation": "NOT_ESTABLISHED",
        "independent_scientific_review": "NOT_COMPLETED",
        "historic_reader_recovery": "NOT_ESTABLISHED",
        "1990_frozen_baseline": "UNCHANGED",
    }
    master = read("physics_delta_matrix.yaml")
    assert master["printed_job_card_sample_audit_r9"].endswith("primary_source_job_card_samples_r9.yaml")
    assert master["runtime_1993_profile_activated"] is False
    assert master["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert len(master["rows"]) == 24


def test_r9_human_report_and_r8_source_matrix_stay_distinct() -> None:
    text = (DOC / "PRIMARY_SOURCE_JOB_CARD_SAMPLES_R9.md").read_text(encoding="utf-8")
    for fragment in (
        "KfK 4853", "KfK 5194", "Table 3", "Table 5", "p.43",
        "p.82", "FKxy", "KARLSRHE", "IBEWE/IRAU/IHOM",
        "IRAU/IHOM/IBEWE", "K2.4", "SOURCE_LIMITED",
        "ORIGINAL_EXECUTABLE_EQUIVALENCE=NOT_ESTABLISHED",
    ):
        assert fragment in text
    r8 = read("primary_source_input_cards_crossedition_r8.yaml")
    assert r8["crossedition_findings"]["parser_equivalence"] == "NOT_ESTABLISHED"
    assert r8["comparison_rows"][1]["differing_last_three_legacy"] == ["IBEWE", "IRAU", "IHOM"]
