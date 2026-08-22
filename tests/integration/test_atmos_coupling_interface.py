from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.coupling.atmos_v3 import (
    AtmosphericForcingMetadata,
    AtmosphericHTOForcing,
)
from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    ResistanceChain,
)
from cteas_ufotri.plant.soil_v3 import (
    SoilParameters,
    SoilProvenance,
    SoilState,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.plant.v3 import V3PlantPathway, V3PlantState


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
ATMOS_PROVENANCE = ForcingProvenance(
    source_id="p7-integration-atmosphere",
    source_version="1",
    artifact_sha256="b" * 64,
    spatial_reference="toy-grid",
    temporal_resolution_s=10.0,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p7-integration-soil",
    source_version="1",
    artifact_sha256="c" * 64,
    spatial_reference="toy-grid",
    temporal_resolution_s=10.0,
)


def make_forcing() -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=START,
        location="toy-site",
        air_hto_concentration=60.0,
        deposition_flux=1.0,
        temperature=293.15,
        humidity=0.5,
        wind_speed=1.0,
        precipitation=0.0,
        source="p7-toy-atmosphere",
        provenance=ATMOS_PROVENANCE,
        metadata=AtmosphericForcingMetadata(
            model_name="toy-atmosphere",
            version="1",
            grid_definition="toy-grid",
            time_resolution=10.0,
            source_dataset="toy-forcing",
            creation_time=START,
            quality_flag="unreviewed",
        ),
    )


def make_plant_state() -> V3PlantState:
    return V3PlantState(
        tfwt=TFWTState.from_inventory(
            plant_identifier="p7-plant",
            crop="toy-crop",
            growth_stage="vegetative",
            tfwt_inventory_bq_m2=0.0,
            water_content_kg_m2=1.0,
            time=START,
            provenance=ATMOS_PROVENANCE,
        )
    )


def make_soil_state() -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="p7-soil",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=0.0,
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )


def test_atmospheric_forcing_reaches_leaf_and_public_tfwt_path() -> None:
    forcing = make_forcing()
    pathway = V3PlantPathway(
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0)
    )

    step = pathway.advance(
        make_plant_state(),
        forcing.to_leaf_forcing(),
        equilibrium_air_concentration_bq_m3=0.0,
        interval_seconds=10.0,
    )

    assert step.leaf_exchange_flux.air_to_leaf_flux_bq_m2_s == pytest.approx(1.0)
    assert step.state.inventory() == pytest.approx(10.0)


def test_atmospheric_deposition_reaches_public_soil_path() -> None:
    next_state = make_soil_state().advance(
        10.0,
        make_forcing().to_soil_forcing(),
        parameters=SoilParameters(tritium_half_life_s=1000.0),
    )

    assert next_state.inventory() > 0.0
    assert next_state.timestamp == datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
