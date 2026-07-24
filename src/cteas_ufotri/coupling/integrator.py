from __future__ import annotations

from dataclasses import dataclass

from ..plant.obt import obt_fluxes_bq_m2_s
from ..plant.tfwt import direct_leaf_flux_bq_m2_s, plant_concentration_bq_m3
from ..reemission.fluxes import (
    basic_reemission_fluxes,
    ufotri_empirical_soil_reemission_bq_m2_s,
)
from ..soil.hto_balance import concentration_bq_m3, limit_inventory_outflows
from ..soil.water_balance import update_water_bucket
from .mass_balance import SurfaceBoxMassClosure
from .state import State


@dataclass(frozen=True)
class StepDiagnostics:
    soil_concentration_bq_m3: float
    plant_concentration_bq_m3: float
    soil_evaporation_m_s: float
    plant_transpiration_m_s: float
    root_uptake_m_s: float
    drainage_m_s: float
    precipitation_m_s: float
    infiltration_m_s: float
    runoff_m_s: float
    rain_infiltration_hto_bq_m2_s: float
    rain_runoff_hto_bq_m2_s: float
    soil_reemission_bq_m2_s: float
    plant_reemission_bq_m2_s: float
    total_reemission_bq_m2_s: float
    surface_box_mass_closure: SurfaceBoxMassClosure

    @property
    def mass_balance(self) -> SurfaceBoxMassClosure:
        """Deprecated compatibility alias for pre-v1 callers."""
        return self.surface_box_mass_closure


