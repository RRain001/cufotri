from __future__ import annotations

from datetime import datetime, timezone
import hashlib

import pytest

from cteas_ufotri.coupling.atmos_v3 import (
    AtmosphericForcingMetadata,
    AtmosphericHTOForcing,
)
from cteas_ufotri.exposure.dose_v3 import DOSE_COEFFICIENT_UNIT, DoseParameters
from cteas_ufotri.exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    ConsumptionParameters,
)
from cteas_ufotri.plant.food_v3 import HarvestParameters
from cteas_ufotri.plant.leaf_exchange_resistance import (
    ForcingProvenance,
    ResistanceChain,
)
from cteas_ufotri.plant.obt_v3 import OBTParameters, OBTState, PlantBiologicalForcing
from cteas_ufotri.plant.root_v3 import RootParameters
from cteas_ufotri.plant.soil_v3 import SoilParameters, SoilProvenance, SoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v3_pipeline import V3PipelineParameters, V3PipelineRunner


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
DT = 10.0


def _sha256(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


ATMOS_PROVENANCE = ForcingProvenance(
    source_id="p7-remediation-composite-atmos",
    source_version="1",
    artifact_sha256=_sha256("p7-remediation-composite-atmos-v1"),
    spatial_reference="synthetic-composite-grid",
    temporal_resolution_s=DT,
)
SOIL_PROVENANCE = SoilProvenance(
    source_id="p7-remediation-composite-soil",
    source_version="1",
    artifact_sha256=_sha256("p7-remediation-composite-soil-v1"),
    spatial_reference="synthetic-composite-grid",
    temporal_resolution_s=DT,
)


def _forcing(timestamp: datetime) -> AtmosphericHTOForcing:
    return AtmosphericHTOForcing(
        timestamp=timestamp,
        location="synthetic-composite-site",
        air_hto_concentration=60.0,
        deposition_flux=1.0,
        temperature=293.15,
        humidity=0.5,
        wind_speed=1.0,
        precipitation=0.0,
        source="synthetic-composite-atmosphere",
        provenance=ATMOS_PROVENANCE,
        metadata=AtmosphericForcingMetadata(
            model_name="synthetic-composite-atmosphere",
            version="1",
            grid_definition="synthetic-composite-grid",
            time_resolution=DT,
            source_dataset="repository-controlled-composite-fixture",
            creation_time=START,
            quality_flag="test-only",
        ),
    )


def _soil() -> SoilState:
    return SoilState.from_inventory(
        soil_identifier="synthetic-composite-soil",
        layer_id="surface",
        layer_depth_m=0.05,
        soil_water_content=0.02,
        soil_water_inventory_bq_m2=40.0,
        timestamp=START,
        provenance=SOIL_PROVENANCE,
    )


def _tfwt() -> TFWTState:
    return TFWTState.from_inventory(
        plant_identifier="synthetic-composite-plant",
        crop="synthetic-composite-crop",
        growth_stage="vegetative",
        tfwt_inventory_bq_m2=0.0,
        water_content_kg_m2=1.0,
        time=START,
        provenance=ATMOS_PROVENANCE,
    )


def _obt() -> OBTState:
    return OBTState.from_inventory(
        plant_identifier="synthetic-composite-plant",
        crop="synthetic-composite-crop",
        growth_stage="vegetative",
        obt_inventory_bq_m2=0.0,
        plant_mass_kg_m2=1.0,
        timestamp=START,
        provenance=ATMOS_PROVENANCE,
    )


def _runner() -> V3PipelineRunner:
    parameters = V3PipelineParameters(
        interval_seconds=DT,
        equilibrium_air_concentration_bq_m3=0.0,
        resistance=ResistanceChain.from_components(10.0, 20.0, 30.0),
        soil_parameters=SoilParameters(tritium_half_life_s=1.0e10),
        root_parameters=RootParameters(k_root_m_s=5.0e-4),
        obt_parameters=OBTParameters(kf_s=0.01, kr_s=0.005),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        root_zone_identifier="synthetic-composite-root-zone",
        harvest_parameters=HarvestParameters(
            plant_identifier="synthetic-composite-plant",
            crop_identifier="synthetic-composite-crop",
            growth_stage="harvest",
            food_product_identifier="synthetic-composite-food",
            harvest_fraction=0.25,
            harvest_area_m2=1.0,
            tfwt_harvest_fraction=0.0,
            provenance=ATMOS_PROVENANCE,
        ),
        consumption_parameters=ConsumptionParameters(
            food_product_identifier="synthetic-composite-food",
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
            dose_coefficient=1.0e-10,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=ATMOS_PROVENANCE,
        ),
        consumer_identifier="synthetic-composite-consumer",
    )
    return V3PipelineRunner(parameters=parameters)


def _physical_storage(soil: SoilState, tfwt: TFWTState, obt: OBTState) -> float:
    """Physical activity-bearing storage used by this baseline closure.

    Food, intake and dose are endpoint readouts in V3 and are therefore not
    additional activity stores in this composite balance.
    """

    return soil.inventory() + tfwt.inventory() + obt.inventory()


def _external_net_from_ledger(state) -> float:
    """Return one-step external activity input minus explicit physical losses.

    Root uptake and TFWT-to-OBT formation are internal transfers and must cancel
    from the top-level balance rather than being counted as sources or sinks.
    """

    ledger = state.ledger
    assert ledger is not None
    soil = ledger.soil_balance
    tfwt = ledger.tfwt_balance
    obt = ledger.obt_balance
    return (
        soil.deposition_input_bq_m2
        + soil.transport_input_bq_m2
        - soil.transport_loss_bq_m2
        + tfwt.leaf_exchange_input_bq_m2
        - soil.decay_loss_bq_m2
        - tfwt.water_loss_bq_m2
        - tfwt.transformation_bq_m2
        - obt.other_loss_bq_m2
    )


def test_composite_activity_closes_each_step_and_cumulatively() -> None:
    runner = _runner()
    initial_soil = _soil()
    initial_tfwt = _tfwt()
    initial_obt = _obt()
    initial_total = _physical_storage(initial_soil, initial_tfwt, initial_obt)

    previous_total = initial_total
    cumulative_external_net = 0.0
    state = None
    exercised_root_transfer = False
    exercised_obt_transfer = False

    for _ in range(4):
        if state is None:
            state = runner.run(
                _forcing(START),
                soil_state=initial_soil,
                tfwt_state=initial_tfwt,
                obt_state=initial_obt,
            )
        else:
            state = runner.advance(state, _forcing(state.timestamp))

        assert state.ledger is not None
        current_total = _physical_storage(
            state.soil_state,
            state.tfwt_state,
            state.obt_state,
        )
        external_net = _external_net_from_ledger(state)
        step_residual = external_net - (current_total - previous_total)
        assert step_residual == pytest.approx(0.0, abs=1.0e-9)

        cumulative_external_net += external_net
        cumulative_residual = cumulative_external_net - (current_total - initial_total)
        assert cumulative_residual == pytest.approx(0.0, abs=1.0e-9)

        exercised_root_transfer |= state.ledger.root_balance.root_transfer_bq_m2 > 0.0
        exercised_obt_transfer |= state.ledger.obt_balance.tfwt_loss_bq_m2 > 0.0
        previous_total = current_total

    assert exercised_root_transfer
    assert exercised_obt_transfer


def test_endpoint_readouts_are_not_double_counted_as_physical_storage() -> None:
    state = _runner().run(
        _forcing(START),
        soil_state=_soil(),
        tfwt_state=_tfwt(),
        obt_state=_obt(),
    )
    assert state.food_state.inventory() > 0.0
    assert state.intake_state.inventory() > 0.0
    assert state.dose_state.dose() > 0.0

    initial_total = _physical_storage(_soil(), _tfwt(), _obt())
    final_total = _physical_storage(state.soil_state, state.tfwt_state, state.obt_state)
    residual = _external_net_from_ledger(state) - (final_total - initial_total)
    assert residual == pytest.approx(0.0, abs=1.0e-9)


def test_current_integrated_soil_adapter_has_zero_signed_transport() -> None:
    """Freeze a capability boundary, not a physical claim.

    The standalone soil solver accepts signed transport, but the current
    atmospheric adapter used by V3PipelineRunner supplies deposition only.
    """

    soil_forcing = _forcing(START).to_soil_forcing()
    assert soil_forcing.deposition_flux_bq_m2_s == pytest.approx(1.0)
    assert soil_forcing.transport_flux_bq_m2_s == pytest.approx(0.0)
