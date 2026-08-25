from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cteas_ufotri.coupling.atmos_v3 import (
    AtmosphericForcingMetadata,
    AtmosphericHTOForcing,
)
from cteas_ufotri.exposure.dose_v3 import (
    DOSE_COEFFICIENT_UNIT,
    DoseParameters,
)
from cteas_ufotri.exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    ConsumptionParameters,
)
from cteas_ufotri.plant.food_v3 import HarvestParameters
from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    ResistanceChain,
)
from cteas_ufotri.plant.obt_v3 import (
    OBTParameters,
    OBTState,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.root_v3 import RootParameters
from cteas_ufotri.plant.soil_v3 import SoilParameters, SoilProvenance, SoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v3_pipeline import (
    PipelineInputError,
    PipelineSerializationError,
    V3PipelineParameters,
    V3PipelineRunner,
    V3SimulationState,
)


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
ATMOS_PROVENANCE = ForcingProvenance(
    source_id="p7-5-pipeline-atmos",
    source_version="1",
    artifact_sha256="a" * 64,
    spatial_reference="pipeline-grid",
    temporal_resolution_s=10.0,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p7-5-pipeline-soil",
    source_version="1",
    artifact_sha256="b" * 64,
    spatial_reference="pipeline-grid",
    temporal_resolution_s=10.0,
)


def make_forcing(
    *,
    timestamp: datetime = START,
    air_hto: float = 60.0,
    deposition: float = 1.0,
) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location="pipeline-site",
        air_hto_concentration=air_hto,
        deposition_flux=deposition,
        temperature=293.15,
        humidity=0.5,
        wind_speed=1.0,
        precipitation=0.0,
        source="p7-5-synthetic-atmosphere",
        provenance=ATMOS_PROVENANCE,
        metadata=AtmosphericForcingMetadata(
            model_name="synthetic-atmosphere",
            version="1",
            grid_definition="pipeline-grid",
            time_resolution=10.0,
            source_dataset="synthetic-pipeline-fixture",
            creation_time=START,
            quality_flag="unreviewed",
        ),
    )


def make_soil(inventory: float = 40.0, timestamp: datetime = START) -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="pipeline-soil",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=inventory,
        timestamp=timestamp,
        provenance=SOIL_PROVENANCE,
    )


def make_tfwt(inventory: float = 0.0, timestamp: datetime = START) -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="pipeline-plant",
        crop="pipeline-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=inventory,
        water_content_kg_m2=1.0,
        time=timestamp,
        provenance=ATMOS_PROVENANCE,
    )


def make_obt(inventory: float = 0.0, timestamp: datetime = START) -> OBTState:
    return OBTState.from_inventory(
        plant_identifier="pipeline-plant",
        crop="pipeline-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=inventory,
        plant_mass_kg_m2=1.0,
        timestamp=timestamp,
        provenance=ATMOS_PROVENANCE,
    )


def make_parameters() -> V3PipelineParameters:
    return V3PipelineParameters(
        interval_seconds=10.0,
        equilibrium_air_concentration_bq_m3=0.0,
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0),
        soil_parameters=SoilParameters(tritium_half_life_s=1.0e10),
        root_parameters=RootParameters(k_root_m_s=5.0e-4),
        obt_parameters=OBTParameters(kf_s=0.01, kr_s=0.0),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        root_zone_identifier="pipeline-root-zone",
        harvest_parameters=HarvestParameters(
            plant_identifier="pipeline-plant",
            crop_identifier="pipeline-crop",
            growth_stage="harvest",
            food_product_identifier="pipeline-food",
            harvest_fraction=1.0,
            harvest_area_m2=1.0,
            tfwt_harvest_fraction=0.0,
            provenance=ATMOS_PROVENANCE,
        ),
        consumption_parameters=ConsumptionParameters(
            food_product_identifier="pipeline-food",
            age_group_identifier="adult",
            annual_consumption_amount=1.0,
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=ATMOS_PROVENANCE,
            food_product_mass_kg=1.0,
        ),
        dose_parameters=DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=0.2,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=ATMOS_PROVENANCE,
        ),
        consumer_identifier="pipeline-consumer",
    )


