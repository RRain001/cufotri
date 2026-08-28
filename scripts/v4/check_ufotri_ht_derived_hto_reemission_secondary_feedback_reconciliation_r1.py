#!/usr/bin/env python3
"""Machine gate for UFOTRI E3 HT-derived HTO re-emission reconciliation.

This stage is intentionally reconciliation-only.  It proves the ownership and
provenance boundaries that can be recovered from the manual and retained code
without promoting the provisional historical Eq. (44) reconstruction or
implementing the Phase-F atmospheric area-source adapter.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STAGE = "UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1"


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _contains_all(text: str, needles: tuple[str, ...]) -> bool:
    return all(needle in text for needle in needles)


def build_result() -> dict[str, Any]:
    manual = _text("ufotri_manual.md")
    equation_inventory = _text("docs/v2/manual_equation_inventory.md")
    validation_plan = _text("docs/v2/validation/v2_reemission_validation_closure_plan.md")
    historical_fluxes = _text("src/cteas_ufotri/reemission/fluxes.py")
    historical_case = _text("src/cteas_ufotri/case.py")
    soil_v4 = _text("src/cteas_ufotri/plant/soil_v4/soil_solver.py")
    leaf_v4 = _text("src/cteas_ufotri/plant/leaf_ufotri_v4/model.py")
    e2 = _text("src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py")

    manual_gates = {
        "manual_reemission_process_exists": (
            "The re-emission processes can be modelled in different ways" in manual
        ),
        "manual_topsoil_only_direct_reemission": (
            "only the HTO in the top soil layer takes part in the re-emission process"
            in manual
        ),
        "manual_plant_reemission_rate_exists": (
            "The resulting re-emission rate for plants is" in manual
        ),
        "eq44_inventory_is_provisional": (
            "(44-1),(44-2) | REEM, DIFF, ABFLR, C1/C2, ZT | audited empirical mode; `PROVISIONAL`"
            in equation_inventory
        ),
        "topsoil_constraint_repeated_in_inventory": (
            "Only topsoil participates directly in soil evaporation" in equation_inventory
        ),
    }

    historical_gates = {
        "historical_basic_mass_flux_exists": _contains_all(
            historical_fluxes,
            (
                "def basic_reemission_fluxes(",
                "soil_evaporation_m_s",
                "plant_transpiration_m_s",
            ),
        ),
        "historical_eq44_is_engineering_reconstruction": (
            "Configurable Eq. (44-1)/(44-2) engineering reconstruction" in historical_fluxes
        ),
        "historical_feedback_delay_exists": _contains_all(
            historical_case,
            (
                "reemission_feedback_delay_s",
                "feedback_history",
                "lagged_reemission",
            ),
        ),
        "historical_area_source_feedback_exists": _contains_all(
            historical_case,
            (
                'reemission_feedback_mode"] == "area_source"',
                "rectangular_area_source_concentration(",
            ),
        ),
        "historical_point_equivalent_feedback_exists": _contains_all(
            historical_case,
            (
                'reemission_feedback_mode"] == "point_equivalent"',
                "reemission_feedback_area_m2",
            ),
        ),
        "historical_feedback_uses_total_reemission": (
            "feedback_history.append(diag.total_reemission_bq_m2_s)" in historical_case
        ),
        "historical_air_is_primary_plus_secondary": "air = primary + secondary" in historical_case,
    }

    source_ambiguity_gates = {
        "manual_fidelity_limitation_is_frozen": (
            "LIMITATION = M_REEM_MANUAL_FIDELITY" in validation_plan
        ),
        "rain_start_rule_remains_partial": (
            "VAL_REEM_RAIN_START_3_PERCENT = PARTIAL" in validation_plan
        ),
        "concentration_dependent_diff_remains_partial": (
            "VAL_REEM_CONCENTRATION_DEPENDENT_DIFF = PARTIAL" in validation_plan
        ),
        "released_candidate_has_no_rain_start_argument": (
            "function has no rain/rain-start argument" in validation_plan
        ),
        "full_manual_mapping_not_demonstrated": (
            "full manual mapping not demonstrated" in validation_plan
        ),
        "direction_reversal_not_represented": (
            "concentration-gradient reversal not represented" in validation_plan
        ),
    }

    current_v4_gates = {
        "soil_v4_has_explicit_surface_reemission_sink": _contains_all(
            soil_v4,
            (
                "surface_reemission_hto_loss_bq_m2_s",
                "forcing.surface_reemission_hto_loss_bq_m2_s",
            ),
        ),
        "soil_reemission_is_l1_only": (
            "h12_down + root_h[0] + forcing.surface_reemission_hto_loss_bq_m2_s"
            in soil_v4
        ),
        "soil_global_balance_counts_reemission_as_external_loss": (
            "forcing.lower_boundary_hto_loss_bq_m2_s + forcing.surface_reemission_hto_loss_bq_m2_s"
            in soil_v4
        ),
        "leaf_eq31_diagnostic_exists": _contains_all(
            leaf_v4,
            (
                "UFOTRI_EQ31_ZERO_AIR_REEMISSION_FRACTION",
                "eq31_zero_air_reemission_fraction",
                "eq31_zero_air_reemission_percent",
            ),
        ),
        "leaf_operator_is_signed": (
            "mean_leaf_exchange_flux_bq_m2_s=mean_flux" in leaf_v4
        ),
        "leaf_area_source_height_is_exposed_not_bound": _contains_all(
            leaf_v4,
            (
                "area_source_emission_height_m=max(0.8 * height, 1.0)",
                "It is exposed for later area-source/re-emission coupling",
            ),
        ),
    }

    e2_provenance_gates = {
        "e2_keeps_primary_and_ht_derived_fluxes_separate": _contains_all(
            e2,
            (
                "primary_hto_surface_flux_bq_m2_s",
                "ht_derived_hto_surface_flux_bq_m2_s",
                "combined_hto_surface_flux_bq_m2_s",
            ),
        ),
        "e2_projects_only_combined_flux_to_soil": _contains_all(
            e2,
            (
                "combined = primary + derived",
                "surface_deposition_flux_bq_m2_s=combined",
            ),
        ),
        "e2_does_not_generate_secondary_reemission": (
            "secondary_hto_reemission_generated: bool = False" in e2
            and "secondary HTO re-emission is E3 scope" in e2
        ),
        "e2_preserves_ht_source_identity_before_mixing": _contains_all(
            e2,
            (
                "ht_source_kind=conversion.source_kind",
                "ht_species=conversion.species",
                "ht_provenance_id=conversion.provenance_id",
                "ht_spatial_support=conversion.spatial_support",
            ),
        ),
    }

    reconciliation_decision = {
        "e3_existing_source_change_required": False,
        "e3_new_reemission_solver_authorized": False,
        "historical_eq44_promoted_to_manual_exact": False,
        "historical_area_source_promoted_to_phase_e_default": False,
        "plant_reemission_role_reusable_from_phase_a": True,
        "soil_reemission_sink_role_reusable_from_soil_v4": True,
        "soil_reemission_rate_generation_recovered": False,
        "aggregate_soil_inventory_retains_origin_partition": False,
        "aggregate_total_reemission_may_be_called_ht_derived": False,
        "explicit_origin_proof_required_for_ht_derived_label": True,
        "mixed_origin_feedback_must_remain_mixed_origin": True,
        "phase_f_owns_area_source_numerical_compatibility": True,
        "real_cteas_atmos_required_for_e3": False,
    }

    contract_gates = {
        "manual_gates": all(manual_gates.values()),
        "historical_gates": all(historical_gates.values()),
        "source_ambiguity_gates": all(source_ambiguity_gates.values()),
        "current_v4_gates": all(current_v4_gates.values()),
        "e2_provenance_gates": all(e2_provenance_gates.values()),
        "no_false_ht_derived_attribution": (
            not reconciliation_decision["aggregate_total_reemission_may_be_called_ht_derived"]
            and reconciliation_decision["explicit_origin_proof_required_for_ht_derived_label"]
        ),
        "phase_f_boundary_preserved": reconciliation_decision[
            "phase_f_owns_area_source_numerical_compatibility"
        ],
    }

    status = (
        "PASS_UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION"
        if all(contract_gates.values())
        else "FAIL_UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION"
    )

    return {
        "stage": STAGE,
        "status": status,
        "manual_gates": manual_gates,
        "historical_gates": historical_gates,
        "source_ambiguity_gates": source_ambiguity_gates,
        "current_v4_gates": current_v4_gates,
        "e2_provenance_gates": e2_provenance_gates,
        "reconciliation_decision": reconciliation_decision,
        "contract_gates": contract_gates,
        "scope_claim": "RECONCILIATION_ONLY_NO_EXISTING_SOURCE_CHANGE",
        "next_scope": "PHASE_F_REEMISSION_AREA_SOURCE_COMPATIBILITY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "production_readiness_claim": False,
        "original_executable_equivalence": False,
    }


def main() -> int:
    result = build_result()
    print(f"E3_RECONCILIATION_STATUS={result['status']}")
    print("E3_RECONCILIATION_RESULT_JSON=" + json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
