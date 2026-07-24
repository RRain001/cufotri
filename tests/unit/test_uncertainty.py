from __future__ import annotations

import numpy as np
import pytest

from cteas_ufotri.analysis.uncertainty import (
    one_at_a_time_sensitivity,
    run_uncertainty,
    sample_parameters,
)


SPECS = [
    {
        "name": "x",
        "path": "parameters.x",
        "distribution": "uniform",
        "low": 0.5,
        "high": 1.5,
    },
    {
        "name": "y",
        "path": "parameters.y",
        "distribution": "uniform",
        "low": 1.0,
        "high": 3.0,
    },
]


def _model(config):
    x = config["parameters"]["x"]
    y = config["parameters"]["y"]
    return {"total": x + 2.0 * y, "path_x": x, "path_y": 2.0 * y}


@pytest.mark.parametrize("method", ["monte_carlo", "latin_hypercube"])
def test_sampling_is_fixed_seed_reproducible_and_bounded(method):
    first = sample_parameters(SPECS, 32, method, 1234)
    second = sample_parameters(SPECS, 32, method, 1234)
    for name in first:
        assert np.array_equal(first[name], second[name])
    assert first["x"].min() >= 0.5
    assert first["x"].max() <= 1.5
    assert first["y"].min() >= 1.0
    assert first["y"].max() <= 3.0


def test_uncertainty_statistics_rank_correlation_and_path_contribution():
    result = run_uncertainty(
        _model,
        {"parameters": {"x": 1.0, "y": 2.0}},
        SPECS,
        128,
        "latin_hypercube",
        20260724,
        pathway_output_names=["path_x", "path_y"],
    )
    assert result.statistics["total"]["p05"] < result.statistics["total"]["median"]
    assert result.statistics["total"]["median"] < result.statistics["total"]["p95"]
    assert result.statistics["total"]["std"] > 0.0
    assert result.rank_correlations["x"]["total"] > 0.0
    assert result.rank_correlations["y"]["total"] > result.rank_correlations["x"]["total"]
    assert sum(result.pathway_contributions.values()) == pytest.approx(1.0)


def test_oat_sensitivity_recovers_linear_derivatives():
    sensitivity = one_at_a_time_sensitivity(
        _model,
        {"parameters": {"x": 1.0, "y": 2.0}},
        SPECS,
        "total",
    )
    assert sensitivity["x"] == pytest.approx(1.0)
    assert sensitivity["y"] == pytest.approx(2.0)

