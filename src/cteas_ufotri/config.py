from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def load_configuration(
    parameters_path: str | Path, case_path: str | Path
) -> dict[str, Any]:
    case_file = Path(case_path)
    case_values = load_yaml(case_file)
    base_case = case_values.pop("_base_case", None)
    if base_case is None:
        config = _merge(load_yaml(parameters_path), case_values)
    else:
        config = _merge(
            load_configuration(parameters_path, case_file.parent / base_case),
            case_values,
        )
    required = (
        "atmosphere", "soil", "plant", "reemission", "physics",
        "numerics", "synthetic_forcing", "outputs", "site", "source",
        "coupling", "evapotranspiration", "crops", "foodchain", "dose",
        "uncertainty", "deposition",
    )
    missing = [name for name in required if name not in config]
    if missing:
        raise ValueError(f"Missing configuration sections: {', '.join(missing)}")
    if config["time_step_seconds"] <= 0 or config["duration_hours"] <= 0:
        raise ValueError("Simulation duration and time step must be positive")
    if config["source"]["pollutant"] != "HTO":
        raise ValueError("The current model supports HTO only")
    calm = config["atmosphere"]["calm_wind"]
    if calm["mode"] not in {"minimum_effective_wind", "skip_gaussian", "error"}:
        raise ValueError("Unsupported calm-wind mode")
    if config["atmosphere"]["reemission_feedback_mode"] not in {
        "area_source", "point_equivalent", "off"
    }:
        raise ValueError("Unsupported re-emission feedback mode")
    depletion = config["atmosphere"]["depletion"]
    if depletion["method"] != "segment_exponential":
        raise ValueError("Unsupported atmospheric depletion method")
    wet_mode = depletion.get(
        "wet_scavenging_mode",
        (
            "constant_scavenging_coefficient"
            if depletion.get("wet_scavenging_enabled", False)
            else "off"
        ),
    )
    if wet_mode not in {
        "off",
        "constant_scavenging_coefficient",
        "precipitation_power_law",
    }:
        raise ValueError("Unsupported wet-scavenging mode")
    if min(
        float(depletion.get("constant_scavenging_coefficient_s", 0.0)),
        float(depletion.get("power_law_a_s", 0.0)),
        float(depletion.get("power_law_b", 1.0)),
    ) < 0:
        raise ValueError("Wet-scavenging parameters must be non-negative")
    depletion["wet_scavenging_mode"] = wet_mode
    wet_sets = depletion.get("wet_scavenging_parameter_sets", {})
    selected_wet_set = depletion.get("wet_scavenging_parameter_set")
    if selected_wet_set not in wet_sets:
        raise ValueError("Selected wet-scavenging parameter set is missing")
    wet_parameters = wet_sets[selected_wet_set]
    if wet_parameters.get("precipitation_unit") != "mm_h":
        raise ValueError("Wet-scavenging precipitation unit must be mm_h")
    if min(
        float(wet_parameters["a"]),
        float(wet_parameters["b"]),
    ) < 0.0:
        raise ValueError("Wet-scavenging parameter-set values must be non-negative")
    depletion["power_law_a_s"] = float(wet_parameters["a"])
    depletion["power_law_b"] = float(wet_parameters["b"])
    depletion["wet_scavenging_parameter_status"] = str(wet_parameters["status"])
    depletion["wet_scavenging_parameter_source"] = str(wet_parameters["source"])
    if config["soil"]["layer_model"] not in {
        "single_top_5cm",
        "surface_root_deep_3box",
    }:
        raise ValueError("Unsupported soil layer model")
    root_fraction = config["plant"]["root_uptake_fraction_from_modelled_layer"]
    if not 0 <= root_fraction <= 1:
        raise ValueError("Modelled-layer root uptake fraction must be within [0, 1]")
    leaf_mode = config["plant"].get(
        "leaf_exchange_mode",
        (
            "deposition_only"
            if config["plant"].get("direct_leaf_uptake_enabled", False)
            else "off"
        ),
    )
    if leaf_mode not in {"off", "deposition_only", "bidirectional_resistance"}:
        raise ValueError("Unsupported leaf-exchange mode")
    config["plant"]["leaf_exchange_mode"] = leaf_mode
    plant = config["plant"]
    if plant.get("leaf_resistance_parameterization") != (
        "golder_monin_obukhov_flat_plate"
    ):
        raise ValueError("Unsupported leaf-resistance parameterization")
    leaf_positive = (
        "leaf_canopy_height_m",
        "leaf_characteristic_length_m",
        "leaf_air_kinematic_viscosity_m2_s",
        "leaf_water_vapour_diffusivity_m2_s",
        "leaf_von_karman_constant",
        "leaf_minimum_wind_speed_m_s",
        "leaf_stomatal_resistance_day_s_m",
        "leaf_stomatal_resistance_night_s_m",
        "leaf_isotope_fractionation_liquid_to_vapour",
    )
    if any(float(plant[name]) <= 0.0 for name in leaf_positive):
        raise ValueError("Leaf-resistance parameters must be positive")
    crops = config["crops"]
    if crops["active_crop"] not in crops["parameters"]:
        raise ValueError("Active crop is missing from crop parameters")
    if crops["lai_mode"] not in {
        "constant",
        "piecewise_growth_stage",
        "smooth_seasonal",
        "external_timeseries",
    }:
        raise ValueError("Unsupported crop LAI mode")
    from .crop.phenology import CropParameters

    for crop_name, crop_values in crops["parameters"].items():
        CropParameters.from_mapping(crop_name, crop_values)
    foodchain = config["foodchain"]
    if foodchain["animal_mode"] not in {"off", "minimal_cow"}:
        raise ValueError("Unsupported animal food-chain mode")
    beef = foodchain["animal_products"]["beef"]
    if beef["mode"] not in {"off", "continuous_herd_turnover"}:
        raise ValueError("Unsupported beef-production mode")
    if min(
        float(beef["turnover_rate_d-1"]),
        float(beef["edible_meat_mass_kg_per_head"]),
    ) < 0.0:
        raise ValueError("Beef-production parameters must be non-negative")
    dose = config["dose"]
    if dose["active_age_group"] not in dose["age_groups"]:
        raise ValueError("Active dose age group is missing")
    if config["uncertainty"]["sampling_method"] not in {
        "monte_carlo",
        "latin_hypercube",
    }:
        raise ValueError("Unsupported uncertainty sampling method")
    shading_mode = config["evapotranspiration"]["lai_shading_mode"]
    if shading_mode not in {"radiation_term_only", "full_penman"}:
        raise ValueError("Unsupported LAI shading mode")
    coupling = config["coupling"]
    rectangle = coupling["feedback_rectangle"]
    derived_area = float(rectangle["length_m"]) * float(rectangle["width_m"])
    configured_area = float(coupling.get("feedback_area_m2", derived_area))
    if abs(configured_area - derived_area) > max(1.0e-9 * derived_area, 1.0e-9):
        raise ValueError("Feedback area must equal rectangle length times width")
    atmosphere_area = float(config["atmosphere"]["reemission_feedback_area_m2"])
    if abs(atmosphere_area - derived_area) > max(1.0e-9 * derived_area, 1.0e-9):
        raise ValueError("Legacy atmospheric feedback area conflicts with coupling rectangle")
    config["atmosphere"]["area_source_length_m"] = float(rectangle["length_m"])
    config["atmosphere"]["area_source_width_m"] = float(rectangle["width_m"])
    deposition = config["deposition"]
    for pathway in ("dry", "wet"):
        footprint = deposition.get(f"{pathway}_footprint")
        if not isinstance(footprint, dict):
            raise ValueError(f"Missing {pathway}-deposition footprint")
        if footprint.get("allocation") != "uniform":
            raise ValueError(
                f"Unsupported {pathway}-deposition footprint allocation"
            )
        if float(footprint.get("area_m2", 0.0)) <= 0:
            raise ValueError(
                f"{pathway.capitalize()}-deposition footprint area must be positive"
            )
    delay = float(coupling["reemission_feedback_delay_s"])
    if delay < 0 or delay % float(config["time_step_seconds"]) != 0:
        raise ValueError("Re-emission delay must be a non-negative multiple of dt")
    return config
