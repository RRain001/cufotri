"""Conservative opt-in V4 three-layer soil water and HTO core.

This solver owns storage and bookkeeping only. Inter-layer water and HTO fluxes
are explicit forcing inputs; no Richards/Darcy equation or hidden hydrology is
solved here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math

from .soil_state import SoilLayerStateV4, ThreeLayerSoilState
from .validation import (
    HALF_LIFE_UNIT,
    HTO_FLUX_UNIT,
    RATE_UNIT,
    WATER_FLUX_UNIT,
    SoilV4InputError,
    SoilV4ParameterError,
    require_finite,
    require_nonnegative,
    require_unit,
    validate_half_life,
    validate_interval,
    validate_triplet,
)


@dataclass(frozen=True)
class ThreeLayerSoilForcing:
    """Explicit interval-start boundary fluxes for the three-layer core.

    Inter-layer fluxes are signed and positive downward: L1->L2 and L2->L3.
    Negative values therefore represent upward capillary-direction transport.
    No relation between water and HTO flux is inferred by this core.
    """

    surface_water_input_m_s: float = 0.0
    surface_water_loss_m_s: float = 0.0
    surface_deposition_flux_bq_m2_s: float = 0.0
    l1_l2_water_flux_m_s: float = 0.0
    l1_l2_hto_flux_bq_m2_s: float = 0.0
    l2_l3_water_flux_m_s: float = 0.0
    l2_l3_hto_flux_bq_m2_s: float = 0.0
    lower_boundary_water_loss_m_s: float = 0.0
    lower_boundary_hto_loss_bq_m2_s: float = 0.0
    surface_reemission_hto_loss_bq_m2_s: float = 0.0
    root_water_extraction_m_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    root_hto_extraction_bq_m2_s: tuple[float, float, float] = (0.0, 0.0, 0.0)
    water_flux_unit: str = WATER_FLUX_UNIT
    hto_flux_unit: str = HTO_FLUX_UNIT

    def __post_init__(self) -> None:
        require_unit(self.water_flux_unit, WATER_FLUX_UNIT, field="water_flux")
        require_unit(self.hto_flux_unit, HTO_FLUX_UNIT, field="hto_flux")
        require_nonnegative(self.surface_water_input_m_s, field="surface_water_input_m_s")
        require_nonnegative(self.surface_water_loss_m_s, field="surface_water_loss_m_s")
        require_nonnegative(
            self.surface_deposition_flux_bq_m2_s,
            field="surface_deposition_flux_bq_m2_s",
        )
        require_finite(self.l1_l2_water_flux_m_s, field="l1_l2_water_flux_m_s")
        require_finite(self.l1_l2_hto_flux_bq_m2_s, field="l1_l2_hto_flux_bq_m2_s")
        require_finite(self.l2_l3_water_flux_m_s, field="l2_l3_water_flux_m_s")
        require_finite(self.l2_l3_hto_flux_bq_m2_s, field="l2_l3_hto_flux_bq_m2_s")
        require_nonnegative(
            self.lower_boundary_water_loss_m_s,
            field="lower_boundary_water_loss_m_s",
        )
        require_nonnegative(
            self.lower_boundary_hto_loss_bq_m2_s,
            field="lower_boundary_hto_loss_bq_m2_s",
        )
        require_nonnegative(
            self.surface_reemission_hto_loss_bq_m2_s,
            field="surface_reemission_hto_loss_bq_m2_s",
        )
        validate_triplet(self.root_water_extraction_m_s, field="root_water_extraction_m_s", nonnegative=True)
        validate_triplet(
            self.root_hto_extraction_bq_m2_s,
            field="root_hto_extraction_bq_m2_s",
            nonnegative=True,
        )


@dataclass(frozen=True)
class ThreeLayerSoilParameters:
    tritium_half_life_s: float
    half_life_unit: str = HALF_LIFE_UNIT
    rate_unit: str = RATE_UNIT

    def __post_init__(self) -> None:
        require_unit(self.half_life_unit, HALF_LIFE_UNIT, field="tritium_half_life")
        require_unit(self.rate_unit, RATE_UNIT, field="tritium_decay_rate")
        validate_half_life(self.tritium_half_life_s)

    @property
    def decay_constant_s(self) -> float:
        return math.log(2.0) / self.tritium_half_life_s


@dataclass(frozen=True)
class LayerSoilBalanceV4:
    layer_id: str
    water_input_m: float
    water_loss_m: float
    water_storage_change_m: float
    water_residual_m: float
    hto_input_bq_m2: float
    hto_loss_bq_m2: float
    decay_loss_bq_m2: float
    hto_storage_change_bq_m2: float
    hto_residual_bq_m2: float


@dataclass(frozen=True)
class GlobalSoilBalanceV4:
    external_water_input_m: float
    external_water_loss_m: float
    water_storage_change_m: float
    water_residual_m: float
    external_hto_input_bq_m2: float
    external_hto_loss_bq_m2: float
    decay_loss_bq_m2: float
    hto_storage_change_bq_m2: float
    hto_residual_bq_m2: float
    interlayer_water_cancellation_m: float
    interlayer_hto_cancellation_bq_m2: float


@dataclass(frozen=True)
class ThreeLayerSoilStepResult:
    state: ThreeLayerSoilState
    layer_balances: tuple[LayerSoilBalanceV4, LayerSoilBalanceV4, LayerSoilBalanceV4]
    global_balance: GlobalSoilBalanceV4


class ThreeLayerSoilStorageSolver:
    """Advance the explicit three-layer state with conservative boundary fluxes."""

    def __init__(
        self,
        parameters: ThreeLayerSoilParameters | None = None,
        *,
        tritium_half_life_s: float | None = None,
    ) -> None:
        if parameters is not None and tritium_half_life_s is not None:
            raise SoilV4ParameterError(
                "parameters cannot be combined with tritium_half_life_s"
            )
        if parameters is None:
            if tritium_half_life_s is None:
                raise SoilV4ParameterError("explicit tritium_half_life_s is required")
            parameters = ThreeLayerSoilParameters(
                tritium_half_life_s=tritium_half_life_s
            )
        self.parameters = parameters

    @staticmethod
    def _split_signed(flux: float) -> tuple[float, float]:
        """Return downward and upward non-negative magnitudes."""
        return max(flux, 0.0), max(-flux, 0.0)

    def _advance_activity(
        self,
        *,
        initial: float,
        input_rate: float,
        loss_rate: float,
        interval: float,
        layer_id: str,
    ) -> tuple[float, float, float]:
        net_rate = input_rate - loss_rate
        decay_constant = self.parameters.decay_constant_s
        decay_factor = math.exp(-decay_constant * interval)
        equilibrium = net_rate / decay_constant
        next_inventory = equilibrium + (initial - equilibrium) * decay_factor
        if next_inventory < -1.0e-12:
            raise SoilV4InputError(
                f"{layer_id} HTO outflux over the interval exceeds available inventory"
            )
        next_inventory = max(next_inventory, 0.0)
        storage_change = next_inventory - initial
        decay_loss = net_rate * interval - storage_change
        tolerance = 1.0e-10 * max(1.0, initial, abs(net_rate * interval))
        if decay_loss < -tolerance:
            raise SoilV4InputError(f"{layer_id} decay balance became negative")
        decay_loss = max(decay_loss, 0.0)
        return next_inventory, storage_change, decay_loss

    def advance(
        self,
        state: ThreeLayerSoilState,
        forcing: ThreeLayerSoilForcing,
        interval_seconds: float,
    ) -> ThreeLayerSoilStepResult:
        if not isinstance(state, ThreeLayerSoilState):
            raise SoilV4InputError("state must be ThreeLayerSoilState")
        if not isinstance(forcing, ThreeLayerSoilForcing):
            raise SoilV4InputError("forcing must be ThreeLayerSoilForcing")
        interval = validate_interval(interval_seconds)

        w12_down, w12_up = self._split_signed(forcing.l1_l2_water_flux_m_s)
        w23_down, w23_up = self._split_signed(forcing.l2_l3_water_flux_m_s)
        h12_down, h12_up = self._split_signed(forcing.l1_l2_hto_flux_bq_m2_s)
        h23_down, h23_up = self._split_signed(forcing.l2_l3_hto_flux_bq_m2_s)
        root_w = validate_triplet(
            forcing.root_water_extraction_m_s,
            field="root_water_extraction_m_s",
            nonnegative=True,
        )
        root_h = validate_triplet(
            forcing.root_hto_extraction_bq_m2_s,
            field="root_hto_extraction_bq_m2_s",
            nonnegative=True,
        )

        water_inputs = (
            forcing.surface_water_input_m_s + w12_up,
            w12_down + w23_up,
            w23_down,
        )
        water_losses = (
            forcing.surface_water_loss_m_s + w12_down + root_w[0],
            w12_up + w23_down + root_w[1],
            w23_up + root_w[2] + forcing.lower_boundary_water_loss_m_s,
        )
        hto_inputs = (
            forcing.surface_deposition_flux_bq_m2_s + h12_up,
            h12_down + h23_up,
            h23_down,
        )
        hto_losses = (
            h12_down + root_h[0] + forcing.surface_reemission_hto_loss_bq_m2_s,
            h12_up + h23_down + root_h[1],
            h23_up + root_h[2] + forcing.lower_boundary_hto_loss_bq_m2_s,
        )

        next_layers: list[SoilLayerStateV4] = []
        balances: list[LayerSoilBalanceV4] = []
        for index, layer in enumerate(state.layers):
            next_water = layer.water_inventory_m + (
                water_inputs[index] - water_losses[index]
            ) * interval
            if next_water <= 0.0:
                raise SoilV4InputError(
                    f"{layer.layer_id} water outflux over the interval exhausts layer water"
                )
            water_change = next_water - layer.water_inventory_m
            water_residual = (
                water_inputs[index] * interval
                - water_losses[index] * interval
                - water_change
            )

            next_hto, hto_change, decay_loss = self._advance_activity(
                initial=layer.hto_inventory_bq_m2,
                input_rate=hto_inputs[index],
                loss_rate=hto_losses[index],
                interval=interval,
                layer_id=layer.layer_id,
            )
            hto_residual = (
                hto_inputs[index] * interval
                - hto_losses[index] * interval
                - decay_loss
                - hto_change
            )
            next_layers.append(
                layer.with_inventories(
                    water_inventory_m=next_water,
                    hto_inventory_bq_m2=next_hto,
                )
            )
            balances.append(
                LayerSoilBalanceV4(
                    layer_id=layer.layer_id,
                    water_input_m=water_inputs[index] * interval,
                    water_loss_m=water_losses[index] * interval,
                    water_storage_change_m=water_change,
                    water_residual_m=water_residual,
                    hto_input_bq_m2=hto_inputs[index] * interval,
                    hto_loss_bq_m2=hto_losses[index] * interval,
                    decay_loss_bq_m2=decay_loss,
                    hto_storage_change_bq_m2=hto_change,
                    hto_residual_bq_m2=hto_residual,
                )
            )

        next_state = ThreeLayerSoilState(
            soil_identifier=state.soil_identifier,
            layers=tuple(next_layers),  # type: ignore[arg-type]
            timestamp=state.timestamp + timedelta(seconds=interval),
            provenance=state.provenance,
            area_basis=state.area_basis,
            version=state.version,
        )

        total_water_change = next_state.total_water_inventory_m - state.total_water_inventory_m
        external_water_input = forcing.surface_water_input_m_s * interval
        external_water_loss = (
            forcing.surface_water_loss_m_s
            + sum(root_w)
            + forcing.lower_boundary_water_loss_m_s
        ) * interval
        total_hto_change = next_state.total_hto_inventory_bq_m2 - state.total_hto_inventory_bq_m2
        external_hto_input = forcing.surface_deposition_flux_bq_m2_s * interval
        external_hto_loss = (
            sum(root_h)
            + forcing.lower_boundary_hto_loss_bq_m2_s
            + forcing.surface_reemission_hto_loss_bq_m2_s
        ) * interval
        total_decay = sum(balance.decay_loss_bq_m2 for balance in balances)

        global_balance = GlobalSoilBalanceV4(
            external_water_input_m=external_water_input,
            external_water_loss_m=external_water_loss,
            water_storage_change_m=total_water_change,
            water_residual_m=(
                external_water_input - external_water_loss - total_water_change
            ),
            external_hto_input_bq_m2=external_hto_input,
            external_hto_loss_bq_m2=external_hto_loss,
            decay_loss_bq_m2=total_decay,
            hto_storage_change_bq_m2=total_hto_change,
            hto_residual_bq_m2=(
                external_hto_input
                - external_hto_loss
                - total_decay
                - total_hto_change
            ),
            interlayer_water_cancellation_m=(w12_down - w12_up + w23_down - w23_up) * interval
            + (-w12_down + w12_up - w23_down + w23_up) * interval,
            interlayer_hto_cancellation_bq_m2=(h12_down - h12_up + h23_down - h23_up) * interval
            + (-h12_down + h12_up - h23_down + h23_up) * interval,
        )
        return ThreeLayerSoilStepResult(
            state=next_state,
            layer_balances=tuple(balances),  # type: ignore[arg-type]
            global_balance=global_balance,
        )

    def step(
        self,
        state: ThreeLayerSoilState,
        forcing: ThreeLayerSoilForcing,
        interval_seconds: float,
    ) -> ThreeLayerSoilState:
        return self.advance(state, forcing, interval_seconds).state


__all__ = [
    "GlobalSoilBalanceV4",
    "LayerSoilBalanceV4",
    "ThreeLayerSoilForcing",
    "ThreeLayerSoilParameters",
    "ThreeLayerSoilStepResult",
    "ThreeLayerSoilStorageSolver",
]
