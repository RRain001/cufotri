#!/usr/bin/env python3
"""Machine-visible synthetic gate for V4 soil->root->TFWT->OBT integration R1."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState, OBTSolver, PlantBiologicalForcing
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
DT = 1800.0
TEST_HALF_LIFE_S = 1.0e12
TEST_KF_S = 2.0e-5
TEST_KR_S = 5.0e-6
Q_PROFILES = (
    (1.0e-7, 2.0e-7, 1.0e-7),
    (1.5e-7, 1.5e-7, 0.8e-7),
    (0.8e-7, 2.2e-7, 1.2e-7),
    (1.2e-7, 1.8e-7, 1.0e-7),
)
DEPOSITION = (2.0e-4, 1.0e-4, 0.0, 1.5e-4)


def plant_provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_TEST_ONLY_PLANT",
        source_version="integration-r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=DT,
    )


def soil_provenance() -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_TEST_ONLY_SOIL",
        source_version="integration-r1",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=DT,
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_TEST_ONLY_ROOT_QW",
        source_locator="scripts/v4/run_soil_root_tfwt_obt_integration_r1.py",
        revision="integration-r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_TEST_ONLY_EXPLICIT_Q_W",
    )


def initial_state(*, tfwt_inventory: float = 2.0, obt_inventory: float = 1.0) -> V4SoilRootTFWTOBTState:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=timestamp,
        provenance=soil_provenance(),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=tfwt_inventory,
        water_content_kg_m2=5.0,
        time=timestamp,
        provenance=plant_provenance(),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=obt_inventory,
        plant_mass_kg_m2=2.0,
        timestamp=timestamp,
        provenance=plant_provenance(),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def integrator() -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=TEST_HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=TEST_KF_S, kr_s=TEST_KR_S),
    )


def step_inputs(state: V4SoilRootTFWTOBTState, index: int):
    soil = ThreeLayerSoilForcing(
        timestamp=state.timestamp,
        surface_water_input_m_s=2.0e-8,
        surface_water_loss_m_s=1.0e-8,
        surface_deposition_flux_bq_m2_s=DEPOSITION[index],
        l1_l2_water_flux_m_s=1.0e-8,
        l1_l2_hto_flux_bq_m2_s=1.0e-5,
        l2_l3_water_flux_m_s=-5.0e-9,
        l2_l3_hto_flux_bq_m2_s=-5.0e-6,
        lower_boundary_water_loss_m_s=2.0e-9,
        lower_boundary_hto_loss_bq_m2_s=1.0e-5,
        surface_reemission_hto_loss_bq_m2_s=5.0e-6,
    )
    root = ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=state.plant_identifier,
        timestamp=state.timestamp,
        water_uptake_fluxes_m_s=Q_PROFILES[index],
        provenance=root_provenance(),
    )
    biological = PlantBiologicalForcing(is_daylight=index < 3)
    return soil, root, biological


def run_sequence(*, restart_after: int | None = None) -> dict[str, Any]:
    model = integrator()
    state = initial_state()
    records: list[dict[str, Any]] = []
    max_root_identity = 0.0
    max_plant_residual = 0.0
    max_coupled_residual = 0.0
    max_soil_residual = 0.0

    for index in range(len(Q_PROFILES)):
        if restart_after is not None and index == restart_after:
            state = V4SoilRootTFWTOBTState.from_json(state.to_json())
        soil, root, biological = step_inputs(state, index)
        result = model.advance(
            state,
            soil_forcing=soil,
            root_forcing=root,
            biological_forcing=biological,
            interval_seconds=DT,
        )
        max_root_identity = max(
            max_root_identity,
            abs(result.balance.soil_root_hto_identity_residual_bq_m2),
        )
        max_plant_residual = max(max_plant_residual, abs(result.balance.plant_residual_bq_m2))
        max_coupled_residual = max(max_coupled_residual, abs(result.balance.coupled_residual_bq_m2))
        max_soil_residual = max(max_soil_residual, abs(result.soil_result.global_balance.hto_residual_bq_m2))
        records.append(
            {
                "index": index,
                "timestamp_start": state.timestamp.isoformat(),
                "root_transfer_bq_m2": result.root_plan.total_hto_transfer_bq_m2,
                "obt_formation_bq_m2": result.obt_result.balance.obt_formation_bq_m2,
                "soil_hto_end_bq_m2": result.state.soil_state.total_hto_inventory_bq_m2,
                "tfwt_end_bq_m2": result.state.tfwt_state.inventory(),
                "obt_end_bq_m2": result.state.obt_state.inventory(),
                "coupled_residual_bq_m2": result.balance.coupled_residual_bq_m2,
            }
        )
        state = result.state

    return {
        "state": state.to_mapping(),
        "records": records,
        "max_abs_root_identity_residual_bq_m2": max_root_identity,
        "max_abs_plant_residual_bq_m2": max_plant_residual,
        "max_abs_coupled_residual_bq_m2": max_coupled_residual,
        "max_abs_soil_residual_bq_m2": max_soil_residual,
    }


def pulse_probe() -> dict[str, float]:
    model = integrator()
    state0 = initial_state(tfwt_inventory=0.0, obt_inventory=0.0)
    root = ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=state0.plant_identifier,
        timestamp=state0.timestamp,
        water_uptake_fluxes_m_s=Q_PROFILES[0],
        provenance=root_provenance(),
    )
    first = model.advance(
        state0,
        soil_forcing=ThreeLayerSoilForcing(timestamp=state0.timestamp),
        root_forcing=root,
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        interval_seconds=DT,
    )
    second_root = ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=first.state.plant_identifier,
        timestamp=first.state.timestamp,
        water_uptake_fluxes_m_s=Q_PROFILES[0],
        provenance=root_provenance(),
    )
    second = model.advance(
        first.state,
        soil_forcing=ThreeLayerSoilForcing(timestamp=first.state.timestamp),
        root_forcing=second_root,
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        interval_seconds=DT,
    )
    return {
        "first_root_transfer_bq_m2": first.root_plan.total_hto_transfer_bq_m2,
        "first_obt_formation_bq_m2": first.obt_result.balance.obt_formation_bq_m2,
        "first_tfwt_end_bq_m2": first.state.tfwt_state.inventory(),
        "second_obt_formation_bq_m2": second.obt_result.balance.obt_formation_bq_m2,
    }


def validate_result(result: dict[str, Any]) -> None:
    tol = 1.0e-10
    if result["selected_operator_split"] != "PRESERVE_V3_POST_OBT_ROOT_GAIN":
        raise RuntimeError("selected operator split drifted")
    if not result["gates"]["deterministic_repeat"]:
        raise RuntimeError("deterministic repeat failed")
    if not result["gates"]["restart_equivalence"]:
        raise RuntimeError("restart equivalence failed")
    if not result["gates"]["root_pulse_post_obt_semantics"]:
        raise RuntimeError("root pulse post-OBT semantics failed")
    for key in (
        "max_abs_root_identity_residual_bq_m2",
        "max_abs_plant_residual_bq_m2",
        "max_abs_coupled_residual_bq_m2",
        "max_abs_soil_residual_bq_m2",
    ):
        value = float(result["direct"][key])
        if not math.isfinite(value) or value > tol:
            raise RuntimeError(f"{key} failed closure: {value}")


def build_result() -> dict[str, Any]:
    direct = run_sequence()
    repeat = run_sequence()
    restarted = run_sequence(restart_after=2)
    pulse = pulse_probe()

    deterministic = repeat == direct
    restart_equivalent = restarted == direct
    pulse_pass = (
        pulse["first_root_transfer_bq_m2"] > 0.0
        and abs(pulse["first_obt_formation_bq_m2"]) <= 1.0e-12
        and pulse["first_tfwt_end_bq_m2"] > 0.0
        and pulse["second_obt_formation_bq_m2"] > 0.0
    )

    result: dict[str, Any] = {
        "schema_version": "v1",
        "stage": "V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1",
        "status": "PASS_INTEGRATION",
        "source_kind": "SYNTHETIC_NUMERICAL_INTEGRATION_ONLY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "selected_operator_split": SELECTED_OPERATOR_SPLIT,
        "common_area_basis": "soil_surface_area",
        "area_basis_conversion": False,
        "test_only_inputs": {
            "soil_half_life_s": TEST_HALF_LIFE_S,
            "obt_kf_s": TEST_KF_S,
            "obt_kr_s": TEST_KR_S,
            "root_q_w_profiles_m_s": Q_PROFILES,
            "runtime_default_or_active_parameter": False,
        },
        "gates": {
            "single_root_plan_application_and_conservation": (
                direct["max_abs_root_identity_residual_bq_m2"] <= 1.0e-10
                and direct["max_abs_plant_residual_bq_m2"] <= 1.0e-10
                and direct["max_abs_coupled_residual_bq_m2"] <= 1.0e-10
                and direct["max_abs_soil_residual_bq_m2"] <= 1.0e-10
            ),
            "deterministic_repeat": deterministic,
            "restart_equivalence": restart_equivalent,
            "root_pulse_post_obt_semantics": pulse_pass,
        },
        "pulse_probe": pulse,
        "direct": direct,
        "hard_boundaries": {
            "v3_default_path_changed": False,
            "parameter_activation": False,
            "calibration": False,
            "leaf_r5": False,
            "ufotri_20_40_40_active": False,
            "ufotri_reference_layer_rates_active": False,
            "short_term_3h_delay_active": False,
            "plant_water_storage_model_added": False,
            "hydrology_generated_inside_root": False,
            "real_cteas_atmos_binding": False,
            "food_intake_dose_integration": False,
        },
    }
    if not all(result["gates"].values()):
        result["status"] = "HOLD_INTEGRATION_GATE_FAILED"
    validate_result(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"V4_SOIL_ROOT_TFWT_OBT_STATUS={result['status']}")
    print(f"V4_SOIL_ROOT_TFWT_OBT_RESULT_JSON={encoded}")
    if args.output is not None:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
