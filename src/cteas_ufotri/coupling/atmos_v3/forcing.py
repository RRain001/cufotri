"""V3 P7 atmospheric forcing record and leaf/soil interface adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...plant.leaf_exchange_resistance import ForcingProvenance
from .metadata import AtmosphericForcingMetadata
from .validation import (
    AIR_CONCENTRATION_UNIT,
    DEPOSITION_FLUX_UNIT,
    HUMIDITY_UNIT,
    PRECIPITATION_UNIT,
    TEMPERATURE_UNIT,
    WIND_SPEED_UNIT,
    validate_forcing,
    validate_location,
)


@dataclass(frozen=True, init=False)
class AtmosphericHTOForcing:
    """Immutable atmospheric forcing at the P7 coupling boundary.

    The canonical concentration name is ``air_hto_concentration``. The
    ``air_ht0_concentration`` spelling is retained as a compatibility alias
    because the P7 contract used that spelling in its initial draft. Both
    fields are stored with the same value and are validated for agreement.
    """

    timestamp: datetime
    location: str | tuple[float, float]
    air_hto_concentration: float
    deposition_flux: float
    temperature: float
    humidity: float
    wind_speed: float
    precipitation: float
    source: str
    provenance: ForcingProvenance
    air_ht0_concentration: float
    air_hto_concentration_unit: str
    air_ht0_concentration_unit: str
    deposition_flux_unit: str
    temperature_unit: str
    humidity_unit: str
    wind_speed_unit: str
    precipitation_unit: str
    metadata: AtmosphericForcingMetadata | None

    def __init__(
        self,
        timestamp: datetime,
        location: str | tuple[float, float] | list[float],
        air_hto_concentration: float | None = None,
        deposition_flux: float | None = None,
        temperature: float | None = None,
        humidity: float | None = None,
        wind_speed: float | None = None,
        precipitation: float | None = None,
        source: str | None = None,
        provenance: ForcingProvenance | None = None,
        *,
        air_ht0_concentration: float | None = None,
        air_hto_concentration_unit: str = AIR_CONCENTRATION_UNIT,
        air_ht0_concentration_unit: str = AIR_CONCENTRATION_UNIT,
        deposition_flux_unit: str = DEPOSITION_FLUX_UNIT,
        temperature_unit: str = TEMPERATURE_UNIT,
        humidity_unit: str = HUMIDITY_UNIT,
        wind_speed_unit: str = WIND_SPEED_UNIT,
        precipitation_unit: str = PRECIPITATION_UNIT,
        metadata: AtmosphericForcingMetadata | None = None,
    ) -> None:
        if air_hto_concentration is None and air_ht0_concentration is None:
            raise ValueError(
                "air_hto_concentration or air_ht0_concentration is required"
            )
        if air_hto_concentration is None:
            air_hto_concentration = air_ht0_concentration
        if air_ht0_concentration is None:
            air_ht0_concentration = air_hto_concentration
        for field, value in (
            ("deposition_flux", deposition_flux),
            ("temperature", temperature),
            ("humidity", humidity),
            ("wind_speed", wind_speed),
            ("precipitation", precipitation),
            ("source", source),
        ):
            if value is None:
                raise ValueError(f"{field} is required")
        if provenance is None:
            raise ValueError("provenance is required")

        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "location", validate_location(location))
        object.__setattr__(self, "air_hto_concentration", air_hto_concentration)
        object.__setattr__(self, "air_ht0_concentration", air_ht0_concentration)
        object.__setattr__(self, "deposition_flux", deposition_flux)
        object.__setattr__(self, "temperature", temperature)
        object.__setattr__(self, "humidity", humidity)
        object.__setattr__(self, "wind_speed", wind_speed)
        object.__setattr__(self, "precipitation", precipitation)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "air_hto_concentration_unit", air_hto_concentration_unit)
        object.__setattr__(self, "air_ht0_concentration_unit", air_ht0_concentration_unit)
        object.__setattr__(self, "deposition_flux_unit", deposition_flux_unit)
        object.__setattr__(self, "temperature_unit", temperature_unit)
        object.__setattr__(self, "humidity_unit", humidity_unit)
        object.__setattr__(self, "wind_speed_unit", wind_speed_unit)
        object.__setattr__(self, "precipitation_unit", precipitation_unit)
        object.__setattr__(self, "metadata", metadata)
        validate_forcing(self)

    def to_leaf_forcing(self) -> Any:
        """Adapt to the existing leaf-resistance forcing input only."""

        from ...plant.leaf_exchange_resistance import AtmosphericHTOForcing as LeafForcing

        return LeafForcing(
            time=self.timestamp,
            air_hto_concentration_bq_m3=self.air_hto_concentration,
            air_temperature_k=self.temperature,
            relative_humidity=self.humidity,
            wind_speed_m_s=self.wind_speed,
            provenance=self.provenance,
        )

    def to_soil_forcing(self) -> Any:
        """Adapt atmospheric deposition to the existing soil forcing input."""

        from ...plant.soil_v3 import SoilForcing

        return SoilForcing(deposition_flux_bq_m2_s=self.deposition_flux)

    def leaf_forcing(self) -> Any:
        """Compatibility alias for :meth:`to_leaf_forcing`."""

        return self.to_leaf_forcing()

    def soil_forcing(self) -> Any:
        """Compatibility alias for :meth:`to_soil_forcing`."""

        return self.to_soil_forcing()


__all__ = ["AtmosphericHTOForcing"]
