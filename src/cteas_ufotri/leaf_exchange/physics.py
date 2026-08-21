"""Replaceable physics seam for V3-P1 Leaf Exchange.

No UFOTRI equation is implemented here.  ``SyntheticLinearLeafExchangePhysics``
exists only to exercise state movement and ledger conservation with explicit
test parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

from .parameters import LeafExchangeParameters
from .state import LeafExchangeForcing, LeafExchangeState, LeafExchangeStateError


@dataclass(frozen=True, slots=True)
class LeafExchangePhysicsResult:
    """Result returned by a physics kernel, with inventories in Bq."""

    tfwt_inventory: float
    obt_inventory: float
    atmospheric_input: float
    leaf_exchange_flux: float
    decay_loss: float

    def validate(self) -> None:
        for name in (
            "tfwt_inventory",
            "obt_inventory",
            "atmospheric_input",
            "leaf_exchange_flux",
            "decay_loss",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0.0:
                raise LeafExchangeStateError(
                    f"physics result {name} must be finite and non-negative"
                )


class LeafExchangePhysics(Protocol):
    """Protocol implemented by a future reviewed Leaf Exchange physics core."""

    status: str

    def step(
        self,
        state: LeafExchangeState,
        forcing: LeafExchangeForcing,
        dt: float,
        parameters: LeafExchangeParameters,
    ) -> LeafExchangePhysicsResult:
        ...


@dataclass(frozen=True, slots=True)
class FrameworkOnlyPhysics:
    """Default fail-closed physics implementation."""

    status: str = "PHYSICS_PENDING_UFOTRI_MIGRATION"

    def step(
        self,
        state: LeafExchangeState,
        forcing: LeafExchangeForcing,
        dt: float,
        parameters: LeafExchangeParameters,
    ) -> LeafExchangePhysicsResult:
        del state, forcing, dt, parameters
        raise RuntimeError(
            "No Leaf Exchange physics kernel is configured; "
            "UFOTRI formula migration is pending"
        )


@dataclass(frozen=True, slots=True)
class ZeroExchangePhysics:
    """TEST_ONLY no-op kernel for closed-system ledger tests."""

    status: str = "TEST_ONLY"

    def step(
        self,
        state: LeafExchangeState,
        forcing: LeafExchangeForcing,
        dt: float,
        parameters: LeafExchangeParameters,
    ) -> LeafExchangePhysicsResult:
        del forcing, dt, parameters
        return LeafExchangePhysicsResult(
            tfwt_inventory=state.tfwt_inventory,
            obt_inventory=state.obt_inventory,
            atmospheric_input=0.0,
            leaf_exchange_flux=0.0,
            decay_loss=0.0,
        )


@dataclass(frozen=True, slots=True)
class SyntheticLinearLeafExchangePhysics:
    """TEST_ONLY explicit-Euler kernel for deterministic framework tests.

    The synthetic kernel relaxes TFWT inventory toward an explicitly scaled
    atmospheric target, transfers a first-order fraction to OBT, and applies
    first-order OBT decay.  It is not a UFOTRI implementation and must never
    be described as physical validation.
    """

    status: str = "TEST_ONLY"

    def step(
        self,
        state: LeafExchangeState,
        forcing: LeafExchangeForcing,
        dt: float,
        parameters: LeafExchangeParameters,
    ) -> LeafExchangePhysicsResult:
        target_tfwt_activity = (
            forcing.hto_air_concentration
            * parameters.air_to_tfwt_partition_m3_per_kg
        )
        target_tfwt_inventory = target_tfwt_activity * state.leaf_water_mass
        net_air_transfer = (
            parameters.tfwt_exchange_rate_s
            * (target_tfwt_inventory - state.tfwt_inventory)
            * dt
        )
        obt_formation = parameters.obt_formation_rate_s * state.tfwt_inventory * dt
        decay_loss = parameters.obt_decay_rate_s * state.obt_inventory * dt
        tfwt_inventory = state.tfwt_inventory + net_air_transfer - obt_formation
        obt_inventory = state.obt_inventory + obt_formation - decay_loss
        if tfwt_inventory < 0.0 or obt_inventory < 0.0:
            raise LeafExchangeStateError(
                "Synthetic Leaf Exchange step would create negative inventory; "
                "reduce dt or use a reviewed positivity-preserving kernel"
            )
        return LeafExchangePhysicsResult(
            tfwt_inventory=tfwt_inventory,
            obt_inventory=obt_inventory,
            atmospheric_input=max(net_air_transfer, 0.0),
            leaf_exchange_flux=max(-net_air_transfer, 0.0),
            decay_loss=decay_loss,
        )
