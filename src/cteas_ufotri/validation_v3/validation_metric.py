"""Deterministic numerical and conservation metrics for P7.7A.

These functions compare supplied model and reference values.  They never
generate reference data from a production solver and never infer missing
parameters.  Inputs are validated strictly so a metric cannot silently drop
non-finite or unpaired observations.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any


class ValidationMetricError(ValueError):
    """A metric input is malformed or not comparable."""


class MetricName(str, Enum):
    """Supported P7.7A metric names."""

    RMSE = "RMSE"
    MAE = "MAE"
    RELATIVE_ERROR = "relative_error"
    BIAS = "bias"
    CONSERVATION_RESIDUAL = "conservation_residual"
    TRAJECTORY_COMPARISON = "trajectory_comparison"
    DECAY_ERROR = "decay_error"
    STATE_DIFFERENCE = "state_difference"


def _number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationMetricError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationMetricError(f"{field} must be finite")
    return result


def _series(value: Iterable[float], *, field: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes, Mapping)):
        raise ValidationMetricError(f"{field} must be a numeric sequence")
    try:
        result = tuple(
            _number(item, field=f"{field}[{index}]")
            for index, item in enumerate(value)
        )
    except TypeError as exc:
        raise ValidationMetricError(f"{field} must be an iterable") from exc
    if not result:
        raise ValidationMetricError(f"{field} must not be empty")
    return result


def _paired(
    model: Iterable[float],
    reference: Iterable[float],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    model_values = _series(model, field="model")
    reference_values = _series(reference, field="reference")
    if len(model_values) != len(reference_values):
        raise ValidationMetricError("model and reference trajectories must align")
    return model_values, reference_values


def rmse(model: Iterable[float], reference: Iterable[float]) -> float:
    """Root-mean-square error in the observable's native unit."""

    model_values, reference_values = _paired(model, reference)
    return math.sqrt(
        math.fsum(
            (model_value - reference_value) ** 2
            for model_value, reference_value in zip(model_values, reference_values)
        )
        / len(model_values)
    )


def mae(model: Iterable[float], reference: Iterable[float]) -> float:
    """Mean absolute error in the observable's native unit."""

    model_values, reference_values = _paired(model, reference)
    return math.fsum(
        abs(model_value - reference_value)
        for model_value, reference_value in zip(model_values, reference_values)
    ) / len(model_values)


def relative_error(model: float, reference: float) -> float:
    """Absolute scalar relative error, with an explicit zero-reference rule."""

    model_value = _number(model, field="model")
    reference_value = _number(reference, field="reference")
    if reference_value == 0.0:
        return 0.0 if model_value == 0.0 else math.inf
    return abs(model_value - reference_value) / abs(reference_value)


def bias(model: Iterable[float], reference: Iterable[float]) -> float:
    """Mean signed model-minus-reference error."""

    model_values, reference_values = _paired(model, reference)
    return math.fsum(
        model_value - reference_value
        for model_value, reference_value in zip(model_values, reference_values)
    ) / len(model_values)


def conservation_residual(
    input_inventory: float,
    output_inventory: float,
    storage_change: float,
) -> float:
    """Return ``input - output - storage_change`` in inventory units.

    Existing solver ledgers remain the source of the three terms.  This
    helper only evaluates their closure and does not replace or mutate those
    ledgers.
    """

    return (
        _number(input_inventory, field="input_inventory")
        - _number(output_inventory, field="output_inventory")
        - _number(storage_change, field="storage_change")
    )


@dataclass(frozen=True)
class ConservationLedger:
    """Minimal adapter for an existing interval inventory ledger."""

    input_inventory: float
    output_inventory: float
    storage_change: float
    residual: float

    def __post_init__(self) -> None:
        for field in (
            "input_inventory",
            "output_inventory",
            "storage_change",
            "residual",
        ):
            value = _number(getattr(self, field), field=field)
            object.__setattr__(self, field, value)

    @property
    def calculated_residual(self) -> float:
        """Recompute closure from ledger terms without overwriting the ledger."""

        return conservation_residual(
            self.input_inventory,
            self.output_inventory,
            self.storage_change,
        )

    @property
    def residual_difference(self) -> float:
        """Difference between the recorded and independently recalculated residual."""

        return self.calculated_residual - self.residual


def trajectory_comparison(
    model: Iterable[float],
    reference: Iterable[float],
) -> float:
    """RMSE over an aligned state trajectory."""

    return rmse(model, reference)


def decay_error(model: Iterable[float], reference: Iterable[float]) -> float:
    """Error in net trajectory decrease, preserving the time ordering."""

    model_values, reference_values = _paired(model, reference)
    model_decrease = model_values[0] - model_values[-1]
    reference_decrease = reference_values[0] - reference_values[-1]
    return abs(model_decrease - reference_decrease)


def state_difference(model: Iterable[float], reference: Iterable[float]) -> float:
    """Maximum absolute difference over an aligned state trajectory."""

    model_values, reference_values = _paired(model, reference)
    return max(
        abs(model_value - reference_value)
        for model_value, reference_value in zip(model_values, reference_values)
    )


def _coerce_metric_name(value: MetricName | str) -> MetricName:
    if isinstance(value, MetricName):
        return value
    if not isinstance(value, str):
        raise ValidationMetricError("metric_name must be text")
    for item in MetricName:
        if value == item.value or value.upper() == item.value.upper():
            return item
    allowed = ", ".join(item.value for item in MetricName)
    raise ValidationMetricError(f"metric_name must be one of {allowed}")


def compute_metric(
    metric_name: MetricName | str,
    model: Any,
    reference: Any = None,
) -> float:
    """Compute one named metric from caller-supplied model/reference values."""

    metric = _coerce_metric_name(metric_name)
    if metric is MetricName.CONSERVATION_RESIDUAL:
        if isinstance(model, ConservationLedger):
            return model.calculated_residual
        if not isinstance(model, Mapping):
            raise ValidationMetricError(
                "conservation_residual requires a ConservationLedger or mapping"
            )
        try:
            return conservation_residual(
                model["input_inventory"],
                model["output_inventory"],
                model["storage_change"],
            )
        except KeyError as exc:
            raise ValidationMetricError(
                "conservation residual mapping requires input_inventory, "
                "output_inventory, and storage_change"
            ) from exc

    if reference is None:
        raise ValidationMetricError(f"{metric.value} requires reference data")
    if metric is MetricName.RMSE:
        return rmse(model, reference)
    if metric is MetricName.MAE:
        return mae(model, reference)
    if metric is MetricName.RELATIVE_ERROR:
        return relative_error(model, reference)
    if metric is MetricName.BIAS:
        return bias(model, reference)
    if metric is MetricName.TRAJECTORY_COMPARISON:
        return trajectory_comparison(model, reference)
    if metric is MetricName.DECAY_ERROR:
        return decay_error(model, reference)
    if metric is MetricName.STATE_DIFFERENCE:
        return state_difference(model, reference)
    raise ValidationMetricError(f"unsupported metric {metric.value}")


__all__ = [
    "ConservationLedger",
    "MetricName",
    "ValidationMetricError",
    "bias",
    "compute_metric",
    "conservation_residual",
    "decay_error",
    "mae",
    "relative_error",
    "rmse",
    "state_difference",
    "trajectory_comparison",
]
