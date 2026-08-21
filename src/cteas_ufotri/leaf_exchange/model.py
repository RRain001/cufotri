"""Coordinator for the V3-P1 Leaf Exchange state/ledger interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import math
from typing import Any, Mapping

from ..parameters import ParameterDatabase
from .balance import LeafExchangeMassBalance
from .parameters import DEFAULT_PARAMETER_NAMES, LeafExchangeParameters
from .physics import (
    FrameworkOnlyPhysics,
    LeafExchangePhysics,
    LeafExchangePhysicsResult,
)
from .state import LeafExchangeForcing, LeafExchangeState, LeafExchangeStateError


class LeafExchangeModelError(ValueError):
    """Raised when a Leaf Exchange step cannot be completed safely."""


def _validate_dt(dt: Any) -> float:
    if isinstance(dt, bool):
        raise LeafExchangeModelError("dt must be a finite positive number of seconds")
    try:
        numeric = float(dt)
    except (TypeError, ValueError) as exc:
        raise LeafExchangeModelError(
            "dt must be a finite positive number of seconds"
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise LeafExchangeModelError("dt must be a finite positive number of seconds")
    return numeric


@dataclass(frozen=True, slots=True)
class LeafExchangeModel:
    """Immutable module coordinator with an injected physics implementation."""

    parameters: LeafExchangeParameters
    physics: LeafExchangePhysics = field(default_factory=FrameworkOnlyPhysics)
    module_id: str = "v3_leaf_exchange"
    module_version: str = "0.1.0"

    @classmethod
    def from_database(
        cls,
        parameter_db: ParameterDatabase,
        *,
        parameter_names: Mapping[str, str] | None = None,
        physics: LeafExchangePhysics | None = None,
    ) -> "LeafExchangeModel":
        parameters = LeafExchangeParameters.from_database(
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
        state: LeafExchangeState,
        forcing: LeafExchangeForcing,
        dt: float,
    ) -> tuple[LeafExchangeState, LeafExchangeMassBalance]:
        """Advance one interval and return the new state plus closed ledger."""

        interval = _validate_dt(dt)
        try:
            state.__post_init__()
            forcing.__post_init__()
        except AttributeError as exc:
            raise LeafExchangeModelError(
                "state and forcing must be LeafExchange contract objects"
            ) from exc
        result = self.physics.step(state, forcing, interval, self.parameters)
        if not isinstance(result, LeafExchangePhysicsResult):
            raise LeafExchangeModelError(
                "physics kernel must return LeafExchangePhysicsResult"
            )
        result.validate()

        new_state = state.copy(
            hto_air_concentration=forcing.hto_air_concentration,
            air_temperature=forcing.air_temperature,
            relative_humidity=forcing.relative_humidity,
            tfwt_activity=result.tfwt_inventory / state.leaf_water_mass,
            obt_activity=result.obt_inventory / state.dry_matter_mass,
            current_time=state.current_time + timedelta(seconds=interval),
            delta_t=interval,
        )
        balance = LeafExchangeMassBalance(
            initial_inventory=state.total_inventory,
            atmospheric_input=result.atmospheric_input,
            leaf_exchange_flux=result.leaf_exchange_flux,
            decay_loss=result.decay_loss,
            final_inventory=new_state.total_inventory,
        )
        balance.assert_closed()
        return new_state, balance

    def provenance(self) -> dict[str, object]:
        """Return deterministic module and parameter provenance."""

        return {
            "module_id": self.module_id,
            "module_version": self.module_version,
            "implementation_status": "FRAMEWORK_COMPLETE",
            "physics_status": self.physics.status,
            "physics_equivalence": "NOT_CLAIMED",
            "parameter_provenance": self.parameters.provenance_mapping(),
        }


def advance(
    state: LeafExchangeState,
    forcing: LeafExchangeForcing,
    dt: float,
    *,
    model: LeafExchangeModel,
) -> tuple[LeafExchangeState, LeafExchangeMassBalance]:
    """Functional adapter for the canonical ``advance(state, forcing, dt)`` API."""

    return model.advance(state, forcing, dt)
