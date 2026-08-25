"""V3 plant pathway facade: forcing -> resistance flux -> TFWT storage."""

from __future__ import annotations

from dataclasses import dataclass

from ..leaf_exchange_resistance import (
    AtmosphericHTOForcing,
    LeafExchangeFlux,
    ResistanceState,
    signed_leaf_exchange_flux,
)
from .state import V3PlantState
from .validation import validate_pathway_forcing, validate_pathway_state


@dataclass(frozen=True)
class V3PathwayStep:
    """Public result of one V3 forcing interval."""

    state: V3PlantState
    leaf_exchange_flux: LeafExchangeFlux


@dataclass(frozen=True)
class V3PlantPathway:
    """Connect an existing resistance state to the public TFWT interface."""

    resistance: ResistanceState

    def leaf_flux(
        self,
        forcing: AtmosphericHTOForcing,
        equilibrium_air_concentration_bq_m3: float,
    ) -> LeafExchangeFlux:
        """Compute the signed flux using the already-frozen resistance state."""

        validate_pathway_forcing(forcing)
        return signed_leaf_exchange_flux(
            forcing,
            self.resistance,
            equilibrium_air_concentration_bq_m3,
        )

    def advance(
        self,
        state: V3PlantState,
        forcing: AtmosphericHTOForcing,
        equilibrium_air_concentration_bq_m3: float,
        interval_seconds: float,
        *,
        water_loss_flux_bq_m2_s: float = 0.0,
        transformation_flux_bq_m2_s: float = 0.0,
    ) -> V3PathwayStep:
        """Advance resistance flux through the public TFWT state interface."""

        validate_pathway_state(state)
        flux = self.leaf_flux(forcing, equilibrium_air_concentration_bq_m3)
        next_tfwt = state.tfwt.advance(
            interval_seconds,
            flux,
            water_loss_flux_bq_m2_s=water_loss_flux_bq_m2_s,
            transformation_flux_bq_m2_s=transformation_flux_bq_m2_s,
        )
        next_state = V3PlantState(tfwt=next_tfwt)
        return V3PathwayStep(state=next_state, leaf_exchange_flux=flux)


__all__ = ["V3PathwayStep", "V3PlantPathway"]
