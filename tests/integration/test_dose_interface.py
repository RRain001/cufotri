from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cteas_ufotri.exposure.dose_v3 import (
    DOSE_COEFFICIENT_UNIT,
    DoseParameters,
    DoseSolver,
)
from cteas_ufotri.exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    ConsumptionParameters,
    FoodIntakeSolver,
)
from cteas_ufotri.plant.food_v3 import FoodTransferSolver, HarvestParameters
from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    LeafExchangeFlux,
)
from cteas_ufotri.plant.obt_v3 import (
    OBTParameters,
    OBTState,
    OBTSolver,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.root_v3 import RootUptakeForcing, RootUptakeSolver
from cteas_ufotri.plant.soil_v3 import SoilProvenance, SoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState


PROVENANCE = ForcingProvenance(
    source_id="p6-6b-dose-integration",
    source_version="1",
    artifact_sha256="e" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p6-6b-soil-integration",
    source_version="1",
    artifact_sha256="f" * 64,
    spatial_reference="test-grid",
    temporal_resolution_s=10.0,
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_soil_root_tfwt_obt_food_intake_dose_toy_pathway_closes() -> None:
    soil = SoilState.from_inventory(
        soil_identifier="soil-to-dose-001",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=40.0,
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )
    root_flux = RootUptakeSolver(k_root_m_s=5.0e-4).advance(
        soil,
        RootUptakeForcing(
            plant_identifier="plant-to-dose-001",
            root_zone_identifier="root-zone-001",
            interval_seconds=10.0,
            provenance=PROVENANCE,
        ),
    )
    tfwt_after_root = TFWTState.from_inventory(
        plant_identifier="plant-to-dose-001",
        crop="test-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=0.0,
        water_content_kg_m2=1.0,
        time=START,
        provenance=PROVENANCE,
    ).advance(
        10.0,
        LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=0.0),
        root_uptake_flux=root_flux,
    )
    obt_initial = OBTState.from_inventory(
        plant_identifier="plant-to-dose-001",
        crop="test-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=0.0,
        plant_mass_kg_m2=1.0,
        timestamp=tfwt_after_root.time,
        provenance=PROVENANCE,
    )
    obt_step = OBTSolver(
        parameters=OBTParameters(kf_s=0.1, kr_s=0.0)
    ).advance(
        tfwt_after_root,
        obt_initial,
        1.0,
        PlantBiologicalForcing(is_daylight=True),
    )
    tfwt_at_harvest = TFWTState.from_inventory(
        plant_identifier="plant-to-dose-001",
        crop="test-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=(
            tfwt_after_root.inventory()
            - obt_step.balance.tfwt_loss_bq_m2
        ),
        water_content_kg_m2=1.0,
        time=obt_step.state.timestamp,
        provenance=PROVENANCE,
    )
    food_step = FoodTransferSolver().advance(
        obt_step.state,
        tfwt_at_harvest,
        HarvestParameters(
            plant_identifier="plant-to-dose-001",
            crop_identifier="test-crop",
            growth_stage="harvest",
            food_product_identifier="food-product-001",
            harvest_fraction=1.0,
            harvest_area_m2=1.0,
            tfwt_harvest_fraction=0.0,
            provenance=PROVENANCE,
        ),
    )
    intake = FoodIntakeSolver(
        consumer_identifier="consumer-001"
    ).advance(
        food_step.food_inventory,
        ConsumptionParameters(
            food_product_identifier="food-product-001",
            age_group_identifier="adult",
            annual_consumption_amount=1.0,
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=PROVENANCE,
            food_product_mass_kg=1.0,
        ),
    )
    dose = DoseSolver().advance(
        intake,
        DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=0.2,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=PROVENANCE,
        ),
    )

    assert root_flux.inventory() == pytest.approx(10.0)
    assert tfwt_after_root.inventory() == pytest.approx(10.0)
    assert obt_step.state.inventory() == pytest.approx(1.0)
    assert food_step.food_inventory.inventory() == pytest.approx(1.0)
    assert food_step.balance.residual_bq == pytest.approx(0.0)
    assert intake.inventory() == pytest.approx(1.0)
    assert dose.inventory() == pytest.approx(intake.inventory())
    assert dose.dose() == pytest.approx(0.2)
    assert dose.dose() == pytest.approx(
        dose.inventory() * dose.dose_coefficient
    )

    remaining_soil = soil.inventory() - root_flux.inventory()
    remaining_tfwt = tfwt_at_harvest.inventory()
    assert soil.inventory() == pytest.approx(
        remaining_soil
        + remaining_tfwt
        + food_step.food_inventory.inventory()
    )
