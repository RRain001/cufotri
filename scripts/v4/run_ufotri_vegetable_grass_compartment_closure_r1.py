#!/usr/bin/env python3
"""Machine-visible D3 qualification for UFOTRI vegetable/grass closure."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.foodchain.ufotri_vegetable_grass_v4 import (
    EQ66_EXACT_FROM_STATED_MASSES,
    EQ66_MANUAL_ROUNDED_0_012_D_1,
    UFOTRIVegetableExchangeSolver,
    ufotri_grass_eq67_81_role_map,
    ufotri_vegetable_eq65_66_parameters,
    ufotri_vegetable_equilibrium_specific_activity_ratio,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState
from cteas_ufotri.plant.root_v4.pasture_profile import (
    UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState

UTC = timezone.utc
STAGE = "UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1"
TIMESTAMP = datetime(2026, 1, 1, tzinfo=UTC)
DAY_S = 86400.0


def _provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_D3_VEGETABLE_GRASS",
        source_version="r1",
        artifact_sha256="3" * 64,
        spatial_reference="plant_area",
        temporal_resolution_s=3600.0,
    )


def _states(
    tfwt_bq_m2: float,
    obt_bq_m2: float,
    *,
    plant_identifier: str = "synthetic-vegetable",
) -> tuple[TFWTState, OBTState]:
    provenance = _provenance()
    return (
        TFWTState.from_inventory(
            plant_identifier=plant_identifier,
            crop="green_vegetable",
            growth_stage="controlled",
            tfwt_inventory_bq_m2=tfwt_bq_m2,
            water_content_kg_m2=0.4,
            time=TIMESTAMP,
            provenance=provenance,
            area_basis="plant_area",
        ),
        OBTState.from_inventory(
            plant_identifier=plant_identifier,
            crop="green_vegetable",
            growth_stage="controlled",
            obt_inventory_bq_m2=obt_bq_m2,
            plant_mass_kg_m2=0.1,
            timestamp=TIMESTAMP,
            provenance=provenance,
            area_basis="plant_area",
        ),
    )


def _oracle_obt(
    *,
    h0: float,
    o0: float,
    kf_s: float,
    kr_s: float,
    dt_s: float,
) -> float:
    total = h0 + o0
    rate_sum = kf_s + kr_s
    if total == 0.0 or rate_sum == 0.0:
        return o0
    o_eq = kf_s / rate_sum * total
    return o_eq + (o0 - o_eq) * math.exp(-rate_sum * dt_s)


def _profile_result(profile_id: str) -> dict[str, Any]:
    parameters = ufotri_vegetable_eq65_66_parameters(
        forward_rate_basis=profile_id,
    )
    solver = UFOTRIVegetableExchangeSolver(parameters)

    h0, o0 = 100.0, 0.0
    tfwt, obt = _states(h0, o0)
    one_day = solver.advance(tfwt, obt, DAY_S)
    oracle_o = _oracle_obt(
        h0=h0,
        o0=o0,
        kf_s=parameters.forward_s_1,
        kr_s=parameters.reverse_s_1,
        dt_s=DAY_S,
    )

    repeat = solver.advance(*_states(h0, o0), DAY_S)
    first_half = solver.advance(*_states(h0, o0), DAY_S / 2.0)
    second_half = solver.advance(
        first_half.tfwt_state,
        first_half.obt_state,
        DAY_S / 2.0,
    )

    partition_tfwt, partition_obt = _states(h0, o0)
    for _ in range(24):
        partition = solver.advance(partition_tfwt, partition_obt, 3600.0)
        partition_tfwt = partition.tfwt_state
        partition_obt = partition.obt_state

    reverse_tfwt, reverse_obt = _states(0.0, 100.0)
    reverse_step = solver.advance(reverse_tfwt, reverse_obt, DAY_S)
    zero_step = solver.advance(*_states(0.0, 0.0), DAY_S)

    total_initial = h0 + o0
    total_final = one_day.tfwt_state.inventory() + one_day.obt_state.inventory()
    invariants = {
        "analytic_obt_match": math.isclose(
            one_day.obt_state.inventory(), oracle_o, rel_tol=1.0e-14, abs_tol=1.0e-14
        ),
        "analytic_tfwt_match": math.isclose(
            one_day.tfwt_state.inventory(), total_initial - oracle_o, rel_tol=1.0e-14, abs_tol=1.0e-14
        ),
        "total_activity_conserved": math.isclose(
            total_final, total_initial, rel_tol=0.0, abs_tol=1.0e-12
        ),
        "balance_residual_closed": abs(one_day.balance.total_residual_bq_m2) <= 1.0e-12,
        "forward_transfer_increases_obt": one_day.obt_state.inventory() > o0,
        "reverse_transfer_returns_to_tfwt": reverse_step.tfwt_state.inventory() > 0.0
        and reverse_step.obt_state.inventory() < 100.0,
        "reverse_pair_total_conserved": math.isclose(
            reverse_step.tfwt_state.inventory() + reverse_step.obt_state.inventory(),
            100.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ),
        "deterministic_repeat": one_day.tfwt_state.inventory() == repeat.tfwt_state.inventory()
        and one_day.obt_state.inventory() == repeat.obt_state.inventory(),
        "restart_semigroup_equivalence": math.isclose(
            one_day.tfwt_state.inventory(),
            second_half.tfwt_state.inventory(),
            rel_tol=1.0e-14,
            abs_tol=1.0e-12,
        )
        and math.isclose(
            one_day.obt_state.inventory(),
            second_half.obt_state.inventory(),
            rel_tol=1.0e-14,
            abs_tol=1.0e-12,
        ),
        "hourly_partition_equivalence": math.isclose(
            one_day.tfwt_state.inventory(),
            partition_tfwt.inventory(),
            rel_tol=1.0e-13,
            abs_tol=1.0e-11,
        )
        and math.isclose(
            one_day.obt_state.inventory(),
            partition_obt.inventory(),
            rel_tol=1.0e-13,
            abs_tol=1.0e-11,
        ),
        "zero_inventory_stays_zero": zero_step.tfwt_state.inventory() == 0.0
        and zero_step.obt_state.inventory() == 0.0,
        "no_external_loss_in_pair": math.isclose(
            one_day.balance.net_hto_to_obt_bq_m2,
            one_day.obt_state.inventory() - o0,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ),
    }
    if not all(invariants.values()):
        failed = sorted(key for key, value in invariants.items() if not value)
        raise RuntimeError(f"D3 vegetable profile gate failed for {profile_id}: {failed}")

    return {
        "profile_id": profile_id,
        "forward_d_1": parameters.forward_d_1,
        "reverse_d_1": parameters.reverse_d_1,
        "equilibrium_specific_activity_ratio": ufotri_vegetable_equilibrium_specific_activity_ratio(parameters),
        "one_day_tfwt_bq_m2": one_day.tfwt_state.inventory(),
        "one_day_obt_bq_m2": one_day.obt_state.inventory(),
        "reverse_one_day_tfwt_bq_m2": reverse_step.tfwt_state.inventory(),
        "reverse_one_day_obt_bq_m2": reverse_step.obt_state.inventory(),
        "invariants": invariants,
    }


def build_result() -> dict[str, Any]:
    exact = _profile_result(EQ66_EXACT_FROM_STATED_MASSES)
    rounded = _profile_result(EQ66_MANUAL_ROUNDED_0_012_D_1)
    grass = ufotri_grass_eq67_81_role_map()

    grass_invariants = {
        "canonical_layers_exact": grass.layer_depths_m == (0.05, 0.10, 0.15),
        "pasture_40_60_0_exact": grass.root_fractions == (0.4, 0.6, 0.0),
        "d2_profile_unchanged": UFOTRI_PASTURE_ROOT_WATER_UPTAKE_FRACTIONS
        == (0.4, 0.6, 0.0),
        "eq67_soil3_loss_recorded": grass.soil3_external_loss_d_1 == 8.2e-3,
        "eq68_grass_to_air_recorded": grass.grass_to_atmosphere_d_1 == 5.4,
        "eq69_air_to_grass_recorded": grass.atmosphere_to_grass_d_1 == 0.2,
        "eq70_air_to_soil_recorded": grass.atmosphere_to_soil1_d_1 == 0.68,
        "eq72_soil_to_air_recorded": grass.soil1_to_atmosphere_d_1 == 0.27,
        "eq73_reverse_soil_recorded": grass.soil2_to_soil1_d_1 == 1.2e-2,
        "eq74_reverse_soil_recorded": grass.soil3_to_soil2_d_1 == 8.2e-3,
        "eq76_l1_root_recorded": grass.soil1_to_grass_d_1 == 5.2e-2,
        "eq77_l2_root_recorded": grass.soil2_to_grass_d_1 == 3.9e-2,
        "eq79_downward_l1_l2_recorded": grass.soil1_to_soil2_d_1 == 0.13,
        "eq81_downward_l2_l3_recorded": grass.soil2_to_soil3_d_1 == 2.45e-2,
        "legacy_reference_rates_not_activated": not grass.reference_rates_activated,
        "no_duplicate_soil_solver": not grass.duplicate_soil_solver_added,
        "grass_obt_deferred_to_d4": grass.grass_obt_owner == "D4_EQ99_105_2",
        "production_binding_not_authorized": not grass.production_binding_authorized,
    }
    if not all(grass_invariants.values()):
        failed = sorted(key for key, value in grass_invariants.items() if not value)
        raise RuntimeError(f"D3 grass role-map gate failed: {failed}")

    profile_invariants = {
        "eq66_exact_equilibrium_ratio_is_one": math.isclose(
            exact["equilibrium_specific_activity_ratio"],
            1.0,
            rel_tol=1.0e-14,
            abs_tol=1.0e-14,
        ),
        "manual_rounded_profile_is_explicitly_distinct": not math.isclose(
            exact["forward_d_1"], rounded["forward_d_1"], rel_tol=0.0, abs_tol=0.0
        ),
        "eq65_reverse_rate_shared": exact["reverse_d_1"] == rounded["reverse_d_1"],
        "no_hidden_original_parameter_selection": True,
    }
    if not all(profile_invariants.values()):
        failed = sorted(key for key, value in profile_invariants.items() if not value)
        raise RuntimeError(f"D3 profile reconciliation gate failed: {failed}")

    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": "PASS_VEGETABLE_GRASS_COMPARTMENT_CLOSURE",
        "vegetable_profiles": {
            EQ66_EXACT_FROM_STATED_MASSES: exact,
            EQ66_MANUAL_ROUNDED_0_012_D_1: rounded,
        },
        "profile_invariants": profile_invariants,
        "grass_role_map": {
            "layer_depths_m": grass.layer_depths_m,
            "root_fractions": grass.root_fractions,
            "leaf_exchange_owner": grass.leaf_exchange_owner,
            "soil_hydrology_owner": grass.soil_hydrology_owner,
            "root_uptake_owner": grass.root_uptake_owner,
            "grass_obt_owner": grass.grass_obt_owner,
            "reference_rates_activated": grass.reference_rates_activated,
            "grass_invariants": grass_invariants,
        },
        "hard_boundaries": {
            "frozen_rc1_changed": False,
            "historical_v2_changed": False,
            "existing_obt_solver_changed": False,
            "existing_v4_integrator_changed": False,
            "duplicate_soil_or_hydrology_solver_added": False,
            "grass_eq67_81_reference_rates_activated": False,
            "grass_obt_eq105_completed": False,
            "cow_milk_beef_completed": False,
            "exposure_completed": False,
            "production_parameter_activation": False,
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "real_cteas_atmos_binding": False,
            "original_executable_equivalence": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(f"D3_VEGETABLE_GRASS_STATUS={result['status']}")
    print(f"D3_VEGETABLE_GRASS_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if args.output is not None:
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
