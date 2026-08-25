"""V3 leaf-exchange resistance chain; no TFWT or OBT solver is included."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .types import (
    AtmosphericHTOForcing,
    CONCENTRATION_UNIT,
    FLUX_UNIT,
    LeafExchangeFlux,
    ResistanceCoordinates,
    ResistanceState,
)
from .validation import (
    EXCHANGE_VELOCITY_UNIT,
    RESISTANCE_UNIT,
    InvalidResistanceError,
    MissingParameterError,
    ParameterUseNotAllowedError,
    require_finite,
    require_unit,
    validate_forcing,
    validate_resistance,
)


class ParameterDatabaseProtocol(Protocol):
    """Minimum P6.1 ParameterDatabase surface consumed by this subsystem."""

    def lookup(
        self,
        name: str,
        coordinates: Mapping[str, object],
        *,
        production: bool = False,
    ) -> float:
        """Return one table value or raise when it is unavailable."""


DEFAULT_PARAMETER_NAMES = {
    "aerodynamic_resistance": "leaf.aerodynamic_resistance",
    "boundary_layer_resistance": "leaf.boundary_layer_resistance",
    "canopy_resistance": "leaf.canopy_resistance",
}


def _parameter_status(database: object, name: str) -> str | None:
    """Read optional P6.1 provenance without requiring its package on main."""

    get_provenance = getattr(database, "get_provenance", None)
    if not callable(get_provenance):
        return None
    provenance = get_provenance(name)
    if isinstance(provenance, Mapping):
        status = provenance.get("status")
    else:
        status = getattr(provenance, "status", None)
    return None if status is None else str(status).upper()


def _lookup_required(
    database: ParameterDatabaseProtocol,
    parameter_name: str,
    coordinates: Mapping[str, object],
) -> float:
    """Resolve a required value with explicit non-production lifecycle gating."""

    lookup = getattr(database, "lookup", None)
    if not callable(lookup):
        raise MissingParameterError(
            "ParameterDatabase must expose lookup(name, coordinates, production=False)"
        )
    try:
        status = _parameter_status(database, parameter_name)
        if status == "ACTIVE":
            raise ParameterUseNotAllowedError(
                f"ACTIVE parameter {parameter_name!r} is forbidden in P6.2B-1"
            )
        value = lookup(parameter_name, coordinates, production=False)
    except ParameterUseNotAllowedError:
        raise
    except Exception as exc:
        raise MissingParameterError(
            f"Required parameter {parameter_name!r} is unavailable; no fallback is allowed"
        ) from exc
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MissingParameterError(
            f"Required parameter {parameter_name!r} has no numeric value"
        )
    return float(value)


@dataclass(frozen=True)
class ResistanceChain(ResistanceState):
    """`r_a + r_b + r_c` and its reciprocal exchange velocity."""

    @classmethod
    def from_components(
        cls,
        aerodynamic_resistance: float,
        boundary_layer_resistance: float,
        canopy_resistance: float,
        *,
        resistance_unit: str = RESISTANCE_UNIT,
    ) -> "ResistanceChain":
        require_unit(resistance_unit, RESISTANCE_UNIT, field="resistance")
        aerodynamic = validate_resistance(
            aerodynamic_resistance,
            field="aerodynamic_resistance",
            unit=resistance_unit,
        )
        boundary = validate_resistance(
            boundary_layer_resistance,
            field="boundary_layer_resistance",
            unit=resistance_unit,
        )
        canopy = validate_resistance(
            canopy_resistance,
            field="canopy_resistance",
            unit=resistance_unit,
        )
        total = total_resistance(
            aerodynamic,
            boundary,
            canopy,
            resistance_unit=resistance_unit,
        )
        exchange_velocity = exchange_coefficient(
            total,
            resistance_unit=resistance_unit,
        )
        return cls(
            aerodynamic_resistance=aerodynamic,
            boundary_layer_resistance=boundary,
            canopy_resistance=canopy,
            total_resistance=total,
            exchange_velocity=exchange_velocity,
            resistance_unit=resistance_unit,
            exchange_velocity_unit=EXCHANGE_VELOCITY_UNIT,
        )

    @classmethod
    def from_parameter_database(
        cls,
        database: ParameterDatabaseProtocol,
        coordinates: ResistanceCoordinates,
        *,
        parameter_names: Mapping[str, str] | None = None,
    ) -> "ResistanceChain":
        """Resolve component resistances through the P6.1 lookup interface.

        The current main branch does not contain the unmerged P6.1 database
        package, so this method depends only on its public structural protocol.
        It calls `production=False`, rejects ACTIVE provenance, and never
        supplies a default or converts a missing placeholder into zero.
        """

        names = dict(DEFAULT_PARAMETER_NAMES)
        if parameter_names is not None:
            names.update(parameter_names)
        coordinate_mapping = coordinates.as_mapping()
        components = {
            component: _lookup_required(database, name, coordinate_mapping)
            for component, name in names.items()
        }
        return cls.from_components(
            components["aerodynamic_resistance"],
            components["boundary_layer_resistance"],
            components["canopy_resistance"],
        )


def signed_leaf_exchange_flux(
    forcing: AtmosphericHTOForcing,
    resistance: ResistanceState,
    equilibrium_air_concentration_bq_m3: float,
    *,
    concentration_unit: str = CONCENTRATION_UNIT,
) -> LeafExchangeFlux:
    """Return the signed air/leaf boundary flux placeholder.

    Positive values are air to leaf and negative values are leaf to air. The
    equilibrium concentration is an atmospheric-equivalent input supplied by
    a later TFWT contract; this function does not compute TFWT, OBT, roots, or
    soil coupling.
    """

    validate_forcing(forcing)
    require_unit(
        concentration_unit,
        CONCENTRATION_UNIT,
        field="air/equilibrium concentration",
    )
    equilibrium = require_finite(
        equilibrium_air_concentration_bq_m3,
        field="equilibrium_air_concentration_bq_m3",
    )
    if equilibrium < 0.0:
        raise ValueError("equilibrium air concentration must be non-negative")
    flux = resistance.exchange_velocity * (
        forcing.air_hto_concentration_bq_m3 - equilibrium
    )
    return LeafExchangeFlux(air_to_leaf_flux_bq_m2_s=flux, flux_unit=FLUX_UNIT)


def total_resistance(
    aerodynamic_resistance: float,
    boundary_layer_resistance: float,
    canopy_resistance: float,
    *,
    resistance_unit: str = RESISTANCE_UNIT,
) -> float:
    """Compute `r_a + r_b + r_c` after exact unit and sign checks."""

    values = (
        validate_resistance(
            aerodynamic_resistance,
            field="aerodynamic_resistance",
            unit=resistance_unit,
        ),
        validate_resistance(
            boundary_layer_resistance,
            field="boundary_layer_resistance",
            unit=resistance_unit,
        ),
        validate_resistance(
            canopy_resistance,
            field="canopy_resistance",
            unit=resistance_unit,
        ),
    )
    total = sum(values)
    if total <= 0.0:
        raise InvalidResistanceError("total resistance must be positive")
    return total


def exchange_coefficient(
    total_resistance_value: float,
    *,
    resistance_unit: str = RESISTANCE_UNIT,
    exchange_velocity_unit: str = EXCHANGE_VELOCITY_UNIT,
) -> float:
    """Compute `g_ex = 1 / r_tot` without implicit unit conversion."""

    total = validate_resistance(
        total_resistance_value,
        field="total_resistance",
        unit=resistance_unit,
    )
    if exchange_velocity_unit != EXCHANGE_VELOCITY_UNIT:
        raise ValueError(
            f"exchange_velocity requires unit {EXCHANGE_VELOCITY_UNIT!r}"
        )
    return 1.0 / total


def build_resistance_chain(
    aerodynamic_resistance: float,
    boundary_layer_resistance: float,
    canopy_resistance: float,
    *,
    resistance_unit: str = RESISTANCE_UNIT,
) -> ResistanceChain:
    """Functional entry point for explicit component resistances."""

    return ResistanceChain.from_components(
        aerodynamic_resistance,
        boundary_layer_resistance,
        canopy_resistance,
        resistance_unit=resistance_unit,
    )


leaf_exchange_flux = signed_leaf_exchange_flux


__all__ = [
    "DEFAULT_PARAMETER_NAMES",
    "ParameterDatabaseProtocol",
    "ResistanceChain",
    "build_resistance_chain",
    "exchange_coefficient",
    "leaf_exchange_flux",
    "signed_leaf_exchange_flux",
    "total_resistance",
]
