#!/usr/bin/env python3
"""Visible machine check for V4 replay-input system orchestration R1."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_exchange_resistance.resistance import ResistanceChain
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
    ReplayDomainProvenance,
    V4ReplayInputSystemOrchestrator,
    V4ReplayIntervalInput,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)


UTC = timezone.utc
DT = 3600.0
SPATIAL = "synthetic-replay-machine-support"
HALF_LIFE_S = 1.0e12
KF_S = 2.0e-5
KR_S = 5.0e-6


def plant_provenance() -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_TEST_ONLY_PLANT",
        source_version="machine-r1",
        artifact_sha256="a" * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=DT,
    )


def domain_provenance(source_id: str, digest: str) -> ReplayDomainProvenance:
    return ReplayDomainProvenance(
        source_id=source_id,
        source_version="machine-r1",
        artifact_sha256=digest * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=DT,
        source_kind="SYNTHETIC_TEST",
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_TEST_ONLY_ROOT_QW",
        source_locator="scripts/v4/run_replay_input_orchestration_r1.py",
        revision="machine-r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_TEST_ONLY_EXPLICIT_Q_W",
    )


def make_state() -> V4SoilRootTFWTOBTState:
    time = datetime(2026, 1, 1, tzinfo=UTC)
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-machine-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=time,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_TEST_ONLY_SOIL_STATE",
            source_version="machine-r1",
            artifact_sha256="b" * 64,
            spatial_reference=SPATIAL,
            temporal_resolution_s=DT,
        ),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        tfwt_inventory_bq_m2=2.0,
        water_content_kg_m2=5.0,
        time=time,
        provenance=plant_provenance(),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-soybean",
        crop="Glycine_max",
        growth_stage="synthetic-stage",
        obt_inventory_bq_m2=1.0,
        plant_mass_kg_m2=2.0,
        timestamp=time,
        provenance=plant_provenance(),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def root_forcing(timestamp: datetime) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="synthetic-soybean",
        timestamp=timestamp,
        water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7, 1.0e-7),
        provenance=root_provenance(),
    )


def atmos(timestamp: datetime, *, air: float, deposition: float, precipitation: float = 0.0) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location="synthetic-machine-support",
        air_hto_concentration=air,
        deposition_flux=deposition,
        temperature=298.15,
        humidity=0.55,
        wind_speed=2.0,
        precipitation=precipitation,
        source="SYNTHETIC_TEST_ONLY_REPLAY",
        provenance=plant_provenance(),
    )


def replay_input(
    state: V4SoilRootTFWTOBTState,
    *,
    air: float,
    equilibrium: float,
    deposition: float,
    precipitation: float = 0.0,
) -> V4ReplayIntervalInput:
    return V4ReplayIntervalInput(
        atmospheric_forcing=atmos(
            state.timestamp,
            air=air,
            deposition=deposition,
            precipitation=precipitation,
        ),
        interval_end=state.timestamp + timedelta(seconds=DT),
        soil_external_forcing=ThreeLayerSoilForcing(timestamp=state.timestamp),
        soil_external_provenance=domain_provenance("SYNTHETIC_SOIL_EXTERNAL", "d"),
        root_forcing=root_forcing(state.timestamp),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        biological_provenance=domain_provenance("SYNTHETIC_BIOLOGICAL", "e"),
        resistance=ResistanceChain.from_components(100.0, 100.0, 800.0),
        equilibrium_air_concentration_bq_m3=equilibrium,
        leaf_exchange_provenance=domain_provenance("SYNTHETIC_LEAF_PARAMETERS", "f"),
    )


def orchestrator() -> V4ReplayInputSystemOrchestrator:
    return V4ReplayInputSystemOrchestrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=KF_S, kr_s=KR_S),
    )


def reference() -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=KF_S, kr_s=KR_S),
    )


def run() -> dict[str, object]:
    state = make_state()
    zero_input = replay_input(
        state,
        air=0.5,
        equilibrium=0.5,
        deposition=0.0,
    )
    zero_result = orchestrator().advance(state, zero_input)
    reference_result = reference().advance(
        state,
        soil_forcing=ThreeLayerSoilForcing(timestamp=state.timestamp),
        root_forcing=zero_input.root_forcing,
        biological_forcing=zero_input.biological_forcing,
        interval_seconds=DT,
    )
    zero_leaf_equivalent = (
        zero_result.state == reference_result.state
        and zero_result.root_plan == reference_result.root_plan
        and zero_result.soil_result == reference_result.soil_result
        and zero_result.obt_result == reference_result.obt_result
        and zero_result.balance.leaf_exchange_transfer_bq_m2 == 0.0
    )

    driven_input = replay_input(
        state,
        air=1.5,
        equilibrium=0.5,
        deposition=2.0e-4,
        precipitation=1.0e-6,
    )
    driven = orchestrator().advance(state, driven_input)
    deterministic = orchestrator().advance(state, driven_input) == driven
    restarted = V4SoilRootTFWTOBTState.from_json(driven.state.to_json())
    restart_input = replay_input(
        restarted,
        air=0.8,
        equilibrium=0.5,
        deposition=5.0e-5,
    )
    direct_next = orchestrator().advance(driven.state, restart_input)
    restarted_next = orchestrator().advance(restarted, restart_input)
    restart_equivalent = direct_next == restarted_next

    invariants = {
        "zero_leaf_exchange_equivalence": zero_leaf_equivalent,
        "same_interval_leaf_exchange_reaches_obt": (
            driven.obt_result.balance.obt_formation_bq_m2
            > reference_result.obt_result.balance.obt_formation_bq_m2
        ),
        "root_gain_post_obt": driven.selected_operator_split == "PRESERVE_V3_POST_OBT_ROOT_GAIN",
        "atmos_deposition_mapped_to_l1_surface": (
            driven.applied_soil_forcing.surface_deposition_flux_bq_m2_s == 2.0e-4
        ),
        "precipitation_not_inferred_as_soil_water": (
            driven.applied_soil_forcing.surface_water_input_m_s == 0.0
        ),
        "root_provenance_independent": (
            driven.root_plan.provenance.source_id == "SYNTHETIC_TEST_ONLY_ROOT_QW"
            and driven.root_plan.provenance.source_id
            != driven_input.atmospheric_forcing.provenance.source_id
        ),
        "plant_balance_closed": abs(driven.balance.plant_residual_bq_m2) <= 1.0e-10,
        "coupled_balance_closed": abs(driven.balance.coupled_residual_bq_m2) <= 1.0e-10,
        "deterministic_repeat": deterministic,
        "restart_equivalence": restart_equivalent,
    }
    status = (
        "PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"
        if all(invariants.values())
        else "FAIL_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION"
    )
    return {
        "schema_version": "v1",
        "stage": "V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1",
        "status": status,
        "source_kind": "SYNTHETIC_TEST_ONLY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "real_cteas_atmos_binding": False,
        "active_parameters": 0,
        "calibration": False,
        "v3_default_changed": False,
        "leaf_r5": False,
        "food_intake_dose_v4_integration": False,
        "full_hydrology": False,
        "selected_operator_split": driven.selected_operator_split,
        "invariants": invariants,
        "driven_balance": {
            "leaf_exchange_transfer_bq_m2": driven.balance.leaf_exchange_transfer_bq_m2,
            "root_hto_transfer_bq_m2": driven.balance.root_hto_transfer_bq_m2,
            "soil_external_hto_input_bq_m2": driven.balance.soil_external_hto_input_bq_m2,
            "plant_residual_bq_m2": driven.balance.plant_residual_bq_m2,
            "coupled_residual_bq_m2": driven.balance.coupled_residual_bq_m2,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(f"V4_REPLAY_ORCHESTRATION_STATUS={result['status']}")
    print(f"V4_REPLAY_ORCHESTRATION_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if not str(result["status"]).startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
