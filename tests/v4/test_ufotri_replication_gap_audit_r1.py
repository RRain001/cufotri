from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "docs/v4/governance/ufotri_replication_gap_audit_r1.yaml"
ADR = ROOT / "docs/v4/adr/ADR-058-ufotri-replication-gap-audit-r1.md"
REPORT = ROOT / "docs/v4/reports/ufotri_replication_gap_audit_r1.md"
CURRENT_STATE = ROOT / "docs/v4/governance/v4_current_system_state.yaml"


def _audit() -> dict:
    return yaml.safe_load(GOVERNANCE.read_text(encoding="utf-8"))


def test_replication_audit_is_governance_only_and_preserves_rc1_boundaries() -> None:
    audit = _audit()
    hard = audit["hard_boundaries"]

    assert audit["stage"] == "UFOTRI_REPLICATION_GAP_AUDIT_R1"
    assert audit["base_main_sha"] == "38f9d5f5a863e195e7140444829d0e674acca6fc"
    assert audit["base_main_tree"] == "8a0c9f14f04629273740733282c567ba7d63c36b"
    assert hard["rc1_baseline_modified"] is False
    assert hard["solver_physics_modified"] is False
    assert hard["src_modified"] is False
    assert hard["production_input_work_reopened"] is False
    assert hard["real_cteas_atmos_binding_reopened"] is False
    assert hard["empirical_validation_claimed"] is False
    assert hard["physical_accuracy_claimed"] is False


def test_original_source_limit_forbids_exact_numerical_equivalence_claim() -> None:
    limits = _audit()["authority_and_limits"]

    assert limits["ufotri_manual_available"] is True
    assert limits["ufotri_original_source_code_available"] is False
    assert limits["ufotri_original_executable_available"] is False
    assert limits["original_parameter_loader_available"] is False
    assert limits["exact_original_numerical_regression_possible"] is False
    assert limits["manual_based_functional_reconstruction_auditable"] is True
    assert limits["full_ufotri_manual_based_replication_complete"] is False
    assert limits["original_ufotri_numerical_equivalence_established"] is False


def test_matrix_is_complete_unique_and_summary_counts_match() -> None:
    audit = _audit()
    rows = audit["replication_matrix"]
    ids = [row["id"] for row in rows]
    statuses = Counter(row["status"] for row in rows)

    assert len(rows) == 30
    assert len(ids) == len(set(ids))
    assert ids == [f"UFR-{index:02d}" for index in range(1, 31)]

    expected = {
        key: value
        for key, value in audit["summary_counts"].items()
        if key != "total_items"
    }
    assert audit["summary_counts"]["total_items"] == 30
    assert dict(statuses) == expected
    assert set(statuses) == set(audit["classification_ontology"])


def test_leaf_decision_requires_manual_reconciliation_not_current_r5_candidate() -> None:
    decision = _audit()["candidate_extension_decisions"]["leaf_r5"]

    assert decision["decision"] == "CURRENT_R5_AS_DESIGNED_NOT_REQUIRED_FOR_REPLICATION"
    assert decision["replication_need"] == "UFOTRI_LEAF_EQ7_31_FIDELITY_RECONCILIATION_REQUIRED"
    assert decision["next_stage"] == "UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1"

    matrix = {row["id"]: row for row in _audit()["replication_matrix"]}
    assert matrix["UFR-07"]["status"] == "MANUAL_ROLE_COVERED"
    assert matrix["UFR-08"]["status"] == "PARTIAL_RECONSTRUCTION"
    assert matrix["UFR-09"]["status"] == "HISTORICAL_IMPLEMENTATION_NOT_IN_RC1"


def test_richards_darcy_is_a_real_manual_replication_gap_but_scope_is_narrow() -> None:
    audit = _audit()
    decision = audit["candidate_extension_decisions"]["richards_darcy"]
    matrix = {row["id"]: row for row in audit["replication_matrix"]}

    assert decision["decision"] == "REPLICATION_REQUIRED_MANUAL_EQ33_37"
    assert decision["replication_need"] == "UFOTRI_EQ33_37_SOIL_HYDROLOGY_REQUIRED"
    assert matrix["UFR-11"]["status"] == "NOT_IMPLEMENTED"
    assert matrix["UFR-11"]["required_for_manual_reconstruction"] is True
    assert "caller-supplied" in matrix["UFR-11"]["replication_gap"]


