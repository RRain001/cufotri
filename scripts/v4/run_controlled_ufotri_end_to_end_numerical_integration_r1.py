#!/usr/bin/env python3
"""Machine-visible controlled UFOTRI end-to-end numerical integration R1."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from typing import Any

from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing
from cteas_ufotri.exposure.dose_v3 import DOSE_COEFFICIENT_UNIT, DoseParameters
from cteas_ufotri.exposure.intake_v3 import CONSUMPTION_RATE_UNIT, ConsumptionParameters
from cteas_ufotri.plant.food_v3 import HarvestParameters
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_exchange_resistance.resistance import ResistanceChain
from cteas_ufotri.plant.mass_basis_v3_1 import (
    AreaBasis,
    AreaBasisKind,
    BasisProvenance,
    MassBasis,
    MassBasisContract,
    TissueScope,
    TissueScopeKind,
)
from cteas_ufotri.plant.obt_v3 import OBTState, OBTSolver, PlantBiologicalForcing, ufotri_obt_baseline_parameters
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    UFOTRIEq39RootUptakeInputV4,
    ufotri_eq39_root_uptake,
)
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilForcing, ThreeLayerSoilState, ThreeLayerSoilStorageSolver
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    ReplayDomainProvenance,
    TerminalHarvestMode,
    V4FoodIntakeDoseEndpointAdapter,
    V4ReplayInputSystemOrchestrator,
    V4ReplayIntervalInput,
    V4SoilRootTFWTOBTState,
    V4TerminalHarvestRequest,
)

UTC = timezone.utc
DT_S = 3600.0
STEPS = 24
START = datetime(2026, 1, 1, tzinfo=UTC)
HALF_LIFE_S = 388_789_632.0
SPATIAL = "synthetic-controlled-ufotri-e2e-r1"
PLANT = "synthetic-soybean"
CROP = "Glycine_max"
STAGE = "maturity"
PRODUCT = "synthetic-soy-food"


def forcing_provenance(source_id: str, digest: str) -> ForcingProvenance:
    return ForcingProvenance(
        source_id=source_id,
        source_version="controlled-ufotri-e2e-r1",
        artifact_sha256=digest * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=DT_S,
    )


def replay_provenance(source_id: str, digest: str) -> ReplayDomainProvenance:
    return ReplayDomainProvenance(
        source_id=source_id,
        source_version="controlled-ufotri-e2e-r1",
        artifact_sha256=digest * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=DT_S,
        source_kind="SYNTHETIC_TEST",
    )


def root_provenance(source_id: str, digest: str, context: str) -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id=source_id,
        source_locator="scripts/v4/run_controlled_ufotri_end_to_end_numerical_integration_r1.py",
        revision="controlled-ufotri-e2e-r1",
        artifact_sha256=digest * 64,
        profile_context=context,
    )


def initial_state() -> V4SoilRootTFWTOBTState:
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-e2e-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=START,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_E2E_SOIL_STATE",
            source_version="controlled-ufotri-e2e-r1",
            artifact_sha256="a" * 64,
            spatial_reference=SPATIAL,
            temporal_resolution_s=DT_S,
        ),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier=PLANT,
        crop=CROP,
        growth_stage=STAGE,
        tfwt_inventory_bq_m2=2.0,
        water_content_kg_m2=5.0,
        time=START,
        provenance=forcing_provenance("SYNTHETIC_E2E_TFWT", "b"),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier=PLANT,
        crop=CROP,
        growth_stage=STAGE,
        obt_inventory_bq_m2=0.0,
        plant_mass_kg_m2=2.0,
        timestamp=START,
        provenance=forcing_provenance("SYNTHETIC_E2E_OBT", "c"),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def orchestrator() -> V4ReplayInputSystemOrchestrator:
    return V4ReplayInputSystemOrchestrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S),
        obt_solver=OBTSolver(parameters=ufotri_obt_baseline_parameters()),
    )


def is_daylight(index: int) -> bool:
    hour = index % 24
    return 6 <= hour < 18


def replay_atmosphere(timestamp: datetime, daylight: bool) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location=SPATIAL,
        air_hto_concentration=1.5 if daylight else 0.8,
        deposition_flux=1.0e-6,
        temperature=293.15 if daylight else 288.15,
        humidity=0.55,
        wind_speed=2.0,
        precipitation=0.0,
        source="SYNTHETIC_REPLAY_NUMERICAL_INTEGRATION",
        provenance=forcing_provenance("SYNTHETIC_E2E_ATMOS", "d"),
    )


def eq39_root_forcing(state: V4SoilRootTFWTOBTState, atmosphere: AtmosphericHTOForcing, daylight: bool):
    eq39 = UFOTRIEq39RootUptakeInputV4(
        plant_identifier=state.plant_identifier,
        timestamp=state.timestamp,
        temperature_k=atmosphere.temperature,
        net_radiation_w_m2=300.0 if daylight else 0.0,
        lai=3.0,
        soil_water_m=state.soil_state.total_water_inventory_m,
        maximum_water_m=0.60,
        wilting_water_m=0.15,
        latent_heat_j_kg=2_450_000.0,
        water_density_kg_m3=1000.0,
        psychrometric_constant_pa_k=66.0,
        meteorology_provenance=root_provenance(
            "SYNTHETIC_E2E_EQ39_METEOROLOGY",
            "e",
            "SYNTHETIC_REPLAY_TEMPERATURE_AND_NET_RADIATION",
        ),
        case_provenance=root_provenance(
            "SYNTHETIC_E2E_EQ39_CASE",
            "f",
            "SYNTHETIC_LAI_AND_SOIL_WATER_CASE",
        ),
        physical_constants_provenance=root_provenance(
            "SYNTHETIC_E2E_EQ39_CONSTANTS",
            "a",
            "CONTROLLED_EQ39_PHYSICAL_CONVERSIONS",
        ),
    )
    return ufotri_eq39_root_uptake(
        eq39,
        output_provenance=root_provenance(
            "CONTROLLED_UFOTRI_EQ39_TO_20_40_40",
            "b",
            "EQ39_TOTAL_UPTAKE_TO_UFOTRI_20_40_40",
        ),
    )


def replay_interval(state: V4SoilRootTFWTOBTState, index: int):
    daylight = is_daylight(index)
    atmosphere = replay_atmosphere(state.timestamp, daylight)
    root = eq39_root_forcing(state, atmosphere, daylight)
    interval = V4ReplayIntervalInput(
        atmospheric_forcing=atmosphere,
        interval_end=state.timestamp + timedelta(seconds=DT_S),
        soil_external_forcing=ThreeLayerSoilForcing(timestamp=state.timestamp),
        soil_external_provenance=replay_provenance("SYNTHETIC_E2E_SOIL_EXTERNAL", "c"),
        root_forcing=root.layer_forcing,
        biological_forcing=PlantBiologicalForcing(is_daylight=daylight),
        biological_provenance=replay_provenance("SYNTHETIC_E2E_BIOLOGY", "d"),
        resistance=ResistanceChain.from_components(100.0, 100.0, 800.0),
        equilibrium_air_concentration_bq_m3=0.5,
        leaf_exchange_provenance=replay_provenance("SYNTHETIC_E2E_LEAF", "e"),
    )
    return daylight, root, interval


def run_dynamic(*, restart_at_half: bool = False) -> tuple[V4SoilRootTFWTOBTState, dict[str, Any]]:
    model = orchestrator()
    state = initial_state()
    daylight_root_positive = True
    nighttime_root_zero = True
    exact_20_40_40 = True
    root_j_q_c = True
    plant_balance_closed = True
    coupled_balance_closed = True
    max_plant_residual = 0.0
    max_coupled_residual = 0.0
    total_root_water_m = 0.0
    total_root_hto_bq_m2 = 0.0

    for index in range(STEPS):
        if restart_at_half and index == STEPS // 2:
            state = V4SoilRootTFWTOBTState.from_json(state.to_json())
        daylight, root, interval = replay_interval(state, index)
        total = root.root_uptake_m_s
        layers = root.layer_forcing.water_uptake_fluxes_m_s
        if daylight:
            daylight_root_positive = daylight_root_positive and total > 0.0
        else:
            nighttime_root_zero = nighttime_root_zero and total == 0.0
        exact_20_40_40 = exact_20_40_40 and all(
            math.isclose(value, total * fraction, rel_tol=1.0e-15, abs_tol=0.0)
            for value, fraction in zip(layers, (0.2, 0.4, 0.4), strict=True)
        ) and math.isclose(sum(layers), total, rel_tol=1.0e-15, abs_tol=0.0)

        result = model.advance(state, interval)
        root_j_q_c = root_j_q_c and all(
            math.isclose(
                transfer.hto_uptake_flux_bq_m2_s,
                transfer.water_uptake_flux_m_s * transfer.soil_hto_concentration_bq_m3_water,
                rel_tol=1.0e-15,
                abs_tol=0.0,
            )
            for transfer in result.root_plan.layer_transfers
        )
        max_plant_residual = max(max_plant_residual, abs(result.balance.plant_residual_bq_m2))
        max_coupled_residual = max(max_coupled_residual, abs(result.balance.coupled_residual_bq_m2))
        plant_balance_closed = plant_balance_closed and abs(result.balance.plant_residual_bq_m2) <= 1.0e-10
        coupled_balance_closed = coupled_balance_closed and abs(result.balance.coupled_residual_bq_m2) <= 1.0e-10
        total_root_water_m += result.root_plan.total_water_transfer_m
        total_root_hto_bq_m2 += result.root_plan.total_hto_transfer_bq_m2
        state = result.state

    metrics = {
        "daylight_root_positive": daylight_root_positive,
        "nighttime_root_zero": nighttime_root_zero,
        "exact_20_40_40": exact_20_40_40,
        "root_j_equals_q_times_c": root_j_q_c,
        "plant_balance_closed": plant_balance_closed,
        "coupled_balance_closed": coupled_balance_closed,
        "max_abs_plant_residual_bq_m2": max_plant_residual,
        "max_abs_coupled_residual_bq_m2": max_coupled_residual,
        "total_root_water_transfer_m": total_root_water_m,
        "total_root_hto_transfer_bq_m2": total_root_hto_bq_m2,
    }
    return state, metrics


def mass_basis(source_id: str) -> MassBasisContract:
    return MassBasisContract(
        subject_id=PRODUCT,
        mass_basis=MassBasis.FRESH_MASS,
        tissue_scope=TissueScope(kind=TissueScopeKind.HARVEST_PRODUCT, identifier=PRODUCT),
        area_basis=AreaBasis(kind=AreaBasisKind.NOT_APPLICABLE),
        provenance=BasisProvenance(
            source_id=source_id,
            source_locator="scripts/v4/run_controlled_ufotri_end_to_end_numerical_integration_r1.py",
            revision="controlled-ufotri-e2e-r1",
        ),
    )


def endpoint_request() -> V4TerminalHarvestRequest:
    return V4TerminalHarvestRequest(
        harvest_mode=TerminalHarvestMode.OBT_PLUS_TFWT,
        harvest_parameters=HarvestParameters(
            plant_identifier=PLANT,
            crop_identifier=CROP,
            growth_stage=STAGE,
            food_product_identifier=PRODUCT,
            harvest_fraction=0.5,
            harvest_area_m2=2.0,
            tfwt_harvest_fraction=0.25,
            provenance=forcing_provenance("SYNTHETIC_E2E_HARVEST", "f"),
        ),
        food_product_basis=mass_basis("SYNTHETIC_E2E_FOOD_BASIS"),
        consumption_basis=mass_basis("SYNTHETIC_E2E_CONSUMPTION_BASIS"),
        consumption_parameters=ConsumptionParameters(
            food_product_identifier=PRODUCT,
            age_group_identifier="adult",
            annual_consumption_amount=20.0,
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=forcing_provenance("SYNTHETIC_E2E_CONSUMPTION", "a"),
            food_product_mass_kg=5.0,
        ),
        dose_parameters=DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=2.0e-11,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=forcing_provenance("SYNTHETIC_E2E_DOSE", "b"),
        ),
        consumer_identifier="synthetic-e2e-consumer",
    )


def build_result() -> dict[str, Any]:
    state, metrics = run_dynamic()
    repeat_state, repeat_metrics = run_dynamic()
    restart_state, restart_metrics = run_dynamic(restart_at_half=True)

    endpoint_before = state.to_json()
    endpoint = V4FoodIntakeDoseEndpointAdapter().advance(state, endpoint_request())

    gates = {
        **{key: bool(value) for key, value in metrics.items() if isinstance(value, bool)},
        "ufotri_obt_baseline_nonzero": state.obt_state.inventory() > 0.0,
        "root_transfer_nonzero": metrics["total_root_water_transfer_m"] > 0.0,
        "deterministic_repeat": repeat_state == state and repeat_metrics == metrics,
        "restart_equivalence": restart_state == state and restart_metrics == metrics,
        "endpoint_non_mutating": state.to_json() == endpoint_before,
        "food_inventory_nonzero": endpoint.food_inventory.inventory() > 0.0,
        "annual_intake_nonzero": endpoint.intake_state.inventory() > 0.0,
        "dose_nonzero": endpoint.dose_state.dose() > 0.0,
        "endpoint_timestamp_identity": (
            endpoint.food_inventory.timestamp
            == endpoint.intake_state.timestamp
            == endpoint.dose_state.timestamp
            == state.timestamp
        ),
        "h3_food_ingestion_identity": (
            endpoint.audit.radionuclide_identifier == "H-3"
            and endpoint.audit.pathway_identifier == "food-ingestion"
        ),
        "harvest_not_environmental_sink": endpoint.audit.downstream_branch_is_environmental_mass_sink is False,
        "no_basis_conversion": endpoint.audit.numerical_basis_conversion_performed is False,
        "no_area_conversion": endpoint.audit.numerical_area_conversion_performed is False,
    }
    status = "PASS_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION" if all(gates.values()) else "FAIL_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION"
    params = ufotri_obt_baseline_parameters()
    return {
        "schema_version": "v1",
        "stage": "V4_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION_R1",
        "status": status,
        "source_kind": "SYNTHETIC_REPLAY_NUMERICAL_INTEGRATION",
        "selected_operator_split": "PRESERVE_V3_POST_OBT_ROOT_GAIN",
        "controlled_profiles": {
            "root_total_uptake": "EQUILIBRIUM_RADIATION_EQ39",
            "root_layer_distribution": [0.2, 0.4, 0.4],
            "obt_kf_s": params.kf_s,
            "obt_kr_s": params.kr_s,
            "obt_daylight_multiplier": params.daylight_multiplier,
            "obt_nighttime_multiplier": params.nighttime_multiplier,
        },
        "gates": gates,
        "dynamic_metrics": metrics,
        "final_state": {
            "timestamp": state.timestamp.isoformat(),
            "soil_hto_bq_m2": state.soil_state.total_hto_inventory_bq_m2,
            "soil_water_m": state.soil_state.total_water_inventory_m,
            "tfwt_bq_m2": state.tfwt_state.inventory(),
            "obt_bq_m2": state.obt_state.inventory(),
        },
        "endpoint": {
            "food_inventory_bq": endpoint.food_inventory.inventory(),
            "annual_intake_bq": endpoint.intake_state.inventory(),
            "committed_dose_sv": endpoint.dose_state.dose(),
        },
        "resolution_state": {
            "eq39_controlled_baseline_active": True,
            "ufotri_20_40_40_controlled_profile_active": True,
            "root_q_w_production_input_resolved": True,
            "ufotri_obt_controlled_baseline_active": True,
            "software_chain_connected_with_controlled_ufotri_profiles": True,
            "full_model_production_ready": False,
        },
        "hard_boundaries": {
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "full_hydrology": False,
            "leaf_r5": False,
            "multi_pool_obt": False,
            "full_penman_eq38_production_active": False,
            "ufotri_reference_layer_rates_active": False,
            "short_term_3h_delay_active": False,
            "real_cteas_atmos_binding": False,
            "v3_default_path_changed": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_result()
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(f"V4_CONTROLLED_UFOTRI_E2E_STATUS={result['status']}")
    print(f"V4_CONTROLLED_UFOTRI_E2E_RESULT_JSON={json.dumps(result, sort_keys=True)}")
    if not str(result["status"]).startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
