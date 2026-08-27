"""Opt-in V4 replay-input orchestration over frozen component solvers.

This module owns only system input validation, fail-closed mapping, and the
selected interval composition. It does not implement atmospheric dispersion,
hydrology, dynamic stomata, parameter activation, food/intake/dose, or real
CTEAS-Atmos binding.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
import math

from cteas_ufotri.coupling.atmos_v3 import AtmosphericHTOForcing
from cteas_ufotri.plant.leaf_exchange_resistance.resistance import (
    signed_leaf_exchange_flux,
)
from cteas_ufotri.plant.leaf_exchange_resistance.types import (
    LeafExchangeFlux,
    ResistanceState,
)
from cteas_ufotri.plant.obt_v3.obt_solver import (
    OBTSolver,
    OBTStepResult,
    PlantBiologicalForcing,
)
from cteas_ufotri.plant.root_v4.root_solver import (
    ThreeLayerRootFluxSolverV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.root_v4.root_state import ThreeLayerRootFluxPlanV4
from cteas_ufotri.plant.soil_v4.soil_solver import (
    ThreeLayerSoilForcing,
    ThreeLayerSoilStepResult,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3.tfwt_solver import (
    TFWTStepResult,
    TFWTStorageSolver,
)

from .soil_root_tfwt_obt import (
    SELECTED_OPERATOR_SPLIT,
    V4SoilRootTFWTOBTState,
)


ALLOWED_REPLAY_SOURCE_KINDS = frozenset(
    {"REPLAY", "SYNTHETIC_TEST", "EXPLICIT_EXTERNAL"}
)


class V4ReplayInputError(ValueError):
    """Fail-closed error for the replay-input orchestration boundary."""


def _require_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise V4ReplayInputError(f"{field} is required")
    return value


def _require_finite(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise V4ReplayInputError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise V4ReplayInputError(f"{field} must be finite")
    return result


def _require_utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise V4ReplayInputError(f"{field} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise V4ReplayInputError(f"{field} must use UTC")
    return value


def _require_sha256(value: object, *, field: str) -> str:
    text = _require_text(value, field=field)
    if len(text) != 64 or any(character not in "0123456789abcdefABCDEF" for character in text):
        raise V4ReplayInputError(f"{field} must be a SHA-256 hex digest")
    return text


def _require_same_resolution(actual: float, expected: float, *, field: str) -> None:
    tolerance = 1.0e-12 * max(1.0, abs(expected))
    if abs(actual - expected) > tolerance:
        raise V4ReplayInputError(
            f"{field} must equal the replay interval length; received {actual} vs {expected} s"
        )


def _require_closed(value: float, *, field: str, scale: float) -> None:
    tolerance = 1.0e-10 * max(1.0, abs(scale))
    if abs(value) > tolerance:
        raise V4ReplayInputError(f"{field} failed conservation closure: {value}")


@dataclass(frozen=True)
class ReplayDomainProvenance:
    """Per-domain provenance carried by the orchestration envelope."""

    source_id: str
    source_version: str
    artifact_sha256: str
    spatial_reference: str
    temporal_resolution_s: float
    source_kind: str

    def __post_init__(self) -> None:
        _require_text(self.source_id, field="source_id")
        _require_text(self.source_version, field="source_version")
        _require_sha256(self.artifact_sha256, field="artifact_sha256")
        _require_text(self.spatial_reference, field="spatial_reference")
        resolution = _require_finite(
            self.temporal_resolution_s,
            field="temporal_resolution_s",
        )
        if resolution <= 0.0:
            raise V4ReplayInputError("temporal_resolution_s must be positive")
        if self.source_kind not in ALLOWED_REPLAY_SOURCE_KINDS:
            raise V4ReplayInputError(
                "source_kind must be REPLAY, SYNTHETIC_TEST, or EXPLICIT_EXTERNAL"
            )


@dataclass(frozen=True)
class V4ReplayIntervalInput:
    """One fail-closed replay interval with explicitly separated ownership."""

    atmospheric_forcing: AtmosphericHTOForcing
    interval_end: datetime
    soil_external_forcing: ThreeLayerSoilForcing
    soil_external_provenance: ReplayDomainProvenance
    root_forcing: ThreeLayerRootWaterFluxForcingV4
    biological_forcing: PlantBiologicalForcing
    biological_provenance: ReplayDomainProvenance
    resistance: ResistanceState
    equilibrium_air_concentration_bq_m3: float
    leaf_exchange_provenance: ReplayDomainProvenance
    area_basis: str = "soil_surface_area"

    def __post_init__(self) -> None:
        if not isinstance(self.atmospheric_forcing, AtmosphericHTOForcing):
            raise V4ReplayInputError("atmospheric_forcing must be AtmosphericHTOForcing")
        if not isinstance(self.soil_external_forcing, ThreeLayerSoilForcing):
            raise V4ReplayInputError("soil_external_forcing must be ThreeLayerSoilForcing")
        if not isinstance(self.root_forcing, ThreeLayerRootWaterFluxForcingV4):
            raise V4ReplayInputError("root_forcing must be ThreeLayerRootWaterFluxForcingV4")
        if not isinstance(self.biological_forcing, PlantBiologicalForcing):
            raise V4ReplayInputError("biological_forcing must be PlantBiologicalForcing")
        if not isinstance(self.resistance, ResistanceState):
            raise V4ReplayInputError("resistance must be ResistanceState")
        for field, value in (
            ("soil_external_provenance", self.soil_external_provenance),
            ("biological_provenance", self.biological_provenance),
            ("leaf_exchange_provenance", self.leaf_exchange_provenance),
        ):
            if not isinstance(value, ReplayDomainProvenance):
                raise V4ReplayInputError(f"{field} must be ReplayDomainProvenance")

        start = _require_utc(self.atmospheric_forcing.timestamp, field="atmospheric_forcing.timestamp")
        end = _require_utc(self.interval_end, field="interval_end")
        if end <= start:
            raise V4ReplayInputError("interval_end must be after atmospheric_forcing.timestamp")
        interval = (end - start).total_seconds()

        if self.soil_external_forcing.timestamp != start:
            raise V4ReplayInputError("soil_external_forcing.timestamp must equal interval start")
        if self.root_forcing.timestamp != start:
            raise V4ReplayInputError("root_forcing.timestamp must equal interval start")
        _require_same_resolution(
            float(self.atmospheric_forcing.provenance.temporal_resolution_s),
            interval,
            field="atmospheric_forcing.provenance.temporal_resolution_s",
        )
        for field, provenance in (
            ("soil_external_provenance", self.soil_external_provenance),
            ("biological_provenance", self.biological_provenance),
            ("leaf_exchange_provenance", self.leaf_exchange_provenance),
        ):
            _require_same_resolution(
                provenance.temporal_resolution_s,
                interval,
                field=f"{field}.temporal_resolution_s",
            )

        common_spatial_reference = self.atmospheric_forcing.provenance.spatial_reference
        for field, provenance in (
            ("soil_external_provenance", self.soil_external_provenance),
            ("biological_provenance", self.biological_provenance),
            ("leaf_exchange_provenance", self.leaf_exchange_provenance),
        ):
            if provenance.spatial_reference != common_spatial_reference:
                raise V4ReplayInputError(
                    f"{field}.spatial_reference must match the atmospheric replay support; "
                    "explicit spatial reconciliation is not implemented in R1"
                )

        if self.area_basis != "soil_surface_area":
            raise V4ReplayInputError(
                "R1 requires area_basis='soil_surface_area'; no area conversion is implemented"
            )
        equilibrium = _require_finite(
            self.equilibrium_air_concentration_bq_m3,
            field="equilibrium_air_concentration_bq_m3",
        )
        if equilibrium < 0.0:
            raise V4ReplayInputError("equilibrium_air_concentration_bq_m3 must be non-negative")

        if self.soil_external_forcing.surface_deposition_flux_bq_m2_s != 0.0:
            raise V4ReplayInputError(
                "soil_external_forcing.surface_deposition_flux_bq_m2_s must be zero; "
                "the atmospheric/replay record exclusively owns surface deposition"
            )
        if any(value != 0.0 for value in self.soil_external_forcing.root_water_extraction_m_s):
            raise V4ReplayInputError(
                "soil_external_forcing.root_water_extraction_m_s must be zero; root_v4 owns the root plan"
            )
        if any(value != 0.0 for value in self.soil_external_forcing.root_hto_extraction_bq_m2_s):
            raise V4ReplayInputError(
                "soil_external_forcing.root_hto_extraction_bq_m2_s must be zero; root_v4 owns the root plan"
            )

    @property
    def interval_start(self) -> datetime:
        return self.atmospheric_forcing.timestamp

    @property
    def interval_seconds(self) -> float:
        return (self.interval_end - self.interval_start).total_seconds()

    @property
    def spatial_reference(self) -> str:
        return self.atmospheric_forcing.provenance.spatial_reference


@dataclass(frozen=True)
class V4ReplaySystemBalance:
    """Signed coupled HTO balance for one replay-driven interval."""

    leaf_exchange_transfer_bq_m2: float
    root_water_transfer_m: float
    root_hto_transfer_bq_m2: float
    soil_root_water_identity_residual_m: float
    soil_root_hto_identity_residual_bq_m2: float
    obt_tfwt_transfer_bq_m2: float
    obt_external_loss_bq_m2: float
    soil_external_hto_input_bq_m2: float
    soil_nonroot_external_hto_loss_bq_m2: float
    soil_decay_loss_bq_m2: float
    plant_storage_change_bq_m2: float
    plant_residual_bq_m2: float
    coupled_storage_change_bq_m2: float
    coupled_residual_bq_m2: float

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _require_finite(getattr(self, field), field=field)


@dataclass(frozen=True)
class V4ReplaySystemStepResult:
    state: V4SoilRootTFWTOBTState
    leaf_exchange_flux: LeafExchangeFlux
    tfwt_leaf_result: TFWTStepResult
    obt_result: OBTStepResult
    root_plan: ThreeLayerRootFluxPlanV4
    applied_soil_forcing: ThreeLayerSoilForcing
    soil_result: ThreeLayerSoilStepResult
    balance: V4ReplaySystemBalance
    selected_operator_split: str = SELECTED_OPERATOR_SPLIT


class V4ReplayInputSystemOrchestrator:
    """Compose frozen components for one opt-in replay interval."""

    def __init__(
        self,
        *,
        soil_solver: ThreeLayerSoilStorageSolver,
        obt_solver: OBTSolver,
        root_solver: ThreeLayerRootFluxSolverV4 | None = None,
        tfwt_solver: TFWTStorageSolver | None = None,
    ) -> None:
        if not isinstance(soil_solver, ThreeLayerSoilStorageSolver):
            raise V4ReplayInputError("explicit ThreeLayerSoilStorageSolver is required")
        if not isinstance(obt_solver, OBTSolver):
            raise V4ReplayInputError("explicit OBTSolver is required")
        if root_solver is not None and not isinstance(root_solver, ThreeLayerRootFluxSolverV4):
            raise V4ReplayInputError("root_solver must be ThreeLayerRootFluxSolverV4")
        if tfwt_solver is not None and not isinstance(tfwt_solver, TFWTStorageSolver):
            raise V4ReplayInputError("tfwt_solver must be TFWTStorageSolver")
        self.soil_solver = soil_solver
        self.obt_solver = obt_solver
        self.root_solver = ThreeLayerRootFluxSolverV4() if root_solver is None else root_solver
        self.tfwt_solver = TFWTStorageSolver() if tfwt_solver is None else tfwt_solver

    @staticmethod
    def _validate_state_alignment(
        state: V4SoilRootTFWTOBTState,
        replay_input: V4ReplayIntervalInput,
    ) -> None:
        if not isinstance(state, V4SoilRootTFWTOBTState):
            raise V4ReplayInputError("state must be V4SoilRootTFWTOBTState")
        if state.timestamp != replay_input.interval_start:
            raise V4ReplayInputError("composite state timestamp must equal replay interval start")
        if state.area_basis != replay_input.area_basis:
            raise V4ReplayInputError("composite state and replay input must share one area_basis")
        if replay_input.root_forcing.plant_identifier != state.plant_identifier:
            raise V4ReplayInputError("root_forcing.plant_identifier must match the composite plant")
        expected_spatial = replay_input.spatial_reference
        state_spatial = {
            state.soil_state.provenance.spatial_reference,
            state.tfwt_state.provenance.spatial_reference,
            state.obt_state.provenance.spatial_reference,
        }
        if state_spatial != {expected_spatial}:
            raise V4ReplayInputError(
                "soil/TFWT/OBT state spatial_reference must match the replay support; "
                "explicit spatial reconciliation is not implemented in R1"
            )

    def advance(
        self,
        state: V4SoilRootTFWTOBTState,
        replay_input: V4ReplayIntervalInput,
    ) -> V4ReplaySystemStepResult:
        if not isinstance(replay_input, V4ReplayIntervalInput):
            raise V4ReplayInputError("replay_input must be V4ReplayIntervalInput")
        self._validate_state_alignment(state, replay_input)
        interval = replay_input.interval_seconds

        leaf_exchange_flux = signed_leaf_exchange_flux(
            replay_input.atmospheric_forcing.to_leaf_forcing(),
            replay_input.resistance,
            replay_input.equilibrium_air_concentration_bq_m3,
        )
        tfwt_leaf_result = self.tfwt_solver.advance(
            state.tfwt_state,
            leaf_exchange_flux,
            interval,
        )

        # Preserve the selected split: OBT sees the same-interval leaf-updated
        # TFWT inventory, but it does not see the same-interval root gain.
        obt_result = self.obt_solver.advance(
            tfwt_leaf_result.state,
            state.obt_state,
            interval,
            replay_input.biological_forcing,
        )
        tfwt_after_obt = (
            tfwt_leaf_result.state.inventory()
            - obt_result.balance.tfwt_loss_bq_m2
        )
        if tfwt_after_obt < -1.0e-12:
            raise V4ReplayInputError(
                "OBT formation exceeds the leaf-updated TFWT inventory under the selected split"
            )
        tfwt_after_obt = max(tfwt_after_obt, 0.0)

        # Root still reads S_n, not the deposition-updated soil endpoint.
        root_plan = self.root_solver.plan(
            state.soil_state,
            replay_input.root_forcing,
            interval,
        )
        if root_plan.area_basis != state.area_basis:
            raise V4ReplayInputError("root plan and composite state must share one area_basis")

        # Atmos/replay owns the total surface-deposition rate. Root owns the
        # only root extraction plan. Other soil transport terms remain exactly
        # the explicit external forcing supplied by their own domain.
        applied_soil_forcing = replace(
            replay_input.soil_external_forcing,
            surface_deposition_flux_bq_m2_s=replay_input.atmospheric_forcing.deposition_flux,
            root_water_extraction_m_s=root_plan.water_uptake_fluxes_m_s,
            root_hto_extraction_bq_m2_s=root_plan.hto_uptake_fluxes_bq_m2_s,
        )
        soil_result = self.soil_solver.advance(
            state.soil_state,
            applied_soil_forcing,
            interval,
        )

        endpoint_tfwt_inventory = tfwt_after_obt + root_plan.total_hto_transfer_bq_m2
        endpoint_tfwt = tfwt_leaf_result.state.with_inventory(
            tfwt_inventory_bq_m2=endpoint_tfwt_inventory,
            time=replay_input.interval_end,
        )
        next_state = V4SoilRootTFWTOBTState(
            soil_state=soil_result.state,
            tfwt_state=endpoint_tfwt,
            obt_state=obt_result.state,
        )

        applied_root_water = sum(applied_soil_forcing.root_water_extraction_m_s) * interval
        applied_root_hto = sum(applied_soil_forcing.root_hto_extraction_bq_m2_s) * interval
        water_identity_residual = root_plan.total_water_transfer_m - applied_root_water
        hto_identity_residual = root_plan.total_hto_transfer_bq_m2 - applied_root_hto

        leaf_transfer = leaf_exchange_flux.air_to_leaf_flux_bq_m2_s * interval
        initial_plant = state.tfwt_state.inventory() + state.obt_state.inventory()
        final_plant = endpoint_tfwt.inventory() + obt_result.state.inventory()
        plant_change = final_plant - initial_plant
        plant_residual = (
            leaf_transfer
            + root_plan.total_hto_transfer_bq_m2
            - obt_result.balance.other_loss_bq_m2
            - plant_change
        )

        soil_global = soil_result.global_balance
        nonroot_soil_loss = (
            soil_global.external_hto_loss_bq_m2
            - root_plan.total_hto_transfer_bq_m2
        )
        loss_tolerance = 1.0e-10 * max(
            1.0,
            abs(soil_global.external_hto_loss_bq_m2),
            abs(root_plan.total_hto_transfer_bq_m2),
        )
        if nonroot_soil_loss < -loss_tolerance:
            raise V4ReplayInputError(
                "soil external HTO loss is smaller than the applied root transfer"
            )
        nonroot_soil_loss = max(nonroot_soil_loss, 0.0)

        initial_coupled = state.soil_state.total_hto_inventory_bq_m2 + initial_plant
        final_coupled = soil_result.state.total_hto_inventory_bq_m2 + final_plant
        coupled_change = final_coupled - initial_coupled
        coupled_residual = (
            soil_global.external_hto_input_bq_m2
            + leaf_transfer
            - nonroot_soil_loss
            - soil_global.decay_loss_bq_m2
            - obt_result.balance.other_loss_bq_m2
            - coupled_change
        )

        balance = V4ReplaySystemBalance(
            leaf_exchange_transfer_bq_m2=leaf_transfer,
            root_water_transfer_m=root_plan.total_water_transfer_m,
            root_hto_transfer_bq_m2=root_plan.total_hto_transfer_bq_m2,
            soil_root_water_identity_residual_m=water_identity_residual,
            soil_root_hto_identity_residual_bq_m2=hto_identity_residual,
            obt_tfwt_transfer_bq_m2=obt_result.balance.tfwt_loss_bq_m2,
            obt_external_loss_bq_m2=obt_result.balance.other_loss_bq_m2,
            soil_external_hto_input_bq_m2=soil_global.external_hto_input_bq_m2,
            soil_nonroot_external_hto_loss_bq_m2=nonroot_soil_loss,
            soil_decay_loss_bq_m2=soil_global.decay_loss_bq_m2,
            plant_storage_change_bq_m2=plant_change,
            plant_residual_bq_m2=plant_residual,
            coupled_storage_change_bq_m2=coupled_change,
            coupled_residual_bq_m2=coupled_residual,
        )

        scale = max(
            state.soil_state.total_hto_inventory_bq_m2,
            initial_plant,
            abs(leaf_transfer),
            root_plan.total_hto_transfer_bq_m2,
            1.0,
        )
        _require_closed(
            water_identity_residual,
            field="soil_root_water_identity_residual_m",
            scale=root_plan.total_water_transfer_m,
        )
        _require_closed(
            hto_identity_residual,
            field="soil_root_hto_identity_residual_bq_m2",
            scale=scale,
        )
        _require_closed(plant_residual, field="plant_residual_bq_m2", scale=scale)
        _require_closed(coupled_residual, field="coupled_residual_bq_m2", scale=scale)
        _require_closed(
            soil_global.hto_residual_bq_m2,
            field="soil_global.hto_residual_bq_m2",
            scale=scale,
        )
        _require_closed(
            soil_global.water_residual_m,
            field="soil_global.water_residual_m",
            scale=state.soil_state.total_water_inventory_m,
        )

        return V4ReplaySystemStepResult(
            state=next_state,
            leaf_exchange_flux=leaf_exchange_flux,
            tfwt_leaf_result=tfwt_leaf_result,
            obt_result=obt_result,
            root_plan=root_plan,
            applied_soil_forcing=applied_soil_forcing,
            soil_result=soil_result,
            balance=balance,
        )

    def step(
        self,
        state: V4SoilRootTFWTOBTState,
        replay_input: V4ReplayIntervalInput,
    ) -> V4SoilRootTFWTOBTState:
        return self.advance(state, replay_input).state


__all__ = [
    "ALLOWED_REPLAY_SOURCE_KINDS",
    "ReplayDomainProvenance",
    "V4ReplayInputError",
    "V4ReplayInputSystemOrchestrator",
    "V4ReplayIntervalInput",
    "V4ReplaySystemBalance",
    "V4ReplaySystemStepResult",
]
