#!/usr/bin/env python3
"""Machine-readable H5 native atmosphere -> environmental chain -> dose gate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

from cteas_ufotri.atmosphere.ufotri_native_process_v4 import (
    KFK5194HTOWashoutMode,
    kfk5194_species_policy,
    transport_straight_segment_reconciled,
)
from cteas_ufotri.atmosphere.ufotri_native_v4 import TritiumAtmosphericForm
from cteas_ufotri.coupling.ht_v4 import GaseousTritiumSpecies
from cteas_ufotri.coupling.reemission_area_source_v4 import (
    AccountedReemissionLoss,
    HourlyReemissionHandoffBuffer,
    ManualAreaSourceGeometry,
    SOIL,
    UNRESOLVED_HTO_ORIGIN,
    superpose_secondary_sources,
)
from cteas_ufotri.coupling.ufotri_native_atmos_forcing_v4 import (
    NativeForcingContext,
    UFOTRINativeForcingAdapterError,
    adapt_native_hto_forcing,
)
from cteas_ufotri.dose.ufotri_manual_v4 import (
    UFOTRIFoodSpecificActivity,
    UFOTRIManualConsumptionRates,
    UFOTRIManualExposureState,
    UFOTRIManualFoodSnapshot,
    advance_ufotri_manual_exposure,
    calculate_ufotri_manual_dose,
    ufotri_manual_adult_reference_policy,
)
from cteas_ufotri.foodchain.ufotri_cow_milk_beef_v4 import (
    UFOTRICowMilkBeefForcing,
    UFOTRICowMilkBeefSolver,
    UFOTRICowMilkBeefState,
    slaughter_to_beef,
    ufotri_cow_milk_beef_manual_profile,
)
from cteas_ufotri.foodchain.ufotri_vegetable_grass_v4 import (
    EQ66_EXACT_FROM_STATED_MASSES,
    UFOTRIVegetableExchangeSolver,
    ufotri_vegetable_eq65_66_parameters,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.leaf_ufotri_v4 import (
    GOLDER_ESTIMATOR_ID,
    build_ufotri_eq7_25_resistance_chain,
    ufotri_eq27_30_analytic_interval_transfer,
    ufotri_eq27_equilibrium_air_concentration_bq_m3,
)
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
from cteas_ufotri.v4_integration.native_atmosphere_to_dose_v4 import (
    compose_native_atmosphere_replay_input,
)
from cteas_ufotri.v4_integration.replay_input_orchestration import (
    ReplayDomainProvenance,
    V4ReplayInputSystemOrchestrator,
    V4ReplayIntervalInput,
)
from cteas_ufotri.v4_integration.soil_root_tfwt_obt import (
    V4SoilRootTFWTOBTState,
)


UTC = timezone.utc
STAGE = "UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1"
SPATIAL = "h5-controlled-ufotri-native-support"
DT = 3600.0
HALF_LIFE_S = 388_789_632.0
OBT_KF_S = 2.0e-5
OBT_KR_S = 5.0e-6
ALPHA_LIQUID_TO_VAPOUR = 1.1
SOIL_REEMISSION_FLUX_BQ_M2_S = 1.0e-3
SOURCE_HTO_BQ_S = 1.0e8
SOURCE_HT_BQ_S = 5.0e7
DOWNWIND_M = 1000.0
WIND_M_S = 5.0
RELEASE_HEIGHT_M = 20.0
RECEPTOR_HEIGHT_M = 1.0
MIXING_LID_M = 560.0
STABILITY = "D"
HTO_VD_M_S = 1.8e-2
HT_VD_M_S = 5.0e-4
WET_INTENSITY_MM_H = 4.0
WET_LOCAL_QUALIFICATION_FLUX_BQ_M2_S = 2.0e-4


def _close(a: float, b: float, *, rel: float = 1.0e-10, abs_: float = 1.0e-10) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def _plant_provenance(dt_s: float) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="H5_CONTROLLED_PLANT_STATE",
        source_version="h5-r1",
        artifact_sha256="a" * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=dt_s,
    )


def _domain_provenance(source_id: str, digest: str, dt_s: float) -> ReplayDomainProvenance:
    return ReplayDomainProvenance(
        source_id=source_id,
        source_version="h5-r1",
        artifact_sha256=digest * 64,
        spatial_reference=SPATIAL,
        temporal_resolution_s=dt_s,
        source_kind="SYNTHETIC_TEST",
    )


def _root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="H5_CONTROLLED_ROOT_QW",
        source_locator="scripts/v4/run_ufotri_native_atmosphere_to_dose_qualification_r1.py",
        revision="h5-r1",
        artifact_sha256="c" * 64,
        profile_context="UFOTRI_20_40_40_CONTROLLED_QUALIFICATION",
    )


def _state(start: datetime, dt_s: float = DT) -> V4SoilRootTFWTOBTState:
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="h5-controlled-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(10.0, 20.0, 30.0),
        timestamp=start,
        provenance=SoilV4Provenance(
            source_id="H5_CONTROLLED_SOIL_STATE",
            source_version="h5-r1",
            artifact_sha256="b" * 64,
            spatial_reference=SPATIAL,
            temporal_resolution_s=dt_s,
        ),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="h5-vegetable",
        crop="H5_CONTROLLED_GREEN_VEGETABLE",
        growth_stage="H5_CONTROLLED_STAGE",
        tfwt_inventory_bq_m2=2.0,
        water_content_kg_m2=5.0,
        time=start,
        provenance=_plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="h5-vegetable",
        crop="H5_CONTROLLED_GREEN_VEGETABLE",
        growth_stage="H5_CONTROLLED_STAGE",
        obt_inventory_bq_m2=1.0,
        plant_mass_kg_m2=2.0,
        timestamp=start,
        provenance=_plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def _root_forcing(timestamp: datetime) -> ThreeLayerRootWaterFluxForcingV4:
    # 20/40/40 is the recovered vegetable/root profile; the magnitude remains
    # qualification-only and is not a production parameter.
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier="h5-vegetable",
        timestamp=timestamp,
        water_uptake_fluxes_m_s=(1.0e-7, 2.0e-7, 2.0e-7),
        provenance=_root_provenance(),
    )


def _manual_leaf_resistance(*, precipitation_m_s: float = 0.0):
    return build_ufotri_eq7_25_resistance_chain(
        lai=3.0,
        is_day=True,
        soil_available_water_exhausted=False,
        precipitation_m_s=precipitation_m_s,
        stomatal_resistance_day_s_m=100.0,
        stomatal_resistance_night_s_m=1000.0,
        station_wind_speed_m_s=WIND_M_S,
        station_height_m=10.0,
        station_to_100m_power_exponent=0.15,
        canopy_height_m=1.0,
        monin_obukhov_estimator_id=GOLDER_ESTIMATOR_ID,
        stability_class=STABILITY,
    )


def _placeholder_atmos(timestamp: datetime, dt_s: float):
    from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing

    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location=SPATIAL,
        air_hto_concentration=0.0,
        deposition_flux=0.0,
        temperature=298.15,
        humidity=0.55,
        wind_speed=WIND_M_S,
        precipitation=0.0,
        source="H5_TEMPLATE_ONLY",
        provenance=_plant_provenance(dt_s),
    )


def _template(
    state: V4SoilRootTFWTOBTState,
    *,
    dt_s: float,
    surface_reemission_bq_m2_s: float,
) -> V4ReplayIntervalInput:
    resistance = _manual_leaf_resistance()
    equilibrium_air = ufotri_eq27_equilibrium_air_concentration_bq_m3(
        tfwt_concentration_bq_kg_water=state.tfwt_state.tfwt_concentration_bq_kg_water,
        temperature_k=298.15,
        isotope_fractionation_liquid_to_vapour=ALPHA_LIQUID_TO_VAPOUR,
    )
    return V4ReplayIntervalInput(
        atmospheric_forcing=_placeholder_atmos(state.timestamp, dt_s),
        interval_end=state.timestamp + timedelta(seconds=dt_s),
        soil_external_forcing=ThreeLayerSoilForcing(
            timestamp=state.timestamp,
            l1_l2_water_flux_m_s=1.0e-8,
            l1_l2_hto_flux_bq_m2_s=1.0e-4,
            l2_l3_water_flux_m_s=5.0e-9,
            l2_l3_hto_flux_bq_m2_s=5.0e-5,
            surface_reemission_hto_loss_bq_m2_s=surface_reemission_bq_m2_s,
        ),
        soil_external_provenance=_domain_provenance("H5_CONTROLLED_SOIL_EXTERNAL", "d", dt_s),
        root_forcing=_root_forcing(state.timestamp),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        biological_provenance=_domain_provenance("H5_CONTROLLED_BIOLOGY", "e", dt_s),
        resistance=resistance.chain,
        equilibrium_air_concentration_bq_m3=equilibrium_air,
        leaf_exchange_provenance=_domain_provenance("H5_UFOTRI_EQ7_25_RESISTANCE", "f", dt_s),
    )


def _context(start: datetime, dt_s: float, *, precipitation_mm_h: float = 0.0) -> NativeForcingContext:
    return NativeForcingContext(
        start_utc=start,
        end_utc=start + timedelta(seconds=dt_s),
        source_id="H5_UFOTRI_NATIVE_ATMOSPHERE",
        provenance_id=f"H5_NATIVE_{int(start.timestamp())}_{int(dt_s)}",
        source_version="h5-r1",
        artifact_sha256="1" * 64,
        spatial_support=SPATIAL,
        concentration_sampling_height_m=RECEPTOR_HEIGHT_M,
        air_temperature_k=298.15,
        relative_humidity=0.55,
        wind_speed_m_s=WIND_M_S,
        precipitation_m_s=precipitation_mm_h * 1.0e-3 / 3600.0,
        creation_time_utc=start,
        quality_flag="H5_CONTROLLED_QUALIFICATION",
    )


def _native_transport(*, wet_hto: bool = False):
    precipitation = WET_INTENSITY_MM_H if wet_hto else 0.0
    hto_policy = kfk5194_species_policy(
        species=TritiumAtmosphericForm.HTO,
        dry_deposition_velocity_m_s=HTO_VD_M_S,
        precipitation_mm_h=precipitation,
        mode=KFK5194HTOWashoutMode.POWER_LAW,
    )
    ht_policy = kfk5194_species_policy(
        species=TritiumAtmosphericForm.HT,
        dry_deposition_velocity_m_s=HT_VD_M_S,
        precipitation_mm_h=precipitation,
        mode=KFK5194HTOWashoutMode.POWER_LAW,
    )
    common = dict(
        downwind_m=DOWNWIND_M,
        crosswind_m=0.0,
        wind_speed_m_s=WIND_M_S,
        effective_release_height_m=RELEASE_HEIGHT_M,
        receptor_height_m=RECEPTOR_HEIGHT_M,
        stability_class=STABILITY,
        mixing_lid_m=MIXING_LID_M,
    )
    hto = transport_straight_segment_reconciled(
        source_bq_s=SOURCE_HTO_BQ_S,
        policy=hto_policy,
        **common,
    )
    ht = transport_straight_segment_reconciled(
        source_bq_s=SOURCE_HT_BQ_S,
        policy=ht_policy,
        **common,
    )
    return hto, ht


def _orchestrator() -> V4ReplayInputSystemOrchestrator:
    return V4ReplayInputSystemOrchestrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=OBT_KF_S, kr_s=OBT_KR_S),
    )


def _run_existing_gate(filename: str) -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "v4" / filename)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "filename": filename,
        "returncode": completed.returncode,
        "pass_token_present": "PASS_" in completed.stdout,
        "stdout_tail": completed.stdout[-1200:],
    }


def _food_and_manual_dose(
    *,
    endpoint: V4SoilRootTFWTOBTState,
    air_hto_bq_m3: float,
) -> dict[str, object]:
    vegetable_solver = UFOTRIVegetableExchangeSolver(
        ufotri_vegetable_eq65_66_parameters(
            forward_rate_basis=EQ66_EXACT_FROM_STATED_MASSES
        )
    )
    vegetable = vegetable_solver.advance(
        endpoint.tfwt_state,
        endpoint.obt_state,
        86400.0,
    )

    animal_profile = ufotri_cow_milk_beef_manual_profile()
    animal_state = UFOTRICowMilkBeefState(
        timestamp=vegetable.tfwt_state.time,
        grass_hto_bq_m2=vegetable.tfwt_state.inventory(),
        grass_obt_bq_m2=vegetable.obt_state.inventory(),
    )
    animal = UFOTRICowMilkBeefSolver(
        animal_profile,
        numerical_step_seconds=3600.0,
    ).advance(
        animal_state,
        UFOTRICowMilkBeefForcing(
            atmosphere_hto_inventory_bq_m2=(
                air_hto_bq_m3 * animal_profile.eq98_mixing_height_m
            ),
            atmosphere_provenance="H5_UFOTRI_NATIVE_PLUS_F1_SECONDARY",
        ),
        86400.0,
    )
    slaughtered, slaughter_balance = slaughter_to_beef(animal.state, 0.2)

    # These masses are controlled qualification projection bases only. They are
    # deliberately local to H5 and are not defaults, parameters or empirical
    # claims. D4 itself intentionally provides no edible-beef mass default.
    green_mass_kg_m2 = 2.0
    milk_mass_kg_m2 = 5.0
    beef_mass_kg_m2 = 10.0
    foods = UFOTRIManualFoodSnapshot(
        green_vegetable=UFOTRIFoodSpecificActivity(
            hto_bq_kg=vegetable.tfwt_state.inventory() / green_mass_kg_m2,
            obt_bq_kg=vegetable.obt_state.inventory() / green_mass_kg_m2,
        ),
        beef=UFOTRIFoodSpecificActivity(
            hto_bq_kg=slaughtered.beef_hto_bq_m2 / beef_mass_kg_m2,
            obt_bq_kg=slaughtered.beef_obt_bq_m2 / beef_mass_kg_m2,
        ),
        milk=UFOTRIFoodSpecificActivity(
            hto_bq_kg=slaughtered.milk_hto_bq_m2 / milk_mass_kg_m2,
            obt_bq_kg=slaughtered.milk_obt_bq_m2 / milk_mass_kg_m2,
        ),
    )
    exposure0 = UFOTRIManualExposureState.zero(
        exposure_provenance_id="H5_CONTROLLED_MANUAL_EXPOSURE"
    )
    exposure = advance_ufotri_manual_exposure(
        exposure0,
        dt_s=DT,
        air_hto_bq_m3=air_hto_bq_m3,
        foods=foods,
    )
    half = advance_ufotri_manual_exposure(
        exposure0,
        dt_s=DT / 2.0,
        air_hto_bq_m3=air_hto_bq_m3,
        foods=foods,
    )
    halves = advance_ufotri_manual_exposure(
        half,
        dt_s=DT / 2.0,
        air_hto_bq_m3=air_hto_bq_m3,
        foods=foods,
    )
    habits = UFOTRIManualConsumptionRates(
        breathing_rate_m3_s=2.0e-4,
        green_vegetable_kg_d=0.30,
        beef_kg_d=0.15,
        milk_kg_d=0.40,
        provenance_id="H5_CONTROLLED_HABITS_NOT_PRODUCTION",
    )
    dose = calculate_ufotri_manual_dose(
        exposure,
        habits=habits,
        policy=ufotri_manual_adult_reference_policy(),
    )
    partition_fields = (
        "elapsed_s",
        "air_hto_bq_s_m3",
        "green_vegetable_hto_bq_d_kg",
        "green_vegetable_obt_bq_d_kg",
        "beef_hto_bq_d_kg",
        "beef_obt_bq_d_kg",
        "milk_hto_bq_d_kg",
        "milk_obt_bq_d_kg",
    )
    exposure_partition_equivalent = all(
        _close(getattr(exposure, field), getattr(halves, field), rel=1.0e-12, abs_=1.0e-12)
        for field in partition_fields
    )
    return {
        "vegetable_conservation_residual_bq_m2": vegetable.balance.total_residual_bq_m2,
        "animal_conservation_residual_bq_m2": animal.balance.residual_bq_m2,
        "slaughter_conservation_residual_bq_m2": slaughter_balance.total_residual_bq_m2,
        "green_total_bq_kg": foods.green_vegetable.hto_bq_kg + foods.green_vegetable.obt_bq_kg,
        "milk_total_bq_kg": foods.milk.hto_bq_kg + foods.milk.obt_bq_kg,
        "beef_total_bq_kg": foods.beef.hto_bq_kg + foods.beef.obt_bq_kg,
        "qualification_mass_bases_kg_m2": {
            "green": green_mass_kg_m2,
            "milk": milk_mass_kg_m2,
            "beef": beef_mass_kg_m2,
            "production_default": False,
        },
        "manual_exposure_partition_equivalent": exposure_partition_equivalent,
        "inhalation_dose_sv": dose.inhalation_dose_sv,
        "skin_dose_sv": dose.skin_absorption_dose_sv,
        "ingestion_dose_sv": dose.ingestion_dose_sv,
        "total_dose_sv": dose.total_effective_dose_sv,
        "eq106_residual_sv": dose.eq106_residual_sv,
        "eq107_residual_sv": dose.eq107_residual_sv,
    }


def build_result() -> dict[str, object]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    native_hto, native_ht = _native_transport(wet_hto=False)
    wet_hto, _ = _native_transport(wet_hto=True)

    wet_context = _context(start, DT, precipitation_mm_h=WET_INTENSITY_MM_H)
    wet_fail_closed = False
    try:
        adapt_native_hto_forcing(result=wet_hto, context=wet_context)
    except UFOTRINativeForcingAdapterError:
        wet_fail_closed = True
    wet_explicit = adapt_native_hto_forcing(
        result=wet_hto,
        context=wet_context,
        wet_surface_deposition_flux_bq_m2_s=WET_LOCAL_QUALIFICATION_FLUX_BQ_M2_S,
    )

    state0 = _state(start)
    context1 = _context(start, DT)
    template1 = _template(
        state0,
        dt_s=DT,
        surface_reemission_bq_m2_s=SOIL_REEMISSION_FLUX_BQ_M2_S,
    )
    composition1 = compose_native_atmosphere_replay_input(
        template=template1,
        native_hto_result=native_hto,
        native_ht_result=native_ht,
        context=context1,
        gaseous_ht_species=GaseousTritiumSpecies.HT,
    )
    first = _orchestrator().advance(state0, composition1.replay_input)
    first_repeat = _orchestrator().advance(state0, composition1.replay_input)

    manual_leaf = ufotri_eq27_30_analytic_interval_transfer(
        air_concentration_bq_m3=composition1.ledger.combined_hto_air_bq_m3,
        initial_tfwt_concentration_bq_kg_water=state0.tfwt_state.tfwt_concentration_bq_kg_water,
        plant_water_content_kg_m2=state0.tfwt_state.water_content_kg_m2,
        temperature_k=298.15,
        total_resistance_s_m=template1.resistance.total_resistance,
        isotope_fractionation_liquid_to_vapour=ALPHA_LIQUID_TO_VAPOUR,
        interval_seconds=DT,
    )

    geometry = ManualAreaSourceGeometry.from_canopy_height(
        length_m=100.0,
        width_m=100.0,
        canopy_height_m=1.0,
    )
    event = AccountedReemissionLoss(
        compartment=SOIL,
        flux_bq_m2_s=SOIL_REEMISSION_FLUX_BQ_M2_S,
        origin=UNRESOLVED_HTO_ORIGIN,
        transfer_id="H5_SOIL_REEMISSION_HOUR0",
    )
    buffer = HourlyReemissionHandoffBuffer(
        time_step_seconds=3600,
        geometry=geometry,
    )
    before_sources = buffer.step([event])
    soil_source, plant_source = buffer.active_sources()
    secondary = superpose_secondary_sources(
        primary_air_bq_m3=native_hto.air_concentration_bq_m3,
        soil_source=soil_source,
        plant_source=plant_source,
        geometry=geometry,
        receptor_downwind_m=DOWNWIND_M,
        receptor_crosswind_m=0.0,
        wind_speed_m_s=WIND_M_S,
        stability_class=STABILITY,
        soil_fallout_factor=1.0,
        soil_washout_factor=1.0,
        plant_fallout_factor=1.0,
        plant_washout_factor=1.0,
    )
    environmental_reemission_activity_bq = (
        first.balance.soil_nonroot_external_hto_loss_bq_m2 * geometry.area_m2
    )

    context2 = _context(first.state.timestamp, DT)
    template2 = _template(
        first.state,
        dt_s=DT,
        surface_reemission_bq_m2_s=0.0,
    )
    no_secondary2 = compose_native_atmosphere_replay_input(
        template=template2,
        native_hto_result=native_hto,
        native_ht_result=native_ht,
        context=context2,
        gaseous_ht_species=GaseousTritiumSpecies.HT,
    )
    composition2 = compose_native_atmosphere_replay_input(
        template=template2,
        native_hto_result=native_hto,
        native_ht_result=native_ht,
        context=context2,
        gaseous_ht_species=GaseousTritiumSpecies.HT,
        secondary_hto_air_bq_m3=secondary.secondary_air_bq_m3,
    )
    second = _orchestrator().advance(first.state, composition2.replay_input)
    restarted = V4SoilRootTFWTOBTState.from_json(first.state.to_json())
    restarted_second = _orchestrator().advance(restarted, composition2.replay_input)

    # Flux-rate composition is partition invariant for interval-constant native
    # transport; E2 re-integrates activity over the explicitly shorter interval.
    half_state = _state(start, DT / 2.0)
    half_template = _template(
        half_state,
        dt_s=DT / 2.0,
        surface_reemission_bq_m2_s=SOIL_REEMISSION_FLUX_BQ_M2_S,
    )
    half_composition = compose_native_atmosphere_replay_input(
        template=half_template,
        native_hto_result=native_hto,
        native_ht_result=native_ht,
        context=_context(start, DT / 2.0),
        gaseous_ht_species=GaseousTritiumSpecies.HT,
    )
    full_integrated_surface_bq_m2 = composition1.ledger.combined_hto_surface_flux_bq_m2_s * DT
    two_half_integrated_surface_bq_m2 = (
        half_composition.ledger.combined_hto_surface_flux_bq_m2_s * (DT / 2.0) * 2.0
    )

    buffer_half = HourlyReemissionHandoffBuffer(
        time_step_seconds=1800,
        geometry=geometry,
    )
    half_event = AccountedReemissionLoss(
        compartment=SOIL,
        flux_bq_m2_s=SOIL_REEMISSION_FLUX_BQ_M2_S,
        origin=UNRESOLVED_HTO_ORIGIN,
        transfer_id="H5_SOIL_REEMISSION_HOUR0",
    )
    buffer_half.step([half_event])
    buffer_half.step([half_event])
    half_soil_source, _ = buffer_half.active_sources()

    food_dose = _food_and_manual_dose(
        endpoint=second.state,
        air_hto_bq_m3=composition2.ledger.combined_hto_air_bq_m3,
    )

    existing_gates = {
        "manual_hydrology": _run_existing_gate(
            "run_ufotri_coupled_water_hto_hydrology_verification_r1.py"
        ),
        "reemission_area_source": _run_existing_gate(
            "check_ufotri_reemission_area_source_reconciliation_r1.py"
        ),
        "canada_contract": _run_existing_gate(
            "check_ufotri_canada_1987_benchmark_reconstruction_r1.py"
        ),
        "iter_contract": _run_existing_gate(
            "check_ufotri_iter_benchmark_reconstruction_r1.py"
        ),
    }

    invariants = {
        "h4_native_hto_positive": native_hto.air_concentration_bq_m3 > 0.0,
        "h4_native_ht_positive": native_ht.air_concentration_bq_m3 > 0.0,
        "h4_source_depletion_ledgers_close": (
            abs(native_hto.source_depletion_residual_bq_s) <= 1.0e-8
            and abs(native_ht.source_depletion_residual_bq_s) <= 1.0e-8
        ),
        "wet_washout_source_loss_positive": wet_hto.wet_source_loss_bq_s > 0.0,
        "wet_source_loss_requires_explicit_local_flux": wet_fail_closed,
        "explicit_wet_local_flux_preserved_once": _close(
            wet_explicit.explicit_wet_surface_flux_bq_m2_s,
            WET_LOCAL_QUALIFICATION_FLUX_BQ_M2_S,
            abs_=1.0e-15,
        ),
        "atmospheric_ht_to_hto_disabled": (
            native_hto.atmospheric_ht_to_hto_generated_bq_s == 0.0
            and native_ht.atmospheric_ht_to_hto_generated_bq_s == 0.0
        ),
        "e2_ht_to_hto_activity_closes": (
            composition1.ht_adaptation is not None
            and abs(composition1.ht_adaptation.soil_conversion.ledger.activity_residual_bq_m2) <= 1.0e-10
        ),
        "primary_plus_ht_derived_surface_flux_closes": _close(
            composition1.ledger.combined_hto_surface_flux_bq_m2_s,
            composition1.ledger.primary_hto_surface_flux_bq_m2_s
            + composition1.ledger.ht_derived_hto_surface_flux_bq_m2_s,
        ),
        "native_replay_deposition_reaches_soil_l1": _close(
            first.applied_soil_forcing.surface_deposition_flux_bq_m2_s,
            composition1.ledger.combined_hto_surface_flux_bq_m2_s,
        ),
        "soil_transport_active": (
            first.applied_soil_forcing.l1_l2_hto_flux_bq_m2_s != 0.0
            and first.applied_soil_forcing.l2_l3_hto_flux_bq_m2_s != 0.0
        ),
        "root_transfer_active": first.balance.root_hto_transfer_bq_m2 > 0.0,
        "manual_eq7_25_resistance_used_by_replay": (
            template1.leaf_exchange_provenance.source_id == "H5_UFOTRI_EQ7_25_RESISTANCE"
            and template1.resistance == _manual_leaf_resistance().chain
        ),
        "manual_eq27_30_crosscheck_finite": (
            math.isfinite(manual_leaf.leaf_transfer_bq_m2)
            and manual_leaf.exchange_rate_constant_s_1 > 0.0
        ),
        "replay_leaf_not_claimed_equal_to_eq27_30": True,
        "first_plant_balance_closes": abs(first.balance.plant_residual_bq_m2) <= 1.0e-8,
        "first_coupled_balance_closes": abs(first.balance.coupled_residual_bq_m2) <= 1.0e-8,
        "first_soil_balance_closes": abs(first.soil_result.global_balance.hto_residual_bq_m2) <= 1.0e-8,
        "deterministic_repeat": first_repeat == first,
        "restart_equivalence": restarted_second == second,
        "first_hour_secondary_is_lagged_zero": (
            before_sources[0].routed_activity_bq == 0.0
            and before_sources[1].routed_activity_bq == 0.0
        ),
        "reemission_handoff_activity_identity": _close(
            soil_source.routed_activity_bq,
            environmental_reemission_activity_bq,
            rel=1.0e-10,
            abs_=1.0e-8,
        ),
        "reemission_fully_routed_without_second_loss": (
            soil_source.fully_routed
            and soil_source.environmental_loss_activity_bq == soil_source.routed_activity_bq
        ),
        "secondary_feedback_changes_air_only_at_adapter": (
            composition2.ledger.secondary_hto_air_bq_m3 > 0.0
            and composition2.ledger.combined_hto_air_bq_m3
            > no_secondary2.ledger.combined_hto_air_bq_m3
            and _close(
                composition2.ledger.combined_hto_surface_flux_bq_m2_s,
                no_secondary2.ledger.combined_hto_surface_flux_bq_m2_s,
            )
        ),
        "surface_flux_partition_invariant": _close(
            composition1.ledger.combined_hto_surface_flux_bq_m2_s,
            half_composition.ledger.combined_hto_surface_flux_bq_m2_s,
        ),
        "surface_activity_partition_invariant": _close(
            full_integrated_surface_bq_m2,
            two_half_integrated_surface_bq_m2,
            rel=1.0e-12,
            abs_=1.0e-8,
        ),
        "reemission_hour_partition_invariant": (
            _close(soil_source.routed_activity_bq, half_soil_source.routed_activity_bq, abs_=1.0e-8)
            and _close(soil_source.flux_bq_m2_s, half_soil_source.flux_bq_m2_s, abs_=1.0e-15)
        ),
        "vegetable_conservation_closes": abs(float(food_dose["vegetable_conservation_residual_bq_m2"])) <= 1.0e-8,
        "animal_conservation_closes": abs(float(food_dose["animal_conservation_residual_bq_m2"])) <= 1.0e-8,
        "slaughter_conservation_closes": abs(float(food_dose["slaughter_conservation_residual_bq_m2"])) <= 1.0e-8,
        "food_chain_outputs_positive": (
            float(food_dose["green_total_bq_kg"]) > 0.0
            and float(food_dose["milk_total_bq_kg"]) > 0.0
            and float(food_dose["beef_total_bq_kg"]) > 0.0
        ),
        "manual_exposure_partition_equivalent": bool(food_dose["manual_exposure_partition_equivalent"]),
        "inhalation_skin_ingestion_all_active": (
            float(food_dose["inhalation_dose_sv"]) > 0.0
            and float(food_dose["skin_dose_sv"]) > 0.0
            and float(food_dose["ingestion_dose_sv"]) > 0.0
        ),
        "manual_eq106_skin_fraction_exact": _close(
            float(food_dose["skin_dose_sv"]),
            0.5 * float(food_dose["inhalation_dose_sv"]),
            rel=1.0e-12,
            abs_=1.0e-20,
        ),
        "manual_eq106_eq107_close": (
            abs(float(food_dose["eq106_residual_sv"])) <= 1.0e-20
            and abs(float(food_dose["eq107_residual_sv"])) <= 1.0e-20
        ),
        "existing_manual_hydrology_gate_passes": (
            existing_gates["manual_hydrology"]["returncode"] == 0
            and existing_gates["manual_hydrology"]["pass_token_present"]
        ),
        "existing_f1_gate_passes": (
            existing_gates["reemission_area_source"]["returncode"] == 0
            and existing_gates["reemission_area_source"]["pass_token_present"]
        ),
        "canada_contract_requalified_source_limited": (
            existing_gates["canada_contract"]["returncode"] == 0
            and existing_gates["canada_contract"]["pass_token_present"]
        ),
        "iter_contract_requalified_without_full_replay_claim": (
            existing_gates["iter_contract"]["returncode"] == 0
            and existing_gates["iter_contract"]["pass_token_present"]
        ),
    }

    forbidden_claims = {
        "replay_leaf_operator_is_original_eq27_30_discretization": False,
        "original_monin_obukhov_estimator_recovered": False,
        "wet_source_loss_equals_local_wet_flux": False,
        "aggregate_reemission_is_ht_derived_without_origin_proof": False,
        "qualification_food_masses_are_production_defaults": False,
        "canada_full_numeric_empirical_replay_complete": False,
        "iter_full_atmospheric_numeric_replay_complete": False,
        "building_wake_complete": False,
        "plume_rise_complete": False,
        "cteas_atmos_binding": False,
        "production_parameter_activation": False,
        "calibration": False,
        "empirical_validation": False,
        "original_ufotri_executable_equivalence": False,
    }

    passed = all(invariants.values()) and not any(forbidden_claims.values())
    return {
        "schema_version": "v1",
        "stage": STAGE,
        "status": (
            "PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION"
            if passed
            else "FAIL_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION"
        ),
        "invariants": invariants,
        "native_atmosphere": {
            "hto_air_bq_m3": native_hto.air_concentration_bq_m3,
            "ht_air_bq_m3": native_ht.air_concentration_bq_m3,
            "primary_hto_surface_flux_bq_m2_s": composition1.ledger.primary_hto_surface_flux_bq_m2_s,
            "ht_derived_hto_surface_flux_bq_m2_s": composition1.ledger.ht_derived_hto_surface_flux_bq_m2_s,
            "combined_hto_surface_flux_bq_m2_s": composition1.ledger.combined_hto_surface_flux_bq_m2_s,
            "wet_probe_source_loss_bq_s": wet_hto.wet_source_loss_bq_s,
            "wet_probe_explicit_local_flux_bq_m2_s": wet_explicit.explicit_wet_surface_flux_bq_m2_s,
        },
        "replay_balances": {
            "first_plant_residual_bq_m2": first.balance.plant_residual_bq_m2,
            "first_coupled_residual_bq_m2": first.balance.coupled_residual_bq_m2,
            "first_soil_residual_bq_m2": first.soil_result.global_balance.hto_residual_bq_m2,
            "root_hto_transfer_bq_m2": first.balance.root_hto_transfer_bq_m2,
            "soil_reemission_loss_bq_m2": first.balance.soil_nonroot_external_hto_loss_bq_m2,
        },
        "secondary_feedback": {
            "routed_activity_bq": soil_source.routed_activity_bq,
            "environmental_loss_activity_bq": environmental_reemission_activity_bq,
            "secondary_air_bq_m3": secondary.secondary_air_bq_m3,
            "origin": soil_source.origin,
            "ht_derived_label_claimed": False,
        },
        "manual_leaf_crosscheck": {
            "eq7_25_resistance_total_s_m": template1.resistance.total_resistance,
            "eq27_30_leaf_transfer_bq_m2": manual_leaf.leaf_transfer_bq_m2,
            "eq27_30_exchange_rate_s_1": manual_leaf.exchange_rate_constant_s_1,
            "replay_operator_numerically_equated_to_eq27_30": False,
            "monin_obukhov_source": GOLDER_ESTIMATOR_ID,
            "original_monin_obukhov_logic_claimed": False,
        },
        "food_and_dose": food_dose,
        "existing_gate_reexecution": existing_gates,
        "benchmark_boundaries": {
            "canada_contract_requalified": True,
            "canada_full_numeric_replay": False,
            "canada_empirical_validation": False,
            "iter_contract_requalified": True,
            "iter_full_atmospheric_numeric_replay": False,
            "iter_empirical_validation": False,
        },
        "forbidden_claims": forbidden_claims,
        "next_stage_after_clean_closure": "UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2",
    }


def main() -> int:
    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"H5_NATIVE_ATMOSPHERE_TO_DOSE_STATUS={result['status']}")
    print(f"H5_NATIVE_ATMOSPHERE_TO_DOSE_RESULT_JSON={encoded}")
    return 0 if str(result["status"]).startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
