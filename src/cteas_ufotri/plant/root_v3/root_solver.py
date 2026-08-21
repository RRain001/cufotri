"""V3 P6.4 provisional soil-to-root HTO uptake solver."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ..leaf_exchange_resistance import ForcingProvenance
from ..soil_v3 import SoilState
from ..soil_v3.validation import validate_state as validate_soil_state
from .root_state import RootFlux, RootState
from .validation import (
    INTEGRATED_ACTIVITY_UNIT,
    ROOT_COEFFICIENT_UNIT,
    RootInputError,
    RootParameterError,
    require_finite,
    require_unit,
    validate_forcing,
    validate_parameters,
)


@dataclass(frozen=True)
class RootUptakeForcing:
    """Identity, provenance, and interval for one root uptake step."""

    plant_identifier: str
    root_zone_identifier: str
    interval_seconds: float
    provenance: ForcingProvenance

    def __post_init__(self) -> None:
        validate_forcing(self)


@dataclass(frozen=True)
class RootParameters:
    """Explicit provisional effective water-uptake coefficient."""

    k_root_m_s: float
    coefficient_unit: str = ROOT_COEFFICIENT_UNIT
    parameter_status: str = "provisional"

    def __post_init__(self) -> None:
        validate_parameters(self)

    @property
    def uptake_coefficient_m_s(self) -> float:
        """Readable alias for the equation coefficient k_root."""

        return self.k_root_m_s


@dataclass(frozen=True)
class RootUptakeBalance:
    """Source-inventory ledger for the root-transfer boundary."""

    initial_soil_inventory_bq_m2: float
    root_transfer_bq_m2: float
    remaining_soil_inventory_bq_m2: float
    other_loss_bq_m2: float
    residual_bq_m2: float
    unit: str = INTEGRATED_ACTIVITY_UNIT

    def __post_init__(self) -> None:
        require_unit(self.unit, INTEGRATED_ACTIVITY_UNIT, field="root_balance")
        for field in (
            "initial_soil_inventory_bq_m2",
            "root_transfer_bq_m2",
            "remaining_soil_inventory_bq_m2",
            "other_loss_bq_m2",
            "residual_bq_m2",
        ):
            value = require_finite(getattr(self, field), field=field)
            if field != "residual_bq_m2" and value < 0.0:
                raise RootInputError(f"{field} must be non-negative")

    @property
    def soil_inventory_decrease_bq_m2(self) -> float:
        """Activity leaving the soil boundary in this minimal interface."""

        return self.root_transfer_bq_m2 + self.other_loss_bq_m2


@dataclass(frozen=True)
class RootUptakeStepResult:
    """Root flux plus the source-inventory balance for one interval."""

    root_flux: RootFlux
    balance: RootUptakeBalance

    @property
    def state(self) -> RootState:
        """Compatibility name for the state-bearing root flux record."""

        return self.root_flux


class RootUptakeSolver:
    """Compute J_root = k_root * C_soil from the public soil API only."""

    def __init__(
        self,
        parameters: RootParameters | None = None,
        *,
        k_root_m_s: float | None = None,
        k_root: float | None = None,
    ) -> None:
        """Create a solver with an explicit provisional coefficient."""

        if parameters is not None and (
            k_root_m_s is not None or k_root is not None
        ):
            raise RootParameterError(
                "parameters cannot be combined with explicit k_root arguments"
            )
        if parameters is None:
            if k_root_m_s is not None and k_root is not None:
                raise RootParameterError(
                    "supply only one of k_root_m_s and k_root"
                )
            coefficient = (
                k_root_m_s if k_root_m_s is not None else k_root
            )
            if coefficient is None:
                raise RootParameterError(
                    "explicit provisional k_root_m_s is required"
                )
            parameters = RootParameters(k_root_m_s=coefficient)
        self.parameters = parameters

    def _soil_inputs(self, soil_state: SoilState) -> tuple[float, float]:
        """Read soil activity through inventory() and concentration()."""

        if not isinstance(soil_state, SoilState):
            raise RootInputError("soil_state must be a V3 SoilState")
        validate_soil_state(soil_state)
        inventory = require_finite(
            soil_state.inventory(),
            field="soil_state.inventory()",
        )
        concentration = require_finite(
            soil_state.concentration(),
            field="soil_state.concentration()",
        )
        if inventory < 0.0 or concentration < 0.0:
            raise RootInputError(
                "soil inventory and concentration must be non-negative"
            )
        return inventory, concentration

    def advance_result(
        self,
        soil_state: SoilState,
        forcing: RootUptakeForcing,
    ) -> RootUptakeStepResult:
        """Return a root flux and its non-mutating source-inventory ledger."""

        initial_inventory, soil_concentration = self._soil_inputs(soil_state)
        validate_forcing(forcing)
        interval = forcing.interval_seconds
        uptake_flux = self.parameters.k_root_m_s * soil_concentration
        uptake_inventory = uptake_flux * interval

        tolerance = 1.0e-12 * max(1.0, initial_inventory)
        if uptake_inventory > initial_inventory + tolerance:
            raise RootInputError(
                "root uptake over the interval exceeds soil inventory"
            )
        remaining_inventory = max(initial_inventory - uptake_inventory, 0.0)
        root_state = RootState.from_transfer(
            plant_identifier=forcing.plant_identifier,
            root_zone_identifier=forcing.root_zone_identifier,
            uptake_inventory_bq_m2=uptake_inventory,
            uptake_flux_bq_m2_s=uptake_flux,
            timestamp=soil_state.timestamp + timedelta(seconds=interval),
            provenance=forcing.provenance,
        )
        balance = RootUptakeBalance(
            initial_soil_inventory_bq_m2=initial_inventory,
            root_transfer_bq_m2=uptake_inventory,
            remaining_soil_inventory_bq_m2=remaining_inventory,
            other_loss_bq_m2=0.0,
            residual_bq_m2=(
                initial_inventory
                - uptake_inventory
                - remaining_inventory
            ),
        )
        return RootUptakeStepResult(root_flux=root_state, balance=balance)

    def advance(
        self,
        soil_state: SoilState,
        forcing: RootUptakeForcing,
    ) -> RootFlux:
        """Return only the typed root uptake flux for the TFWT boundary."""

        return self.advance_result(soil_state, forcing).root_flux

    def step(
        self,
        soil_state: SoilState,
        forcing: RootUptakeForcing,
    ) -> RootFlux:
        """Alias for the public one-interval root flux operation."""

        return self.advance(soil_state, forcing)


__all__ = [
    "RootParameters",
    "RootUptakeBalance",
    "RootUptakeForcing",
    "RootUptakeSolver",
    "RootUptakeStepResult",
]
