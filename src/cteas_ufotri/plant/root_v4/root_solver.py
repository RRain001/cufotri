"""Non-mutating V4 three-layer root HTO transfer core."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..soil_v4 import ThreeLayerSoilState
from .root_state import LayerRootTransferV4, RootWaterFluxProvenanceV4, ThreeLayerRootFluxPlanV4
from .validation import (
    HTO_CONCENTRATION_UNIT,
    WATER_FLUX_UNIT,
    RootV4InputError,
    require_text,
    require_unit,
    validate_interval,
    validate_nonnegative_triplet,
    validate_provenance,
    validate_utc_timestamp,
)


@dataclass(frozen=True)
class ThreeLayerRootWaterFluxForcingV4:
    """Explicit interval-start layer water uptake forcing.

    The forcing contains q_w,i only. It does not infer transpiration, hydrology,
    layer fractions, or the UFOTRI short-term delay.
    """

    plant_identifier: str
    timestamp: datetime
    water_uptake_fluxes_m_s: tuple[float, float, float]
    provenance: RootWaterFluxProvenanceV4
    water_flux_unit: str = WATER_FLUX_UNIT
    interval_semantics: str = "start"

    def __post_init__(self) -> None:
        require_text(self.plant_identifier, field="plant_identifier")
        validate_utc_timestamp(self.timestamp, field="forcing.timestamp")
        validate_nonnegative_triplet(self.water_uptake_fluxes_m_s, field="water_uptake_fluxes_m_s")
        require_unit(self.water_flux_unit, WATER_FLUX_UNIT, field="water_uptake_flux")
        if self.interval_semantics != "start":
            raise RootV4InputError("forcing.interval_semantics must be 'start'")
        if not isinstance(self.provenance, RootWaterFluxProvenanceV4):
            raise RootV4InputError("forcing.provenance must be RootWaterFluxProvenanceV4")
        validate_provenance(self.provenance)


class ThreeLayerRootFluxSolverV4:
    """Evaluate J_root,i = q_w,i * C_w,i(S_n) without mutating reservoirs."""

    def plan(
        self,
        soil_state: ThreeLayerSoilState,
        forcing: ThreeLayerRootWaterFluxForcingV4,
        interval_seconds: float,
    ) -> ThreeLayerRootFluxPlanV4:
        if not isinstance(soil_state, ThreeLayerSoilState):
            raise RootV4InputError("soil_state must be ThreeLayerSoilState")
        if not isinstance(forcing, ThreeLayerRootWaterFluxForcingV4):
            raise RootV4InputError("forcing must be ThreeLayerRootWaterFluxForcingV4")
        if forcing.timestamp != soil_state.timestamp:
            raise RootV4InputError("forcing.timestamp must equal soil_state.timestamp for interval-start forcing")
        interval = validate_interval(interval_seconds)
        q_values = validate_nonnegative_triplet(forcing.water_uptake_fluxes_m_s, field="water_uptake_fluxes_m_s")

        transfers: list[LayerRootTransferV4] = []
        for layer, q_w in zip(soil_state.layers, q_values, strict=True):
            require_unit(layer.hto_concentration_unit, HTO_CONCENTRATION_UNIT, field=f"{layer.layer_id}.hto_concentration")
            concentration = layer.hto_concentration_bq_m3_water
            hto_flux = q_w * concentration
            water_transfer = q_w * interval
            hto_transfer = hto_flux * interval

            if water_transfer >= layer.water_inventory_m:
                raise RootV4InputError(
                    f"{layer.layer_id} root water uptake over the interval would exhaust layer water"
                )
            tolerance = 1.0e-12 * max(1.0, layer.hto_inventory_bq_m2)
            if hto_transfer > layer.hto_inventory_bq_m2 + tolerance:
                raise RootV4InputError(
                    f"{layer.layer_id} root HTO uptake over the interval exceeds available HTO inventory"
                )

            remaining_water = layer.water_inventory_m - water_transfer
            remaining_hto = max(layer.hto_inventory_bq_m2 - hto_transfer, 0.0)
            transfers.append(
                LayerRootTransferV4(
                    layer_id=layer.layer_id,
                    water_uptake_flux_m_s=q_w,
                    soil_hto_concentration_bq_m3_water=concentration,
                    hto_uptake_flux_bq_m2_s=hto_flux,
                    water_transfer_m=water_transfer,
                    hto_transfer_bq_m2=hto_transfer,
                    source_water_inventory_m=layer.water_inventory_m,
                    source_hto_inventory_bq_m2=layer.hto_inventory_bq_m2,
                    remaining_water_if_applied_m=remaining_water,
                    remaining_hto_if_applied_bq_m2=remaining_hto,
                    water_balance_residual_m=(
                        layer.water_inventory_m - water_transfer - remaining_water
                    ),
                    hto_balance_residual_bq_m2=(
                        layer.hto_inventory_bq_m2 - hto_transfer - remaining_hto
                    ),
                )
            )

        return ThreeLayerRootFluxPlanV4(
            plant_identifier=forcing.plant_identifier,
            soil_identifier=soil_state.soil_identifier,
            timestamp_start=soil_state.timestamp,
            timestamp_end=soil_state.timestamp + timedelta(seconds=interval),
            interval_seconds=interval,
            layer_transfers=tuple(transfers),  # type: ignore[arg-type]
            provenance=forcing.provenance,
            area_basis=soil_state.area_basis,
        )

    def step(
        self,
        soil_state: ThreeLayerSoilState,
        forcing: ThreeLayerRootWaterFluxForcingV4,
        interval_seconds: float,
    ) -> ThreeLayerRootFluxPlanV4:
        """Alias for the public non-mutating transfer-plan operation."""

        return self.plan(soil_state, forcing, interval_seconds)


__all__ = ["ThreeLayerRootFluxSolverV4", "ThreeLayerRootWaterFluxForcingV4"]
