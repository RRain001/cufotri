"""Opt-in V4 terminal food -> intake -> dose diagnostic adapter.

The adapter is intentionally one-way. It reads a completed V4 replay endpoint,
performs explicit system-level identity and basis checks, and composes the
existing V3 FoodTransferSolver -> FoodIntakeSolver -> DoseSolver APIs.

It does not mutate replay state, insert harvest into the environmental mass
ledger, perform mass/area conversion, activate parameters, or change any
upstream solver equation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any

from cteas_ufotri.exposure.dose_v3 import DoseParameters, DoseSolver, DoseState
from cteas_ufotri.exposure.intake_v3 import (
    ConsumptionParameters,
    FoodIntakeSolver,
    IntakeState,
)
from cteas_ufotri.plant.food_v3 import (
    FoodTransferResult,
    FoodTransferSolver,
    HarvestParameters,
)
from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.mass_basis_v3_1 import (
    AreaBasisKind,
    BasisCompatibilityError,
    BasisProvenance,
    MassBasisContract,
    TissueScopeKind,
    require_direct_comparison,
)

from .soil_root_tfwt_obt import V4SoilRootTFWTOBTState


class V4EndpointAdapterError(ValueError):
    """Fail-closed error at the V4 terminal diagnostic boundary."""


class TerminalHarvestMode(str, Enum):
    """Explicitly selected terminal diagnostic harvest composition."""

    OBT_ONLY = "OBT_ONLY"
    OBT_PLUS_TFWT = "OBT_PLUS_TFWT"


@dataclass(frozen=True)
class V4TerminalHarvestRequest:
    """All explicit downstream inputs for one terminal diagnostic readout."""

    harvest_mode: TerminalHarvestMode
    harvest_parameters: HarvestParameters
    food_product_basis: MassBasisContract
    consumption_basis: MassBasisContract
    consumption_parameters: ConsumptionParameters
    dose_parameters: DoseParameters
    consumer_identifier: str
    harvest_area_basis: str = "soil_surface_area"

    def __post_init__(self) -> None:
        if not isinstance(self.harvest_mode, TerminalHarvestMode):
            raise V4EndpointAdapterError(
                "harvest_mode must be TerminalHarvestMode.OBT_ONLY or "
                "TerminalHarvestMode.OBT_PLUS_TFWT"
            )
        if not isinstance(self.harvest_parameters, HarvestParameters):
            raise V4EndpointAdapterError(
                "harvest_parameters must be HarvestParameters"
            )
        if not isinstance(self.food_product_basis, MassBasisContract):
            raise V4EndpointAdapterError(
                "food_product_basis must be MassBasisContract"
            )
        if not isinstance(self.consumption_basis, MassBasisContract):
            raise V4EndpointAdapterError(
                "consumption_basis must be MassBasisContract"
            )
        if not isinstance(self.consumption_parameters, ConsumptionParameters):
            raise V4EndpointAdapterError(
                "consumption_parameters must be ConsumptionParameters"
            )
        if not isinstance(self.dose_parameters, DoseParameters):
            raise V4EndpointAdapterError("dose_parameters must be DoseParameters")
        if not isinstance(self.consumer_identifier, str) or not self.consumer_identifier.strip():
            raise V4EndpointAdapterError("consumer_identifier is required")
        if self.harvest_area_basis != "soil_surface_area":
            raise V4EndpointAdapterError(
                "harvest_area_basis must be 'soil_surface_area'; "
                "no area conversion is implemented"
            )

        tfwt_fraction = self.harvest_parameters.tfwt_harvest_fraction
        if self.harvest_mode is TerminalHarvestMode.OBT_ONLY:
            if tfwt_fraction is not None:
                raise V4EndpointAdapterError(
                    "OBT_ONLY requires tfwt_harvest_fraction=None"
                )
        elif tfwt_fraction is None:
            raise V4EndpointAdapterError(
                "OBT_PLUS_TFWT requires an explicit tfwt_harvest_fraction"
            )


@dataclass(frozen=True)
class V4FoodIntakeDoseAudit:
    """Composite audit record preserving independently owned provenance."""

    endpoint_sha256: str
    endpoint_area_basis: str
    harvest_mode: TerminalHarvestMode
    plant_identifier: str
    crop_identifier: str
    growth_stage: str
    food_product_identifier: str
    age_group_identifier: str
    radionuclide_identifier: str
    pathway_identifier: str
    replay_tfwt_provenance: ForcingProvenance
    replay_obt_provenance: ForcingProvenance
    harvest_provenance: ForcingProvenance
    food_product_basis_provenance: BasisProvenance
    consumption_basis_provenance: BasisProvenance
    consumption_provenance: ForcingProvenance
    dose_provenance: Any
    source_state_mutated: bool = False
    downstream_branch_is_environmental_mass_sink: bool = False
    numerical_basis_conversion_performed: bool = False
    numerical_area_conversion_performed: bool = False
    version: str = "v4-food-intake-dose-endpoint-adapter-r1"


@dataclass(frozen=True)
class V4FoodIntakeDoseEndpointResult:
    """Terminal diagnostic food/intake/dose outputs and composite audit."""

    food_transfer_result: FoodTransferResult
    intake_state: IntakeState
    dose_state: DoseState
    audit: V4FoodIntakeDoseAudit

    @property
    def food_inventory(self):
        return self.food_transfer_result.food_inventory

    @property
    def harvest_state(self):
        return self.food_transfer_result.harvest_state


def _validate_basis_contract(
    contract: MassBasisContract,
    *,
    product_identifier: str,
    field: str,
) -> None:
    if contract.subject_id != product_identifier:
        raise V4EndpointAdapterError(
            f"{field}.subject_id must equal the food product identifier"
        )
    if contract.tissue_scope.kind is not TissueScopeKind.HARVEST_PRODUCT:
        raise V4EndpointAdapterError(
            f"{field}.tissue_scope.kind must be HARVEST_PRODUCT"
        )
    if contract.tissue_scope.identifier != product_identifier:
        raise V4EndpointAdapterError(
            f"{field}.tissue_scope.identifier must equal the food product identifier"
        )
    if contract.area_basis.kind is not AreaBasisKind.NOT_APPLICABLE:
        raise V4EndpointAdapterError(
            f"{field}.area_basis.kind must be NOT_APPLICABLE"
        )


def _validate_request_against_endpoint(
    endpoint: V4SoilRootTFWTOBTState,
    request: V4TerminalHarvestRequest,
) -> None:
    if endpoint.area_basis != "soil_surface_area":
        raise V4EndpointAdapterError(
            "endpoint area_basis must be 'soil_surface_area'; "
            "no area conversion is implemented"
        )

    harvest = request.harvest_parameters
    if harvest.plant_identifier != endpoint.tfwt_state.plant_identifier:
        raise V4EndpointAdapterError(
            "harvest plant_identifier must exactly match the replay endpoint"
        )
    if harvest.crop_identifier != endpoint.tfwt_state.crop:
        raise V4EndpointAdapterError(
            "harvest crop_identifier must exactly match the replay endpoint"
        )
    if harvest.growth_stage != endpoint.tfwt_state.growth_stage:
        raise V4EndpointAdapterError(
            "harvest growth_stage must exactly match the replay endpoint"
        )

    product = harvest.food_product_identifier
    if request.consumption_parameters.food_product_identifier != product:
        raise V4EndpointAdapterError(
            "consumption food_product_identifier must exactly match harvest"
        )

    _validate_basis_contract(
        request.food_product_basis,
        product_identifier=product,
        field="food_product_basis",
    )
    _validate_basis_contract(
        request.consumption_basis,
        product_identifier=product,
        field="consumption_basis",
    )
    try:
        require_direct_comparison(
            request.food_product_basis,
            request.consumption_basis,
        )
    except BasisCompatibilityError as exc:
        raise V4EndpointAdapterError(
            f"food-product and consumption basis mismatch: {exc}"
        ) from exc

    if (
        request.consumption_parameters.age_group_identifier
        != request.dose_parameters.age_group_identifier
    ):
        raise V4EndpointAdapterError(
            "consumption and dose age_group_identifier values must match"
        )
    if request.dose_parameters.radionuclide_identifier != "H-3":
        raise V4EndpointAdapterError(
            "dose radionuclide_identifier must be exactly 'H-3'"
        )
    if request.dose_parameters.pathway_identifier != "food-ingestion":
        raise V4EndpointAdapterError(
            "dose pathway_identifier must be exactly 'food-ingestion'"
        )


def _require_food_balance_closed(result: FoodTransferResult) -> None:
    scale = max(
        1.0,
        abs(result.balance.obt_source_bq),
        abs(result.balance.tfwt_source_bq),
        abs(result.balance.harvest_transfer_bq),
    )
    tolerance = 1.0e-12 * scale
    if abs(result.balance.residual_bq) > tolerance:
        raise V4EndpointAdapterError(
            "food-transfer internal balance failed closure"
        )


class V4FoodIntakeDoseEndpointAdapter:
    """Compose existing V3 endpoint solvers without altering replay dynamics."""

    def advance(
        self,
        endpoint: V4SoilRootTFWTOBTState,
        request: V4TerminalHarvestRequest,
    ) -> V4FoodIntakeDoseEndpointResult:
        if not isinstance(endpoint, V4SoilRootTFWTOBTState):
            raise V4EndpointAdapterError(
                "endpoint must be V4SoilRootTFWTOBTState"
            )
        if not isinstance(request, V4TerminalHarvestRequest):
            raise V4EndpointAdapterError(
                "request must be V4TerminalHarvestRequest"
            )

        _validate_request_against_endpoint(endpoint, request)

        endpoint_before = endpoint.to_json()
        endpoint_sha256 = hashlib.sha256(
            endpoint_before.encode("utf-8")
        ).hexdigest()

        food_result = FoodTransferSolver(
            parameters=request.harvest_parameters
        ).advance(
            endpoint.obt_state,
            endpoint.tfwt_state,
        )
        _require_food_balance_closed(food_result)

        if food_result.harvest_state.timestamp != endpoint.timestamp:
            raise V4EndpointAdapterError(
                "harvest timestamp must equal replay endpoint timestamp"
            )
        if food_result.food_inventory.timestamp != endpoint.timestamp:
            raise V4EndpointAdapterError(
                "food timestamp must equal replay endpoint timestamp"
            )
        if (
            request.harvest_mode is TerminalHarvestMode.OBT_ONLY
            and food_result.food_inventory.tfwt_inventory_bq != 0.0
        ):
            raise V4EndpointAdapterError(
                "OBT_ONLY must produce exactly zero food TFWT inventory"
            )

        intake_state = FoodIntakeSolver(
            consumer_identifier=request.consumer_identifier
        ).advance(
            food_result.food_inventory,
            request.consumption_parameters,
        )
        if intake_state.timestamp != endpoint.timestamp:
            raise V4EndpointAdapterError(
                "intake timestamp must preserve replay endpoint timestamp"
            )

        dose_state = DoseSolver().advance(
            intake_state,
            request.dose_parameters,
        )
        if dose_state.timestamp != endpoint.timestamp:
            raise V4EndpointAdapterError(
                "dose timestamp must preserve replay endpoint timestamp"
            )
        if dose_state.pathway_identifier != "food-ingestion":
            raise V4EndpointAdapterError(
                "dose output pathway_identifier must remain 'food-ingestion'"
            )

        endpoint_after = endpoint.to_json()
        if endpoint_after != endpoint_before:
            raise V4EndpointAdapterError(
                "terminal diagnostic readout mutated the replay endpoint"
            )

        harvest = request.harvest_parameters
        audit = V4FoodIntakeDoseAudit(
            endpoint_sha256=endpoint_sha256,
            endpoint_area_basis=endpoint.area_basis,
            harvest_mode=request.harvest_mode,
            plant_identifier=endpoint.tfwt_state.plant_identifier,
            crop_identifier=endpoint.tfwt_state.crop,
            growth_stage=endpoint.tfwt_state.growth_stage,
            food_product_identifier=harvest.food_product_identifier,
            age_group_identifier=request.consumption_parameters.age_group_identifier,
            radionuclide_identifier=request.dose_parameters.radionuclide_identifier,
            pathway_identifier=request.dose_parameters.pathway_identifier,
            replay_tfwt_provenance=endpoint.tfwt_state.provenance,
            replay_obt_provenance=endpoint.obt_state.provenance,
            harvest_provenance=harvest.provenance,
            food_product_basis_provenance=request.food_product_basis.provenance,
            consumption_basis_provenance=request.consumption_basis.provenance,
            consumption_provenance=request.consumption_parameters.provenance,
            dose_provenance=request.dose_parameters.provenance,
        )
        return V4FoodIntakeDoseEndpointResult(
            food_transfer_result=food_result,
            intake_state=intake_state,
            dose_state=dose_state,
            audit=audit,
        )

    def step(
        self,
        endpoint: V4SoilRootTFWTOBTState,
        request: V4TerminalHarvestRequest,
    ) -> V4FoodIntakeDoseEndpointResult:
        """Alias for the explicit one-event terminal diagnostic readout."""

        return self.advance(endpoint, request)


__all__ = [
    "TerminalHarvestMode",
    "V4EndpointAdapterError",
    "V4FoodIntakeDoseAudit",
    "V4FoodIntakeDoseEndpointAdapter",
    "V4FoodIntakeDoseEndpointResult",
    "V4TerminalHarvestRequest",
]
