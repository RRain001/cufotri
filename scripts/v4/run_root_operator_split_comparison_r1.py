#!/usr/bin/env python3
"""Compare the two frozen V4 root->TFWT->OBT operator-split candidates.

This is a validation harness, not a production pipeline. It uses explicit
synthetic q_w forcing and a common soil-surface area basis so no area mapping,
UFOTRI profile, 3 h delay, or active parameter is inferred.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTParameters, OBTState, OBTSolver, PlantBiologicalForcing
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootFluxSolverV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState


POST = "PRESERVE_V3_POST_OBT_ROOT_GAIN"
PRE = "ROOT_GAIN_BEFORE_OBT"
CANDIDATES = (POST, PRE)
AREA_BASIS = "soil_surface_area"
HORIZON_SECONDS = 12.0 * 3600.0
COARSE_DT = 3600.0
REFINEMENT_DTS = (3600.0, 1800.0, 900.0)
REFERENCE_DT = 225.0
Q_W = (2.0e-8, 3.0e-8, 4.0e-8)
TRITIUM_HALF_LIFE_S = 12.32 * 365.25 * 86400.0
KF_S = 2.0e-5
KR_S = 0.0
TOL = 1.0e-10

PLANT_PROVENANCE = ForcingProvenance(
    source_id="v4-root-operator-split-comparison-r1",
    source_version="synthetic-r1",
    artifact_sha256="2" * 64,
    spatial_reference="synthetic-common-soil-surface-area",
    temporal_resolution_s=COARSE_DT,
)
SOIL_PROVENANCE = SoilV4Provenance(
    source_id="v4-root-operator-split-comparison-r1",
    source_version="synthetic-r1",
    artifact_sha256="3" * 64,
    spatial_reference="synthetic-common-soil-surface-area",
    temporal_resolution_s=COARSE_DT,
)
ROOT_PROVENANCE = RootWaterFluxProvenanceV4(
    source_id="v4-root-operator-split-comparison-r1",
    source_locator="scripts/v4/run_root_operator_split_comparison_r1.py",
    revision="synthetic-r1",
    artifact_sha256="4" * 64,
    profile_context="synthetic_test_explicit_q_w_no_ufotri_activation",
)


@dataclass(frozen=True)
class ComparisonState:
    soil: ThreeLayerSoilState
    tfwt: TFWTState
    obt: OBTState

    def __post_init__(self) -> None:
        if not (self.soil.timestamp == self.tfwt.time == self.obt.timestamp):
            raise ValueError("soil, TFWT and OBT timestamps must match")
        if not (self.soil.area_basis == self.tfwt.area_basis == self.obt.area_basis == AREA_BASIS):
            raise ValueError("comparison requires one explicit common area basis")


@dataclass(frozen=True)
class StepDiagnostics:
    root_transfer_bq_m2: float
    obt_formation_bq_m2: float
    soil_root_transfer_identity_residual_bq_m2: float
    plant_transfer_conservation_residual_bq_m2: float
    coupled_balance_residual_bq_m2: float


def _initial_state(*, zero_plant: bool = False) -> ComparisonState:
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    water = (0.0125, 0.0250, 0.0375)
    concentrations = (1200.0, 900.0, 600.0)
    hto = tuple(w * c for w, c in zip(water, concentrations, strict=True))
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-three-layer-column",
        water_inventories_m=water,
        hto_inventories_bq_m2=hto,
        timestamp=t0,
        provenance=SOIL_PROVENANCE,
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic_stage",
        tfwt_inventory_bq_m2=0.0 if zero_plant else 5.0,
        water_content_kg_m2=10.0,
        time=t0,
        provenance=PLANT_PROVENANCE,
        area_basis=AREA_BASIS,
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic_stage",
        obt_inventory_bq_m2=0.0 if zero_plant else 1.0,
        plant_mass_kg_m2=2.0,
        timestamp=t0,
        provenance=PLANT_PROVENANCE,
        area_basis=AREA_BASIS,
    )
    return ComparisonState(soil=soil, tfwt=tfwt, obt=obt)


def _root_forcing(state: ComparisonState, q_w: tuple[float, float, float]) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=state.tfwt.plant_identifier,
        timestamp=state.soil.timestamp,
        water_uptake_fluxes_m_s=q_w,
        provenance=ROOT_PROVENANCE,
    )


def _advance_one(
    state: ComparisonState,
    *,
    candidate: str,
    dt: float,
    q_w: tuple[float, float, float],
) -> tuple[ComparisonState, StepDiagnostics]:
    if candidate not in CANDIDATES:
        raise ValueError(f"unknown candidate: {candidate}")

    root_plan = ThreeLayerRootFluxSolverV4().plan(state.soil, _root_forcing(state, q_w), dt)
    if root_plan.area_basis != state.tfwt.area_basis:
        raise ValueError("root transfer and TFWT area basis must match explicitly")

    soil_result = ThreeLayerSoilStorageSolver(
        tritium_half_life_s=TRITIUM_HALF_LIFE_S
    ).advance(
        state.soil,
        ThreeLayerSoilForcing(
            timestamp=state.soil.timestamp,
            root_water_extraction_m_s=root_plan.water_uptake_fluxes_m_s,
            root_hto_extraction_bq_m2_s=root_plan.hto_uptake_fluxes_bq_m2_s,
        ),
        dt,
    )

    root_transfer = root_plan.total_hto_transfer_bq_m2
    obt_solver = OBTSolver(parameters=OBTParameters(kf_s=KF_S, kr_s=KR_S))
    biological = PlantBiologicalForcing(is_daylight=True)

    if candidate == POST:
        tfwt_for_obt = state.tfwt
    else:
        tfwt_for_obt = state.tfwt.with_inventory(
            tfwt_inventory_bq_m2=state.tfwt.inventory() + root_transfer,
            time=state.tfwt.time,
        )

    obt_result = obt_solver.advance(tfwt_for_obt, state.obt, dt, biological)
    formation = obt_result.balance.tfwt_loss_bq_m2
    if candidate == POST:
        final_tfwt_inventory = state.tfwt.inventory() - formation + root_transfer
    else:
        final_tfwt_inventory = tfwt_for_obt.inventory() - formation
    if final_tfwt_inventory < -TOL:
        raise ValueError("comparison produced negative TFWT inventory")
    final_tfwt_inventory = max(final_tfwt_inventory, 0.0)
    next_tfwt = state.tfwt.with_inventory(
        tfwt_inventory_bq_m2=final_tfwt_inventory,
        time=soil_result.state.timestamp,
    )
    next_state = ComparisonState(soil=soil_result.state, tfwt=next_tfwt, obt=obt_result.state)

    soil_root_identity = soil_result.global_balance.external_hto_loss_bq_m2 - root_transfer
    plant_change = (
        next_state.tfwt.inventory()
        + next_state.obt.inventory()
        - state.tfwt.inventory()
        - state.obt.inventory()
    )
    plant_residual = plant_change - root_transfer
    coupled_residual = (
        next_state.soil.total_hto_inventory_bq_m2
        + next_state.tfwt.inventory()
        + next_state.obt.inventory()
        - state.soil.total_hto_inventory_bq_m2
        - state.tfwt.inventory()
        - state.obt.inventory()
        + soil_result.global_balance.decay_loss_bq_m2
    )
    return next_state, StepDiagnostics(
        root_transfer_bq_m2=root_transfer,
        obt_formation_bq_m2=formation,
        soil_root_transfer_identity_residual_bq_m2=soil_root_identity,
        plant_transfer_conservation_residual_bq_m2=plant_residual,
        coupled_balance_residual_bq_m2=coupled_residual,
    )


def _serialize_state(state: ComparisonState) -> str:
    payload = {
        "soil": state.soil.to_mapping(),
        "tfwt": {
            "plant_identifier": state.tfwt.plant_identifier,
            "crop": state.tfwt.crop,
            "growth_stage": state.tfwt.growth_stage,
            "inventory": state.tfwt.inventory(),
            "water_content": state.tfwt.water_content_kg_m2,
            "time": state.tfwt.time.isoformat(),
            "area_basis": state.tfwt.area_basis,
        },
        "obt": {
            "plant_identifier": state.obt.plant_identifier,
            "crop": state.obt.crop,
            "growth_stage": state.obt.growth_stage,
            "inventory": state.obt.inventory(),
            "plant_mass": state.obt.plant_mass_kg_m2,
            "timestamp": state.obt.timestamp.isoformat(),
            "area_basis": state.obt.area_basis,
        },
    }
    return json.dumps(payload, sort_keys=True)


def _restore_state(payload: str) -> ComparisonState:
    data = json.loads(payload)
    soil = ThreeLayerSoilState.from_mapping(data["soil"])
    tfwt_data = data["tfwt"]
    obt_data = data["obt"]
    tfwt = TFWTState.from_inventory(
        plant_identifier=tfwt_data["plant_identifier"],
        crop=tfwt_data["crop"],
        growth_stage=tfwt_data["growth_stage"],
        tfwt_inventory_bq_m2=tfwt_data["inventory"],
        water_content_kg_m2=tfwt_data["water_content"],
        time=datetime.fromisoformat(tfwt_data["time"]),
        provenance=PLANT_PROVENANCE,
        area_basis=tfwt_data["area_basis"],
    )
    obt = OBTState.from_inventory(
        plant_identifier=obt_data["plant_identifier"],
        crop=obt_data["crop"],
        growth_stage=obt_data["growth_stage"],
        obt_inventory_bq_m2=obt_data["inventory"],
        plant_mass_kg_m2=obt_data["plant_mass"],
        timestamp=datetime.fromisoformat(obt_data["timestamp"]),
        provenance=PLANT_PROVENANCE,
        area_basis=obt_data["area_basis"],
    )
    return ComparisonState(soil=soil, tfwt=tfwt, obt=obt)


def _simulate(
    candidate: str,
    dt: float,
    *,
    horizon_seconds: float = HORIZON_SECONDS,
    restart_at_half: bool = False,
) -> dict[str, Any]:
    steps_float = horizon_seconds / dt
    if abs(steps_float - round(steps_float)) > 1.0e-12:
        raise ValueError("horizon must be an integer number of timesteps")
    steps = int(round(steps_float))
    state = _initial_state()
    diagnostics: list[StepDiagnostics] = []
    for index in range(steps):
        state, diag = _advance_one(state, candidate=candidate, dt=dt, q_w=Q_W)
        diagnostics.append(diag)
        if restart_at_half and index + 1 == steps // 2:
            state = _restore_state(_serialize_state(state))
    return {
        "candidate": candidate,
        "dt_seconds": dt,
        "steps": steps,
        "final_soil_hto_bq_m2": state.soil.total_hto_inventory_bq_m2,
        "final_tfwt_bq_m2": state.tfwt.inventory(),
        "final_obt_bq_m2": state.obt.inventory(),
        "final_plant_total_bq_m2": state.tfwt.inventory() + state.obt.inventory(),
        "total_root_transfer_bq_m2": sum(item.root_transfer_bq_m2 for item in diagnostics),
        "max_abs_soil_root_identity_residual_bq_m2": max(
            abs(item.soil_root_transfer_identity_residual_bq_m2) for item in diagnostics
        ),
        "max_abs_plant_conservation_residual_bq_m2": max(
            abs(item.plant_transfer_conservation_residual_bq_m2) for item in diagnostics
        ),
        "max_abs_coupled_balance_residual_bq_m2": max(
            abs(item.coupled_balance_residual_bq_m2) for item in diagnostics
        ),
    }


def _state_error(run: dict[str, Any], reference: dict[str, Any]) -> float:
    return abs(run["final_tfwt_bq_m2"] - reference["final_tfwt_bq_m2"]) + abs(
        run["final_obt_bq_m2"] - reference["final_obt_bq_m2"]
    )


def _refinement(candidate: str) -> dict[str, Any]:
    reference = _simulate(candidate, REFERENCE_DT)
    runs = {str(dt): _simulate(candidate, dt) for dt in REFINEMENT_DTS}
    errors = {key: _state_error(run, reference) for key, run in runs.items()}
    e1 = errors[str(REFINEMENT_DTS[0])]
    e2 = errors[str(REFINEMENT_DTS[1])]
    e3 = errors[str(REFINEMENT_DTS[2])]
    return {
        "reference_dt_seconds": REFERENCE_DT,
        "runs": runs,
        "l1_tfwt_obt_error_vs_reference": errors,
        "converged_monotonically": e3 < e2 < e1,
    }


def _pulse_lag_probe() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for candidate in CANDIDATES:
        state = _initial_state(zero_plant=True)
        state1, diag1 = _advance_one(state, candidate=candidate, dt=COARSE_DT, q_w=Q_W)
        state2, diag2 = _advance_one(
            state1,
            candidate=candidate,
            dt=COARSE_DT,
            q_w=(0.0, 0.0, 0.0),
        )
        results[candidate] = {
            "first_step_root_transfer_bq_m2": diag1.root_transfer_bq_m2,
            "first_step_obt_formation_bq_m2": diag1.obt_formation_bq_m2,
            "second_step_obt_formation_bq_m2": diag2.obt_formation_bq_m2,
            "obt_after_first_step_bq_m2": state1.obt.inventory(),
            "obt_after_second_step_bq_m2": state2.obt.inventory(),
        }
    return results


def run_comparison() -> dict[str, Any]:
    refinement = {candidate: _refinement(candidate) for candidate in CANDIDATES}
    deterministic = {
        candidate: _simulate(candidate, 1800.0) == _simulate(candidate, 1800.0)
        for candidate in CANDIDATES
    }
    restart = {}
    for candidate in CANDIDATES:
        direct = _simulate(candidate, 1800.0)
        restarted = _simulate(candidate, 1800.0, restart_at_half=True)
        restart[candidate] = {
            "equivalent": all(
                abs(direct[key] - restarted[key]) <= TOL
                for key in (
                    "final_soil_hto_bq_m2",
                    "final_tfwt_bq_m2",
                    "final_obt_bq_m2",
                    "final_plant_total_bq_m2",
                    "total_root_transfer_bq_m2",
                )
            ),
            "direct": direct,
            "restarted": restarted,
        }

    pulse = _pulse_lag_probe()
    post_pulse = pulse[POST]
    pre_pulse = pulse[PRE]
    all_converged = all(refinement[c]["converged_monotonically"] for c in CANDIDATES)
    conservation_pass = all(
        refinement[c]["runs"][str(COARSE_DT)]["max_abs_coupled_balance_residual_bq_m2"] <= TOL
        and refinement[c]["runs"][str(COARSE_DT)]["max_abs_plant_conservation_residual_bq_m2"] <= TOL
        and refinement[c]["runs"][str(COARSE_DT)]["max_abs_soil_root_identity_residual_bq_m2"] <= TOL
        for c in CANDIDATES
    )
    pulse_semantics_pass = (
        abs(post_pulse["first_step_obt_formation_bq_m2"]) <= TOL
        and post_pulse["second_step_obt_formation_bq_m2"] > 0.0
        and pre_pulse["first_step_obt_formation_bq_m2"] > 0.0
    )
    restart_pass = all(restart[c]["equivalent"] for c in CANDIDATES)
    deterministic_pass = all(deterministic.values())

    selected = POST if all(
        (all_converged, conservation_pass, pulse_semantics_pass, restart_pass, deterministic_pass)
    ) else "HOLD_NO_SELECTION"

    return {
        "schema_version": "v1",
        "stage": "V4_ROOT_OPERATOR_SPLIT_COMPARISON_R1",
        "source_kind": "SYNTHETIC_NUMERICAL_SEMANTICS_ONLY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "area_basis": AREA_BASIS,
        "area_basis_conversion": False,
        "ufotri_reference_profile_active": False,
        "three_hour_delay_active": False,
        "candidates": list(CANDIDATES),
        "refinement": refinement,
        "restart_equivalence": restart,
        "deterministic_repeat": deterministic,
        "pulse_lag_probe": pulse,
        "gates": {
            "both_candidates_monotonic_timestep_refinement": all_converged,
            "single_application_and_conservation": conservation_pass,
            "restart_equivalence": restart_pass,
            "deterministic_repeat": deterministic_pass,
            "root_to_obt_lag_difference_explicit": pulse_semantics_pass,
        },
        "selection": {
            "selected_candidate": selected,
            "basis": [
                "P7.5B interval-start explicit operator semantics remain the compatibility baseline",
                "root_v4 transfer is accumulated over the interval and is not an interval-start TFWT state",
                "post-OBT root gain avoids treating the full interval-integrated root transfer as present for the entire same interval",
                "both candidate splits must converge under timestep refinement; synthetic error ranking is not treated as physical evidence",
                "selection changes V4 numerical coupling semantics only and does not change V3",
            ],
            "pre_obt_candidate_disposition": (
                "NOT_SELECTED_RIGHT_BIASED_LIE_SPLIT"
                if selected == POST
                else "UNRESOLVED"
            ),
        },
        "next_authorization_if_selected": "V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1",
        "hard_boundaries": {
            "production_pipeline_changed": False,
            "v3_changed": False,
            "parameter_activation": False,
            "calibration": False,
            "real_cteas_atmos_binding": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_comparison()
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"V4_ROOT_OPERATOR_SPLIT_STATUS={'PASS_SELECTION' if result['selection']['selected_candidate'] == POST else 'HOLD'}")
    print("V4_ROOT_OPERATOR_SPLIT_RESULT_JSON=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["selection"]["selected_candidate"] == POST else 2


if __name__ == "__main__":
    raise SystemExit(main())
