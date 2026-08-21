"""Explicit V3-P1 Leaf Exchange state and meteorological forcing."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import math
from typing import Any


class LeafExchangeStateError(ValueError):
    """Raised when a leaf-exchange state or forcing record is invalid."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise LeafExchangeStateError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise LeafExchangeStateError(f"{name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise LeafExchangeStateError(f"{name} must be finite")
    return numeric


def _nonnegative(value: Any, name: str) -> float:
    numeric = _finite(value, name)
    if numeric < 0.0:
        raise LeafExchangeStateError(f"{name} must be non-negative")
    return numeric


def _validate_meteorology(
    hto_air_concentration: Any,
    air_temperature: Any,
    relative_humidity: Any,
) -> None:
    _nonnegative(hto_air_concentration, "hto_air_concentration")
    if _finite(air_temperature, "air_temperature") <= 0.0:
        raise LeafExchangeStateError("air_temperature must be greater than 0 K")
    humidity = _finite(relative_humidity, "relative_humidity")
    if not 0.0 <= humidity <= 1.0:
        raise LeafExchangeStateError(
            "relative_humidity must be a fraction in the interval [0, 1]"
        )


@dataclass(frozen=True, slots=True)
class LeafExchangeForcing:
    """Meteorological forcing for one leaf-exchange step.

    Units are ``Bq m-3 air`` for HTO concentration, K for temperature, and
    a 0--1 fraction for relative humidity.  The forcing is immutable and has
    no hidden time or module-level state.
    """

    hto_air_concentration: float
    air_temperature: float
    relative_humidity: float

    def __post_init__(self) -> None:
        _validate_meteorology(
            self.hto_air_concentration,
            self.air_temperature,
            self.relative_humidity,
        )


@dataclass(frozen=True, slots=True)
class LeafExchangeState:
    """State of the two leaf activity pools at one time.

    ``tfwt_activity`` is ``Bq kg-1 fresh`` and ``obt_activity`` is
    ``Bq kg-1 dry``.  The two masses are kg on the module's declared leaf
    reference basis, so their products are total Bq inventories.  Air
    concentration is ``Bq m-3 air``.  Temperature is K, relative humidity is
    a fraction, ``delta_t`` is s, and ``current_time`` is a datetime.
    """

    hto_air_concentration: float
    air_temperature: float
    relative_humidity: float
    tfwt_activity: float
    obt_activity: float
    leaf_water_mass: float
    dry_matter_mass: float
    current_time: datetime
    delta_t: float = 0.0

    def __post_init__(self) -> None:
        _validate_meteorology(
            self.hto_air_concentration,
            self.air_temperature,
            self.relative_humidity,
        )
        _nonnegative(self.tfwt_activity, "tfwt_activity")
        _nonnegative(self.obt_activity, "obt_activity")
        if _finite(self.leaf_water_mass, "leaf_water_mass") <= 0.0:
            raise LeafExchangeStateError("leaf_water_mass must be greater than 0 kg")
        if _finite(self.dry_matter_mass, "dry_matter_mass") <= 0.0:
            raise LeafExchangeStateError("dry_matter_mass must be greater than 0 kg")
        if not isinstance(self.current_time, datetime):
            raise LeafExchangeStateError("current_time must be a datetime")
        _nonnegative(self.delta_t, "delta_t")

    @property
    def tfwt_inventory(self) -> float:
        """Return the TFWT inventory in Bq."""

        return float(self.tfwt_activity) * float(self.leaf_water_mass)

    @property
    def obt_inventory(self) -> float:
        """Return the OBT inventory in Bq."""

        return float(self.obt_activity) * float(self.dry_matter_mass)

    @property
    def total_inventory(self) -> float:
        """Return the total leaf inventory in Bq."""

        return self.tfwt_inventory + self.obt_inventory

    def copy(self, **changes: Any) -> "LeafExchangeState":
        """Return a validated copy with explicitly supplied field changes."""

        return replace(self, **changes)
