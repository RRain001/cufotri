from __future__ import annotations

from dataclasses import replace
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
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.mass_basis_v3_1 import (
    AreaBasis,
    AreaBasisKind,
    BasisProvenance,
    MassBasis,
    MassBasisContract,
    TissueScope,
    TissueScopeKind,
)
from cteas_ufotri.plant.obt_v3 import OBTState
from cteas_ufotri.plant.soil_v4 import SoilV4Provenance, ThreeLayerSoilState
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    TerminalHarvestMode,
    V4EndpointAdapterError,
    V4FoodIntakeDoseEndpointAdapter,
    V4SoilRootTFWTOBTState,
    V4TerminalHarvestRequest,
)


UTC = timezone.utc
END = datetime(2026, 1, 2, tzinfo=UTC)
PRODUCT = "synthetic-soy-food"
PLANT = "synthetic-soybean"
CROP = "Glycine_max"
STAGE = "maturity"
AGE = "adult"
CONSUMER = "synthetic-consumer"


def forcing_provenance(source_id: str, digest: str) -> ForcingProvenance:
    return ForcingProvenance(
        source_id=source_id,
        source_version="implementation-r1",
        artifact_sha256=digest * 64,
        spatial_reference="synthetic-endpoint-support",
        temporal_resolution_s=3600.0,
    )


TFWT_PROVENANCE = forcing_provenance("SYNTHETIC_TFWT_ENDPOINT", "a")
OBT_PROVENANCE = forcing_provenance("SYNTHETIC_OBT_ENDPOINT", "b")
HARVEST_PROVENANCE = forcing_provenance("SYNTHETIC_HARVEST", "c")
CONSUMPTION_PROVENANCE = forcing_provenance("SYNTHETIC_CONSUMPTION", "d")
DOSE_PROVENANCE = forcing_provenance("SYNTHETIC_DOSE", "e")
FOOD_BASIS_PROVENANCE = BasisProvenance(
    source_id="SYNTHETIC_FOOD_BASIS",
    source_locator="tests/v4/test_v4_system_food_intake_dose_adapter_implementation_r1.py",
    revision="implementation-r1",
)
CONSUMPTION_BASIS_PROVENANCE = BasisProvenance(
    source_id="SYNTHETIC_CONSUMPTION_BASIS",
    source_locator="tests/v4/test_v4_system_food_intake_dose_adapter_implementation_r1.py",
    revision="implementation-r1",
)


def make_endpoint() -> V4SoilRootTFWTOBTState:
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-endpoint-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(1.0, 2.0, 3.0),
        timestamp=END,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_SOIL_ENDPOINT",
            source_version="implementation-r1",
            artifact_sha256="f" * 64,
            spatial_reference="synthetic-endpoint-support",
            temporal_resolution_s=3600.0,
        ),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier=PLANT,
        crop=CROP,
        growth_stage=STAGE,
        tfwt_inventory_bq_m2=30.0,
        water_content_kg_m2=5.0,
        time=END,
        provenance=TFWT_PROVENANCE,
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier=PLANT,
        crop=CROP,
        growth_stage=STAGE,
        obt_inventory_bq_m2=10.0,
        plant_mass_kg_m2=2.0,
        timestamp=END,
        provenance=OBT_PROVENANCE,
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(
        soil_state=soil,
        tfwt_state=tfwt,
        obt_state=obt,
    )


def make_basis(
    *,
    mass_basis: MassBasis = MassBasis.FRESH_MASS,
    provenance: BasisProvenance = FOOD_BASIS_PROVENANCE,
    subject_id: str = PRODUCT,
    tissue_identifier: str = PRODUCT,
    area_kind: AreaBasisKind = AreaBasisKind.NOT_APPLICABLE,
) -> MassBasisContract:
    return MassBasisContract(
        subject_id=subject_id,
        mass_basis=mass_basis,
        tissue_scope=TissueScope(
            kind=TissueScopeKind.HARVEST_PRODUCT,
            identifier=tissue_identifier,
        ),
        area_basis=AreaBasis(kind=area_kind),
        provenance=provenance,
    )


def make_harvest(
    *,
    tfwt_fraction: float | None,
    plant_identifier: str = PLANT,
    crop_identifier: str = CROP,
    growth_stage: str = STAGE,
    product_identifier: str = PRODUCT,
) -> HarvestParameters:
    return HarvestParameters(
        plant_identifier=plant_identifier,
        crop_identifier=crop_identifier,
        growth_stage=growth_stage,
        food_product_identifier=product_identifier,
        harvest_fraction=0.5,
        harvest_area_m2=2.0,
        tfwt_harvest_fraction=tfwt_fraction,
        provenance=HARVEST_PROVENANCE,
    )


