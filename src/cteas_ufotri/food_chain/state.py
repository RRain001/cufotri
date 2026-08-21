"""Immutable state and coupling records for the V3-P3 food-chain framework.

The records in this module carry inventories and interface inputs only.  They
do not infer plant uptake, transfer factors, harvest rates, or dose quantities.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import math
from typing import Any


class FoodChainStateError(ValueError):
    """Raised when a V3-P3 state or coupling record is invalid."""


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise FoodChainStateError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise FoodChainStateError(f"{name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise FoodChainStateError(f"{name} must be finite")
    return numeric


def _nonnegative(value: Any, name: str) -> float:
    numeric = _finite(value, name)
    if numeric < 0.0:
        raise FoodChainStateError(f"{name} must be non-negative")
    return numeric


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FoodChainStateError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class PlantState:
    """Plant activity and dry-matter inventory on one declared plant basis.

    ``total_activity``, ``tfwt_activity``, and ``obt_activity`` are activity
    inventories in Bq.  ``dry_matter_inventory`` is kg dry matter on the same
    plant basis.  The total is explicit and must equal TFWT plus OBT; no
    activity concentration or transfer factor is inferred here.
    """

    plant_id: str
    growth_stage: str
    total_activity: float
    tfwt_activity: float
    obt_activity: float
    dry_matter_inventory: float

    def __post_init__(self) -> None:
        _identifier(self.plant_id, "plant_id")
        _identifier(self.growth_stage, "growth_stage")
        total = _nonnegative(self.total_activity, "total_activity")
        tfwt = _nonnegative(self.tfwt_activity, "tfwt_activity")
        obt = _nonnegative(self.obt_activity, "obt_activity")
        _nonnegative(self.dry_matter_inventory, "dry_matter_inventory")
        tolerance = max(1.0e-12, 1.0e-12 * max(total, tfwt, obt, 1.0))
        if abs(total - tfwt - obt) > tolerance:
            raise FoodChainStateError(
                "total_activity must equal tfwt_activity + obt_activity"
            )

    @property
    def tfwt_inventory(self) -> float:
        """Alias for the TFWT activity inventory in Bq."""

        return float(self.tfwt_activity)

    @property
    def obt_inventory(self) -> float:
        """Alias for the OBT activity inventory in Bq."""

        return float(self.obt_activity)

    @property
    def total_inventory(self) -> float:
        """Alias for the total plant activity inventory in Bq."""

        return float(self.total_activity)

    def copy(self, **changes: Any) -> "PlantState":
        """Return a validated immutable copy."""

        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class LeafActivityInput:
    """Activity supplied by the leaf-exchange coupling seam.

    Activities are integrated Bq inputs for the current framework interval;
    ``exposure_time_s`` is retained as metadata and is not converted by this
    framework.
    """

    tfwt_activity: float
    obt_activity: float
    exposure_time_s: float

    def __post_init__(self) -> None:
        _nonnegative(self.tfwt_activity, "tfwt_activity")
        _nonnegative(self.obt_activity, "obt_activity")
        _nonnegative(self.exposure_time_s, "exposure_time_s")


@dataclass(frozen=True, slots=True)
class RootZoneActivityInput:
    """Read-only soil coupling seam; no root uptake is implied."""

    root_zone_activity: float
    soil_water_activity: float
    status: str = "SEAM_ONLY_NO_ROOT_UPTAKE"

    def __post_init__(self) -> None:
        _nonnegative(self.root_zone_activity, "root_zone_activity")
        _nonnegative(self.soil_water_activity, "soil_water_activity")
        _identifier(self.status, "status")


@dataclass(frozen=True, slots=True)
class PlantInputs:
    """Accumulated typed inputs for one plant-framework advance.

    Leaf inputs are accepted as plant activity inputs.  Root-zone and
    soil-water values are retained for the coupling seam only; they are not
    converted to plant activity and therefore cannot create root uptake.
    """

    leaf_tfwt_activity: float = 0.0
    leaf_obt_activity: float = 0.0
    plant_exposure_time_s: float = 0.0
    root_zone_activity: float = 0.0
    soil_water_activity: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "leaf_tfwt_activity",
            "leaf_obt_activity",
            "plant_exposure_time_s",
            "root_zone_activity",
            "soil_water_activity",
        ):
            _nonnegative(getattr(self, name), name)

    @property
    def tfwt_activity(self) -> float:
        """Compatibility alias for the accumulated leaf TFWT input."""

        return float(self.leaf_tfwt_activity)

    @property
    def obt_activity(self) -> float:
        """Compatibility alias for the accumulated leaf OBT input."""

        return float(self.leaf_obt_activity)

    @property
    def exposure_time_s(self) -> float:
        """Compatibility alias for accumulated plant exposure time."""

        return float(self.plant_exposure_time_s)

    @property
    def leaf_input(self) -> float:
        """Return integrated leaf activity input in Bq."""

        return float(self.leaf_tfwt_activity) + float(self.leaf_obt_activity)

    def receive_leaf_activity(
        self,
        tfwt_activity: float,
        obt_activity: float,
        plant_exposure_time_s: float,
    ) -> "PlantInputs":
        """Append leaf activity while retaining exposure metadata."""

        received = LeafActivityInput(
            tfwt_activity, obt_activity, plant_exposure_time_s
        )
        return replace(
            self,
            leaf_tfwt_activity=self.leaf_tfwt_activity + received.tfwt_activity,
            leaf_obt_activity=self.leaf_obt_activity + received.obt_activity,
            plant_exposure_time_s=(
                self.plant_exposure_time_s + received.exposure_time_s
            ),
        )

    def receive_root_zone_activity(
        self,
        root_zone_activity: float,
        soil_water_activity: float,
    ) -> "PlantInputs":
        """Append soil values to the seam without performing root uptake."""

        received = RootZoneActivityInput(root_zone_activity, soil_water_activity)
        return replace(
            self,
            root_zone_activity=self.root_zone_activity + received.root_zone_activity,
            soil_water_activity=self.soil_water_activity + received.soil_water_activity,
        )


def receive_leaf_activity(
    tfwt_activity: float,
    obt_activity: float,
    plant_exposure_time_s: float,
    *,
    inputs: PlantInputs | None = None,
) -> PlantInputs:
    """Create or extend the leaf-exchange coupling input record."""

    base = PlantInputs() if inputs is None else inputs
    if not isinstance(base, PlantInputs):
        raise FoodChainStateError("inputs must be a PlantInputs record")
    return base.receive_leaf_activity(
        tfwt_activity, obt_activity, plant_exposure_time_s
    )


def receive_root_zone_activity(
    root_zone_activity: float,
    soil_water_activity: float,
    *,
    inputs: PlantInputs | None = None,
) -> PlantInputs:
    """Create or extend the soil coupling seam without root uptake."""

    base = PlantInputs() if inputs is None else inputs
    if not isinstance(base, PlantInputs):
        raise FoodChainStateError("inputs must be a PlantInputs record")
    return base.receive_root_zone_activity(root_zone_activity, soil_water_activity)


@dataclass(frozen=True, slots=True)
class HarvestProduct:
    """Edible product boundary record, with no human-consumption behavior."""

    crop_id: str
    harvest_time: datetime
    edible_activity: float
    edible_mass: float

    def __post_init__(self) -> None:
        _identifier(self.crop_id, "crop_id")
        if not isinstance(self.harvest_time, datetime):
            raise FoodChainStateError("harvest_time must be a datetime")
        _nonnegative(self.edible_activity, "edible_activity")
        mass = _nonnegative(self.edible_mass, "edible_mass")
        if mass == 0.0 and self.edible_activity != 0.0:
            raise FoodChainStateError(
                "positive edible_activity requires positive edible_mass"
            )

    @property
    def activity_concentration(self) -> float:
        """Return edible activity concentration in Bq kg-1 dry matter."""

        if self.edible_mass == 0.0:
            return 0.0
        return float(self.edible_activity) / float(self.edible_mass)

    @classmethod
    def from_crop(
        cls,
        crop: "CropCompartment",
        harvest_time: datetime,
    ) -> "HarvestProduct":
        if not isinstance(crop, CropCompartment):
            raise FoodChainStateError("crop must be a CropCompartment")
        fraction = crop.edible_fraction
        return cls(
            crop_id=crop.crop_id,
            harvest_time=harvest_time,
            edible_activity=crop.plant_state.total_activity * fraction,
            edible_mass=crop.plant_state.dry_matter_inventory * fraction,
        )


@dataclass(frozen=True, slots=True)
class CropCompartment:
    """Crop-agnostic plant compartment with an explicit edible fraction."""

    crop_id: str
    plant_state: PlantState
    edible_fraction: float
    harvest_state: str = "NOT_HARVESTED"

    def __post_init__(self) -> None:
        _identifier(self.crop_id, "crop_id")
        if not isinstance(self.plant_state, PlantState):
            raise FoodChainStateError("plant_state must be a PlantState")
        fraction = _finite(self.edible_fraction, "edible_fraction")
        if not 0.0 <= fraction <= 1.0:
            raise FoodChainStateError("edible_fraction must be in the interval [0, 1]")
        _identifier(self.harvest_state, "harvest_state")

    def copy(self, **changes: Any) -> "CropCompartment":
        """Return a validated immutable crop copy."""

        return replace(self, **changes)

    def harvest(self, harvest_time: datetime) -> HarvestProduct:
        """Create an edible product boundary record for this crop."""

        return HarvestProduct.from_crop(self, harvest_time)

    def mark_harvested(self) -> "CropCompartment":
        """Return a copy with an explicit harvested state."""

        return replace(self, harvest_state="HARVESTED")
