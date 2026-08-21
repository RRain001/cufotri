"""V3 TFWT state record for the storage-only solver."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from ..leaf_exchange_resistance import ForcingProvenance
from .validation import (
    TFWT_CONCENTRATION_UNIT,
    TFWT_INVENTORY_UNIT,
    TFWTStateError,
    WATER_CONTENT_UNIT,
    require_finite,
    validate_state,
)

if TYPE_CHECKING:
    from ..leaf_exchange_resistance import LeafExchangeFlux
    from ..root_v3 import RootFlux


@dataclass(frozen=True)
class TFWTState:
    """Plant TFWT state; no OBT, root, soil, or dose state is included."""

    plant_identifier: str
    crop: str
    growth_stage: str
    tfwt_concentration_bq_kg_water: float
    tfwt_inventory_bq_m2: float
    water_content_kg_m2: float
    time: datetime
    provenance: ForcingProvenance
    area_basis: str = "plant_area"
    concentration_unit: str = TFWT_CONCENTRATION_UNIT
    inventory_unit: str = TFWT_INVENTORY_UNIT
    water_content_unit: str = WATER_CONTENT_UNIT
    version: str = "v3-p6-2b-2"

    def __post_init__(self) -> None:
        validate_state(self)

    @classmethod
    def from_inventory(
        cls,
        *,
        plant_identifier: str,
        crop: str,
        growth_stage: str,
        tfwt_inventory_bq_m2: float,
        water_content_kg_m2: float,
        time: datetime,
        provenance: ForcingProvenance,
        area_basis: str = "plant_area",
    ) -> "TFWTState":
        """Construct a consistent state without changing the water basis."""

        inventory = require_finite(
            tfwt_inventory_bq_m2,
            field="tfwt_inventory_bq_m2",
        )
        water_content = require_finite(
            water_content_kg_m2,
            field="water_content_kg_m2",
        )
        if inventory < 0.0:
            raise TFWTStateError("tfwt_inventory_bq_m2 must be non-negative")
        if water_content <= 0.0:
            raise TFWTStateError("water_content_kg_m2 must be strictly positive")
        concentration = inventory / water_content
        return cls(
            plant_identifier=plant_identifier,
            crop=crop,
            growth_stage=growth_stage,
            tfwt_concentration_bq_kg_water=concentration,
            tfwt_inventory_bq_m2=inventory,
            water_content_kg_m2=water_content,
            time=time,
            provenance=provenance,
            area_basis=area_basis,
        )

    def with_inventory(
        self,
        *,
        tfwt_inventory_bq_m2: float,
        time: datetime,
    ) -> "TFWTState":
        """Return the next state at fixed water content and metadata."""

        return replace(
            self,
            tfwt_concentration_bq_kg_water=(
                tfwt_inventory_bq_m2 / self.water_content_kg_m2
            ),
            tfwt_inventory_bq_m2=tfwt_inventory_bq_m2,
            time=time,
        )

    def inventory(self) -> float:
        """Return the public TFWT inventory in ``Bq m^-2``."""

        return self.tfwt_inventory_bq_m2

    def activity_concentration(self) -> float:
        """Return the public TFWT concentration in ``Bq kg^-1 water``."""

        return self.tfwt_concentration_bq_kg_water

    def advance(
        self,
        dt: float,
        forcing: "LeafExchangeFlux",
        *,
        root_uptake_flux: "RootFlux | None" = None,
        water_loss_flux_bq_m2_s: float = 0.0,
        transformation_flux_bq_m2_s: float = 0.0,
    ) -> "TFWTState":
        """Advance through the frozen public flux interface.

        ``forcing`` is the signed P6.2B-1 ``LeafExchangeFlux``. The method
        intentionally delegates to the storage solver and never exposes its
        internal bookkeeping to downstream modules.
        """

        from .tfwt_solver import TFWTStorageSolver

        return TFWTStorageSolver().step(
            self,
            forcing,
            dt,
            root_uptake_flux=root_uptake_flux,
            water_loss_flux_bq_m2_s=water_loss_flux_bq_m2_s,
            transformation_flux_bq_m2_s=transformation_flux_bq_m2_s,
        )


__all__ = ["TFWTState"]
