#!/usr/bin/env python3
"""Machine-visible D4 qualification for UFOTRI cow/milk/beef closure."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.foodchain.ufotri_cow_milk_beef_v4 import (
    MANUAL_GRASS_SURROGATE_ONLY,
    UFOTRICowMilkBeefForcing,
    UFOTRICowMilkBeefSolver,
    UFOTRICowMilkBeefState,
    slaughter_to_beef,
    ufotri_cow_milk_beef_manual_profile,
)

UTC = timezone.utc
STAGE = "UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1"
STATUS = "PASS_UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE"
T0 = datetime(2026, 1, 1, tzinfo=UTC)
DAY_S = 86400.0


def _state() -> UFOTRICowMilkBeefState:
    return UFOTRICowMilkBeefState(
        timestamp=T0,
        grass_hto_bq_m2=100.0,
        grass_obt_bq_m2=50.0,
        cow_hto_bq_m2=25.0,
        cow_obt_bq_m2=10.0,
    )


def _forcing(atmosphere: float = 1000.0) -> UFOTRICowMilkBeefForcing:
    return UFOTRICowMilkBeefForcing(
        atmosphere_hto_inventory_bq_m2=atmosphere,
        atmosphere_provenance="SYNTHETIC_D4_CONTROLLED_COLUMN",
        feed_mode=MANUAL_GRASS_SURROGATE_ONLY,
    )


def _vector(state: UFOTRICowMilkBeefState) -> tuple[float, ...]:
    return (
        state.grass_hto_bq_m2,
        state.grass_obt_bq_m2,
        state.cow_hto_bq_m2,
        state.cow_obt_bq_m2,
        state.milk_hto_bq_m2,
        state.milk_obt_bq_m2,
        state.beef_hto_bq_m2,
        state.beef_obt_bq_m2,
    )


def _max_relative_state_error(
    candidate: UFOTRICowMilkBeefState,
    reference: UFOTRICowMilkBeefState,
) -> float:
    c = _vector(candidate)
    r = _vector(reference)
    scale = max(max(abs(value) for value in r), 1.0)
    return max(abs(a - b) for a, b in zip(c, r)) / scale


def build_result() -> dict[str, Any]:
    p = ufotri_cow_milk_beef_manual_profile()
    solver = UFOTRICowMilkBeefSolver(p, numerical_step_seconds=3600.0)

    one_day = solver.advance(_state(), _forcing(), DAY_S)
    repeat = solver.advance(_state(), _forcing(), DAY_S)

    half = solver.advance(_state(), _forcing(), DAY_S / 2.0)
    restarted = solver.advance(half.state, _forcing(), DAY_S / 2.0)

    partition_state = _state()
    for _ in range(24):
        partition_state = solver.advance(
            partition_state, _forcing(), 3600.0
        ).state

    grass_obt_only = UFOTRICowMilkBeefState(timestamp=T0, grass_obt_bq_m2=100.0)
    grass_routes = solver.advance(grass_obt_only, _forcing(0.0), 3600.0)

    atmosphere_only = UFOTRICowMilkBeefState(timestamp=T0)
    eq98 = solver.advance(atmosphere_only, _forcing(1000.0), DAY_S)

    zero = solver.advance(
        UFOTRICowMilkBeefState(timestamp=T0),
        _forcing(0.0),
        DAY_S,
    )

    slaughter_start = UFOTRICowMilkBeefState(
        timestamp=T0,
        cow_hto_bq_m2=80.0,
        cow_obt_bq_m2=20.0,
        beef_hto_bq_m2=3.0,
        beef_obt_bq_m2=2.0,
    )
    slaughter_state, slaughter_balance = slaughter_to_beef(slaughter_start, 0.25)

    duration = 30.0 * DAY_S
    reference = UFOTRICowMilkBeefSolver(
        p, numerical_step_seconds=225.0
    ).advance(_state(), _forcing(), duration).state
    refinement_errors: dict[str, float] = {}
    for step in (3600.0, 1800.0, 900.0, 450.0):
        candidate = UFOTRICowMilkBeefSolver(
            p, numerical_step_seconds=step
        ).advance(_state(), _forcing(), duration).state
        refinement_errors[str(int(step))] = _max_relative_state_error(candidate, reference)

    profile_gates = {
        "eq82_exact_half_time_visible": math.isclose(
            p.cow_water_overall_loss_exact_d_1,
            math.log(2.0) / 3.5,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
        "eq98_exact_geometry_visible": math.isclose(
            p.atmosphere_to_cow_hto_eq98_exact_d_1,
            4.875e-5,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
        "eq98_manual_rounding_preserved": p.atmosphere_to_cow_hto_manual_rounded_d_1 == 4.9e-5,
        "eq105_2_identity": math.isclose(
            p.grass_obt_eq105_2_reconstructed_d_1,
            p.grass_obt_to_grass_hto_d_1,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
        "cow_hto_manual_rounding_tension_preserved": p.cow_hto_total_hazard_d_1 == 0.2014,
        "cow_obt_manual_rounding_tension_preserved": p.cow_obt_total_hazard_d_1 == 0.0171,
        "eq86_ocr_ambiguity_explicit": p.eq86_heading_ocr_ambiguous
        and p.eq86_role_resolved_from_compartment_indices_and_context,
        "project_feed_not_activated": not p.project_external_feed_activated,
        "project_drinking_water_not_activated": not p.project_drinking_water_activated,
        "project_support_area_not_activated": not p.project_support_area_normalization_activated,
        "continuous_beef_turnover_not_activated": not p.continuous_beef_turnover_activated,
        "edible_beef_mass_default_not_activated": not p.edible_beef_mass_default_activated,
        "production_binding_not_authorized": not p.production_binding_authorized,
        "original_discretization_not_claimed": not p.original_numerical_discretization_recovered,
    }

    numerical_gates = {
        "one_day_activity_balance": abs(one_day.balance.residual_bq_m2) <= 1.0e-11,
        "eq98_is_positive_animal_input": eq98.balance.eq98_atmosphere_input_bq_m2 > 0.0
        and eq98.state.cow_hto_bq_m2 > 0.0,
        "cow_atmosphere_boundary_positive": one_day.balance.cow_to_atmosphere_boundary_bq_m2 > 0.0,
        "cow_soil_boundary_positive": one_day.balance.cow_to_soil1_boundary_bq_m2 > 0.0,
        "milk_hto_receiver_positive": one_day.state.milk_hto_bq_m2 > 0.0,
        "milk_obt_receiver_positive": one_day.state.milk_obt_bq_m2 > 0.0,
        "grass_obt_to_grass_hto": grass_routes.state.grass_hto_bq_m2 > 0.0,
        "grass_obt_to_cow_hto": grass_routes.state.cow_hto_bq_m2 > 0.0,
        "grass_obt_to_cow_obt": grass_routes.state.cow_obt_bq_m2 > 0.0,
        "grass_obt_to_milk_obt": grass_routes.state.milk_obt_bq_m2 > 0.0,
        "deterministic_repeat": one_day == repeat,
        "restart_equivalence": all(
            math.isclose(a, b, rel_tol=1.0e-13, abs_tol=1.0e-12)
            for a, b in zip(_vector(one_day.state), _vector(restarted.state))
        ),
        "hourly_partition_equivalence": all(
            math.isclose(a, b, rel_tol=1.0e-13, abs_tol=1.0e-12)
            for a, b in zip(_vector(one_day.state), _vector(partition_state))
        ),
        "zero_inventory_limit": zero.state.total_internal_bq_m2 == 0.0
        and zero.balance.residual_bq_m2 == 0.0,
        "slaughter_activity_conserved": slaughter_balance.total_residual_bq_m2 == 0.0
        and slaughter_state.total_internal_bq_m2 == slaughter_start.total_internal_bq_m2,
        "slaughter_fraction_exact": slaughter_balance.cow_activity_removed_bq_m2 == 25.0
        and slaughter_balance.beef_activity_added_bq_m2 == 25.0,
        "refinement_strictly_improves": (
            refinement_errors["3600"]
            > refinement_errors["1800"]
            > refinement_errors["900"]
            > refinement_errors["450"]
            > 0.0
        ),
        "refinement_450_under_one_percent": refinement_errors["450"] < 0.01,
    }

    if not all(profile_gates.values()):
        failed = sorted(key for key, value in profile_gates.items() if not value)
        raise RuntimeError(f"D4 manual-profile gate failed: {failed}")
    if not all(numerical_gates.values()):
        failed = sorted(key for key, value in numerical_gates.items() if not value)
        raise RuntimeError(f"D4 numerical gate failed: {failed}")

    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": STATUS,
        "manual_anchor": "KfK4605_Eq82_105_2",
        "profile": {
            "profile_id": p.profile_id,
            "eq82_exact_d_1": p.cow_water_overall_loss_exact_d_1,
            "cow_hto_total_manual_hazard_d_1": p.cow_hto_total_hazard_d_1,
            "eq92_exact_d_1": p.cow_obt_overall_loss_exact_d_1,
            "cow_obt_total_manual_hazard_d_1": p.cow_obt_total_hazard_d_1,
            "eq98_exact_d_1": p.atmosphere_to_cow_hto_eq98_exact_d_1,
            "eq98_manual_rounded_d_1": p.atmosphere_to_cow_hto_manual_rounded_d_1,
            "eq105_2_reconstructed_d_1": p.grass_obt_eq105_2_reconstructed_d_1,
            "profile_gates": profile_gates,
        },
        "numerical": {
            "selected_step_s": 3600.0,
            "reference_step_s": 225.0,
            "refinement_errors": refinement_errors,
            "one_day_balance_residual_bq_m2": one_day.balance.residual_bq_m2,
            "eq98_one_day_input_bq_m2": eq98.balance.eq98_atmosphere_input_bq_m2,
            "numerical_gates": numerical_gates,
        },
        "hard_boundaries": {
            "historical_v2_changed": False,
            "frozen_rc1_changed": False,
            "existing_v4_integrator_changed": False,
            "d3_source_changed": False,
            "project_feed_50kg_day_activated": False,
            "project_drinking_water_50l_day_activated": False,
            "project_support_area_4000m2_activated": False,
            "project_beef_mass_200kg_activated": False,
            "project_continuous_herd_turnover_activated": False,
            "public_exposure_completed": False,
            "production_parameter_activation": False,
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "real_cteas_atmos_binding": False,
            "original_numerical_discretization_recovered": False,
            "original_executable_equivalence": False,
        },
        "next_stage": "UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(f"D4_COW_MILK_BEEF_STATUS={result['status']}")
    print(f"D4_COW_MILK_BEEF_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
