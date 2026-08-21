"""V3 TFWT storage equation consuming a precomputed LeafExchangeFlux."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from ..leaf_exchange_resistance import LeafExchangeFlux
from .tfwt_state import TFWTState
from .validation import (
    INTEGRATED_FLUX_UNIT,
    TFWTFluxError,
    require_finite,
    require_unit,
    validate_interval,
    validate_leaf_exchange_flux,
    validate_nonnegative_flux,
    validate_state,
)


@dataclass(frozen=True)
class TFWTStorageBalance:
    """Integrated balance terms for one storage interval."""

    leaf_exchange_input_bq_m2: float
    water_loss_bq_m2: float
    transformation_bq_m2: float
    storage_change_bq_m2: float
    residual_bq_m2: float
    unit: str = INTEGRATED_FLUX_UNIT

    def __post_init__(self) -> None:
        require_unit(self.unit, INTEGRATED_FLUX_UNIT, field="storage_balance")
        for field in (
            "leaf_exchange_input_bq_m2",
            "water_loss_bq_m2",
            "transformation_bq_m2",
            "storage_change_bq_m2",
            "residual_bq_m2",
        ):
            require_finite(getattr(self, field), field=field)


@dataclass(frozen=True)
class TFWTStepResult:
    """Updated state plus an auditable storage balance."""

    state: TFWTState
    balance: TFWTStorageBalance


class TFWTStorageSolver:
    """Advance only plant TFWT storage at fixed water content.

    The solver consumes `LeafExchangeFlux`; it never reconstructs resistance
    or calls the resistance chain. Water-loss and transformation terms are
    explicit external rates. They are accepted for the storage equation but
    are not computed here, and no OBT state is created.
    """

    def advance(
        self,
        state: TFWTState,
        leaf_exchange_flux: LeafExchangeFlux,
        interval_seconds: float,
        *,
        water_loss_flux_bq_m2_s: float = 0.0,
        transformation_flux_bq_m2_s: float = 0.0,
    ) -> TFWTStepResult:
        validate_state(state)
        interval = validate_interval(interval_seconds)
        leaf_flux = validate_leaf_exchange_flux(leaf_exchange_flux)
        water_loss = validate_nonnegative_flux(
            water_loss_flux_bq_m2_s,
            field="water_loss_flux_bq_m2_s",
        )
        transformation = validate_nonnegative_flux(
            transformation_flux_bq_m2_s,
            field="transformation_flux_bq_m2_s",
        )
        leaf_transfer = leaf_flux * interval
        water_loss_inventory = water_loss * interval
        transformation_inventory = transformation * interval
        storage_change = (
            leaf_transfer - water_loss_inventory - transformation_inventory
        )
        new_inventory = state.tfwt_inventory_bq_m2 + storage_change
        if new_inventory < 0.0:
            raise TFWTFluxError(
                "storage step would create a negative TFWT inventory"
            )
        next_state = state.with_inventory(
            tfwt_inventory_bq_m2=new_inventory,
            time=state.time + timedelta(seconds=interval),
        )
        balance = TFWTStorageBalance(
            leaf_exchange_input_bq_m2=leaf_transfer,
            water_loss_bq_m2=water_loss_inventory,
            transformation_bq_m2=transformation_inventory,
            storage_change_bq_m2=storage_change,
            residual_bq_m2=(
                storage_change
                - leaf_transfer
                + water_loss_inventory
                + transformation_inventory
            ),
        )
        return TFWTStepResult(state=next_state, balance=balance)

    def step(
        self,
        state: TFWTState,
        leaf_exchange_flux: LeafExchangeFlux,
        interval_seconds: float,
        *,
        water_loss_flux_bq_m2_s: float = 0.0,
        transformation_flux_bq_m2_s: float = 0.0,
    ) -> TFWTState:
        """Return only the updated TFWT state for the simple pathway."""

        return self.advance(
            state,
            leaf_exchange_flux,
            interval_seconds,
            water_loss_flux_bq_m2_s=water_loss_flux_bq_m2_s,
            transformation_flux_bq_m2_s=transformation_flux_bq_m2_s,
        ).state


__all__ = ["TFWTStorageBalance", "TFWTStorageSolver", "TFWTStepResult"]
