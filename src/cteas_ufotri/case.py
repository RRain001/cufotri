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
from .atmosphere.calm_wind import resolve_calm_wind
from .atmosphere.depletion import segment_exponential_depletion
from .atmosphere.deposition import surface_deposition_ledger
from .atmosphere.wet_deposition import (
    scavenging_coefficient_s,
)
from .coupling.integrator import advance
from .coupling.state import State
from .meteorology.fallback_fluxes import (
    penman_ufotri_components_m_s,
    partition_evapotranspiration,
)
from .meteorology.derived_variables import wind_speed_at_height
from .plant.obt import day_night_formation_rate_s
from .crop.phenology import (
    CropParameters,
    growth_fraction_at_time,
    harvest_fraction_at_transition,
    lai_at_time,
)
from .plant.edible import edible_concentrations
from .foodchain.model import (
    AnimalState,
    BeefProductState,
    plant_food_outputs,
    step_animal,
    step_beef_product,
)
from .dose.public import DoseIncrement, calculate_public_dose_step


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
    if config["soil"]["layer_model"] == "surface_root_deep_3box":
        raise ValueError(
            "surface_root_deep_3box is an experimental standalone soil API; "
            "use advance_three_box_soil"
        )
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
    feedback_delay_s = int(config["coupling"]["reemission_feedback_delay_s"])
    feedback_delay_steps = feedback_delay_s // int(dt)
    feedback_history: deque[float] = deque([0.0] * feedback_delay_steps)
    delay_seconds = int(config["soil"].get("root_uptake_delay_seconds", 0))
    if delay_seconds < 0 or delay_seconds % int(dt) != 0:
        raise ValueError("root_uptake_delay_seconds must be a non-negative multiple of dt")
    delay_steps = delay_seconds // int(dt)
    root_history: deque[float] = deque([0.0] * delay_steps)
    rows: list[dict] = []
    crop_config = config["crops"]
    crop = CropParameters.from_mapping(
        crop_config["active_crop"],
        crop_config["parameters"][crop_config["active_crop"]],
    )
    animal_state = AnimalState()
    beef_product_state = BeefProductState()
    dose_totals = {
        name: 0.0
        for name in DoseIncrement.__dataclass_fields__
    }
    calm_wind_event_count = 0
    cumulative_stack_release_bq = 0.0
    cumulative_dry_plume_loss_bq = 0.0
    cumulative_wet_plume_loss_bq = 0.0
    cumulative_dry_surface_input_bq = 0.0
    cumulative_wet_surface_input_bq = 0.0
    cumulative_surface_boundary_output_bq_m2 = 0.0
    cumulative_surface_decay_bq_m2 = 0.0
    cumulative_surface_input_bq_m2 = 0.0
    cumulative_surface_feed_bq_m2 = 0.0
    cumulative_deep_loss_bq_m2 = 0.0
    cumulative_runoff_bypass_bq_m2 = 0.0
    cumulative_beef_produced_hto_bq_m2 = 0.0
    cumulative_beef_produced_obt_bq_m2 = 0.0
    cumulative_beef_consumed_hto_bq_m2 = 0.0
    cumulative_beef_consumed_obt_bq_m2 = 0.0
    cumulative_beef_decay_bq_m2 = 0.0
    cumulative_animal_input_bq_m2 = 0.0
    cumulative_animal_milk_output_bq_m2 = 0.0
    cumulative_animal_excretion_bq_m2 = 0.0
    cumulative_animal_decay_bq_m2 = 0.0
    cumulative_animal_slaughter_bq_m2 = 0.0
    for index in range(steps):
        elapsed = index * dt
        release_duration_h = config["source"].get(
            "release_duration_hours", config["duration_hours"]
        )
        stack_release_bq_s = (
            config["source"]["emission_rate_bq_s"]
            if elapsed < float(release_duration_h) * 3600.0
            else 0.0
        )
        if hourly_forcing is None:
            met = _forcing(elapsed, config)
        else:
            forcing_index = int(elapsed // forcing_step)
            met = hourly_forcing.iloc[forcing_index].to_dict()
        step_time = start + timedelta(seconds=index * dt)
        external_lai = met.get(crop_config.get("external_lai_column", "lai"))
        crop_lai = lai_at_time(
            step_time,
            crop,
            crop_config["lai_mode"],
            external_lai=external_lai,
        )
        growth_fraction = growth_fraction_at_time(
            step_time,
            crop,
            crop_config["lai_mode"],
            external_lai=external_lai,
        )
        next_step_time = step_time + timedelta(seconds=dt)
        harvest_fraction = harvest_fraction_at_transition(
            step_time,
            next_step_time,
            crop,
        )
        harvest_event = harvest_fraction > 0.0
        calm = resolve_calm_wind(
            met["wind_m_s"], config["atmosphere"]["calm_wind"]
        )
        calm_wind_event_count += int(calm.applied)
        lagged_reemission = (
            feedback_history[0] if feedback_delay_steps else 0.0
        )
        downwind_m, crosswind_m = _receptor_wind_coordinates(config, met)
        height = effective_stack_height_m(
            config["source"]["stack_height_m"],
            config["atmosphere"]["plume_rise_mode"],
            config["atmosphere"]["fixed_plume_rise_m"],
            stack_diameter_m=config["source"]["stack_diameter_m"],
            exit_velocity_m_s=config["source"]["exit_velocity_m_s"],
            stack_temperature_k=config["source"]["stack_temperature_k"],
            ambient_temperature_k=met["temperature_k"],
            wind_speed_m_s=calm.effective_wind_speed_m_s,
            downwind_distance_m=max(downwind_m, 0.0),
        )
        plume_wind_speed = float(
            wind_speed_at_height(
                calm.effective_wind_speed_m_s,
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
        depletion_config = config["atmosphere"]["depletion"]
        wet_mode = depletion_config.get(
            "wet_scavenging_mode",
            (
                "constant_scavenging_coefficient"
                if depletion_config.get("wet_scavenging_enabled", False)
                else "off"
            ),
        )
        wet_rate = scavenging_coefficient_s(
            met["precipitation_m_s"],
            wet_mode,
            constant_coefficient_s=depletion_config.get(
                "constant_scavenging_coefficient_s",
                depletion_config.get("wet_scavenging_rate_s", 0.0),
            ),
            power_law_a_s=depletion_config.get("power_law_a_s", 0.0),
            power_law_b=depletion_config.get("power_law_b", 1.0),
        )
        if depletion_config["enabled"]:
            depletion = segment_exponential_depletion(
                stack_release_bq_s,
                max(downwind_m, 0.0),
                plume_wind_speed,
                config["atmosphere"]["deposition_velocity_m_s"],
                depletion_config["mixing_height_m"],
                depletion_config["segments"],
                dry_enabled=depletion_config["dry_deposition_enabled"],
                wet_enabled=wet_mode != "off",
                wet_scavenging_rate_s=wet_rate,
            )
        else:
            depletion = segment_exponential_depletion(
                stack_release_bq_s,
                max(downwind_m, 0.0),
                plume_wind_speed,
                0.0,
                depletion_config["mixing_height_m"],
                depletion_config["segments"],
                dry_enabled=False,
            )
        dry_ledger = surface_deposition_ledger(
            depletion.dry_depletion_bq_s,
            config["deposition"]["dry_footprint"],
        )
        wet_ledger = surface_deposition_ledger(
            depletion.wet_depletion_bq_s,
            config["deposition"]["wet_footprint"],
        )
        cumulative_stack_release_bq += stack_release_bq_s * dt
        cumulative_dry_plume_loss_bq += depletion.dry_depletion_bq_s * dt
        cumulative_wet_plume_loss_bq += depletion.wet_depletion_bq_s * dt
        cumulative_dry_surface_input_bq += dry_ledger.surface_input_bq_s * dt
        cumulative_wet_surface_input_bq += wet_ledger.surface_input_bq_s * dt
        primary = point_source_ground_concentration(
            0.0 if calm.skip_gaussian else depletion.source_after_bq_s,
            downwind_m,
            crosswind_m,
            plume_wind_speed,
            height,
            stability_class,
            mixing_height,
            image_terms,
        )
        if config["atmosphere"]["reemission_feedback_mode"] == "off":
            secondary = 0.0
        elif config["atmosphere"]["reemission_feedback_mode"] == "area_source":
            secondary = rectangular_area_source_concentration(
                lagged_reemission,
                downwind_m,
                crosswind_m,
                calm.effective_wind_speed_m_s,
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
                calm.effective_wind_speed_m_s,
                0.0,
                stability_class,
                mixing_height,
                image_terms,
            )
        else:
            raise ValueError("Unsupported reemission feedback mode")
        air = primary + secondary
        pet, radiation_pet, aerodynamic_pet = penman_ufotri_components_m_s(
            met["temperature_k"], met["dewpoint_k"], met["wind_m_s"],
            met["net_radiation_w_m2"], config["physics"]["latent_heat_j_kg"],
            config["physics"]["water_density_kg_m3"],
            config["physics"]["psychrometric_constant_pa_k"],
            config["physics"]["penman_aerodynamic_coefficient_w_m2_pa"],
        )
        water_fluxes = partition_evapotranspiration(
            pet, crop_lai, state.soil_water_m,
            config["soil"]["maximum_water_m"], config["soil"]["wilting_water_m"],
            config["evapotranspiration"]["lai_shading_mode"],
            radiation_pet,
            aerodynamic_pet,
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
        pre_edible_fresh_mass = (
            crop.aboveground_biomass_kg_fresh_m2
            * crop.edible_fraction
            * growth_fraction
        )
        pre_edible = edible_concentrations(
            state.edible_tfwt_bq_m2,
            state.edible_obt_bq_m2,
            pre_edible_fresh_mass,
            crop.water_content_fraction_fresh,
            config["physics"]["water_density_kg_m3"],
        )
        pre_food = plant_food_outputs(
            crop.name,
            pre_edible.tfwt_bq_m3_water,
            pre_edible.obt_bq_kg_fresh,
            crop.water_content_fraction_fresh,
            config["physics"]["water_density_kg_m3"],
        )
        animal_enabled = (
            config["foodchain"]["enabled"]
            and config["foodchain"]["animal_mode"] == "minimal_cow"
            and crop.name in {"grass", "pasture"}
        )
        feed_rate_kg_m2_s = (
            config["foodchain"]["feed_intake_kg_fresh_day"]
            / 86400.0
            / config["foodchain"]["animal_support_area_m2"]
            if animal_enabled
            else 0.0
        )
        feed_hto_rate = (
            feed_rate_kg_m2_s * pre_food["pasture_tfwt_bq_kg_fresh"]
        )
        feed_obt_rate = (
            feed_rate_kg_m2_s * pre_food["pasture_obt_bq_kg_fresh"]
        )
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
            atmospheric_dry_deposition_bq_m2_s=(
                dry_ledger.surface_flux_bq_m2_s
            ),
            atmospheric_wet_deposition_bq_m2_s=(
                wet_ledger.surface_flux_bq_m2_s
            ),
            air_temperature_k=met["temperature_k"],
            dewpoint_temperature_k=met["dewpoint_k"],
            wind_speed_m_s=calm.effective_wind_speed_m_s,
            stability_class=stability_class,
            leaf_area_index=crop_lai,
            edible_allocation_rate_s=(
                crop.edible_allocation_rate_s
                if crop_lai > 0 and crop_config["edible_compartments_enabled"]
                else 0.0
            ),
            harvest_event=(
                harvest_event and crop_config["edible_compartments_enabled"]
            ),
            harvest_fraction=harvest_fraction,
            harvest_loss_fraction=crop.harvest_loss_fraction,
            edible_tfwt_consumption_bq_m2_s=feed_hto_rate,
            edible_obt_consumption_bq_m2_s=feed_obt_rate,
        )
        cumulative_surface_boundary_output_bq_m2 += (
            diag.surface_box_mass_closure.boundary_output_bq_m2
        )
        cumulative_surface_decay_bq_m2 += (
            diag.surface_box_mass_closure.decay_bq_m2
        )
        cumulative_surface_input_bq_m2 += (
            diag.surface_box_mass_closure.external_input_bq_m2
        )
        cumulative_surface_feed_bq_m2 += dt * (
            diag.edible_feed_hto_bq_m2_s
            + diag.edible_feed_obt_bq_m2_s
        )
        cumulative_deep_loss_bq_m2 += (
            dt * diag.deep_drainage_hto_bq_m2_s
        )
        cumulative_runoff_bypass_bq_m2 += (
            dt * diag.rain_runoff_hto_bq_m2_s
        )
        edible_fresh_mass = (
            crop.aboveground_biomass_kg_fresh_m2
            * crop.edible_fraction
            * growth_fraction
        )
        edible = edible_concentrations(
            state.edible_tfwt_bq_m2,
            state.edible_obt_bq_m2,
            edible_fresh_mass,
            crop.water_content_fraction_fresh,
            config["physics"]["water_density_kg_m3"],
        )
        food_outputs = plant_food_outputs(
            crop.name,
            edible.tfwt_bq_m3_water,
            edible.obt_bq_kg_fresh,
            crop.water_content_fraction_fresh,
            config["physics"]["water_density_kg_m3"],
        )
        if animal_enabled:
            beef_config = config["foodchain"]["animal_products"]["beef"]
            slaughter_rate_s = (
                float(beef_config["turnover_rate_d-1"]) / 86400.0
                if beef_config["mode"] == "continuous_herd_turnover"
                else 0.0
            )
            animal_state, animal_diag = step_animal(
                animal_state,
                dt,
                pre_food["pasture_tfwt_bq_kg_fresh"],
                pre_food["pasture_obt_bq_kg_fresh"],
                config["foodchain"]["drinking_water_hto_bq_l"],
                config["foodchain"],
                slaughter_rate_s=slaughter_rate_s,
                feed_hto_input_bq_m2_s=diag.edible_feed_hto_bq_m2_s,
                feed_obt_input_bq_m2_s=diag.edible_feed_obt_bq_m2_s,
            )
        else:
            beef_config = config["foodchain"]["animal_products"]["beef"]
            slaughter_rate_s = 0.0
            _, animal_diag = step_animal(
                AnimalState(),
                dt,
                0.0,
                0.0,
                0.0,
                config["foodchain"],
            )
        beef_mass_production_kg_m2_s = (
            slaughter_rate_s
            * float(beef_config["edible_meat_mass_kg_per_head"])
            / float(config["foodchain"]["animal_support_area_m2"])
        )
        requested_beef_consumption_kg_m2_s = (
            float(
                config["dose"]["age_groups"][
                    config["dose"]["active_age_group"]
                ]["beef_kg_day"]
            )
            / 86400.0
            / float(config["foodchain"]["animal_support_area_m2"])
            if config["dose"]["enabled"]
            else 0.0
        )
        beef_product_state, beef_diag = step_beef_product(
            beef_product_state,
            dt,
            animal_diag.slaughter_hto_output_bq_s,
            animal_diag.slaughter_obt_output_bq_s,
            beef_mass_production_kg_m2_s,
            requested_beef_consumption_kg_m2_s,
            float(config["foodchain"]["decay_rate_s"]),
        )
        cumulative_beef_produced_hto_bq_m2 += (
            beef_diag.produced_hto_bq_m2_s * dt
        )
        cumulative_beef_produced_obt_bq_m2 += (
            beef_diag.produced_obt_bq_m2_s * dt
        )
        cumulative_beef_consumed_hto_bq_m2 += (
            beef_diag.consumed_hto_bq_m2_s * dt
        )
        cumulative_beef_consumed_obt_bq_m2 += (
            beef_diag.consumed_obt_bq_m2_s * dt
        )
        cumulative_beef_decay_bq_m2 += beef_diag.decay_loss_bq_m2_s * dt
        cumulative_animal_input_bq_m2 += animal_diag.closure.input_bq
        cumulative_animal_milk_output_bq_m2 += (
            animal_diag.milk_hto_output_bq_s
            + animal_diag.milk_obt_output_bq_s
        ) * dt
        cumulative_animal_excretion_bq_m2 += (
            animal_diag.excretion_output_bq_s * dt
        )
        cumulative_animal_decay_bq_m2 += animal_diag.closure.decay_bq
        cumulative_animal_slaughter_bq_m2 += (
            animal_diag.slaughter_output_bq_s * dt
        )
        dose_concentrations = {
            **food_outputs,
            "milk_hto_bq_l": animal_diag.milk_hto_bq_l,
            "milk_obt_bq_l": animal_diag.milk_obt_bq_l,
            "beef_hto_bq_kg": beef_diag.beef_hto_bq_kg,
            "beef_obt_bq_kg": beef_diag.beef_obt_bq_kg,
            "beef_consumed_hto_bq_step": (
                beef_diag.consumed_hto_bq_m2_s
                * dt
                * float(config["foodchain"]["animal_support_area_m2"])
            ),
            "beef_consumed_obt_bq_step": (
                beef_diag.consumed_obt_bq_m2_s
                * dt
                * float(config["foodchain"]["animal_support_area_m2"])
            ),
            "drinking_water_hto_bq_l": config["dose"][
                "drinking_water_hto_bq_l"
            ],
        }
        if config["dose"]["enabled"]:
            dose_increment = calculate_public_dose_step(
                dt,
                air,
                dose_concentrations,
                config["dose"]["age_groups"][
                    config["dose"]["active_age_group"]
                ],
                skin_to_inhalation_factor=config["dose"][
                    "skin_to_inhalation_factor"
                ],
            )
            for name in dose_totals:
                dose_totals[name] += getattr(dose_increment, name)
        if delay_steps:
            root_history.popleft()
            root_history.append(diag.plant_transpiration_m_s)
        if feedback_delay_steps:
            feedback_history.popleft()
            feedback_history.append(diag.total_reemission_bq_m2_s)
        activity_area_m2 = float(
            config["deposition"]["dry_footprint"]["area_m2"]
        )
        ecological_inventory_bq_m2 = (
            state.total_hto_bq_m2
            + animal_state.total_bq
            + beef_product_state.total_bq_m2
        )
        external_ecological_input_bq_m2 = (
            cumulative_surface_input_bq_m2
            + cumulative_animal_input_bq_m2
            - cumulative_surface_feed_bq_m2
        )
        ecological_boundary_bq_m2 = (
            cumulative_surface_boundary_output_bq_m2
            - cumulative_surface_feed_bq_m2
            + cumulative_animal_milk_output_bq_m2
            + cumulative_animal_excretion_bq_m2
            + cumulative_beef_consumed_hto_bq_m2
            + cumulative_beef_consumed_obt_bq_m2
        )
        ecological_decay_bq_m2 = (
            cumulative_surface_decay_bq_m2
            + cumulative_animal_decay_bq_m2
            + cumulative_beef_decay_bq_m2
        )
        activity_residual_bq = activity_area_m2 * (
            external_ecological_input_bq_m2
            - ecological_inventory_bq_m2
            - ecological_boundary_bq_m2
            - ecological_decay_bq_m2
        )
        harvested_activity_bq = activity_area_m2 * (
            state.harvested_hto_bq_m2
            + state.harvested_obt_bq_m2
            + state.cut_plant_hto_bq_m2
            + state.cut_plant_obt_bq_m2
        )
        milk_activity_bq = (
            activity_area_m2 * cumulative_animal_milk_output_bq_m2
        )
        beef_activity_bq = activity_area_m2 * (
            cumulative_beef_consumed_hto_bq_m2
            + cumulative_beef_consumed_obt_bq_m2
        )
        excreted_activity_bq = (
            activity_area_m2 * cumulative_animal_excretion_bq_m2
        )
        deep_loss_bq = activity_area_m2 * cumulative_deep_loss_bq_m2
        decay_loss_bq = activity_area_m2 * ecological_decay_bq_m2
        environmental_inventory_bq = (
            activity_area_m2 * ecological_inventory_bq_m2
        )
        accounted_activity_bq = activity_area_m2 * (
            ecological_inventory_bq_m2
            + ecological_boundary_bq_m2
            + ecological_decay_bq_m2
        )
        rows.append({
            "time": start + timedelta(seconds=(index + 1) * dt),
            "air_hto_concentration": air,
            "primary_air_hto_concentration": primary,
            "secondary_air_hto_concentration": secondary,
            "raw_wind_speed_m_s": calm.raw_wind_speed_m_s,
            "effective_wind_speed_m_s": calm.effective_wind_speed_m_s,
            "calm_wind_applied": calm.applied,
            "calm_wind_event_count": calm_wind_event_count,
            "reemission_feedback_delay_s": feedback_delay_s,
            "stack_release_bq_s": stack_release_bq_s,
            "plume_source_before_depletion_bq_s": depletion.source_before_bq_s,
            "plume_source_after_depletion_bq_s": depletion.source_after_bq_s,
            "remaining_source_bq_s": depletion.source_after_bq_s,
            "dry_depletion_bq_s": depletion.dry_depletion_bq_s,
            "wet_depletion_bq_s": depletion.wet_depletion_bq_s,
            "wet_scavenging_coefficient_s": wet_rate,
            "wet_scavenging_parameter_set": depletion_config[
                "wet_scavenging_parameter_set"
            ],
            "wet_scavenging_power_law_a": depletion_config["power_law_a_s"],
            "wet_scavenging_power_law_b": depletion_config["power_law_b"],
            "dry_deposition_flux_bq_m2_s": dry_ledger.surface_flux_bq_m2_s,
            "dry_deposition_footprint_area_m2": dry_ledger.footprint_area_m2,
            "wet_deposition_flux_bq_m2_s": wet_ledger.surface_flux_bq_m2_s,
            "wet_deposition_footprint_area_m2": wet_ledger.footprint_area_m2,
            "dry_vd_cair_diagnostic_bq_m2_s": (
                diag.dry_vd_cair_diagnostic_bq_m2_s
            ),
            "surface_dry_input_bq_s": dry_ledger.surface_input_bq_s,
            "surface_wet_input_bq_s": wet_ledger.surface_input_bq_s,
            "dry_interface_residual_bq_s": dry_ledger.interface_residual_bq_s,
            "wet_interface_residual_bq_s": wet_ledger.interface_residual_bq_s,
            "combined_deposition_interface_residual_bq_s": (
                dry_ledger.interface_residual_bq_s
                + wet_ledger.interface_residual_bq_s
            ),
            "stack_release_bq": cumulative_stack_release_bq,
            "external_stack_input_bq": cumulative_stack_release_bq,
            "plume_dry_loss_bq": cumulative_dry_plume_loss_bq,
            "dry_plume_loss_bq": cumulative_dry_plume_loss_bq,
            "plume_wet_loss_bq": cumulative_wet_plume_loss_bq,
            "wet_plume_loss_bq": cumulative_wet_plume_loss_bq,
            "surface_dry_input_bq": cumulative_dry_surface_input_bq,
            "dry_surface_input_bq": cumulative_dry_surface_input_bq,
            "surface_wet_input_bq": cumulative_wet_surface_input_bq,
            "wet_surface_input_bq": cumulative_wet_surface_input_bq,
            "activity_accounting_area_m2": activity_area_m2,
            "environmental_input_bq": (
                activity_area_m2 * external_ecological_input_bq_m2
            ),
            "environmental_inventory_bq": environmental_inventory_bq,
            "harvested_activity_bq": harvested_activity_bq,
            "milk_activity_bq": milk_activity_bq,
            "beef_activity_bq": beef_activity_bq,
            "excreted_activity_bq": excreted_activity_bq,
            "deep_loss_bq": deep_loss_bq,
            "runoff_bypass_bq": (
                activity_area_m2 * cumulative_runoff_bypass_bq_m2
            ),
            "decay_loss_bq": decay_loss_bq,
            "accounted_environmental_activity_bq": accounted_activity_bq,
            "activity_residual_bq": activity_residual_bq,
            "activity_relative_residual": (
                abs(activity_residual_bq)
                / max(
                    activity_area_m2 * external_ecological_input_bq_m2,
                    1.0e-30,
                )
            ),
            "stack_activity_margin_bq": (
                cumulative_stack_release_bq - accounted_activity_bq
            ),
            "dry_interface_residual_bq": (
                cumulative_dry_plume_loss_bq
                - cumulative_dry_surface_input_bq
            ),
            "wet_interface_residual_bq": (
                cumulative_wet_plume_loss_bq
                - cumulative_wet_surface_input_bq
            ),
            "combined_deposition_interface_residual_bq": (
                cumulative_dry_plume_loss_bq
                + cumulative_wet_plume_loss_bq
                - cumulative_dry_surface_input_bq
                - cumulative_wet_surface_input_bq
            ),
            "surface_environmental_inventory_bq_m2": state.total_hto_bq_m2,
            "surface_boundary_output_bq_m2": (
                cumulative_surface_boundary_output_bq_m2
            ),
            "surface_decay_loss_bq_m2": cumulative_surface_decay_bq_m2,
            "surface_deposition_bq_s": (
                depletion.dry_depletion_bq_s + depletion.wet_depletion_bq_s
            ),
            "depletion_deposition_mismatch_bq_s": (
                depletion.source_before_bq_s
                - depletion.source_after_bq_s
                - depletion.dry_depletion_bq_s
                - depletion.wet_depletion_bq_s
            ),
            "surface_reemission_to_air_bq_s": (
                diag.total_reemission_bq_m2_s
                * config["coupling"]["feedback_area_m2"]
            ),
            "secondary_area_source_bq_s": (
                lagged_reemission * config["coupling"]["feedback_area_m2"]
            ),
            "soil_water_storage": state.soil_water_m,
            "soil_hto_inventory": state.soil_hto_bq_m2,
            "soil_hto_concentration": state.soil_hto_bq_m2 / state.soil_water_m,
            "soil_evaporation": diag.soil_evaporation_m_s,
            "plant_transpiration": diag.plant_transpiration_m_s,
            "root_water_uptake": diag.root_uptake_m_s,
            "precipitation": diag.precipitation_m_s,
            "infiltration": diag.infiltration_m_s,
            "runoff": diag.runoff_m_s,
            "rain_infiltration_hto_flux": diag.rain_infiltration_hto_bq_m2_s,
            "rain_runoff_hto_flux": diag.rain_runoff_hto_bq_m2_s,
            "atmospheric_wet_deposition_hto_flux": (
                diag.atmospheric_wet_deposition_bq_m2_s
            ),
            "atmospheric_dry_deposition_hto_flux": (
                diag.atmospheric_dry_deposition_bq_m2_s
            ),
            "net_leaf_exchange_flux": diag.net_leaf_exchange_bq_m2_s,
            "leaf_uptake_flux": diag.leaf_uptake_bq_m2_s,
            "leaf_release_flux": diag.leaf_release_bq_m2_s,
            "leaf_exchange_conductance_m_s": diag.leaf_conductance_m_s,
            "leaf_equilibrium_air_concentration": (
                diag.leaf_equilibrium_air_bq_m3
            ),
            "leaf_aerodynamic_resistance_s_m": (
                diag.leaf_aerodynamic_resistance_s_m
            ),
            "leaf_boundary_resistance_s_m": (
                diag.leaf_boundary_resistance_s_m
            ),
            "leaf_canopy_resistance_s_m": (
                diag.leaf_canopy_resistance_s_m
            ),
            "leaf_friction_velocity_m_s": diag.leaf_friction_velocity_m_s,
            "leaf_wind_speed_m_s": diag.leaf_wind_speed_m_s,
            "leaf_monin_obukhov_length_m": (
                diag.leaf_monin_obukhov_length_m
                if math.isfinite(diag.leaf_monin_obukhov_length_m)
                else 0.0
            ),
            "crop_lai": crop_lai,
            "crop_present": crop_lai > 0.0,
            "crop_growth_fraction": growth_fraction,
            "edible_fresh_mass_kg_m2": edible_fresh_mass,
            "edible_tfwt_inventory_bq_m2": state.edible_tfwt_bq_m2,
            "edible_obt_inventory_bq_m2": state.edible_obt_bq_m2,
            "edible_tfwt_bq_m3_water": edible.tfwt_bq_m3_water,
            "edible_obt_bq_kg_fresh": edible.obt_bq_kg_fresh,
            "edible_obt_bq_kg_dry": edible.obt_bq_kg_dry,
            "harvested_hto_bq_m2": state.harvested_hto_bq_m2,
            "harvested_obt_bq_m2": state.harvested_obt_bq_m2,
            "cut_plant_hto_bq_m2": state.cut_plant_hto_bq_m2,
            "cut_plant_obt_bq_m2": state.cut_plant_obt_bq_m2,
            "tfwt_to_edible_flux": diag.tfwt_to_edible_bq_m2_s,
            "obt_to_edible_flux": diag.obt_to_edible_bq_m2_s,
            "harvest_event": harvest_event,
            "harvest_fraction": harvest_fraction,
            "harvest_effective_doy": (
                next_step_time.timetuple().tm_yday if harvest_event else 0
            ),
            **food_outputs,
            "milk_hto_bq_l": animal_diag.milk_hto_bq_l,
            "milk_obt_bq_l": animal_diag.milk_obt_bq_l,
            "beef_hto_bq_kg": beef_diag.beef_hto_bq_kg,
            "beef_obt_bq_kg": beef_diag.beef_obt_bq_kg,
            "beef_product_hto_bq_m2": beef_product_state.hto_bq_m2,
            "beef_product_obt_bq_m2": beef_product_state.obt_bq_m2,
            "beef_product_mass_kg_m2": beef_product_state.edible_mass_kg_m2,
            "beef_produced_hto_bq_m2": cumulative_beef_produced_hto_bq_m2,
            "beef_produced_obt_bq_m2": cumulative_beef_produced_obt_bq_m2,
            "beef_consumed_hto_bq_m2": cumulative_beef_consumed_hto_bq_m2,
            "beef_consumed_obt_bq_m2": cumulative_beef_consumed_obt_bq_m2,
            "beef_product_decay_bq_m2": cumulative_beef_decay_bq_m2,
            "beef_produced_mass_kg_m2_s": beef_diag.produced_mass_kg_m2_s,
            "beef_consumed_mass_kg_m2_s": beef_diag.consumed_mass_kg_m2_s,
            "beef_product_activity_residual_bq_m2": (
                beef_diag.activity_closure.residual_bq
            ),
            "beef_product_mass_residual_kg_m2": beef_diag.mass_residual_kg_m2,
            "animal_body_hto_bq_m2": animal_state.body_hto_bq,
            "animal_body_obt_bq_m2": animal_state.body_obt_bq,
            "animal_input_bq_m2": cumulative_animal_input_bq_m2,
            "animal_milk_output_bq_m2": (
                cumulative_animal_milk_output_bq_m2
            ),
            "animal_excretion_bq_m2": cumulative_animal_excretion_bq_m2,
            "animal_decay_bq_m2": cumulative_animal_decay_bq_m2,
            "animal_slaughter_bq_m2": cumulative_animal_slaughter_bq_m2,
            "animal_product_activity_residual_bq_m2": (
                cumulative_animal_input_bq_m2
                - cumulative_animal_milk_output_bq_m2
                - cumulative_animal_excretion_bq_m2
                - cumulative_animal_decay_bq_m2
                - cumulative_beef_consumed_hto_bq_m2
                - cumulative_beef_consumed_obt_bq_m2
                - cumulative_beef_decay_bq_m2
                - animal_state.total_bq
                - beef_product_state.total_bq_m2
            ),
            "ecological_box_relative_residual": (
                diag.surface_box_mass_closure.residual_bq_m2
                + animal_diag.closure.residual_bq
                + beef_diag.activity_closure.residual_bq
            )
            / max(
                state.total_hto_bq_m2
                + animal_state.total_bq
                + beef_product_state.total_bq_m2,
                1.0e-30,
            ),
            **dose_totals,
            "dose_age_group": config["dose"]["active_age_group"],
            "dose_receptor_downwind_m": downwind_m,
            "dose_receptor_crosswind_m": crosswind_m,
            "deep_drainage": diag.drainage_m_s,
            "plant_tfwt_inventory": state.plant_tfwt_bq_m2,
            "whole_plant_water_bq_m2": state.plant_tfwt_bq_m2,
            "plant_tfwt_concentration": state.plant_tfwt_bq_m2 / config["plant"]["water_storage_m"],
            "plant_obt_inventory": state.plant_obt_bq_m2,
            "whole_plant_obt_bq_m2": state.plant_obt_bq_m2,
            "soil_reemission_flux": diag.soil_reemission_bq_m2_s,
            "plant_reemission_flux": diag.plant_reemission_bq_m2_s,
            "total_reemission_flux": diag.total_reemission_bq_m2_s,
            "surface_box_absolute_residual_bq_m2": (
                diag.surface_box_mass_closure.residual_bq_m2
            ),
            "surface_box_relative_residual": (
                diag.surface_box_mass_closure.relative_error
            ),
            # Deprecated output aliases retained for one compatibility cycle.
            "mass_balance_error": diag.surface_box_mass_closure.residual_bq_m2,
            "mass_balance_relative_error": (
                diag.surface_box_mass_closure.relative_error
            ),
        })
    frame = pd.DataFrame(rows)
    numeric = frame.select_dtypes(include=[np.number])
    physical = numeric.drop(
        columns=[
            "mass_balance_error",
            "surface_box_absolute_residual_bq_m2",
            "depletion_deposition_mismatch_bq_s",
            "dry_interface_residual_bq_s",
            "wet_interface_residual_bq_s",
            "combined_deposition_interface_residual_bq_s",
            "dry_interface_residual_bq",
            "wet_interface_residual_bq",
            "combined_deposition_interface_residual_bq",
            "net_leaf_exchange_flux",
            "leaf_monin_obukhov_length_m",
            "beef_product_activity_residual_bq_m2",
            "beef_product_mass_residual_kg_m2",
            "ecological_box_relative_residual",
            "animal_product_activity_residual_bq_m2",
            "activity_residual_bq",
            "stack_activity_margin_bq",
        ]
    )
    if not np.isfinite(numeric.to_numpy()).all():
        raise RuntimeError("Short case produced non-finite values")
    negative_columns = physical.columns[(physical < -1.0e-12).any()].tolist()
    if negative_columns:
        raise RuntimeError(
            f"Short case produced negative physical values: {negative_columns}"
        )
    return frame
