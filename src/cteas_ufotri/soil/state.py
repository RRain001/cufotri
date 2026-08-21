"""Explicit V3-P2 three-layer soil state and atmospheric forcing."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import math
from typing import Any


class SoilStateError(ValueError):
    """Raised when a soil state, layer, or forcing record is invalid."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise SoilStateError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise SoilStateError(f"{name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise SoilStateError(f"{name} must be finite")
    return numeric


def _nonnegative(value: Any, name: str) -> float:
    numeric = _finite(value, name)
    if numeric < 0.0:
        raise SoilStateError(f"{name} must be non-negative")
    return numeric


@dataclass(frozen=True, slots=True)
class SoilLayer:
    """One ordered soil layer on a declared reference-area basis.

    ``water_inventory`` is water storage in m (equivalent to m3 m-2), and
    ``hto_activity`` is HTO inventory in Bq m-2.  The derived water
    concentration is Bq m-3 water.  Layer geometry is explicit in metres.
    """

    layer_id: int
    depth_top: float
    depth_bottom: float
    water_inventory: float
    hto_activity: float

    def __post_init__(self) -> None:
        if isinstance(self.layer_id, bool) or not isinstance(self.layer_id, int):
            raise SoilStateError("layer_id must be an integer")
        if self.layer_id < 1:
            raise SoilStateError("layer_id must be positive")
        top = _finite(self.depth_top, "depth_top")
        bottom = _finite(self.depth_bottom, "depth_bottom")
        if top < 0.0 or bottom <= top:
            raise SoilStateError(
                "soil layer must satisfy 0 <= depth_top < depth_bottom"
            )
        water = _nonnegative(self.water_inventory, "water_inventory")
        activity = _nonnegative(self.hto_activity, "hto_activity")
        if water == 0.0 and activity > 0.0:
            raise SoilStateError(
                "positive soil-water HTO inventory requires positive water_inventory"
            )

    @property
    def depth(self) -> float:
        """Return layer thickness in m."""

        return float(self.depth_bottom) - float(self.depth_top)

    @property
    def water_content(self) -> float:
        """Return volumetric water content as a dimensionless ratio."""

        return float(self.water_inventory) / self.depth

    @property
    def hto_inventory(self) -> float:
        """Alias exposing the explicit HTO inventory contract in Bq m-2."""

        return float(self.hto_activity)

    @property
    def hto_concentration(self) -> float:
        """Return HTO concentration in soil water, in Bq m-3 water."""

        if self.water_inventory == 0.0:
            return 0.0
        return float(self.hto_activity) / float(self.water_inventory)

    def copy(self, **changes: Any) -> "SoilLayer":
        """Return a validated immutable layer copy."""

        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class SoilState:
    """Fixed three-layer soil profile with no shared leaf or global state."""

    layers: tuple[SoilLayer, SoilLayer, SoilLayer]
    current_time: datetime = field(default_factory=lambda: datetime(1970, 1, 1))
    delta_t: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.layers, tuple) or len(self.layers) != 3:
            raise SoilStateError("SoilState must contain exactly three layers")
        if any(not isinstance(layer, SoilLayer) for layer in self.layers):
            raise SoilStateError("SoilState layers must be SoilLayer records")
        identifiers = tuple(layer.layer_id for layer in self.layers)
        if identifiers != (1, 2, 3):
            raise SoilStateError(
                "SoilState layer IDs must be the ordered fixed interface (1, 2, 3)"
            )
        if not isinstance(self.current_time, datetime):
            raise SoilStateError("current_time must be a datetime")
        _nonnegative(self.delta_t, "delta_t")

    @property
    def total_water_inventory(self) -> float:
        """Return total water storage in m."""

        return sum(layer.water_inventory for layer in self.layers)

    @property
    def total_hto_inventory(self) -> float:
        """Return total soil HTO inventory in Bq m-2."""

        return sum(layer.hto_inventory for layer in self.layers)

    def layer(self, layer_id: int) -> SoilLayer:
        """Return one layer by explicit ID, rejecting implicit indices."""

        if layer_id not in (1, 2, 3):
            raise SoilStateError("layer_id must be one of 1, 2, or 3")
        return self.layers[layer_id - 1]

    def copy(self, **changes: Any) -> "SoilState":
        """Return a validated immutable profile copy."""

        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class SoilForcing:
    """Atmospheric HTO forcing for one soil step.

    ``hto_air_concentration`` is Bq m-3 air. ``deposition_flux`` is an
    externally supplied Bq m-2 s-1 boundary flux. The P2 framework does not
    derive deposition from air concentration.
    """

    hto_air_concentration: float
    deposition_flux: float

    def __post_init__(self) -> None:
        _nonnegative(self.hto_air_concentration, "hto_air_concentration")
        _nonnegative(self.deposition_flux, "deposition_flux")

    @property
    def air_hto_concentration(self) -> float:
        """Compatibility-readable name for the atmospheric concentration."""

        return float(self.hto_air_concentration)

    @property
    def deposition_flux_bq_m2_s(self) -> float:
        return float(self.deposition_flux)
