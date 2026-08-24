"""Isolated V3 P6.3 soil HTO storage and signed layer transport solver."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math

from .soil_state import SoilState
from .validation import (
    FLUX_UNIT,
    HALF_LIFE_UNIT,
    INTEGRATED_ACTIVITY_UNIT,
    RATE_UNIT,
    SoilInputError,
    SoilParameterError,
    require_finite,
    require_unit,
    validate_deposition_flux,
    validate_half_life,
    validate_interval,
    validate_state,
    validate_transport_flux,
)


@dataclass(frozen=True)
class SoilForcing:
    """Deposition and signed layer transport fluxes.

    ``transport_flux_bq_m2_s`` is positive into the current layer and negative
    out of it. This is an interface input; P6.3 does not calculate it from
    hydrology, diffusion, percolation, or atmospheric dispersion.
    """

    deposition_flux_bq_m2_s: float = 0.0
    transport_flux_bq_m2_s: float = 0.0
    flux_unit: str = FLUX_UNIT

    def __post_init__(self) -> None:
        require_unit(self.flux_unit, FLUX_UNIT, field="soil_flux")
        validate_deposition_flux(self.deposition_flux_bq_m2_s)
        validate_transport_flux(self.transport_flux_bq_m2_s)

    @property
    def deposition_flux(self) -> float:
        """Short public alias for the deposition flux."""

        return self.deposition_flux_bq_m2_s

    @property
    def transport_flux(self) -> float:
        """Short public alias for the signed transport flux."""

        return self.transport_flux_bq_m2_s


@dataclass(frozen=True)
class SoilParameters:
    """Explicit half-life parameter and derived tritium decay constant."""

    tritium_half_life_s: float
    half_life_unit: str = HALF_LIFE_UNIT
    rate_unit: str = RATE_UNIT

    def __post_init__(self) -> None:
        require_unit(
            self.half_life_unit,
            HALF_LIFE_UNIT,
            field="tritium_half_life",
        )
        require_unit(self.rate_unit, RATE_UNIT, field="decay_rate")
        validate_half_life(self.tritium_half_life_s)

    @property
    def decay_constant_s(self) -> float:
        """Return ``lambda = ln(2) / T_half`` in ``s^-1``."""

        return math.log(2.0) / self.tritium_half_life_s


@dataclass(frozen=True)
class SoilStorageBalance:
    """Integrated single-layer soil activity ledger."""

    deposition_input_bq_m2: float
    transport_input_bq_m2: float
    transport_loss_bq_m2: float
    decay_loss_bq_m2: float
    storage_change_bq_m2: float
    residual_bq_m2: float
    unit: str = INTEGRATED_ACTIVITY_UNIT

    def __post_init__(self) -> None:
        require_unit(self.unit, INTEGRATED_ACTIVITY_UNIT, field="soil_balance")
        for field in (
            "deposition_input_bq_m2",
            "transport_input_bq_m2",
            "transport_loss_bq_m2",
            "decay_loss_bq_m2",
            "storage_change_bq_m2",
            "residual_bq_m2",
        ):
            require_finite(getattr(self, field), field=field)
        for field in (
            "deposition_input_bq_m2",
            "transport_input_bq_m2",
            "transport_loss_bq_m2",
            "decay_loss_bq_m2",
        ):
            if getattr(self, field) < 0.0:
                raise SoilInputError(f"{field} must be non-negative")

    @property
    def input_bq_m2(self) -> float:
        """Total external plus signed-transport input to this layer."""

        return self.deposition_input_bq_m2 + self.transport_input_bq_m2

    @property
    def total_loss_bq_m2(self) -> float:
        """Transport-out plus radioactive-decay loss."""

        return self.transport_loss_bq_m2 + self.decay_loss_bq_m2


@dataclass(frozen=True)
class SoilStepResult:
    """Updated soil state plus its auditable activity balance."""

    state: SoilState
    balance: SoilStorageBalance


class SoilStorageSolver:
    """Advance one soil-layer HTO inventory without external model coupling."""

    def __init__(
        self,
        parameters: SoilParameters | None = None,
        *,
        tritium_half_life_s: float | None = None,
        half_life_s: float | None = None,
    ) -> None:
        """Create a solver with an explicit tritium half-life."""

        if parameters is not None and (
            tritium_half_life_s is not None or half_life_s is not None
        ):
            raise SoilParameterError(
                "parameters cannot be combined with explicit half-life arguments"
            )
        if parameters is None:
            if tritium_half_life_s is not None and half_life_s is not None:
                raise SoilParameterError(
                    "supply only one of tritium_half_life_s and half_life_s"
                )
            resolved_half_life = (
                tritium_half_life_s
                if tritium_half_life_s is not None
                else half_life_s
            )
            if resolved_half_life is None:
                raise SoilParameterError(
                    "explicit tritium_half_life_s is required"
                )
            parameters = SoilParameters(
                tritium_half_life_s=resolved_half_life
            )
        self.parameters = parameters

    def _public_inventory(self, state: SoilState) -> float:
        """Read the authoritative state only through its public methods."""

        validate_state(state)
        inventory = require_finite(state.inventory(), field="soil_state.inventory()")
        concentration = require_finite(
            state.concentration(),
            field="soil_state.concentration()",
        )
        if inventory < 0.0 or concentration < 0.0:
            raise SoilInputError(
                "soil inventory and concentration must be non-negative"
            )
        return inventory

    def advance(
        self,
        state: SoilState,
        forcing: SoilForcing,
        interval_seconds: float,
    ) -> SoilStepResult:
        """Advance ``dM/dt = deposition + transport - decay`` analytically."""

        initial_inventory = self._public_inventory(state)
        interval = validate_interval(interval_seconds)
        if not isinstance(forcing, SoilForcing):
            raise SoilInputError("forcing must be a SoilForcing")

        deposition = forcing.deposition_flux_bq_m2_s
        transport = forcing.transport_flux_bq_m2_s
        net_rate = deposition + transport
        decay_constant = self.parameters.decay_constant_s

        if decay_constant == 0.0:
            next_inventory = initial_inventory + net_rate * interval
            decay_loss = 0.0
        else:
            decay_factor = math.exp(-decay_constant * interval)
            equilibrium_inventory = net_rate / decay_constant
            next_inventory = (
                equilibrium_inventory
                + (initial_inventory - equilibrium_inventory) * decay_factor
            )
            storage_change = next_inventory - initial_inventory
            decay_loss = net_rate * interval - storage_change

        if next_inventory < -1.0e-12:
            raise SoilInputError("soil step would create a negative inventory")
        next_inventory = max(next_inventory, 0.0)
        storage_change = next_inventory - initial_inventory
        if decay_loss < -1.0e-10:
            raise SoilInputError("soil decay balance became negative")
        decay_loss = max(decay_loss, 0.0)

        next_state = state.with_inventory(
            soil_water_inventory_bq_m2=next_inventory,
            timestamp=state.timestamp + timedelta(seconds=interval),
        )
        balance = SoilStorageBalance(
            deposition_input_bq_m2=deposition * interval,
            transport_input_bq_m2=max(transport, 0.0) * interval,
            transport_loss_bq_m2=max(-transport, 0.0) * interval,
            decay_loss_bq_m2=decay_loss,
            storage_change_bq_m2=storage_change,
            residual_bq_m2=(
                deposition * interval
                + max(transport, 0.0) * interval
                - storage_change
                - max(-transport, 0.0) * interval
                - decay_loss
            ),
        )
        return SoilStepResult(state=next_state, balance=balance)

    def step(
        self,
        state: SoilState,
        forcing: SoilForcing,
        interval_seconds: float,
    ) -> SoilState:
        """Return only the updated public soil state."""

        return self.advance(state, forcing, interval_seconds).state


__all__ = [
    "SoilForcing",
    "SoilParameters",
    "SoilStepResult",
    "SoilStorageBalance",
    "SoilStorageSolver",
]
