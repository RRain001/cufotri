from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def _finite_scalar(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _paired(
    model: Iterable[float],
    reference: Iterable[float],
) -> tuple[np.ndarray, np.ndarray]:
    model_array = np.asarray(list(model), dtype=float)
    reference_array = np.asarray(list(reference), dtype=float)
    if model_array.shape != reference_array.shape:
        raise ValueError("Model and reference arrays must have the same shape")
    mask = np.isfinite(model_array) & np.isfinite(reference_array)
    if not np.any(mask):
        raise ValueError("No finite paired observations")
    return model_array[mask], reference_array[mask]


def absolute_error(model: float, reference: float) -> float:
    """Absolute scalar error in the observable's native unit."""

    return abs(
        _finite_scalar(model, "model")
        - _finite_scalar(reference, "reference")
    )


def relative_error(model: float, reference: float) -> float:
    """Absolute relative scalar error; exact zero/zero is zero."""

    model_value = _finite_scalar(model, "model")
    reference_value = _finite_scalar(reference, "reference")
    if reference_value == 0.0:
        return 0.0 if model_value == 0.0 else math.inf
    return abs(model_value - reference_value) / abs(reference_value)


def bias(model: Iterable[float], reference: Iterable[float]) -> float:
    """Mean signed error in the observable's native unit."""

    model_array, reference_array = _paired(model, reference)
    return float(np.mean(model_array - reference_array))


def normalized_mean_bias(
    model: Iterable[float],
    reference: Iterable[float],
) -> float:
    """Sum(model-reference)/sum(reference), dimensionless."""

    model_array, reference_array = _paired(model, reference)
    denominator = float(np.sum(reference_array))
    numerator = float(np.sum(model_array - reference_array))
    if denominator == 0.0:
        return 0.0 if numerator == 0.0 else math.inf
    return numerator / denominator


def rmse(model: Iterable[float], reference: Iterable[float]) -> float:
    """Root-mean-square error in the observable's native unit."""

    model_array, reference_array = _paired(model, reference)
    return float(np.sqrt(np.mean((model_array - reference_array) ** 2)))


def normalized_rmse(
    model: Iterable[float],
    reference: Iterable[float],
    *,
    normalization: str = "mean",
) -> float:
    """RMSE divided by absolute reference mean or reference range."""

    model_array, reference_array = _paired(model, reference)
    error = float(np.sqrt(np.mean((model_array - reference_array) ** 2)))
    if normalization == "mean":
        denominator = abs(float(np.mean(reference_array)))
    elif normalization == "range":
        denominator = float(np.max(reference_array) - np.min(reference_array))
    else:
        raise ValueError("Normalization must be 'mean' or 'range'")
    if denominator == 0.0:
        return 0.0 if error == 0.0 else math.inf
    return error / denominator


def correlation(
    model: Iterable[float],
    reference: Iterable[float],
) -> float:
    """Pearson correlation; NaN for fewer than two or constant pairs."""

    model_array, reference_array = _paired(model, reference)
    if (
        len(model_array) < 2
        or np.ptp(model_array) == 0.0
        or np.ptp(reference_array) == 0.0
    ):
        return math.nan
    return float(np.corrcoef(model_array, reference_array)[0, 1])


def peak_ratio(model: Iterable[float], reference: Iterable[float]) -> float:
    """Ratio of finite model and reference maxima, dimensionless."""

    model_array, reference_array = _paired(model, reference)
    model_peak = float(np.max(model_array))
    reference_peak = float(np.max(reference_array))
    if reference_peak == 0.0:
        return 1.0 if model_peak == 0.0 else math.inf
    return model_peak / reference_peak


def time_to_peak_error(
    model: Iterable[float],
    reference: Iterable[float],
    time_seconds: Iterable[float],
) -> float:
    """Signed model-minus-reference peak-time error in seconds."""

    model_array = np.asarray(list(model), dtype=float)
    reference_array = np.asarray(list(reference), dtype=float)
    time_array = np.asarray(list(time_seconds), dtype=float)
    if not (
        model_array.shape == reference_array.shape == time_array.shape
    ):
        raise ValueError("Model, reference, and time arrays must align")
    mask = (
        np.isfinite(model_array)
        & np.isfinite(reference_array)
        & np.isfinite(time_array)
    )
    if not np.any(mask):
        raise ValueError("No finite time-to-peak observations")
    model_values = model_array[mask]
    reference_values = reference_array[mask]
    times = time_array[mask]
    return float(
        times[int(np.argmax(model_values))]
        - times[int(np.argmax(reference_values))]
    )


def cumulative_activity_error(
    model_rate: Iterable[float],
    reference_rate: Iterable[float],
    time_seconds: Iterable[float],
) -> float:
    """Absolute trapezoidal cumulative-activity error in rate-unit seconds."""

    model_array = np.asarray(list(model_rate), dtype=float)
    reference_array = np.asarray(list(reference_rate), dtype=float)
    time_array = np.asarray(list(time_seconds), dtype=float)
    if not (
        model_array.shape == reference_array.shape == time_array.shape
    ):
        raise ValueError("Rates and time arrays must align")
    mask = (
        np.isfinite(model_array)
        & np.isfinite(reference_array)
        & np.isfinite(time_array)
    )
    if np.count_nonzero(mask) < 2:
        raise ValueError("At least two finite cumulative-activity points required")
    model_total = float(np.trapezoid(model_array[mask], time_array[mask]))
    reference_total = float(
        np.trapezoid(reference_array[mask], time_array[mask])
    )
    return abs(model_total - reference_total)


def mass_balance_residual(
    initial: float,
    inputs: float,
    outputs: float,
    decay: float,
    final: float,
) -> float:
    """Signed inventory residual in activity units."""

    return (
        _finite_scalar(initial, "initial")
        + _finite_scalar(inputs, "inputs")
        - _finite_scalar(outputs, "outputs")
        - _finite_scalar(decay, "decay")
        - _finite_scalar(final, "final")
    )


def interval_coverage(
    observations: Iterable[float],
    lower: Iterable[float],
    upper: Iterable[float],
) -> float:
    """Fraction of finite observations inside inclusive prediction bounds."""

    observation_array = np.asarray(list(observations), dtype=float)
    lower_array = np.asarray(list(lower), dtype=float)
    upper_array = np.asarray(list(upper), dtype=float)
    if not (
        observation_array.shape == lower_array.shape == upper_array.shape
    ):
        raise ValueError("Observation and interval arrays must align")
    mask = (
        np.isfinite(observation_array)
        & np.isfinite(lower_array)
        & np.isfinite(upper_array)
    )
    if not np.any(mask):
        raise ValueError("No finite interval observations")
    if np.any(lower_array[mask] > upper_array[mask]):
        raise ValueError("Lower interval bound exceeds upper bound")
    covered = (
        (observation_array[mask] >= lower_array[mask])
        & (observation_array[mask] <= upper_array[mask])
    )
    return float(np.mean(covered))


def detection_limit_aware_error(
    model: float,
    reference: float,
    detection_limit: float,
) -> float:
    """Absolute error with nondetect references treated as [0, DL].

    If the reference is at or below the detection limit, any model value in
    [0, DL] has zero error; values above DL are penalized by their exceedance.
    """

    model_value = float(model)
    reference_value = float(reference)
    limit = float(detection_limit)
    if limit < 0.0:
        raise ValueError("Detection limit must be non-negative")
    if not all(math.isfinite(value) for value in (model_value, reference_value)):
        raise ValueError("Detection-limit comparison requires finite values")
    if reference_value <= limit:
        return 0.0 if 0.0 <= model_value <= limit else abs(model_value - limit)
    return abs(model_value - reference_value)