def advance(
    state: State,
    dt_s: float,
    air_concentration_bq_m3: float,
    precipitation_m_s: float,
    requested_soil_evaporation_m_s: float,
    requested_transpiration_m_s: float,
    config: dict,
    rain_hto_concentration_bq_m3: float = 0.0,
    root_uptake_m_s: float | None = None,
    obt_formation_rate_s: float | None = None,
    elapsed_since_release_s: float = 0.0,
    is_day: bool = True,
) -> tuple[State, StepDiagnostics]:
    soil = config["soil"]
    plant = config["plant"]
    physics = config["physics"]
    water = update_water_bucket(
        state.soil_water_m,
        precipitation_m_s,
        requested_soil_evaporation_m_s,
        requested_transpiration_m_s,
        dt_s,
        soil["minimum_water_m"],
        soil["maximum_water_m"],
        soil["runoff_enabled"],
        soil["infiltration_capacity_m_s"],
    )
    rain_concentration = max(rain_hto_concentration_bq_m3, 0.0)
    rain_infiltration = water.infiltration_m_s * rain_concentration
    mixed_soil_inventory = state.soil_hto_bq_m2 + rain_infiltration * dt_s
    mixed_soil_water = state.soil_water_m + water.infiltration_m_s * dt_s
    cs = concentration_bq_m3(
        mixed_soil_inventory,
        mixed_soil_water,
        config["numerics"]["concentration_epsilon_m"],
    )
    cp = plant_concentration_bq_m3(
        state.plant_tfwt_bq_m2, plant["water_storage_m"]
    )
    dry_deposition = (
        config["atmosphere"]["deposition_velocity_m_s"]
        * max(air_concentration_bq_m3, 0.0)
    )
    rain_runoff = water.runoff_m_s * rain_concentration
    deposition = dry_deposition + rain_infiltration
    leaf = direct_leaf_flux_bq_m2_s(
        air_concentration_bq_m3,
        plant["direct_leaf_velocity_m_s"],
        plant["direct_leaf_uptake_enabled"],
    )
    basic_soil_reem, plant_reem, _ = basic_reemission_fluxes(
        water.evaporation_m_s, cs, water.transpiration_m_s, cp
    )
    reemission = config["reemission"]
    if reemission["mode"] == "basic_mass_flux":
        soil_reem = basic_soil_reem
    elif reemission["mode"] == "ufotri_empirical":
        rain_depth = max(precipitation_m_s, 0.0) * dt_s
        drainage_fraction = (
            min(water.drainage_m_s * dt_s / rain_depth, 1.0)
            if rain_depth > 0
            else 0.0
        )
        soil_reem = ufotri_empirical_soil_reemission_bq_m2_s(
            state.soil_hto_bq_m2,
            water.evaporation_m_s,
            state.soil_water_m,
            drainage_fraction,
            elapsed_since_release_s,
            is_day,
            reference_evaporation_m_s=reemission[
                "empirical_reference_evaporation_m_s"
            ],
            reference_water_m=reemission["empirical_reference_water_m"],
            radiative_reference_fraction_h=reemission[
                "empirical_radiative_reference_fraction_h"
            ],
            diffusive_fraction_h=reemission["empirical_diffusive_fraction_h"],
            zt_half_life_h=reemission["empirical_zt_half_life_h"],
            ht_correction=reemission["empirical_ht_correction"],
        )
    else:
        raise ValueError(f"Unsupported re-emission mode: {reemission['mode']}")
    actual_root_uptake = (
        water.root_uptake_m_s if root_uptake_m_s is None else max(root_uptake_m_s, 0.0)
    )
    soil_out = limit_inventory_outflows(
        mixed_soil_inventory,
        dt_s,
        evaporation=soil_reem,
        root=(
            actual_root_uptake
            * cs
            * plant["root_uptake_fraction_from_modelled_layer"]
        ),
        drainage=water.drainage_m_s * cs,
        decay=physics["tritium_decay_constant_s"] * state.soil_hto_bq_m2,
    )
    formation, turnover = obt_fluxes_bq_m2_s(
        state.plant_tfwt_bq_m2,
        state.plant_obt_bq_m2,
        (
            plant["obt_formation_rate_s"]
            if obt_formation_rate_s is None
            else obt_formation_rate_s
        ),
        plant["obt_turnover_rate_s"],
    )
    plant_out = limit_inventory_outflows(
        state.plant_tfwt_bq_m2,
        dt_s,
        transpiration=plant_reem,
        formation=formation,
        decay=physics["tritium_decay_constant_s"] * state.plant_tfwt_bq_m2,
    )
    obt_out = limit_inventory_outflows(
        state.plant_obt_bq_m2,
        dt_s,
        turnover=turnover,
        decay=physics["tritium_decay_constant_s"] * state.plant_obt_bq_m2,
    )
    new_state = State(
        water.water_m,
        state.soil_hto_bq_m2
        + dt_s * (deposition - sum(soil_out.values())),
        state.plant_tfwt_bq_m2
        + dt_s
        * (
            soil_out["root"]
            + leaf
            + obt_out["turnover"]
            - sum(plant_out.values())
        ),
        state.plant_obt_bq_m2
        + dt_s * (plant_out["formation"] - sum(obt_out.values())),
    )
    boundary = (
        soil_out["evaporation"]
        + soil_out["drainage"]
        + plant_out["transpiration"]
    ) * dt_s
    decay = (
        soil_out["decay"] + plant_out["decay"] + obt_out["decay"]
    ) * dt_s
    balance = SurfaceBoxMassClosure(
        state.total_hto_bq_m2,
        (deposition + leaf) * dt_s,
        boundary,
        decay,
        new_state.total_hto_bq_m2,
    )
    diagnostics = StepDiagnostics(
        cs,
        cp,
        water.evaporation_m_s,
        water.transpiration_m_s,
        actual_root_uptake,
        water.drainage_m_s,
        water.precipitation_m_s,
        water.infiltration_m_s,
        water.runoff_m_s,
        rain_infiltration,
        rain_runoff,
        soil_out["evaporation"],
        plant_out["transpiration"],
        soil_out["evaporation"] + plant_out["transpiration"],
        balance,
    )
    return new_state, diagnostics