def make_consumption(
    *,
    product_identifier: str = PRODUCT,
    age_group: str = AGE,
) -> ConsumptionParameters:
    return ConsumptionParameters(
        food_product_identifier=product_identifier,
        age_group_identifier=age_group,
        annual_consumption_amount=20.0,
        consumption_unit=CONSUMPTION_RATE_UNIT,
        provenance=CONSUMPTION_PROVENANCE,
        food_product_mass_kg=5.0,
    )


def make_dose(
    *,
    age_group: str = AGE,
    radionuclide: str = "H-3",
    pathway: str = "food-ingestion",
) -> DoseParameters:
    return DoseParameters(
        age_group_identifier=age_group,
        radionuclide_identifier=radionuclide,
        pathway_identifier=pathway,
        dose_coefficient=2.0e-11,
        dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
        provenance=DOSE_PROVENANCE,
    )


def make_request(
    *,
    mode: TerminalHarvestMode = TerminalHarvestMode.OBT_PLUS_TFWT,
    tfwt_fraction: float | None = 0.25,
    harvest: HarvestParameters | None = None,
    food_basis: MassBasisContract | None = None,
    consumption_basis: MassBasisContract | None = None,
    consumption: ConsumptionParameters | None = None,
    dose: DoseParameters | None = None,
) -> V4TerminalHarvestRequest:
    return V4TerminalHarvestRequest(
        harvest_mode=mode,
        harvest_parameters=harvest or make_harvest(tfwt_fraction=tfwt_fraction),
        food_product_basis=food_basis or make_basis(),
        consumption_basis=consumption_basis
        or make_basis(provenance=CONSUMPTION_BASIS_PROVENANCE),
        consumption_parameters=consumption or make_consumption(),
        dose_parameters=dose or make_dose(),
        consumer_identifier=CONSUMER,
    )


def test_mixed_mode_exactly_composes_existing_v3_solver_chain() -> None:
    endpoint = make_endpoint()
    request = make_request()
    result = V4FoodIntakeDoseEndpointAdapter().advance(endpoint, request)

    direct_food = FoodTransferSolver(
        parameters=request.harvest_parameters
    ).advance(endpoint.obt_state, endpoint.tfwt_state)
    direct_intake = FoodIntakeSolver(
        consumer_identifier=CONSUMER
    ).advance(direct_food.food_inventory, request.consumption_parameters)
    direct_dose = DoseSolver().advance(direct_intake, request.dose_parameters)

    assert result.food_transfer_result == direct_food
    assert result.intake_state == direct_intake
    assert result.dose_state == direct_dose

    assert result.food_inventory.obt_inventory_bq == pytest.approx(10.0)
    assert result.food_inventory.tfwt_inventory_bq == pytest.approx(15.0)
    assert result.food_inventory.inventory() == pytest.approx(25.0)
    assert result.intake_state.inventory() == pytest.approx(100.0)
    assert result.dose_state.dose() == pytest.approx(2.0e-9)
    assert result.food_transfer_result.balance.residual_bq == pytest.approx(0.0)


def test_obt_only_requires_none_and_produces_exactly_zero_tfwt_food() -> None:
    endpoint = make_endpoint()
    request = make_request(
        mode=TerminalHarvestMode.OBT_ONLY,
        tfwt_fraction=None,
    )
    result = V4FoodIntakeDoseEndpointAdapter().advance(endpoint, request)

    assert result.food_inventory.obt_inventory_bq == pytest.approx(10.0)
    assert result.food_inventory.tfwt_inventory_bq == 0.0
    assert result.food_inventory.inventory() == pytest.approx(10.0)
    assert result.intake_state.inventory() == pytest.approx(40.0)
    assert result.dose_state.dose() == pytest.approx(8.0e-10)

    with pytest.raises(V4EndpointAdapterError, match="OBT_ONLY"):
        make_request(
            mode=TerminalHarvestMode.OBT_ONLY,
            tfwt_fraction=0.25,
        )

    with pytest.raises(V4EndpointAdapterError, match="OBT_PLUS_TFWT"):
        make_request(
            mode=TerminalHarvestMode.OBT_PLUS_TFWT,
            tfwt_fraction=None,
        )


