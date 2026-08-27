#!/usr/bin/env python3
"""Visible synthetic machine check for the V4 terminal endpoint adapter R1."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from cteas_ufotri.exposure.dose_v3 import DOSE_COEFFICIENT_UNIT, DoseParameters
from cteas_ufotri.exposure.intake_v3 import (
    CONSUMPTION_RATE_UNIT,
    ConsumptionParameters,
)
from cteas_ufotri.plant.food_v3 import HarvestParameters
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
    V4FoodIntakeDoseEndpointAdapter,
    V4SoilRootTFWTOBTState,
    V4TerminalHarvestRequest,
)


UTC = timezone.utc
END = datetime(2026, 1, 2, tzinfo=UTC)
PRODUCT = "synthetic-machine-soy-food"
PLANT = "synthetic-machine-soybean"
CROP = "Glycine_max"
STAGE = "maturity"


def forcing_provenance(source_id: str, digest: str) -> ForcingProvenance:
    return ForcingProvenance(
        source_id=source_id,
        source_version="machine-r1",
        artifact_sha256=digest * 64,
        spatial_reference="synthetic-endpoint-support",
        temporal_resolution_s=3600.0,
    )


def make_endpoint() -> V4SoilRootTFWTOBTState:
    tfwt_provenance = forcing_provenance("SYNTHETIC_TFWT_ENDPOINT", "a")
    obt_provenance = forcing_provenance("SYNTHETIC_OBT_ENDPOINT", "b")
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-machine-soil",
        water_inventories_m=(0.10, 0.15, 0.20),
        hto_inventories_bq_m2=(1.0, 2.0, 3.0),
        timestamp=END,
        provenance=SoilV4Provenance(
            source_id="SYNTHETIC_SOIL_ENDPOINT",
            source_version="machine-r1",
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
        provenance=tfwt_provenance,
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier=PLANT,
        crop=CROP,
        growth_stage=STAGE,
        obt_inventory_bq_m2=10.0,
        plant_mass_kg_m2=2.0,
        timestamp=END,
        provenance=obt_provenance,
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(
        soil_state=soil,
        tfwt_state=tfwt,
        obt_state=obt,
    )


def make_basis(source_id: str) -> MassBasisContract:
    return MassBasisContract(
        subject_id=PRODUCT,
        mass_basis=MassBasis.FRESH_MASS,
        tissue_scope=TissueScope(
            kind=TissueScopeKind.HARVEST_PRODUCT,
            identifier=PRODUCT,
        ),
        area_basis=AreaBasis(kind=AreaBasisKind.NOT_APPLICABLE),
        provenance=BasisProvenance(
            source_id=source_id,
            source_locator="scripts/v4/run_food_intake_dose_endpoint_adapter_r1.py",
            revision="machine-r1",
        ),
    )


def make_request(mode: TerminalHarvestMode) -> V4TerminalHarvestRequest:
    tfwt_fraction = None if mode is TerminalHarvestMode.OBT_ONLY else 0.25
    return V4TerminalHarvestRequest(
        harvest_mode=mode,
        harvest_parameters=HarvestParameters(
            plant_identifier=PLANT,
            crop_identifier=CROP,
            growth_stage=STAGE,
            food_product_identifier=PRODUCT,
            harvest_fraction=0.5,
            harvest_area_m2=2.0,
            tfwt_harvest_fraction=tfwt_fraction,
            provenance=forcing_provenance("SYNTHETIC_HARVEST", "c"),
        ),
        food_product_basis=make_basis("SYNTHETIC_FOOD_BASIS"),
        consumption_basis=make_basis("SYNTHETIC_CONSUMPTION_BASIS"),
        consumption_parameters=ConsumptionParameters(
            food_product_identifier=PRODUCT,
            age_group_identifier="adult",
            annual_consumption_amount=20.0,
            consumption_unit=CONSUMPTION_RATE_UNIT,
            provenance=forcing_provenance("SYNTHETIC_CONSUMPTION", "d"),
            food_product_mass_kg=5.0,
        ),
        dose_parameters=DoseParameters(
            age_group_identifier="adult",
            radionuclide_identifier="H-3",
            pathway_identifier="food-ingestion",
            dose_coefficient=2.0e-11,
            dose_coefficient_unit=DOSE_COEFFICIENT_UNIT,
            provenance=forcing_provenance("SYNTHETIC_DOSE", "e"),
        ),
        consumer_identifier="synthetic-machine-consumer",
    )


def run() -> dict[str, object]:
    endpoint = make_endpoint()
    endpoint_before = endpoint.to_json()
    adapter = V4FoodIntakeDoseEndpointAdapter()

    mixed_request = make_request(TerminalHarvestMode.OBT_PLUS_TFWT)
    mixed = adapter.advance(endpoint, mixed_request)
    mixed_repeat = adapter.advance(endpoint, mixed_request)
    obt_only = adapter.advance(endpoint, make_request(TerminalHarvestMode.OBT_ONLY))

    invariants = {
        "endpoint_unchanged": endpoint.to_json() == endpoint_before,
        "deterministic_repeat": mixed_repeat == mixed,
        "mixed_obt_bq": mixed.food_inventory.obt_inventory_bq == 10.0,
        "mixed_tfwt_bq": mixed.food_inventory.tfwt_inventory_bq == 15.0,
        "mixed_total_food_bq": mixed.food_inventory.inventory() == 25.0,
        "mixed_annual_intake_bq": mixed.intake_state.inventory() == 100.0,
        "mixed_dose_sv": math.isclose(
            mixed.dose_state.dose(),
            2.0e-9,
            rel_tol=1.0e-12,
            abs_tol=0.0,
        ),
        "obt_only_tfwt_exact_zero": obt_only.food_inventory.tfwt_inventory_bq == 0.0,
        "food_balance_closed": mixed.food_transfer_result.balance.residual_bq == 0.0,
        "endpoint_timestamp_preserved": (
            mixed.food_inventory.timestamp
            == mixed.intake_state.timestamp
            == mixed.dose_state.timestamp
            == endpoint.timestamp
        ),
        "h3_food_ingestion_identity": (
            mixed.audit.radionuclide_identifier == "H-3"
            and mixed.audit.pathway_identifier == "food-ingestion"
        ),
        "independent_provenance_retained": (
            mixed.audit.replay_tfwt_provenance.source_id == "SYNTHETIC_TFWT_ENDPOINT"
            and mixed.audit.replay_obt_provenance.source_id == "SYNTHETIC_OBT_ENDPOINT"
            and mixed.audit.harvest_provenance.source_id == "SYNTHETIC_HARVEST"
            and mixed.audit.food_product_basis_provenance.source_id == "SYNTHETIC_FOOD_BASIS"
            and mixed.audit.consumption_basis_provenance.source_id == "SYNTHETIC_CONSUMPTION_BASIS"
            and mixed.audit.consumption_provenance.source_id == "SYNTHETIC_CONSUMPTION"
            and mixed.audit.dose_provenance.source_id == "SYNTHETIC_DOSE"
        ),
        "not_environmental_mass_sink": (
            mixed.audit.downstream_branch_is_environmental_mass_sink is False
        ),
        "no_basis_conversion": mixed.audit.numerical_basis_conversion_performed is False,
        "no_area_conversion": mixed.audit.numerical_area_conversion_performed is False,
    }

    status = (
        "PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION"
        if all(invariants.values())
        else "FAIL_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION"
    )
    return {
        "schema_version": "v1",
        "stage": "V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_IMPLEMENTATION_R1",
        "status": status,
        "source_kind": "SYNTHETIC_TEST_ONLY",
        "empirical_validation": False,
        "physical_accuracy_claim": False,
        "real_cteas_atmos_binding": False,
        "active_parameters": 0,
        "calibration": False,
        "v3_default_changed": False,
        "leaf_r5": False,
        "obt_redesign": False,
        "full_hydrology": False,
        "state_mutating_harvest": False,
        "numerical_mass_basis_conversion": False,
        "numerical_area_conversion": False,
        "invariants": invariants,
        "mixed_output": {
            "food_total_bq": mixed.food_inventory.inventory(),
            "food_obt_bq": mixed.food_inventory.obt_inventory_bq,
            "food_tfwt_bq": mixed.food_inventory.tfwt_inventory_bq,
            "annual_intake_bq": mixed.intake_state.inventory(),
            "committed_dose_sv": mixed.dose_state.dose(),
        },
        "obt_only_output": {
            "food_total_bq": obt_only.food_inventory.inventory(),
            "food_obt_bq": obt_only.food_inventory.obt_inventory_bq,
            "food_tfwt_bq": obt_only.food_inventory.tfwt_inventory_bq,
            "annual_intake_bq": obt_only.intake_state.inventory(),
            "committed_dose_sv": obt_only.dose_state.dose(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = run()
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)

    if not str(result["status"]).startswith("PASS_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