def make_runner() -> V3PipelineRunner:
    return V3PipelineRunner(parameters=make_parameters())


def test_minimal_synthetic_pathway_produces_all_states_and_ledgers() -> None:
    state = make_runner().run(
        make_forcing(),
        soil_state=make_soil(),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )

    assert isinstance(state, V3SimulationState)
    assert state.timestamp == START + timedelta(seconds=10.0)
    assert state.root_state.inventory() == pytest.approx(10.0)
    assert state.soil_state.inventory() == pytest.approx(40.0)
    assert state.tfwt_state.inventory() == pytest.approx(19.0)
    assert state.obt_state.inventory() == pytest.approx(1.0)
    assert state.food_state.inventory() == pytest.approx(1.0)
    assert state.intake_state.inventory() == pytest.approx(1.0)
    assert state.dose_state.dose() == pytest.approx(0.2)
    assert state.ledger is not None
    assert state.ledger.soil_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.root_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.tfwt_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.obt_balance.residual_bq_m2 == pytest.approx(0.0)
    assert state.ledger.food_balance.residual_bq == pytest.approx(0.0)
    assert state.tfwt_state.inventory() == pytest.approx(
        state.ledger.tfwt_balance.leaf_exchange_input_bq_m2
        + state.root_state.inventory()
        - state.ledger.obt_balance.tfwt_loss_bq_m2
    )


def test_zero_atmospheric_forcing_does_not_generate_inventory() -> None:
    state = make_runner().run(
        make_forcing(air_hto=0.0, deposition=0.0),
        soil_state=make_soil(inventory=0.0),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )

    assert state.soil_state.inventory() == pytest.approx(0.0)
    assert state.root_state.inventory() == pytest.approx(0.0)
    assert state.tfwt_state.inventory() == pytest.approx(0.0)
    assert state.obt_state.inventory() == pytest.approx(0.0)
    assert state.food_state.inventory() == pytest.approx(0.0)
    assert state.intake_state.inventory() == pytest.approx(0.0)
    assert state.dose_state.dose() == pytest.approx(0.0)


def test_state_serialization_roundtrip_and_restart_continue() -> None:
    runner = make_runner()
    first = runner.run(
        make_forcing(),
        soil_state=make_soil(),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )
    restored = V3SimulationState.from_json(first.to_json())

    assert restored == first
    second = runner.advance(
        restored,
        make_forcing(timestamp=first.timestamp),
    )
    assert second.timestamp == START + timedelta(seconds=20.0)
    assert second.soil_state.timestamp == second.timestamp
    assert second.dose_state.dose() > first.dose_state.dose()


def test_invalid_forcing_and_restart_timestamp_fail_closed() -> None:
    runner = make_runner()
    missing_metadata = AtmosphericHTOForcing(
        timestamp=START,
        location="pipeline-site",
        air_hto_concentration=0.0,
        deposition_flux=0.0,
        temperature=293.15,
        humidity=0.5,
        wind_speed=1.0,
        precipitation=0.0,
        source="missing-metadata",
        provenance=ATMOS_PROVENANCE,
    )
    with pytest.raises(PipelineInputError):
        runner.run(
            missing_metadata,
            soil_state=make_soil(inventory=0.0),
            tfwt_state=make_tfwt(),
            obt_state=make_obt(),
        )

    first = runner.run(
        make_forcing(),
        soil_state=make_soil(),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )
    with pytest.raises(PipelineInputError):
        runner.advance(first, make_forcing(timestamp=START))


def test_tampered_serialized_state_fails_closed() -> None:
    runner = make_runner()
    state = runner.run(
        make_forcing(),
        soil_state=make_soil(),
        tfwt_state=make_tfwt(),
        obt_state=make_obt(),
    )
    payload = state.to_mapping()
    del payload["dose_state"]

    with pytest.raises(PipelineSerializationError):
        V3SimulationState.from_mapping(payload)
