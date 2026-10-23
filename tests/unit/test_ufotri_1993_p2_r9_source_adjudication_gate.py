"""P2 R9: fail-closed traceability for unresolved KfK5194 Eq.(28)-(30).

This is a governance/source audit, NOT scientific acceptance of a canopy solver.
The original KfK5194 PDF is not shipped in the public repository.
"""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/v4/1993_upgrade"
SOURCE_HASH = "9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5"


def _gate():
    registry = yaml.safe_load((DOC / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    matches = [row for row in registry["rows"] if row["id"] == "UF93-13"]
    assert len(matches) == 1
    return registry, matches[0], matches[0]["p2_r9_source_gate"]


def test_r9_primary_page_and_edition_are_frozen_without_parity_claim():
    registry, row, gate = _gate()
    assert registry["target_version"] == "UFOTRI_4_0_1993"
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert row["implementation_phase"] == "P2"
    assert row["independent_scientific_review"] == "NOT_COMPLETED"
    assert gate["source_pdf_sha256"] == SOURCE_HASH
    assert gate["printed_page"] == 20
    assert gate["pdf_page_index_zero_based"] == 29
    assert not (ROOT / "3813483.pdf").exists()


def test_r9_source_ambiguities_remain_explicit_and_fail_closed():
    _, _, gate = _gate()
    assert gate["eq28_printed_vs_eq26_27_integral"] == "INCONSISTENT_TWO_TERMS"
    assert gate["eq29_co_unit_printed"] == "MG_CO2_M2_H"
    assert gate["eq26_pm_unit_printed"] == "G_CO2_M2_H"
    assert gate["eq29_co_to_pm_bridge"] == "NOT_ESTABLISHED"
    assert gate["eq30_w_unit_printed"] == "G_CO2_EQUIVALENT_PER_M2"
    for field in (
        "eq30_dry_matter_to_w_bridge",
        "eq30_respiration_area_basis",
        "eq28_eq30_original_solve_order",
    ):
        assert gate[field] == "NOT_ESTABLISHED"
    assert gate["original_executable_parity"] == "NOT_RUN"
    assert gate["independent_scientific_review"] == "NOT_RUN"
    assert gate["production_coupling_allowed"] is False


def test_r9_packet_and_human_matrix_match_machine_gate():
    _, _, gate = _gate()
    packet = ROOT / gate["audit_packet"]
    assert packet.is_file()
    page = packet.read_text(encoding="utf-8")
    index = (DOC / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
    for anchor in (
        "Eq.(28)", "Eq.(29)", "Eq.(30)", "printed p.20",
        SOURCE_HASH, "PRODUCTION_COUPLING_BLOCKED",
        "INDEPENDENT_REVIEW_NOT_RUN", "CO2 equivalents",
    ):
        assert anchor in page
    assert packet.name in index
    assert "UF93-13.p2_r9_source_gate" in index
    assert "1990 默认路径不变" in index


def test_r9_no_production_wiring_of_source_audit():
    # The R2/R8 conditional audit must remain separate from the frozen 1990
    # runtime and the active TFWT/OBT/CLI pathways.
    for relative_path in (
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "kfk5194_1993_photo_r2_audit" not in text
        assert "P2_R9_SOURCE_ADJUDICATION_GATE" not in text
