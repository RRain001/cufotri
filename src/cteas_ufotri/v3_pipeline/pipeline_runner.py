"""V3 P7.5 orchestration over the existing typed subsystem APIs."""

from __future__ import annotations

from dataclasses import dataclass

from ..coupling.atmos_v3 import AtmosphericHTOForcing
from ..exposure.dose_v3 import DoseParameters, DoseSolver
from ..exposure.intake_v3 import ConsumptionParameters, FoodIntakeSolver
from ..plant.food_v3 import FoodTransferSolver, HarvestParameters
from ..plant.leaf_exchange_resistance import ResistanceState
from ..plant.obt_v3 import (
    OBTParameters,
    OBTState,
    OBTSolver,
    PlantBiologicalForcing,
)
from ..plant.root_v3 import (
    RootParameters,
    RootUptakeForcing,
    RootUptakeSolver,
)
from ..plant.soil_v3 import (
    SoilParameters,
    SoilState,
    SoilStorageSolver,
)
from ..plant.tfwt_v3 import TFWTState, TFWTStorageSolver
from ..plant.v3 import V3PlantPathway
from .pipeline_state import V3PipelineLedger, V3SimulationState
from .validation import (
    PipelineInputError,
    PipelineStateError,
    validate_forcing,
    validate_initial_state,
    validate_parameters,
    validate_restart_timestamp,
)


@dataclass(frozen=True)
class V3PipelineParameters:
    """All non-state inputs required for one controlled pipeline step."""

    interval_seconds: float
    equilibrium_air_concentration_bq_m3: float
    resistance: ResistanceState
    soil_parameters: SoilParameters
    root_parameters: RootParameters
    obt_parameters: OBTParameters
    biological_forcing: PlantBiologicalForcing
    root_zone_identifier: str
    harvest_parameters: HarvestParameters
    consumption_parameters: ConsumptionParameters
    dose_parameters: DoseParameters
    consumer_identifier: str

    def __post_init__(self) -> None:
        validate_parameters(self)


V3PipelineConfig = V3PipelineParameters


