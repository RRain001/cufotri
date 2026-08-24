"""Validation for the V3 plant pathway facade."""

from __future__ import annotations

from ..leaf_exchange_resistance.validation import validate_forcing
from ..tfwt_v3.validation import validate_state


def validate_pathway_forcing(forcing: object) -> None:
    """Validate the public atmospheric forcing boundary."""

    validate_forcing(forcing)


def validate_pathway_state(state: object) -> None:
    """Validate TFWT state and reject the reserved OBT slot."""

    validate_state(state.tfwt)
    if state.obt is not None:
        raise ValueError("OBT pathway is reserved and not implemented")
