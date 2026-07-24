from __future__ import annotations

from dataclasses import dataclass

from ..plant.obt import obt_fluxes_bq_m2_s
from ..plant.tfwt import direct_leaf_flux_bq_m2_s, plant_concentration_bq_m3
from ..plant.leaf_exchange import bidirectional_leaf_exchange
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
    atmospheric_dry_deposition_bq_m2_s: float
    atmospheric_wet_deposition_bq_m2_s: float
    dry_vd_cair_diagnostic_bq_m2_s: float
    net_leaf_exchange_bq_m2_s: float
    leaf_uptake_bq_m2_s: float
    leaf_release_bq_m2_s: float
    leaf_conductance_m_s: float
    leaf_equilibrium_air_bq_m3: float
    leaf_aerodynamic_resistance_s_m: float
    leaf_boundary_resistance_s_m: float
    leaf_canopy_resistance_s_m: float
    leaf_friction_velocity_m_s: float
    leaf_wind_speed_m_s: float
    leaf_monin_obukhov_length_m: float
    tfwt_to_edible_bq_m2_s: float
    obt_to_edible_bq_m2_s: float
    harvested_hto_bq_m2_s: float
    harvested_obt_bq_m2_s: float
    harvest_loss_bq_m2_s: float
    edible_feed_hto_bq_m2_s: float
    edible_feed_obt_bq_m2_s: float
    deep_drainage_hto_bq_m2_s: float
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
    atmospheric_dry_deposition_bq_m2_s: float = 0.0,
    atmospheric_wet_deposition_bq_m2_s: float = 0.0,
    air_temperature_k: float = 293.15,
    dewpoint_temperature_k: float = 288.15,
    wind_speed_m_s: float = 1.0,
    stability_class: str = "D",
    leaf_area_index: float | None = None,
    edible_allocation_rate_s: float = 0.0,
    harvest_event: bool = False,
    harvest_fraction: float = 1.0,
    harvest_loss_fraction: float = 0.0,
    edible_tfwt_consumption_bq_m2_s: float = 0.0,
    edible_obt_consumption_bq_m2_s: float = 0.0,
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
    active_lai = plant["lai"] if leaf_area_index is None else max(leaf_area_index, 0.0)
    dry_vd_cair_diagnostic = (
        config["atmosphere"]["deposition_velocity_m_s"]
        * max(air_concentration_bq_m3, 0.0)
    )
    dry_deposition = max(atmospheric_dry_deposition_bq_m2_s, 0.0)
    rain_runoff = water.runoff_m_s * rain_concentration
    wet_deposition = max(atmospheric_wet_deposition_bq_m2_s, 0.0)
    deposition = dry_deposition + rain_infiltration + wet_deposition
    leaf_mode = plant.get(
        "leaf_exchange_mode",
        "deposition_only" if plant["direct_leaf_uptake_enabled"] else "off",
    )
    leaf_conductance = 0.0
    leaf_equilibrium_air = 0.0
    leaf_aerodynamic_resistance = 0.0
    leaf_boundary_resistance = 0.0
    leaf_canopy_resistance = 0.0
    leaf_friction_velocity = 0.0
    leaf_wind_speed = 0.0
    leaf_monin_obukhov_length = 0.0
    if leaf_mode == "off":
        leaf = 0.0
    elif leaf_mode == "deposition_only":
        leaf = direct_leaf_flux_bq_m2_s(
            air_concentration_bq_m3,
            plant["direct_leaf_velocity_m_s"],
            True,
        )
        leaf_conductance = max(plant["direct_leaf_velocity_m_s"], 0.0)
    elif leaf_mode == "bidirectional_resistance":
        exchange = bidirectional_leaf_exchange(
            air_concentration_bq_m3,
            cp,
            air_temperature_k,
            dewpoint_temperature_k,
            active_lai,
            is_day,
            wind_speed_m_s=wind_speed_m_s,
            stability_class=stability_class,
            roughness_length_m=config["atmosphere"]["surface_roughness_m"],
            canopy_height_m=plant["leaf_canopy_height_m"],
            wind_measurement_height_m=config["atmosphere"][
                "wind_reference_height_m"
            ],
            leaf_characteristic_length_m=plant[
                "leaf_characteristic_length_m"
            ],
            air_kinematic_viscosity_m2_s=plant[
                "leaf_air_kinematic_viscosity_m2_s"
            ],
            water_vapour_diffusivity_m2_s=plant[
                "leaf_water_vapour_diffusivity_m2_s"
            ],
            stomatal_resistance_day_s_m=plant[
                "leaf_stomatal_resistance_day_s_m"
            ],
            stomatal_resistance_night_s_m=plant[
                "leaf_stomatal_resistance_night_s_m"
            ],
            vpd_sensitivity_per_kpa=plant["leaf_vpd_sensitivity_per_kpa"],
            isotope_fractionation_liquid_to_vapour=plant[
                "leaf_isotope_fractionation_liquid_to_vapour"
            ],
            water_density_kg_m3=physics["water_density_kg_m3"],
            precipitation_m_s=precipitation_m_s,
            von_karman_constant=plant["leaf_von_karman_constant"],
            minimum_wind_speed_m_s=plant["leaf_minimum_wind_speed_m_s"],
        )
        leaf = exchange.net_to_plant_bq_m2_s
        leaf_conductance = exchange.conductance_m_s
        leaf_equilibrium_air = exchange.equilibrium_air_concentration_bq_m3
        leaf_aerodynamic_resistance = exchange.aerodynamic_resistance_s_m
        leaf_boundary_resistance = exchange.boundary_resistance_s_m
        leaf_canopy_resistance = exchange.canopy_resistance_s_m
        leaf_friction_velocity = exchange.friction_velocity_m_s
        leaf_wind_speed = exchange.leaf_wind_speed_m_s
        leaf_monin_obukhov_length = exchange.monin_obukhov_length_m
    else:
        raise ValueError(f"Unsupported leaf-exchange mode: {leaf_mode}")
    leaf_uptake = max(leaf, 0.0)
    requested_leaf_release = max(-leaf, 0.0)
    if edible_allocation_rate_s < 0:
        raise ValueError("Edible allocation rate must be non-negative")
    if not 0.0 <= harvest_loss_fraction <= 1.0:
        raise ValueError("Harvest loss fraction must be within [0, 1]")
    if not 0.0 <= harvest_fraction <= 1.0:
        raise ValueError("Harvest fraction must be within [0, 1]")
    allocation_rate = 0.0 if harvest_event else edible_allocation_rate_s
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
        leaf_release=requested_leaf_release,
        edible_allocation=allocation_rate * state.plant_tfwt_bq_m2,
        crop_reset=(
            state.plant_tfwt_bq_m2 * harvest_fraction / dt_s
            if harvest_event
            else 0.0
        ),
    )
    obt_out = limit_inventory_outflows(
        state.plant_obt_bq_m2,
        dt_s,
        turnover=turnover,
        decay=physics["tritium_decay_constant_s"] * state.plant_obt_bq_m2,
        edible_allocation=allocation_rate * state.plant_obt_bq_m2,
        crop_reset=(
            state.plant_obt_bq_m2 * harvest_fraction / dt_s
            if harvest_event
            else 0.0
        ),
    )
    edible_tfwt_out = limit_inventory_outflows(
        state.edible_tfwt_bq_m2,
        dt_s,
        decay=physics["tritium_decay_constant_s"] * state.edible_tfwt_bq_m2,
        harvested=(
            state.edible_tfwt_bq_m2
            * harvest_fraction
            * (1.0 - harvest_loss_fraction)
            / dt_s
            if harvest_event
            else 0.0
        ),
        harvest_loss=(
            state.edible_tfwt_bq_m2
            * harvest_fraction
            * harvest_loss_fraction
            / dt_s
            if harvest_event
            else 0.0
        ),
        feed=max(edible_tfwt_consumption_bq_m2_s, 0.0),
    )
    edible_obt_out = limit_inventory_outflows(
        state.edible_obt_bq_m2,
        dt_s,
        decay=physics["tritium_decay_constant_s"] * state.edible_obt_bq_m2,
        harvested=(
            state.edible_obt_bq_m2
            * harvest_fraction
            * (1.0 - harvest_loss_fraction)
            / dt_s
            if harvest_event
            else 0.0
        ),
        harvest_loss=(
            state.edible_obt_bq_m2
            * harvest_fraction
            * harvest_loss_fraction
            / dt_s
            if harvest_event
            else 0.0
        ),
        feed=max(edible_obt_consumption_bq_m2_s, 0.0),
    )
    new_state = State(
        soil_water_m=water.water_m,
        soil_hto_bq_m2=state.soil_hto_bq_m2
        + dt_s * (deposition - sum(soil_out.values())),
        plant_tfwt_bq_m2=state.plant_tfwt_bq_m2
        + dt_s
        * (
            soil_out["root"]
            + leaf_uptake
            + obt_out["turnover"]
            - sum(plant_out.values())
        ),
        plant_obt_bq_m2=state.plant_obt_bq_m2
        + dt_s * (plant_out["formation"] - sum(obt_out.values())),
        edible_tfwt_bq_m2=state.edible_tfwt_bq_m2
        + dt_s * (plant_out["edible_allocation"] - sum(edible_tfwt_out.values())),
        edible_obt_bq_m2=state.edible_obt_bq_m2
        + dt_s * (obt_out["edible_allocation"] - sum(edible_obt_out.values())),
        harvested_hto_bq_m2=(
            state.harvested_hto_bq_m2 + edible_tfwt_out["harvested"] * dt_s
        ),
        harvested_obt_bq_m2=(
            state.harvested_obt_bq_m2 + edible_obt_out["harvested"] * dt_s
        ),
        cut_plant_hto_bq_m2=(
            state.cut_plant_hto_bq_m2 + plant_out["crop_reset"] * dt_s
        ),
        cut_plant_obt_bq_m2=(
            state.cut_plant_obt_bq_m2 + obt_out["crop_reset"] * dt_s
        ),
    )
    boundary = (
        soil_out["evaporation"]
        + soil_out["drainage"]
        + plant_out["transpiration"]
        + plant_out["leaf_release"]
        + edible_tfwt_out["harvested"]
        + edible_tfwt_out["harvest_loss"]
        + edible_obt_out["harvested"]
        + edible_obt_out["harvest_loss"]
        + edible_tfwt_out["feed"]
        + edible_obt_out["feed"]
        + plant_out["crop_reset"]
        + obt_out["crop_reset"]
    ) * dt_s
    decay = (
        soil_out["decay"]
        + plant_out["decay"]
        + obt_out["decay"]
        + edible_tfwt_out["decay"]
        + edible_obt_out["decay"]
    ) * dt_s
    balance = SurfaceBoxMassClosure(
        state.total_hto_bq_m2,
        (deposition + leaf_uptake) * dt_s,
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
        dry_deposition,
        wet_deposition,
        dry_vd_cair_diagnostic,
        leaf_uptake - plant_out["leaf_release"],
        leaf_uptake,
        plant_out["leaf_release"],
        leaf_conductance,
        leaf_equilibrium_air,
        leaf_aerodynamic_resistance,
        leaf_boundary_resistance,
        leaf_canopy_resistance,
        leaf_friction_velocity,
        leaf_wind_speed,
        leaf_monin_obukhov_length,
        plant_out["edible_allocation"],
        obt_out["edible_allocation"],
        edible_tfwt_out["harvested"],
        edible_obt_out["harvested"],
        edible_tfwt_out["harvest_loss"] + edible_obt_out["harvest_loss"],
        edible_tfwt_out["feed"],
        edible_obt_out["feed"],
        soil_out["drainage"],
        soil_out["evaporation"],
        plant_out["transpiration"] + plant_out["leaf_release"],
        (
            soil_out["evaporation"]
            + plant_out["transpiration"]
            + plant_out["leaf_release"]
        ),
        balance,
    )
    return new_state, diagnostics