@dataclass(frozen=True)
class V3PipelineRunner:
    """Stateless orchestration facade; every call returns a new state."""

    parameters: V3PipelineParameters

    def __post_init__(self) -> None:
        validate_parameters(self.parameters)

    def run(
        self,
        atmospheric_forcing: AtmosphericHTOForcing,
        initial_state: V3SimulationState | None = None,
        *,
        soil_state: SoilState | None = None,
        tfwt_state: TFWTState | None = None,
        obt_state: OBTState | None = None,
    ) -> V3SimulationState:
        """Run one explicit interval and return a complete new state.

        Either a complete previous ``V3SimulationState`` or the three
        initial public states must be supplied. No state is retained on the
        runner, and the runner never constructs hidden defaults.
        """

        validate_forcing(atmospheric_forcing)
        if initial_state is not None:
            if any(value is not None for value in (soil_state, tfwt_state, obt_state)):
                raise PipelineInputError(
                    "initial_state cannot be combined with component states"
                )
            validate_restart_timestamp(
                atmospheric_forcing,
                initial_state.timestamp,
            )
            soil_state = initial_state.soil_state
            tfwt_state = initial_state.tfwt_state
            obt_state = initial_state.obt_state
        else:
            if soil_state is None or tfwt_state is None or obt_state is None:
                raise PipelineInputError(
                    "soil_state, tfwt_state, and obt_state are required"
                )
            validate_initial_state(
                atmospheric_forcing,
                soil_state,
                tfwt_state,
                obt_state,
            )

        if self.parameters.harvest_parameters.plant_identifier != tfwt_state.plant_identifier:
            raise PipelineInputError(
                "harvest plant identifier must match TFWT plant identifier"
            )
        if self.parameters.harvest_parameters.crop_identifier != tfwt_state.crop:
            raise PipelineInputError(
                "harvest crop identifier must match TFWT crop"
            )

        interval = self.parameters.interval_seconds
        soil_result = SoilStorageSolver(
            parameters=self.parameters.soil_parameters
        ).advance(
            soil_state,
            atmospheric_forcing.to_soil_forcing(),
            interval,
        )

        leaf_flux = V3PlantPathway(
            resistance=self.parameters.resistance
        ).leaf_flux(
            atmospheric_forcing.to_leaf_forcing(),
            self.parameters.equilibrium_air_concentration_bq_m3,
        )

        tfwt_result = TFWTStorageSolver().advance(
            tfwt_state,
            leaf_flux,
            interval,
        )
        obt_result = OBTSolver(
            parameters=self.parameters.obt_parameters
        ).advance(
            tfwt_result.state,
            obt_state,
            interval,
            self.parameters.biological_forcing,
        )

        root_result = RootUptakeSolver(
            parameters=self.parameters.root_parameters
        ).advance_result(
            soil_state,
            RootUptakeForcing(
                plant_identifier=tfwt_state.plant_identifier,
                root_zone_identifier=self.parameters.root_zone_identifier,
                interval_seconds=interval,
                provenance=atmospheric_forcing.provenance,
            ),
        )
        root_transfer = root_result.root_flux.inventory()
        soil_after_deposition = soil_result.state
        remaining_soil = soil_after_deposition.inventory() - root_transfer
        if remaining_soil < 0.0:
            raise PipelineStateError(
                "root transfer exceeds the post-deposition soil inventory"
            )
        soil_after_root = soil_after_deposition.with_inventory(
            soil_water_inventory_bq_m2=remaining_soil,
            timestamp=root_result.root_flux.timestamp,
        )

        tfwt_after_obt_inventory = (
            tfwt_result.state.inventory()
            - obt_result.balance.tfwt_loss_bq_m2
        )
        if tfwt_after_obt_inventory < 0.0:
            raise PipelineStateError(
                "OBT transfer exceeds the available TFWT inventory"
            )
        tfwt_after_obt = tfwt_result.state.with_inventory(
            tfwt_inventory_bq_m2=tfwt_after_obt_inventory,
            time=obt_result.state.timestamp,
        )
        tfwt_after_root = tfwt_after_obt.with_inventory(
            tfwt_inventory_bq_m2=(
                tfwt_after_obt.inventory() + root_transfer
            ),
            time=root_result.root_flux.timestamp,
        )
        food_result = FoodTransferSolver(
            parameters=self.parameters.harvest_parameters
        ).advance(
            obt_result.state,
            tfwt_after_root,
        )
        intake_state = FoodIntakeSolver(
            consumer_identifier=self.parameters.consumer_identifier
        ).advance(
            food_result.food_inventory,
            self.parameters.consumption_parameters,
        )
        dose_state = DoseSolver().advance(
            intake_state,
            self.parameters.dose_parameters,
        )

        return V3SimulationState(
            timestamp=dose_state.timestamp,
            atmospheric_state=atmospheric_forcing,
            soil_state=soil_after_root,
            tfwt_state=tfwt_after_root,
            obt_state=obt_result.state,
            root_state=root_result.root_flux,
            harvest_state=food_result.harvest_state,
            food_state=food_result.food_inventory,
            intake_state=intake_state,
            dose_state=dose_state,
            provenance=atmospheric_forcing.provenance,
            ledger=V3PipelineLedger(
                soil_balance=soil_result.balance,
                root_balance=root_result.balance,
                tfwt_balance=tfwt_result.balance,
                obt_balance=obt_result.balance,
                food_balance=food_result.balance,
            ),
        )

    def advance(
        self,
        state: V3SimulationState,
        atmospheric_forcing: AtmosphericHTOForcing,
    ) -> V3SimulationState:
        """Restart one step from a previously serialized public state."""

        if not isinstance(state, V3SimulationState):
            raise PipelineInputError("state must be a V3SimulationState")
        return self.run(atmospheric_forcing, initial_state=state)

    def step(
        self,
        atmospheric_forcing: AtmosphericHTOForcing,
        initial_state: V3SimulationState | None = None,
        *,
        soil_state: SoilState | None = None,
        tfwt_state: TFWTState | None = None,
        obt_state: OBTState | None = None,
    ) -> V3SimulationState:
        """Alias for :meth:`run` with the same explicit input contract."""

        return self.run(
            atmospheric_forcing,
            initial_state,
            soil_state=soil_state,
            tfwt_state=tfwt_state,
            obt_state=obt_state,
        )


__all__ = [
    "V3PipelineConfig",
    "V3PipelineParameters",
    "V3PipelineRunner",
]
