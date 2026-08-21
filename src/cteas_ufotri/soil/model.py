"""Coordinator for the V3-P2 three-layer soil framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import math
from typing import Any, Mapping

from ..parameters import ParameterDatabase
from .balance import SoilMassBalance
from .parameters import DEFAULT_PARAMETER_NAMES, SoilParameters
from .physics import FrameworkOnlyPhysics, SoilPhysics, SoilPhysicsResult
from .state import SoilForcing, SoilLayer, SoilState, SoilStateError


class SoilModelError(ValueError):
    """Raised when a P2 soil step cannot be completed safely."""


def _validate_dt(dt: Any) -> float:
    if isinstance(dt, bool):
        raise SoilModelError("dt must be a finite positive number of seconds")
    try:
        numeric = float(dt)
    except (TypeError, ValueError) as exc:
        raise SoilModelError(
            "dt must be a finite positive number of seconds"
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise SoilModelError("dt must be a finite positive number of seconds")
    return numeric


@dataclass(frozen=True, slots=True)
class RootZoneActivity:
    """Read-only root-zone coupling seam; no plant uptake is performed."""

    layer_id: int
    hto_activity: float
    hto_concentration: float
    status: str = "SEAM_ONLY_NO_ROOT_UPTAKE"


def apply_atmospheric_input(
    state: SoilState,
    forcing: SoilForcing,
    dt: float,
) -> tuple[SoilState, float]:
    """Apply supplied deposition to layer 1 and return integrated input.

    Air concentration is retained as forcing metadata. No deposition velocity,
    scavenging, or UFOTRI atmospheric equation is inferred in P2.
    """

    interval = _validate_dt(dt)
    if not isinstance(state, SoilState) or not isinstance(forcing, SoilForcing):
        raise SoilModelError("state and forcing must be P2 contract objects")
    input_bq_m2 = forcing.deposition_flux * interval
    surface = state.layer(1).copy(
        hto_activity=state.layer(1).hto_inventory + input_bq_m2
    )
    return state.copy(layers=(surface, state.layer(2), state.layer(3))), input_bq_m2


def get_root_zone_activity(
    state: SoilState,
    *,
    layer_id: int = 2,
) -> RootZoneActivity:
    """Expose root-zone activity without changing soil or plant inventories."""

    if not isinstance(state, SoilState):
        raise SoilModelError("state must be a SoilState")
    try:
        layer = state.layer(layer_id)
    except SoilStateError as exc:
        raise SoilModelError(str(exc)) from exc
    return RootZoneActivity(
        layer_id=layer.layer_id,
        hto_activity=layer.hto_inventory,
        hto_concentration=layer.hto_concentration,
    )


@dataclass(frozen=True, slots=True)
class SoilModel:
    """Immutable three-layer coordinator with injected transport physics."""

    parameters: SoilParameters
    physics: SoilPhysics = field(default_factory=FrameworkOnlyPhysics)
    module_id: str = "v3_soil_layer"
    module_version: str = "0.1.0"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] | None = None,
        physics: SoilPhysics | None = None,
    ) -> "SoilModel":
        parameters = SoilParameters.from_database(
            parameter_db,
            parameter_names=(
                DEFAULT_PARAMETER_NAMES if parameter_names is None else parameter_names
            ),
        )
        return cls(
            parameters=parameters,
            physics=FrameworkOnlyPhysics() if physics is None else physics,
        )

    def advance(
        self,
        soil_state: SoilState,
        forcing: SoilForcing,
        dt: float,
    ) -> tuple[SoilState, SoilMassBalance]:
        """Advance one interval and return final state plus closed ledger."""

        interval = _validate_dt(dt)
        if not isinstance(soil_state, SoilState) or not isinstance(forcing, SoilForcing):
            raise SoilModelError("state and forcing must be P2 contract objects")
        with_input, atmospheric_input = apply_atmospheric_input(
            soil_state, forcing, interval
        )
        result = self.physics.step(
            with_input,
            forcing,
            interval,
            self.parameters,
        )
        if not isinstance(result, SoilPhysicsResult):
            raise SoilModelError("soil physics must return SoilPhysicsResult")
        result.validate()
        final_state = with_input.copy(
            layers=result.layers,
            current_time=soil_state.current_time + timedelta(seconds=interval),
            delta_t=interval,
        )
        balance = SoilMassBalance(
            initial_inventory=soil_state.total_hto_inventory,
            atmospheric_input=atmospheric_input,
            internal_transfer=result.internal_transfer,
            decay_loss=result.decay_loss,
            output_to_plants=result.output_to_plants,
            final_inventory=final_state.total_hto_inventory,
        )
        balance.assert_closed()
        return final_state, balance

    def root_zone_activity(self, soil_state: SoilState, *, layer_id: int = 2) -> RootZoneActivity:
        return get_root_zone_activity(soil_state, layer_id=layer_id)

    def provenance(self) -> dict[str, object]:
        """Return module, physics, and parameter provenance."""

        return {
            "module_id": self.module_id,
            "module_version": self.module_version,
            "implementation_status": "FRAMEWORK_COMPLETE",
            "physics_status": self.physics.status,
            "root_uptake_status": "NOT_IMPLEMENTED",
            "physics_equivalence": "NOT_CLAIMED",
            "parameter_provenance": self.parameters.provenance_mapping(),
        }


def advance(
    soil_state: SoilState,
    forcing: SoilForcing,
    dt: float,
    *,
    model: SoilModel,
) -> tuple[SoilState, SoilMassBalance]:
    """Functional adapter for the canonical ``advance`` interface."""

    return model.advance(soil_state, forcing, dt)
