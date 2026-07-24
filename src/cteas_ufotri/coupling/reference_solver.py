from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from ..plant.tfwt import direct_leaf_flux_bq_m2_s
from ..reemission.fluxes import ufotri_empirical_soil_reemission_bq_m2_s
from ..soil.water_balance import update_water_bucket
from .state import State


def solve_linear_inventory_reference(
    initial_bq_m2: tuple[float, float, float],
    duration_s: float,
    external_soil_input_bq_m2_s: float,
    soil_evaporation_rate_s: float,
    root_transfer_rate_s: float,
    drainage_rate_s: float,
    plant_transpiration_rate_s: float,
    obt_formation_rate_s: float,
    obt_turnover_rate_s: float,
    decay_rate_s: float,
):
    """SciPy reference for the fixed-rate three-inventory subsystem.

    This is intentionally independent of water/meteorology parameterizations;
    it provides a high-accuracy check for compartment transfer signs and
    explicit-step convergence.
    """
    if duration_s <= 0 or any(value < 0 for value in initial_bq_m2):
        raise ValueError("Invalid reference-solver interval or initial inventory")

    def derivative(_time, values):
        soil, plant, obt = values
        return np.array([
            external_soil_input_bq_m2_s
            - (soil_evaporation_rate_s + root_transfer_rate_s
               + drainage_rate_s + decay_rate_s) * soil,
            root_transfer_rate_s * soil + obt_turnover_rate_s * obt
            - (plant_transpiration_rate_s + obt_formation_rate_s
               + decay_rate_s) * plant,
            obt_formation_rate_s * plant
            - (obt_turnover_rate_s + decay_rate_s) * obt,
        ])

    return solve_ivp(
        derivative,
        (0.0, duration_s),
        np.asarray(initial_bq_m2, dtype=float),
        method="DOP853",
        rtol=1.0e-11,
        atol=1.0e-12,
    )


def solve_coupled_step_reference(
    state: State,
    dt_s: float,
    air_concentration_bq_m3: float,
    precipitation_m_s: float,
    requested_soil_evaporation_m_s: float,
    requested_transpiration_m_s: float,
    config: dict,
    *,
    rain_hto_concentration_bq_m3: float = 0.0,
    root_uptake_m_s: float | None = None,
    obt_formation_rate_s: float | None = None,
    elapsed_since_release_s: float = 0.0,
    is_day: bool = True,
) -> State:
    """Continuous four-state reference for one piecewise-constant forcing step."""
    soil = config["soil"]
    plant = config["plant"]
    physics = config["physics"]
    water_flux = update_water_bucket(
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
    root = (
        water_flux.root_uptake_m_s
        if root_uptake_m_s is None
        else max(root_uptake_m_s, 0.0)
    )
    formation = (
        plant["obt_formation_rate_s"]
        if obt_formation_rate_s is None
        else max(obt_formation_rate_s, 0.0)
    )
    turnover = plant["obt_turnover_rate_s"]
    decay = physics["tritium_decay_constant_s"]
    deposition = (
        config["atmosphere"]["deposition_velocity_m_s"]
        * max(air_concentration_bq_m3, 0.0)
        + max(precipitation_m_s, 0.0)
        * max(rain_hto_concentration_bq_m3, 0.0)
    )
    leaf = direct_leaf_flux_bq_m2_s(
        air_concentration_bq_m3,
        plant["direct_leaf_velocity_m_s"],
        plant["direct_leaf_uptake_enabled"],
    )
    net_water_rate = (
        max(precipitation_m_s, 0.0)
        - water_flux.evaporation_m_s
        - water_flux.transpiration_m_s
        - water_flux.drainage_m_s
    )
    rain_depth = max(precipitation_m_s, 0.0) * dt_s
    drainage_fraction = (
        min(water_flux.drainage_m_s * dt_s / rain_depth, 1.0)
        if rain_depth > 0
        else 0.0
    )

    def derivative(time_in_step, values):
        water_m, soil_inventory, plant_inventory, obt_inventory = values
        soil_concentration = soil_inventory / max(
            water_m, config["numerics"]["concentration_epsilon_m"]
        )
        plant_concentration = plant_inventory / plant["water_storage_m"]
        if config["reemission"]["mode"] == "basic_mass_flux":
            soil_to_air = water_flux.evaporation_m_s * soil_concentration
        elif config["reemission"]["mode"] == "ufotri_empirical":
            reemission = config["reemission"]
            soil_to_air = ufotri_empirical_soil_reemission_bq_m2_s(
                soil_inventory,
                water_flux.evaporation_m_s,
                water_m,
                drainage_fraction,
                elapsed_since_release_s + time_in_step,
                is_day,
                reference_evaporation_m_s=reemission[
                    "empirical_reference_evaporation_m_s"
                ],
                reference_water_m=reemission["empirical_reference_water_m"],
                radiative_reference_fraction_h=reemission[
                    "empirical_radiative_reference_fraction_h"
                ],
                diffusive_fraction_h=reemission[
                    "empirical_diffusive_fraction_h"
                ],
                zt_half_life_h=reemission["empirical_zt_half_life_h"],
                ht_correction=reemission["empirical_ht_correction"],
            )
        else:
            raise ValueError(
                f"Unsupported re-emission mode: {config['reemission']['mode']}"
            )
        soil_to_plant = root * soil_concentration * plant["topsoil_root_fraction"]
        drainage = water_flux.drainage_m_s * soil_concentration
        plant_to_air = water_flux.transpiration_m_s * plant_concentration
        return np.array([
            net_water_rate,
            deposition - soil_to_air - soil_to_plant - drainage - decay * soil_inventory,
            soil_to_plant + leaf + turnover * obt_inventory
            - plant_to_air - formation * plant_inventory - decay * plant_inventory,
            formation * plant_inventory - turnover * obt_inventory - decay * obt_inventory,
        ])

    solution = solve_ivp(
        derivative,
        (0.0, dt_s),
        np.array([
            state.soil_water_m,
            state.soil_hto_bq_m2,
            state.plant_tfwt_bq_m2,
            state.plant_obt_bq_m2,
        ]),
        method="DOP853",
        rtol=1.0e-11,
        atol=1.0e-12,
    )
    if not solution.success:
        raise RuntimeError(f"SciPy coupled reference failed: {solution.message}")
    final = solution.y[:, -1]
    return State(*map(float, final))
