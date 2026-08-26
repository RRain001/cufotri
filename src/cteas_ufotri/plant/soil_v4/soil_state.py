"""Immutable opt-in V4 three-layer soil water and HTO state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import json
from typing import Any, Mapping

from .validation import (
    CANONICAL_LAYER_GEOMETRY,
    DEPTH_UNIT,
    SOIL_CONCENTRATION_UNIT,
    SOIL_INVENTORY_UNIT,
    WATER_INVENTORY_UNIT,
    SoilV4StateError,
    require_finite,
    require_unit,
    validate_layer_geometry,
    validate_provenance,
    validate_utc_timestamp,
)


@dataclass(frozen=True)
class SoilV4Provenance:
    source_id: str
    source_version: str
    artifact_sha256: str
    spatial_reference: str
    temporal_resolution_s: float

    def __post_init__(self) -> None:
        validate_provenance(self)


@dataclass(frozen=True)
class SoilLayerStateV4:
    layer_id: str
    depth_top_m: float
    depth_bottom_m: float
    water_inventory_m: float
    hto_inventory_bq_m2: float
    hto_concentration_bq_m3_water: float
    depth_unit: str = DEPTH_UNIT
    water_inventory_unit: str = WATER_INVENTORY_UNIT
    hto_inventory_unit: str = SOIL_INVENTORY_UNIT
    hto_concentration_unit: str = SOIL_CONCENTRATION_UNIT

    def __post_init__(self) -> None:
        require_unit(self.depth_unit, DEPTH_UNIT, field="layer_depth")
        require_unit(self.water_inventory_unit, WATER_INVENTORY_UNIT, field="water_inventory")
        require_unit(self.hto_inventory_unit, SOIL_INVENTORY_UNIT, field="hto_inventory")
        require_unit(self.hto_concentration_unit, SOIL_CONCENTRATION_UNIT, field="hto_concentration")
        validate_layer_geometry(self.layer_id, self.depth_top_m, self.depth_bottom_m)
        water = require_finite(self.water_inventory_m, field=f"{self.layer_id}.water_inventory_m")
        activity = require_finite(self.hto_inventory_bq_m2, field=f"{self.layer_id}.hto_inventory_bq_m2")
        concentration = require_finite(
            self.hto_concentration_bq_m3_water,
            field=f"{self.layer_id}.hto_concentration_bq_m3_water",
        )
        if water <= 0.0:
            raise SoilV4StateError(f"{self.layer_id}.water_inventory_m must be strictly positive")
        if activity < 0.0 or concentration < 0.0:
            raise SoilV4StateError(f"{self.layer_id} HTO values must be non-negative")
        expected = activity / water
        tolerance = 1.0e-12 * max(1.0, abs(expected))
        if abs(concentration - expected) > tolerance:
            raise SoilV4StateError(
                f"{self.layer_id} concentration must equal HTO inventory divided by water inventory"
            )

    @classmethod
    def from_inventories(
        cls,
        *,
        layer_id: str,
        depth_top_m: float,
        depth_bottom_m: float,
        water_inventory_m: float,
        hto_inventory_bq_m2: float,
    ) -> "SoilLayerStateV4":
        water = require_finite(water_inventory_m, field=f"{layer_id}.water_inventory_m")
        activity = require_finite(hto_inventory_bq_m2, field=f"{layer_id}.hto_inventory_bq_m2")
        if water <= 0.0:
            raise SoilV4StateError(f"{layer_id}.water_inventory_m must be strictly positive")
        if activity < 0.0:
            raise SoilV4StateError(f"{layer_id}.hto_inventory_bq_m2 must be non-negative")
        return cls(
            layer_id=layer_id,
            depth_top_m=depth_top_m,
            depth_bottom_m=depth_bottom_m,
            water_inventory_m=water,
            hto_inventory_bq_m2=activity,
            hto_concentration_bq_m3_water=activity / water,
        )

    @property
    def thickness_m(self) -> float:
        return self.depth_bottom_m - self.depth_top_m

    def with_inventories(self, *, water_inventory_m: float, hto_inventory_bq_m2: float) -> "SoilLayerStateV4":
        water = require_finite(water_inventory_m, field=f"{self.layer_id}.water_inventory_m")
        activity = require_finite(hto_inventory_bq_m2, field=f"{self.layer_id}.hto_inventory_bq_m2")
        if water <= 0.0:
            raise SoilV4StateError(f"{self.layer_id}.water_inventory_m must remain strictly positive")
        if activity < 0.0:
            raise SoilV4StateError(f"{self.layer_id}.hto_inventory_bq_m2 must remain non-negative")
        return replace(
            self,
            water_inventory_m=water,
            hto_inventory_bq_m2=activity,
            hto_concentration_bq_m3_water=activity / water,
        )


@dataclass(frozen=True)
class ThreeLayerSoilState:
    soil_identifier: str
    layers: tuple[SoilLayerStateV4, SoilLayerStateV4, SoilLayerStateV4]
    timestamp: datetime
    provenance: SoilV4Provenance
    area_basis: str = "soil_surface_area"
    version: str = "v4-three-layer-r1"

    def __post_init__(self) -> None:
        if not isinstance(self.soil_identifier, str) or not self.soil_identifier.strip():
            raise SoilV4StateError("soil_identifier is required")
        if not isinstance(self.area_basis, str) or not self.area_basis.strip():
            raise SoilV4StateError("area_basis is required")
        validate_utc_timestamp(self.timestamp)
        validate_provenance(self.provenance)
        if not isinstance(self.layers, tuple) or len(self.layers) != 3:
            raise SoilV4StateError("layers must be a tuple containing exactly L1, L2, and L3")
        for layer, expected in zip(self.layers, CANONICAL_LAYER_GEOMETRY, strict=True):
            if not isinstance(layer, SoilLayerStateV4):
                raise SoilV4StateError("all layers must be SoilLayerStateV4")
            if layer.layer_id != expected[0]:
                raise SoilV4StateError("layers must be ordered L1, L2, L3")
            validate_layer_geometry(layer.layer_id, layer.depth_top_m, layer.depth_bottom_m)

    @classmethod
    def from_inventories(
        cls,
        *,
        soil_identifier: str,
        water_inventories_m: tuple[float, float, float],
        hto_inventories_bq_m2: tuple[float, float, float],
        timestamp: datetime,
        provenance: SoilV4Provenance,
    ) -> "ThreeLayerSoilState":
        if len(water_inventories_m) != 3 or len(hto_inventories_bq_m2) != 3:
            raise SoilV4StateError("three water and three HTO inventories are required")
        layers = tuple(
            SoilLayerStateV4.from_inventories(
                layer_id=layer_id,
                depth_top_m=top,
                depth_bottom_m=bottom,
                water_inventory_m=water,
                hto_inventory_bq_m2=activity,
            )
            for (layer_id, top, bottom), water, activity in zip(
                CANONICAL_LAYER_GEOMETRY,
                water_inventories_m,
                hto_inventories_bq_m2,
                strict=True,
            )
        )
        return cls(
            soil_identifier=soil_identifier,
            layers=layers,  # type: ignore[arg-type]
            timestamp=timestamp,
            provenance=provenance,
        )

    @property
    def total_water_inventory_m(self) -> float:
        return sum(layer.water_inventory_m for layer in self.layers)

    @property
    def total_hto_inventory_bq_m2(self) -> float:
        return sum(layer.hto_inventory_bq_m2 for layer in self.layers)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "soil_identifier": self.soil_identifier,
            "layers": [
                {
                    "layer_id": layer.layer_id,
                    "depth_top_m": layer.depth_top_m,
                    "depth_bottom_m": layer.depth_bottom_m,
                    "water_inventory_m": layer.water_inventory_m,
                    "hto_inventory_bq_m2": layer.hto_inventory_bq_m2,
                    "hto_concentration_bq_m3_water": layer.hto_concentration_bq_m3_water,
                    "depth_unit": layer.depth_unit,
                    "water_inventory_unit": layer.water_inventory_unit,
                    "hto_inventory_unit": layer.hto_inventory_unit,
                    "hto_concentration_unit": layer.hto_concentration_unit,
                }
                for layer in self.layers
            ],
            "timestamp": self.timestamp.isoformat(),
            "provenance": {
                "source_id": self.provenance.source_id,
                "source_version": self.provenance.source_version,
                "artifact_sha256": self.provenance.artifact_sha256,
                "spatial_reference": self.provenance.spatial_reference,
                "temporal_resolution_s": self.provenance.temporal_resolution_s,
            },
            "area_basis": self.area_basis,
            "version": self.version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ThreeLayerSoilState":
        try:
            layers_payload = payload["layers"]
            if not isinstance(layers_payload, list) or len(layers_payload) != 3:
                raise SoilV4StateError("serialized layers must contain exactly three entries")
            layers = tuple(SoilLayerStateV4(**dict(item)) for item in layers_payload)
            provenance = SoilV4Provenance(**dict(payload["provenance"]))
            timestamp = datetime.fromisoformat(str(payload["timestamp"]))
            return cls(
                soil_identifier=str(payload["soil_identifier"]),
                layers=layers,  # type: ignore[arg-type]
                timestamp=timestamp,
                provenance=provenance,
                area_basis=str(payload.get("area_basis", "soil_surface_area")),
                version=str(payload.get("version", "v4-three-layer-r1")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, SoilV4StateError):
                raise
            raise SoilV4StateError(f"invalid serialized three-layer soil state: {exc}") from exc

    @classmethod
    def from_json(cls, payload: str) -> "ThreeLayerSoilState":
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise SoilV4StateError(f"invalid three-layer soil JSON: {exc}") from exc
        if not isinstance(decoded, Mapping):
            raise SoilV4StateError("serialized three-layer soil JSON must be an object")
        return cls.from_mapping(decoded)


__all__ = ["SoilLayerStateV4", "SoilV4Provenance", "ThreeLayerSoilState"]
