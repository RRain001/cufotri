from __future__ import annotations

from datetime import datetime, timedelta, timezone
from collections import deque
import math

import numpy as np
import pandas as pd

from .atmosphere.gaussian import (
    geographic_offset_m,
    point_source_ground_concentration,
    rectangular_area_source_concentration,
    rotate_to_wind,
)
from .atmosphere.plume_rise import effective_stack_height_m
from .atmosphere.dispersion_parameters import classify_pasquill_gifford
from .coupling.integrator import advance
from .coupling.state import State
from .meteorology.fallback_fluxes import penman_ufotri_m_s, partition_evapotranspiration
from .meteorology.derived_variables import wind_speed_at_height
from .plant.obt import day_night_formation_rate_s


def _forcing(elapsed_s: float, config: dict) -> dict[str, float]:
    """Deterministic replaceable forcing for tests and examples."""
    forcing = config["synthetic_forcing"]
    period = forcing["diurnal_period_hours"]
    hour = (elapsed_s / 3600.0) % period
    daylight = max(
        math.sin(
            math.pi
            * (hour - forcing["sunrise_hour"])
            / forcing["daylight_hours"]
        ),
        0.0,
    )
    temperature = forcing["mean_temperature_k"] + forcing[
        "temperature_amplitude_k"
    ] * math.sin(
        2.0
        * math.pi
        * (hour - forcing["temperature_phase_hour"])
        / period
    )
    return {
        "temperature_k": temperature,
        "dewpoint_k": temperature - forcing["dewpoint_depression_k"],
        "wind_m_s": forcing["mean_wind_m_s"]
        + forcing["wind_amplitude_m_s"]
        * math.sin(2.0 * math.pi * hour / period),
        "wind_from_deg": forcing["wind_from_deg"],
        "net_radiation_w_m2": forcing["maximum_net_radiation_w_m2"] * daylight,
        "precipitation_m_s": (
            forcing["rain_rate_m_s"]
            if forcing["rain_start_hour"]
            <= elapsed_s / 3600.0
            < forcing["rain_end_hour"]
            else 0.0
        ),
    }


def _receptor_wind_coordinates(config: dict, met: dict) -> tuple[float, float]:
    site = config["site"]
    mode = site.get("receptor_mode", "downwind_fixed")
    if mode == "downwind_fixed":
        return site["receptor_downwind_m"], site["receptor_crosswind_m"]
    if mode == "local_cartesian":
        return rotate_to_wind(
            site["receptor_east_m"],
            site["receptor_north_m"],
            met["wind_from_deg"],
        )
    if mode == "geographic":
        east, north = geographic_offset_m(
            site["longitude_deg"],
            site["latitude_deg"],
            site["receptor_longitude_deg"],
            site["receptor_latitude_deg"],
        )
        return rotate_to_wind(east, north, met["wind_from_deg"])
    raise ValueError(f"Unsupported receptor mode: {mode}")