def test_terminal_readout_preserves_endpoint_and_all_domain_provenance() -> None:
    endpoint = make_endpoint()
    before = endpoint.to_json()
    request = make_request()

    first = V4FoodIntakeDoseEndpointAdapter().advance(endpoint, request)
    second = V4FoodIntakeDoseEndpointAdapter().advance(endpoint, request)

    assert endpoint.to_json() == before
    assert first == second
    assert first.harvest_state.timestamp == endpoint.timestamp
    assert first.food_inventory.timestamp == endpoint.timestamp
    assert first.intake_state.timestamp == endpoint.timestamp
    assert first.dose_state.timestamp == endpoint.timestamp

    audit = first.audit
    assert audit.source_state_mutated is False
    assert audit.downstream_branch_is_environmental_mass_sink is False
    assert audit.numerical_basis_conversion_performed is False
    assert audit.numerical_area_conversion_performed is False
    assert audit.replay_tfwt_provenance == TFWT_PROVENANCE
    assert audit.replay_obt_provenance == OBT_PROVENANCE
    assert audit.harvest_provenance == HARVEST_PROVENANCE
    assert audit.food_product_basis_provenance == FOOD_BASIS_PROVENANCE
    assert (
        audit.consumption_basis_provenance
        == CONSUMPTION_BASIS_PROVENANCE
    )
    assert audit.consumption_provenance == CONSUMPTION_PROVENANCE
    assert audit.dose_provenance == DOSE_PROVENANCE
    assert len(audit.endpoint_sha256) == 64


@pytest.mark.parametrize(
    ("harvest", "message"),
    [
        (make_harvest(tfwt_fraction=0.25, plant_identifier="other"), "plant_identifier"),
        (make_harvest(tfwt_fraction=0.25, crop_identifier="other"), "crop_identifier"),
        (make_harvest(tfwt_fraction=0.25, growth_stage="other"), "growth_stage"),
    ],
)
def test_endpoint_identity_mismatch_fails_closed(
    harvest: HarvestParameters,
    message: str,
) -> None:
    with pytest.raises(V4EndpointAdapterError, match=message):
        V4FoodIntakeDoseEndpointAdapter().advance(
            make_endpoint(),
            make_request(harvest=harvest),
        )


def test_product_age_radionuclide_and_pathway_mismatches_fail_closed() -> None:
    endpoint = make_endpoint()

    with pytest.raises(V4EndpointAdapterError, match="food_product_identifier"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(
                consumption=make_consumption(product_identifier="other-food")
            ),
        )

    with pytest.raises(V4EndpointAdapterError, match="age_group_identifier"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(dose=make_dose(age_group="child")),
        )

    with pytest.raises(V4EndpointAdapterError, match="H-3"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(dose=make_dose(radionuclide="C-14")),
        )

    with pytest.raises(V4EndpointAdapterError, match="food-ingestion"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(dose=make_dose(pathway="inhalation")),
        )


def test_mass_tissue_area_and_subject_basis_mismatches_fail_closed() -> None:
    endpoint = make_endpoint()

    with pytest.raises(V4EndpointAdapterError, match="basis mismatch"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(
                consumption_basis=make_basis(
                    mass_basis=MassBasis.DRY_MASS,
                    provenance=CONSUMPTION_BASIS_PROVENANCE,
                )
            ),
        )

    with pytest.raises(V4EndpointAdapterError, match="subject_id"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(
                food_basis=make_basis(subject_id="other-food")
            ),
        )

    with pytest.raises(V4EndpointAdapterError, match="tissue_scope.identifier"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(
                food_basis=make_basis(tissue_identifier="whole-plant")
            ),
        )

    with pytest.raises(V4EndpointAdapterError, match="NOT_APPLICABLE"):
        V4FoodIntakeDoseEndpointAdapter().advance(
            endpoint,
            make_request(
                food_basis=make_basis(area_kind=AreaBasisKind.GROUND_AREA)
            ),
        )

    with pytest.raises(V4EndpointAdapterError, match="area_basis"):
        replace(make_request(), harvest_area_basis="leaf_area")


def test_adapter_remains_an_opt_in_v4_boundary() -> None:
    import cteas_ufotri.v3_pipeline.pipeline_runner as v3_runner

    assert not hasattr(v3_runner, "V4FoodIntakeDoseEndpointAdapter")
