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
    )
    missing = [name for name in required if name not in config]
    if missing:
        raise ValueError(f"Missing configuration sections: {', '.join(missing)}")
    if config["time_step_seconds"] <= 0 or config["duration_hours"] <= 0:
        raise ValueError("Simulation duration and time step must be positive")
    if config["source"]["pollutant"] != "HTO":
        raise ValueError("The current model supports HTO only")
    return config
