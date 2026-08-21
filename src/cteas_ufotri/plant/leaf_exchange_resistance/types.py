"""Typed interfaces for the V3 leaf-exchange resistance subsystem."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from .validation import (
    CONCENTRATION_UNIT,
    EXCHANGE_VELOCITY_UNIT,
    FLUX_UNIT,
    RESISTANCE_UNIT,
    require_finite,
    require_unit,
    validate_exchange_velocity,
    validate_forcing,
    validate_provenance,
    validate_resistance,
)


@dataclass(frozen=True)
class ForcingProvenance:
    """Immutable provenance required by AtmosphericHTOForcing."""

    source_id: str
    source_version: str
    artifact_sha256: str
    spatial_reference: str
    temporal_resolution_s: float

    def __post_init__(self) -> None:
        validate_provenance(self)


@dataclass(frozen=True)
class AtmosphericHTOForcing:
    """Validated forcing boundary; no dispersion or weather repair is done."""

    time: datetime
    air_hto_concentration_bq_m3: float
    air_temperature_k: float
    relative_humidity: float
    provenance: ForcingProvenance
    wind_speed_m_s: float | None = None
    shortwave_radiation_w_m2: float | None = None
    boundary_layer_height_m: float | None = None
    day_night: str | None = None

    def __post_init__(self) -> None:
        validate_forcing(self)


@dataclass(frozen=True)
class ResistanceCoordinates:
    """Future lookup coordinates; no interpolation or fallback is implicit."""

    crop: str
    growth_stage: str
    temperature_k: float
    relative_humidity: float
    day_night: str | None = None

    def as_mapping(self) -> Mapping[str, object]:
        temperature = require_finite(self.temperature_k, field="temperature_k")
        humidity = require_finite(
            self.relative_humidity,
            field="relative_humidity",
        )
        if temperature <= 0.0:
            raise ValueError("temperature_k must be positive")
        if not 0.0 <= humidity <= 1.0:
            raise ValueError("relative_humidity must be in [0, 1]")
        if not self.crop.strip() or not self.growth_stage.strip():
            raise ValueError("crop and growth_stage are required")
        if self.day_night is not None and self.day_night not in {"day", "night"}:
            raise ValueError("day_night must be 'day', 'night', or None")
        result: dict[str, object] = {
            "crop": self.crop,
            "growth_stage": self.growth_stage,
            "temperature": temperature,
            "humidity": humidity,
        }
        if self.day_night is not None:
            result["period"] = self.day_night
        return result


@dataclass(frozen=True)
class ResistanceState:
    """Resistance-chain state with explicit SI units."""

    aerodynamic_resistance: float
    boundary_layer_resistance: float
    canopy_resistance: float
    total_resistance: float
    exchange_velocity: float
    resistance_unit: str = RESISTANCE_UNIT
    exchange_velocity_unit: str = EXCHANGE_VELOCITY_UNIT

    def __post_init__(self) -> None:
        validate_resistance(
            self.aerodynamic_resistance,
            field="aerodynamic_resistance",
            unit=self.resistance_unit,
        )
        validate_resistance(
            self.boundary_layer_resistance,
            field="boundary_layer_resistance",
            unit=self.resistance_unit,
        )
        validate_resistance(
            self.canopy_resistance,
            field="canopy_resistance",
            unit=self.resistance_unit,
        )
        validate_resistance(
            self.total_resistance,
            field="total_resistance",
            unit=self.resistance_unit,
        )
        validate_exchange_velocity(
            self.exchange_velocity,
            unit=self.exchange_velocity_unit,
        )
        expected_total = (
            self.aerodynamic_resistance
            + self.boundary_layer_resistance
            + self.canopy_resistance
        )
        if self.total_resistance != expected_total:
            raise ValueError("total_resistance must equal r_a + r_b + r_c")
        if self.exchange_velocity != 1.0 / self.total_resistance:
            raise ValueError("exchange_velocity must equal 1 / total_resistance")


@dataclass(frozen=True)
class LeafExchangeFlux:
    """Signed placeholder flux; positive is air to leaf, negative leaf to air."""

    air_to_leaf_flux_bq_m2_s: float
    flux_unit: str = FLUX_UNIT

    def __post_init__(self) -> None:
        require_unit(self.flux_unit, FLUX_UNIT, field="air_to_leaf_flux")
        require_finite(
            self.air_to_leaf_flux_bq_m2_s,
            field="air_to_leaf_flux_bq_m2_s",
        )

    @property
    def net_air_to_leaf_bq_m2_s(self) -> float:
        """Compatibility view of the single authoritative signed flux."""

        return self.air_to_leaf_flux_bq_m2_s

    @property
    def has_separate_reemission_flux(self) -> bool:
        """The placeholder deliberately exposes no second re-emission field."""

        return False


__all__ = [
    "AtmosphericHTOForcing",
    "CONCENTRATION_UNIT",
    "EXCHANGE_VELOCITY_UNIT",
    "FLUX_UNIT",
    "ForcingProvenance",
    "LeafExchangeFlux",
    "RESISTANCE_UNIT",
    "ResistanceCoordinates",
    "ResistanceState",
]
