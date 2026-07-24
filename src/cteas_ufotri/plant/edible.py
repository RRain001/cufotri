from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EdibleConcentrations:
    tfwt_bq_m3_water: float
    obt_bq_kg_fresh: float
    obt_bq_kg_dry: float


def edible_concentrations(
    tfwt_inventory_bq_m2: float,
    obt_inventory_bq_m2: float,
    edible_fresh_mass_kg_m2: float,
    water_content_fraction_fresh: float,
    water_density_kg_m3: float,
) -> EdibleConcentrations:
    if water_density_kg_m3 <= 0:
        raise ValueError("Water density must be positive")
    if not 0.0 <= water_content_fraction_fresh < 1.0:
        raise ValueError("Edible water-content fraction must be within [0, 1)")
    fresh = max(edible_fresh_mass_kg_m2, 0.0)
    water_m = fresh * water_content_fraction_fresh / water_density_kg_m3
    dry = fresh * (1.0 - water_content_fraction_fresh)
    return EdibleConcentrations(
        max(tfwt_inventory_bq_m2, 0.0) / water_m if water_m > 0 else 0.0,
        max(obt_inventory_bq_m2, 0.0) / fresh if fresh > 0 else 0.0,
        max(obt_inventory_bq_m2, 0.0) / dry if dry > 0 else 0.0,
    )

