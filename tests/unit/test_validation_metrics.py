from __future__ import annotations

import math

import pytest

from validation.metrics import (
    absolute_error,
    bias,
    correlation,
    cumulative_activity_error,
    detection_limit_aware_error,
    interval_coverage,
    mass_balance_residual,
    normalized_mean_bias,
    normalized_rmse,
    peak_ratio,
    relative_error,
    rmse,
    time_to_peak_error,
)


def test_scalar_errors_and_zero_reference_policy():
    assert absolute_error(4.0, 3.0) == 1.0
    assert relative_error(4.0, 2.0) == 1.0
    assert relative_error(0.0, 0.0) == 0.0
    assert math.isinf(relative_error(1.0, 0.0))


def test_series_metrics_ignore_only_unpaired_missing_values():
    model = [1.0, 2.0, math.nan, 4.0]
    reference = [1.0, 1.0, 3.0, 5.0]
    assert bias(model, reference) == pytest.approx(0.0)
    assert normalized_mean_bias(model, reference) == pytest.approx(0.0)
    assert rmse(model, reference) == pytest.approx(math.sqrt(2.0 / 3.0))
    assert normalized_rmse(model, reference) == pytest.approx(
        math.sqrt(2.0 / 3.0) / (7.0 / 3.0)
    )


def test_correlation_peak_and_time_to_peak():
    assert correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert math.isnan(correlation([1, 1], [2, 3]))
    assert peak_ratio([1, 4, 2], [1, 2, 1]) == pytest.approx(2.0)
    assert time_to_peak_error(
        [1, 2, 3], [1, 3, 2], [0, 60, 120]
    ) == pytest.approx(60.0)


def test_cumulative_activity_and_mass_balance():
    assert cumulative_activity_error(
        [0, 2, 0], [0, 1, 0], [0, 1, 2]
    ) == pytest.approx(1.0)
    assert mass_balance_residual(10, 5, 3, 2, 10) == pytest.approx(0.0)


def test_interval_coverage_and_detection_limit_policy():
    assert interval_coverage(
        [1, 2, 5], [0, 2, 0], [2, 3, 4]
    ) == pytest.approx(2.0 / 3.0)
    assert detection_limit_aware_error(0.5, 0.2, 1.0) == 0.0
    assert detection_limit_aware_error(2.5, 0.2, 1.0) == pytest.approx(1.5)
    assert detection_limit_aware_error(3.0, 2.0, 1.0) == pytest.approx(1.0)


def test_scalar_metrics_reject_nonfinite_values():
    with pytest.raises(ValueError, match="model must be finite"):
        absolute_error(math.nan, 0.0)
    with pytest.raises(ValueError, match="reference must be finite"):
        relative_error(1.0, math.inf)
    with pytest.raises(ValueError, match="inputs must be finite"):
        mass_balance_residual(0.0, math.nan, 0.0, 0.0, 0.0)
