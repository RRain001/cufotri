#!/usr/bin/env python3
"""Machine-visible V4 UFOTRI OBT baseline numerical integration R1."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import (
    OBTState,
    OBTSolver,
    PlantBiologicalForcing,
    UFOTRI_OBT_KF_S,
    UFOTRI_OBT_KR_S,
    ufotri_obt_baseline_parameters,
)
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    SELECTED_OPERATOR_SPLIT,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)

UTC = timezone.utc
DURATION_S = 24.0 * 3600.0
TRITIUM_HALF_LIFE_S = 388_789_632.0
ROOT_Q_W_M_S = (1.0e-8, 2.0e-8, 1.0e-8)
REF_DT_S = 225.0
REFINEMENT_DTS_S = (3600.0, 1800.0, 900.0, 450.0)
BALANCE_TOL = 1.0e-10


def plant_provenance(dt_s: float) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_NUMERICAL_INTEGRATION_PLANT",
        source_version="ufotri-obt-baseline-r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=dt_s,
    )


def soil_provenance(dt_s: float) -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_NUMERICAL_INTEGRATION_SOIL",
        source_version="ufotri-obt-baseline-r1",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=dt_s,
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_NUMERICAL_INTEGRATION_ROOT_QW",
        source_locator="scripts/v4/run_obt_ufotri_baseline_numerical_integration_r1.py",
        revision="ufotri-obt-baseline-r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_EXPLICIT_Q_W_NOT_PRODUCTION",
    )


def initial_state(dt_s: float) -> V4SoilRootTFWTOBTState:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=timestamp,
        provenance=soil_provenance(dt_s),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=2.0,
        water_content_kg_m2=5.0,
        time=timestamp,
        provenance=plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=0.0,
        plant_mass_kg_m2=2.0,
        timestamp=timestamp,
        provenance=plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def integrator() -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=TRITIUM_HALF_LIFE_S),
        obt_solver=OBTSolver(parameters=ufotri_obt_baseline_parameters()),
    )


def run_case(dt_s: float, *, restart_at_half: bool = False) -> dict[str, Any]:
    steps = int(round(DURATION_S / dt_s))
    if not math.isclose(steps * dt_s, DURATION_S, rel_tol=0.0, abs_tol=1.0e-9):
        raise RuntimeError("dt must divide the 24 h integration window")

    model = integrator()
    state = initial_state(dt_s)
    max_root_identity = 0.0
    max_plant_residual = 0.0
    max_coupled_residual = 0.0
    max_soil_residual = 0.0

    for index in range(steps):
        if restart_at_half and index == steps // 2:
            state = V4SoilRootTFWTOBTState.from_json(state.to_json())
        soil_forcing = ThreeLayerSoilForcing(timestamp=state.timestamp)
        root_forcing = ThreeLayerRootWaterFluxForcingV4(
            plant_identifier=state.plant_identifier,
            timestamp=state.timestamp,
            water_uptake_fluxes_m_s=ROOT_Q_W_M_S,
            provenance=root_provenance(),
        )
        result = model.advance(
            state,
            soil_forcing=soil_forcing,
            root_forcing=root_forcing,
            biological_forcing=PlantBiologicalForcing(is_daylight=(index % 24) < 12),
            interval_seconds=dt_s,
        )
        max_root_identity = max(max_root_identity, abs(result.balance.soil_root_hto_identity_residual_bq_m2))
        max_plant_residual = max(max_plant_residual, abs(result.balance.plant_residual_bq_m2))
        max_coupled_residual = max(max_coupled_residual, abs(result.balance.coupled_residual_bq_m2))
        max_soil_residual = max(max_soil_residual, abs(result.soil_result.global_balance.hto_residual_bq_m2))
        state = result.state

    return {
        "dt_s": dt_s,
        "steps": steps,
        "soil_hto_bq_m2": state.soil_state.total_hto_inventory_bq_m2,
        "tfwt_bq_m2": state.tfwt_state.inventory(),
        "obt_bq_m2": state.obt_state.inventory(),
        "plant_total_bq_m2": state.tfwt_state.inventory() + state.obt_state.inventory(),
        "max_abs_root_identity_residual_bq_m2": max_root_identity,
        "max_abs_plant_residual_bq_m2": max_plant_residual,
        "max_abs_coupled_residual_bq_m2": max_coupled_residual,
        "max_abs_soil_residual_bq_m2": max_soil_residual,
        "final_state": state.to_mapping(),
    }


def state_error(case: dict[str, Any], reference: dict[str, Any]) -> float:
    return sum(
        abs(float(case[key]) - float(reference[key]))
        for key in ("soil_hto_bq_m2", "tfwt_bq_m2", "obt_bq_m2")
    )


def build_result() -> dict[str, Any]:
    reference = run_case(REF_DT_S)
    runs = {str(int(dt)): run_case(dt) for dt in REFINEMENT_DTS_S}
    errors = {key: state_error(case, reference) for key, case in runs.items()}
    ordered_errors = [errors[str(int(dt))] for dt in REFINEMENT_DTS_S]
    refinement_pass = all(later < earlier for earlier, later in zip(ordered_errors, ordered_errors[1:]))

    direct = runs["1800"]
    repeat = run_case(1800.0)
    restarted = run_case(1800.0, restart_at_half=True)
    deterministic = repeat == direct
    restart_equivalent = restarted == direct

    balance_pass = all(
        float(case[key]) <= BALANCE_TOL
        for case in [reference, *runs.values()]
        for key in (
            "max_abs_root_identity_residual_bq_m2",
            "max_abs_plant_residual_bq_m2",
            "max_abs_coupled_residual_bq_m2",
            "max_abs_soil_residual_bq_m2",
        )
    )
    obt_formed = all(float(case["obt_bq_m2"]) > 0.0 for case in runs.values())

    gates = {
        "ufotri_profile_exact": (
            math.isclose(ufotri_obt_baseline_parameters().kf_s, UFOTRI_OBT_KF_S, rel_tol=0.0, abs_tol=0.0)
            and math.isclose(ufotri_obt_baseline_parameters().kr_s, UFOTRI_OBT_KR_S, rel_tol=0.0, abs_tol=0.0)
        ),
        "selected_operator_split_preserved": SELECTED_OPERATOR_SPLIT == "PRESERVE_V3_POST_OBT_ROOT_GAIN",
        "conservation_closed": balance_pass,
        "deterministic_repeat": deterministic,
        "restart_equivalence": restart_equivalent,
        "timestep_refinement": refinement_pass,
        "obt_formation_nonzero": obt_formed,
    }

    result: dict[str, Any] = {
        "schema_version": "v1",
        "stage": "V4_OBT_UFOTRI_BASELINE_NUMERICAL_INTEGRATION_R1",
        "status": "PASS_UFOTRI_BASELINE_NUMERICAL_INTEGRATION" if all(gates.values()) else "HOLD_NUMERICAL_GATE_FAILED",
        "source_kind": "UFOTRI_PARAMETER_BASELINE_PLUS_SYNTHETIC_NUMERICAL_FORCING",
        "ufotri_parameters": {
            "kf_s": UFOTRI_OBT_KF_S,
            "kr_s": UFOTRI_OBT_KR_S,
            "daylight_multiplier": ufotri_obt_baseline_parameters().daylight_multiplier,
            "nighttime_multiplier": ufotri_obt_baseline_parameters().nighttime_multiplier,
        },
        "selected_operator_split": SELECTED_OPERATOR_SPLIT,
        "duration_s": DURATION_S,
        "reference_dt_s": REF_DT_S,
        "refinement_errors": errors,
        "runs": runs,
        "gates": gates,
        "hard_boundaries": {
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "multi_pool_obt": False,
            "leaf_r5": False,
            "production_root_q_w": False,
            "full_hydrology": False,
            "real_cteas_atmos_binding": False,
            "v3_default_path_changed": False,
        },
    }
    if result["status"] != "PASS_UFOTRI_BASELINE_NUMERICAL_INTEGRATION":
        raise RuntimeError(json.dumps(gates, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"V4_OBT_UFOTRI_BASELINE_NUMERICAL_STATUS={result['status']}")
    print(f"V4_OBT_UFOTRI_BASELINE_NUMERICAL_RESULT_JSON={encoded}")
    if args.output is not None:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