def test_multi_pool_decision_is_limited_to_ufotri_exchangeable_nonexchangeable_semantics() -> None:
    audit = _audit()
    decision = audit["candidate_extension_decisions"]["multi_pool_obt"]
    matrix = {row["id"]: row for row in audit["replication_matrix"]}

    assert decision["decision"] == "REPLICATION_REQUIRED_IN_NARROW_UFOTRI_FORM_ONLY"
    assert decision["replication_need"] == "UFOTRI_EXCHANGEABLE_NONEXCHANGEABLE_OBT_COMPARTMENTS_REQUIRED"
    assert decision["next_decision_stage"] == "UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1"
    assert matrix["UFR-18"]["status"] == "PARTIAL_RECONSTRUCTION"
    assert matrix["UFR-19"]["status"] == "NOT_IMPLEMENTED"


def test_audit_exposes_other_mandatory_gaps_and_selects_only_leaf_reconciliation_next() -> None:
    audit = _audit()
    matrix = {row["id"]: row for row in audit["replication_matrix"]}
    ranking = audit["post_audit_ranking"]
    hard = audit["hard_boundaries"]

    assert matrix["UFR-05"]["process"] == "HT_PRIMARY_ATMOSPHERIC_TRANSPORT"
    assert matrix["UFR-05"]["status"] == "NOT_IMPLEMENTED"
    assert matrix["UFR-06"]["process"] == "HT_TO_HTO_SOIL_CONVERSION"
    assert matrix["UFR-06"]["status"] == "NOT_IMPLEMENTED"
    assert matrix["UFR-26"]["status"] == "PROJECT_REPLACEMENT_NOT_EQUIVALENT"
    assert matrix["UFR-27"]["status"] == "NOT_IMPLEMENTED_AS_VALIDATION"
    assert matrix["UFR-28"]["status"] == "NOT_IMPLEMENTED_AS_VALIDATION"

    assert ranking["immediate_internal_next_stage"] == "UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1"
    assert hard["leaf_r5_implementation_authorized"] is False
    assert hard["generic_multi_pool_obt_implementation_authorized"] is False
    assert hard["generic_full_hydrology_implementation_authorized"] is False
    assert hard["next_stage_authorized_after_clean_merge"] == "UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1"


def test_rc1_current_state_remains_frozen_and_complete() -> None:
    current = yaml.safe_load(CURRENT_STATE.read_text(encoding="utf-8"))

    assert current["current_state_stage"] == "V4_DEVELOPMENT_BASELINE_RC1"
    assert current["project_phase"] == "INTERNAL_V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE"
    assert current["completion_target"]["achieved"] is True
    assert current["development_baseline_rc1"]["selected_internal_baseline_frozen"] is True
    assert current["development_baseline_rc1"]["mandatory_internal_stage_count_remaining"] == 0
    assert current["readiness_boundaries"]["full_model_production_ready"] is False
    assert current["readiness_boundaries"]["real_cteas_atmos_binding"] is False


def test_adr_and_report_carry_the_same_non_claims_and_candidate_decisions() -> None:
    adr = ADR.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for token in (
        "CURRENT_R5_AS_DESIGNED_NOT_REQUIRED_FOR_REPLICATION",
        "REPLICATION_REQUIRED_MANUAL_EQ33_37",
        "REPLICATION_REQUIRED_IN_NARROW_UFOTRI_FORM_ONLY",
        "UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1",
    ):
        assert token in adr
        assert token in report

    assert "UFOTRI_FULL_REPLICATION_COMPLETE" in report
    assert "UFOTRI_ORIGINAL_EXECUTABLE_NUMERICAL_EQUIVALENCE_ESTABLISHED" in report
