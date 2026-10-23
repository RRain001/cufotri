"""P2 R10 bibliography provenance: publisher abstracts are not equation validation."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"


def _source_row():
    registry = yaml.safe_load((DOC / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    rows = [row for row in registry["rows"] if row["id"] == "UF93-13"]
    assert len(rows) == 1
    return registry, rows[0]


def test_r10_two_original_bibliographic_identities_are_pinned():
    _, row = _source_row()
    evidence = row["p2_r10_bibliography_evidence"]
    assert evidence["evidence_level"] == "PUBLISHER_METADATA_AND_ABSTRACT_ONLY"
    assert evidence["weir_1984"]["kfk5194_reference"] == "39"
    assert evidence["weir_1984"]["doi"] == "10.1017/S0021859600042702"
    assert evidence["mitchell_1991"]["kfk5194_reference"] == "21"
    assert evidence["mitchell_1991"]["doi"] == "10.1093/oxfordjournals.aob.a088102"
    assert evidence["mitchell_1991"]["abstract_respiration_normalization"] == "PER_UNIT_DRY_MASS"


def test_r10_full_text_and_derived_equations_remain_unverified():
    _, row = _source_row()
    evidence = row["p2_r10_bibliography_evidence"]
    assert evidence["weir_1984"]["full_text_equation_review"] == "NOT_RUN"
    assert evidence["weir_1984"]["eq29_co_to_pm_bridge"] == "NOT_ESTABLISHED"
    assert evidence["mitchell_1991"]["full_text_equation_review"] == "NOT_RUN"
    assert evidence["mitchell_1991"]["eq30_dry_matter_to_w_bridge"] == "NOT_ESTABLISHED"
    assert evidence["mitchell_1991"]["eq30_respiration_area_basis"] == "NOT_ESTABLISHED"
    assert evidence["independent_scientific_review"] == "NOT_RUN"
    assert evidence["production_coupling_allowed"] is False


def test_r10_r9_scientific_block_and_1990_default_remain_intact():
    registry, row = _source_row()
    gate = row["p2_r9_source_gate"]
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["runtime_1993_profile_activated"] is False
    assert gate["eq28_printed_vs_eq26_27_integral"] == "INCONSISTENT_TWO_TERMS"
    assert gate["eq29_co_to_pm_bridge"] == "NOT_ESTABLISHED"
    assert gate["eq30_respiration_area_basis"] == "NOT_ESTABLISHED"
    assert gate["independent_scientific_review"] == "NOT_RUN"
    assert gate["production_coupling_allowed"] is False


def test_r10_audit_document_is_linked_and_declares_limits():
    _, row = _source_row()
    evidence = row["p2_r10_bibliography_evidence"]
    packet = ROOT / evidence["audit_packet"]
    assert packet.is_file()
    page = packet.read_text(encoding="utf-8")
    index = (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
    for text in ("10.1017/S0021859600042702",
                 "10.1093/oxfordjournals.aob.a088102",
                 "PRODUCTION_COUPLING_BLOCKED", "NOT_RUN",
                 "dry mass", "1990"):
        assert text in page
    assert packet.name in index
