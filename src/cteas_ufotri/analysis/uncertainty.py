from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from statistics import NormalDist
from typing import Callable

import numpy as np
from scipy.stats import spearmanr


@dataclass(frozen=True)
class UncertaintyResult:
    seed: int
    method: str
    parameter_samples: dict[str, np.ndarray]
    outcomes: dict[str, np.ndarray]
    statistics: dict[str, dict[str, float]]
    rank_correlations: dict[str, dict[str, float]]
    pathway_contributions: dict[str, float]


def _unit_samples(count: int, dimensions: int, method: str, seed: int) -> np.ndarray:
    if count <= 0 or dimensions <= 0:
        raise ValueError("Sample count and dimension must be positive")
    rng = np.random.default_rng(seed)
    if method == "monte_carlo":
        return rng.random((count, dimensions))
    if method == "latin_hypercube":
        values = np.empty((count, dimensions), dtype=float)
        for dimension in range(dimensions):
            strata = (np.arange(count) + rng.random(count)) / count
            values[:, dimension] = strata[rng.permutation(count)]
        return values
    raise ValueError(f"Unsupported sampling method: {method}")


def sample_parameters(
    specifications: list[dict],
    count: int,
    method: str,
    seed: int,
) -> dict[str, np.ndarray]:
    unit = _unit_samples(count, len(specifications), method, seed)
    normal = NormalDist()
    result: dict[str, np.ndarray] = {}
    for index, specification in enumerate(specifications):
        name = specification["name"]
        distribution = specification["distribution"]
        u = np.clip(unit[:, index], 1.0e-12, 1.0 - 1.0e-12)
        if distribution == "uniform":
            values = float(specification["low"]) + u * (
                float(specification["high"]) - float(specification["low"])
            )
        elif distribution in {"normal", "lognormal"}:
            z = np.array([normal.inv_cdf(float(value)) for value in u])
            values = float(specification["mean"]) + float(
                specification["std"]
            ) * z
            if distribution == "lognormal":
                values = np.exp(values)
        else:
            raise ValueError(f"Unsupported distribution: {distribution}")
        result[name] = values
    return result


def _set_path(config: dict, path: str, value: float) -> None:
    keys = path.split(".")
    target = config
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = float(value)


def run_uncertainty(
    model: Callable[[dict], dict[str, float]],
    base_config: dict,
    specifications: list[dict],
    count: int,
    method: str,
    seed: int,
    *,
    pathway_output_names: list[str] | None = None,
) -> UncertaintyResult:
    samples = sample_parameters(specifications, count, method, seed)
    collected: dict[str, list[float]] = {}
    for sample_index in range(count):
        config = deepcopy(base_config)
        for specification in specifications:
            _set_path(
                config,
                specification["path"],
                samples[specification["name"]][sample_index],
            )
        output = model(config)
        for name, value in output.items():
            collected.setdefault(name, []).append(float(value))
    outcomes = {name: np.asarray(values) for name, values in collected.items()}
    statistics = {
        name: {
            "median": float(np.median(values)),
            "p05": float(np.quantile(values, 0.05)),
            "p95": float(np.quantile(values, 0.95)),
            "mean": float(np.mean(values)),
            "std": float(np.std(values, ddof=1)) if count > 1 else 0.0,
        }
        for name, values in outcomes.items()
    }
    correlations: dict[str, dict[str, float]] = {}
    for parameter, values in samples.items():
        correlations[parameter] = {}
        for output_name, output_values in outcomes.items():
            if np.all(values == values[0]) or np.all(output_values == output_values[0]):
                coefficient = 0.0
            else:
                coefficient = spearmanr(values, output_values).statistic
            correlations[parameter][output_name] = (
                float(coefficient) if np.isfinite(coefficient) else 0.0
            )
    pathway_names = pathway_output_names or []
    pathway_means = {
        name: max(float(np.mean(outcomes[name])), 0.0)
        for name in pathway_names
        if name in outcomes
    }
    total = sum(pathway_means.values())
    contributions = {
        name: value / total if total > 0 else 0.0
        for name, value in pathway_means.items()
    }
    return UncertaintyResult(
        seed,
        method,
        samples,
        outcomes,
        statistics,
        correlations,
        contributions,
    )


def one_at_a_time_sensitivity(
    model: Callable[[dict], dict[str, float]],
    base_config: dict,
    specifications: list[dict],
    output_name: str,
    relative_delta: float = 0.10,
) -> dict[str, float]:
    if not 0.0 < relative_delta < 1.0:
        raise ValueError("OAT relative delta must be within (0, 1)")
    sensitivities: dict[str, float] = {}
    for specification in specifications:
        keys = specification["path"].split(".")
        value = base_config
        for key in keys:
            value = value[key]
        base_value = float(value)
        low = deepcopy(base_config)
        high = deepcopy(base_config)
        _set_path(low, specification["path"], base_value * (1.0 - relative_delta))
        _set_path(high, specification["path"], base_value * (1.0 + relative_delta))
        low_output = float(model(low)[output_name])
        high_output = float(model(high)[output_name])
        denominator = 2.0 * relative_delta * base_value
        sensitivities[specification["name"]] = (
            (high_output - low_output) / denominator
            if denominator != 0
            else 0.0
        )
    return sensitivities