def run_short_case(config: dict, hourly_forcing: pd.DataFrame | None = None) -> pd.DataFrame:
    dt = float(config["time_step_seconds"])
    steps = int(config["duration_hours"] * 3600 / dt)
    forcing_step = float(config["meteorology_step_seconds"])
    if forcing_step <= 0:
        raise ValueError("meteorology_step_seconds must be positive")
    start = datetime.fromisoformat(config["start"].replace("Z", "+00:00"))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    state = State(config["soil"]["initial_water_m"])
    if hourly_forcing is not None:
        required_rows = math.ceil(config["duration_hours"] * 3600 / forcing_step)
        if len(hourly_forcing) < required_rows:
            raise ValueError(
                f"Forcing has {len(hourly_forcing)} rows; {required_rows} required"
            )
        if "time" in hourly_forcing:
            forcing_start = pd.Timestamp(hourly_forcing["time"].iloc[0])
            if forcing_start.tzinfo is None:
                forcing_start = forcing_start.tz_localize("UTC")
            if forcing_start.tz_convert("UTC").to_pydatetime() != start.astimezone(
                timezone.utc
            ):
                raise ValueError("Forcing start time does not match case start")
    lagged_reemission = 0.0
    delay_seconds = int(config["soil"].get("root_uptake_delay_seconds", 0))
    if delay_seconds < 0 or delay_seconds % int(dt) != 0:
        raise ValueError("root_uptake_delay_seconds must be a non-negative multiple of dt")
    delay_steps = delay_seconds // int(dt)
    root_history: deque[float] = deque([0.0] * delay_steps)
    rows: list[dict] = []
    for index in range(steps):
        elapsed = index * dt
        if hourly_forcing is None:
            met = _forcing(elapsed, config)
        else:
            forcing_index = int(elapsed // forcing_step)
            met = hourly_forcing.iloc[forcing_index].to_dict()
        downwind_m, crosswind_m = _receptor_wind_coordinates(config, met)
        height = effective_stack_height_m(
            config["source"]["stack_height_m"],
            config["atmosphere"]["plume_rise_mode"],
            config["atmosphere"]["fixed_plume_rise_m"],
            stack_diameter_m=config["source"]["stack_diameter_m"],
            exit_velocity_m_s=config["source"]["exit_velocity_m_s"],
            stack_temperature_k=config["source"]["stack_temperature_k"],
            ambient_temperature_k=met["temperature_k"],
            wind_speed_m_s=met["wind_m_s"],
            downwind_distance_m=max(downwind_m, 0.0),
        )
        plume_wind_speed = float(
            wind_speed_at_height(
                met["wind_m_s"],
                max(height, config["atmosphere"]["wind_reference_height_m"]),
                config["atmosphere"]["wind_reference_height_m"],
                config["atmosphere"]["rural_wind_profile_exponent"],
            )
        )
        forcing_mixing_height = met.get("boundary_layer_height_m")
        mixing_height = (
            float(forcing_mixing_height)
            if forcing_mixing_height is not None
            and np.isfinite(float(forcing_mixing_height))
            and float(forcing_mixing_height) > 0
            else config["atmosphere"].get("mixing_height_m")
        )
        image_terms = config["atmosphere"].get("mixing_layer_image_terms", 4)
        if config["atmosphere"]["stability_mode"] == "fixed":
            stability_class = config["atmosphere"]["stability_class"]
        elif config["atmosphere"]["stability_mode"] == "turner_simple":
            stability_class = classify_pasquill_gifford(
                met["wind_m_s"],
                met["net_radiation_w_m2"],
                met.get("total_cloud_cover_fraction"),
            )
        else:
            raise ValueError("Unsupported atmospheric stability mode")
        primary = point_source_ground_concentration(
            config["source"]["emission_rate_bq_s"],
            downwind_m,
            crosswind_m,
            plume_wind_speed,
            height,
            stability_class,
            mixing_height,
            image_terms,
        )
        if config["atmosphere"]["reemission_feedback_mode"] == "area_source":
            secondary = rectangular_area_source_concentration(
                lagged_reemission,
                downwind_m,
                crosswind_m,
                met["wind_m_s"],
                config["atmosphere"]["area_source_length_m"],
                config["atmosphere"]["area_source_width_m"],
                stability_class,
                quadrature_x=config["atmosphere"]["area_source_quadrature_x"],
                quadrature_y=config["atmosphere"]["area_source_quadrature_y"],
                mixing_height_m=mixing_height,
                image_terms=image_terms,
            )
        elif config["atmosphere"]["reemission_feedback_mode"] == "point_equivalent":
            secondary = point_source_ground_concentration(
                lagged_reemission * config["atmosphere"]["reemission_feedback_area_m2"],
                downwind_m,
                crosswind_m,
                met["wind_m_s"],
                0.0,
                stability_class,
                mixing_height,
                image_terms,
            )
        else:
            raise ValueError("Unsupported reemission feedback mode")
        air = primary + secondary
        pet = penman_ufotri_m_s(
            met["temperature_k"], met["dewpoint_k"], met["wind_m_s"],
            met["net_radiation_w_m2"], config["physics"]["latent_heat_j_kg"],
            config["physics"]["water_density_kg_m3"],
            config["physics"]["psychrometric_constant_pa_k"],
            config["physics"]["penman_aerodynamic_coefficient_w_m2_pa"],
        )
        water_fluxes = partition_evapotranspiration(
            pet, config["plant"]["lai"], state.soil_water_m,
            config["soil"]["maximum_water_m"], config["soil"]["wilting_water_m"],
        )
        is_day = met["net_radiation_w_m2"] > 0.0
        formation_rate = day_night_formation_rate_s(
            config["plant"]["obt_formation_rate_s"],
            is_day,
            config["plant"]["obt_day_night_enabled"],
            config["plant"]["obt_day_multiplier"],
            config["plant"]["obt_night_multiplier"],
        )
        delayed_root_uptake = root_history[0] if delay_steps else None
        state, diag = advance(
            state, dt, air, met["precipitation_m_s"],
            water_fluxes.soil_evaporation_m_s,
            water_fluxes.plant_transpiration_m_s,
            config,
            met.get(
                "rain_hto_concentration_bq_m3",
                config["soil"]["rain_hto_concentration_bq_m3"],
            ),
            root_uptake_m_s=delayed_root_uptake,
            obt_formation_rate_s=formation_rate,
            elapsed_since_release_s=elapsed,
            is_day=is_day,
        )
        if delay_steps:
            root_history.popleft()
            root_history.append(diag.plant_transpiration_m_s)
        lagged_reemission = diag.total_reemission_bq_m2_s
        rows.append({
            "time": start + timedelta(seconds=(index + 1) * dt),
            "air_hto_concentration": air,
            "soil_water_storage": state.soil_water_m,
            "soil_hto_inventory": state.soil_hto_bq_m2,
            "soil_hto_concentration": state.soil_hto_bq_m2 / state.soil_water_m,
            "soil_evaporation": diag.soil_evaporation_m_s,
            "plant_transpiration": diag.plant_transpiration_m_s,
            "root_water_uptake": diag.root_uptake_m_s,
            "deep_drainage": diag.drainage_m_s,
            "plant_tfwt_inventory": state.plant_tfwt_bq_m2,
            "plant_tfwt_concentration": state.plant_tfwt_bq_m2 / config["plant"]["water_storage_m"],
            "plant_obt_inventory": state.plant_obt_bq_m2,
            "soil_reemission_flux": diag.soil_reemission_bq_m2_s,
            "plant_reemission_flux": diag.plant_reemission_bq_m2_s,
            "total_reemission_flux": diag.total_reemission_bq_m2_s,
            "mass_balance_error": diag.mass_balance.residual_bq_m2,
            "mass_balance_relative_error": diag.mass_balance.relative_error,
        })
    frame = pd.DataFrame(rows)
    numeric = frame.select_dtypes(include=[np.number])
    physical = numeric.drop(columns=["mass_balance_error"])
    if not np.isfinite(numeric.to_numpy()).all() or (physical < -1.0e-12).any().any():
        raise RuntimeError("Short case produced invalid values")
    return frame
