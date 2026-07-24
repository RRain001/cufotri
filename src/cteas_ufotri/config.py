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
    config = _merge(load_yaml(parameters_path), load_yaml(case_path))
    required = (
        "atmosphere", "soil", "plant", "reemission", "physics",
        "numerics", "synthetic_forcing", "outputs", "site", "source",
        "coupling", "evapotranspiration",
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
    if depletion["wet_scavenging_enabled"] and depletion["wet_scavenging_rate_s"] < 0:
        raise ValueError("Wet scavenging rate must be non-negative")
    if config["soil"]["layer_model"] != "single_top_5cm":
        raise ValueError("The formal minimal baseline supports one 5 cm soil layer")
    root_fraction = config["plant"]["root_uptake_fraction_from_modelled_layer"]
    if not 0 <= root_fraction <= 1:
        raise ValueError("Modelled-layer root uptake fraction must be within [0, 1]")
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
    delay = float(coupling["reemission_feedback_delay_s"])
    if delay < 0 or delay % float(config["time_step_seconds"]) != 0:
        raise ValueError("Re-emission delay must be a non-negative multiple of dt")
    return config
