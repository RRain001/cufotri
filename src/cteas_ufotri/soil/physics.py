"""Replaceable P2 soil transport seam.

No UFOTRI soil equation is implemented. The synthetic kernel exists only to
exercise deterministic internal transfer and conservation with test values.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol

from .parameters import SoilParameters
from .state import SoilForcing, SoilLayer, SoilState, SoilStateError


@dataclass(frozen=True, slots=True)
class SoilPhysicsResult:
    """Final layers and integrated non-boundary activity terms."""

    layers: tuple[SoilLayer, SoilLayer, SoilLayer]
    internal_transfer: float
    decay_loss: float
    output_to_plants: float

    def validate(self) -> None:
        try:
            SoilState(self.layers)
        except SoilStateError:
            raise
        for name in (
            "internal_transfer",
            "decay_loss",
            "output_to_plants",
        ):
            value = getattr(self, name)
            try:
                numeric = float(value)
            except (TypeError, ValueError) as exc:
                raise SoilStateError(
                    f"physics result {name} must be finite and non-negative"
                ) from exc
            if not math.isfinite(numeric) or numeric < 0.0:
                raise SoilStateError(
                    f"physics result {name} must be finite and non-negative"
                )


class SoilPhysics(Protocol):
    """Protocol for a future reviewed UFOTRI soil physics implementation."""

    status: str

    def step(
        self,
        state: SoilState,
        forcing: SoilForcing,
        dt: float,
        parameters: SoilParameters,
    ) -> SoilPhysicsResult:
        ...


@dataclass(frozen=True, slots=True)
class FrameworkOnlyPhysics:
    """Default fail-closed implementation before soil physics migration."""

    status: str = "PHYSICS_PENDING_UFOTRI_MIGRATION"

    def step(
        self,
        state: SoilState,
        forcing: SoilForcing,
        dt: float,
        parameters: SoilParameters,
    ) -> SoilPhysicsResult:
        del state, forcing, dt, parameters
        raise RuntimeError(
            "No Soil physics kernel is configured; UFOTRI soil equation "
            "migration is pending"
        )


@dataclass(frozen=True, slots=True)
class ZeroTransportKernel:
    """TEST_ONLY kernel preserving all three layers and all HTO inventory."""

    status: str = "TEST_ONLY"

    def step(
        self,
        state: SoilState,
        forcing: SoilForcing,
        dt: float,
        parameters: SoilParameters,
    ) -> SoilPhysicsResult:
        del forcing, dt, parameters
        return SoilPhysicsResult(
            layers=state.layers,
            internal_transfer=0.0,
            decay_loss=0.0,
            output_to_plants=0.0,
        )


@dataclass(frozen=True, slots=True)
class SyntheticTransportKernel:
    """TEST_ONLY conservative kernel for deterministic framework tests.

    It transfers activity down-gradient between adjacent layer inventories and
    applies explicit first-order decay. This is a dimensional test harness,
    not a UFOTRI soil-process implementation.
    """

    status: str = "TEST_ONLY"

    def step(
        self,
        state: SoilState,
        forcing: SoilForcing,
        dt: float,
        parameters: SoilParameters,
    ) -> SoilPhysicsResult:
        del forcing
        working = [layer.hto_inventory for layer in state.layers]
        internal_transfer = 0.0
        for index in (0, 1):
            difference = max(working[index] - working[index + 1], 0.0)
            transfer = parameters.interlayer_transport_rate_s * difference * dt
            if transfer > working[index]:
                raise SoilStateError(
                    "Synthetic soil transport would create negative inventory; "
                    "reduce dt or use a reviewed positivity-preserving kernel"
                )
            working[index] -= transfer
            working[index + 1] += transfer
            internal_transfer += transfer

        decay_loss = 0.0
        for index, inventory in enumerate(working):
            decay = parameters.decay_rate_s * inventory * dt
            if decay > inventory:
                raise SoilStateError(
                    "Synthetic soil decay would create negative inventory; "
                    "reduce dt or use a reviewed positivity-preserving kernel"
                )
            working[index] -= decay
            decay_loss += decay

        layers = tuple(
            layer.copy(hto_activity=working[index])
            for index, layer in enumerate(state.layers)
        )
        return SoilPhysicsResult(
            layers=(layers[0], layers[1], layers[2]),
            internal_transfer=internal_transfer,
            decay_loss=decay_loss,
            output_to_plants=0.0,
        )


def advance(
    soil_state: SoilState,
    forcing: SoilForcing,
    dt: float,
    parameters: SoilParameters,
    *,
    kernel: SoilPhysics | None = None,
) -> SoilPhysicsResult:
    """Call the replaceable P2 physics seam with an explicit kernel.

    The optional default is deliberately fail-closed; no numerical soil
    behavior is selected implicitly.
    """

    if isinstance(dt, bool):
        raise SoilStateError("dt must be a finite positive number of seconds")
    try:
        interval = float(dt)
    except (TypeError, ValueError) as exc:
        raise SoilStateError(
            "dt must be a finite positive number of seconds"
        ) from exc
    if not math.isfinite(interval) or interval <= 0.0:
        raise SoilStateError("dt must be a finite positive number of seconds")
    selected = FrameworkOnlyPhysics() if kernel is None else kernel
    return selected.step(soil_state, forcing, interval, parameters)
