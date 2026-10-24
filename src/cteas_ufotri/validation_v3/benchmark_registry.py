"""Auditable P7.7B synthetic-benchmark result records and acceptance gate."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import math
import re
from types import MappingProxyType
from typing import Any

from .validation_case import (
    ParameterSnapshot,
    ParameterStatus,
    Provenance,
    ValidationCaseError,
    _thaw_value as _thaw,
)


class BenchmarkResultError(ValueError):
    """A P7.7B benchmark result violates the result contract."""


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_COMPARISONS = frozenset({"ABSOLUTE_LTE", "LTE", "GTE", "EXACT"})


def _text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkResultError(f"{field} must be a non-empty string")
    return value


def _identifier(value: Any, *, field: str) -> str:
    text = _text(value, field=field)
    if _IDENTIFIER.fullmatch(text) is None:
        raise BenchmarkResultError(f"{field} must be a lower-case identifier")
    return text


def _finite(value: Any, *, field: str, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkResultError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise BenchmarkResultError(f"{field} must be finite")
    if non_negative and number < 0.0:
        raise BenchmarkResultError(f"{field} must be non-negative")
    return number


def _freeze(value: Any, *, field: str) -> Any:
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            raise BenchmarkResultError(f"{field} must contain finite numbers")
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                _text(key, field=f"{field}.key"): _freeze(
                    item,
                    field=f"{field}.{key}",
                )
                for key, item in value.items()
            }
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(
            _freeze(item, field=f"{field}[{index}]")
            for index, item in enumerate(value)
        )
    raise BenchmarkResultError(
        f"{field} must contain only JSON-compatible values"
    )


def _passes(value: float, threshold: float, comparison: str) -> bool:
    if comparison == "ABSOLUTE_LTE":
        return abs(value) <= threshold
    if comparison == "LTE":
        return value <= threshold
    if comparison == "GTE":
        return value >= threshold
    if comparison == "EXACT":
        return value == threshold
    raise BenchmarkResultError(
        "comparison must be ABSOLUTE_LTE, LTE, GTE, or EXACT"
    )


@dataclass(frozen=True)
class BenchmarkMetricResult:
    """One scalar metric with its explicit acceptance rule."""

    metric_name: str
    value: float
    threshold: float
    pass_fail: bool
    unit: str = "1"
    comparison: str = "ABSOLUTE_LTE"
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _text(self.metric_name, field="metric_name")
        value = _finite(self.value, field="value")
        threshold = _finite(self.threshold, field="threshold", non_negative=True)
        if not isinstance(self.pass_fail, bool):
            raise BenchmarkResultError("pass_fail must be a boolean")
        _text(self.unit, field="unit")
        if self.comparison not in _COMPARISONS:
            raise BenchmarkResultError(
                "comparison must be ABSOLUTE_LTE, LTE, GTE, or EXACT"
            )
        if _passes(value, threshold, self.comparison) is not self.pass_fail:
            raise BenchmarkResultError(
                "pass_fail does not match value, threshold, and comparison"
            )
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "threshold", threshold)
        object.__setattr__(self, "details", _freeze(self.details, field="details"))

    @classmethod
    def from_value(
        cls,
        *,
        metric_name: str,
        value: float,
        threshold: float,
        unit: str = "1",
        comparison: str = "ABSOLUTE_LTE",
        details: Mapping[str, Any] | None = None,
    ) -> "BenchmarkMetricResult":
        numeric_value = _finite(value, field="value")
        numeric_threshold = _finite(
            threshold,
            field="threshold",
            non_negative=True,
        )
        return cls(
            metric_name=metric_name,
            value=numeric_value,
            threshold=numeric_threshold,
            pass_fail=_passes(numeric_value, numeric_threshold, comparison),
            unit=unit,
            comparison=comparison,
            details={} if details is None else details,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BenchmarkMetricResult":
        if not isinstance(value, Mapping):
            raise BenchmarkResultError("metric result must be a mapping")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise BenchmarkResultError(f"invalid metric result: {exc}") from exc

    def to_mapping(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "value": self.value,
            "threshold": self.threshold,
            "pass_fail": self.pass_fail,
            "unit": self.unit,
            "comparison": self.comparison,
            "details": _thaw(self.details),
        }


def _coerce_snapshot(value: Any) -> ParameterSnapshot:
    if isinstance(value, ParameterSnapshot):
        return value
    if not isinstance(value, Mapping):
        raise BenchmarkResultError("parameter_snapshot entries must be mappings")
    try:
        return ParameterSnapshot.from_mapping(value)
    except ValidationCaseError as exc:
        raise BenchmarkResultError(str(exc)) from exc


def _coerce_audit(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BenchmarkResultError(f"{field} must be a mapping")
    if not isinstance(value.get("passed"), bool):
        raise BenchmarkResultError(f"{field}.passed must be a boolean")
    frozen = _freeze(value, field=field)
    if not isinstance(frozen, Mapping):
        raise BenchmarkResultError(f"{field} must be a mapping")
    return frozen


@dataclass(frozen=True)
class BenchmarkResult:
    """One deterministic, synthetic-only benchmark execution result."""

    benchmark_id: str
    execution_id: str
    solver_version: str
    input_hash: str
    parameter_snapshot: tuple[ParameterSnapshot, ...] | Sequence[ParameterSnapshot]
    metrics: tuple[BenchmarkMetricResult, ...] | Sequence[BenchmarkMetricResult]
    conservation_result: Mapping[str, Any]
    restart_result: Mapping[str, Any]
    status: str
    provenance: Provenance | Mapping[str, Any]

    def __post_init__(self) -> None:
        _identifier(self.benchmark_id, field="benchmark_id")
        _identifier(self.execution_id, field="execution_id")
        _text(self.solver_version, field="solver_version")
        if not isinstance(self.input_hash, str) or _SHA256.fullmatch(self.input_hash) is None:
            raise BenchmarkResultError("input_hash must be lowercase hexadecimal SHA-256")
        _text(self.status, field="status")

        snapshots = tuple(_coerce_snapshot(item) for item in self.parameter_snapshot)
        ids = [item.parameter_id for item in snapshots]
        if len(ids) != len(set(ids)):
            raise BenchmarkResultError("parameter_snapshot ids must be unique")
        if any(item.status is ParameterStatus.ACTIVE for item in snapshots):
            raise BenchmarkResultError(
                "ACTIVE parameters are forbidden in synthetic benchmark results"
            )
        object.__setattr__(self, "parameter_snapshot", snapshots)

        metrics = tuple(
            item
            if isinstance(item, BenchmarkMetricResult)
            else BenchmarkMetricResult.from_mapping(item)
            for item in self.metrics
        )
        metric_names = [item.metric_name for item in metrics]
        if len(metric_names) != len(set(metric_names)):
            raise BenchmarkResultError("metric names must be unique")
        if not metrics:
            raise BenchmarkResultError("metrics must not be empty")
        object.__setattr__(self, "metrics", metrics)

        object.__setattr__(
            self,
            "conservation_result",
            _coerce_audit(self.conservation_result, field="conservation_result"),
        )
        object.__setattr__(
            self,
            "restart_result",
            _coerce_audit(self.restart_result, field="restart_result"),
        )

        provenance = self.provenance
        if not isinstance(provenance, Provenance):
            if not isinstance(provenance, Mapping):
                raise BenchmarkResultError("provenance must be a mapping")
            try:
                provenance = Provenance.from_mapping(provenance)
            except ValidationCaseError as exc:
                raise BenchmarkResultError(str(exc)) from exc
        object.__setattr__(self, "provenance", provenance)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "execution_id": self.execution_id,
            "solver_version": self.solver_version,
            "input_hash": self.input_hash,
            "parameter_snapshot": [
                item.to_mapping() for item in self.parameter_snapshot
            ],
            "metrics": [item.to_mapping() for item in self.metrics],
            "conservation_result": _thaw(self.conservation_result),
            "restart_result": _thaw(self.restart_result),
            "status": self.status,
            "provenance": self.provenance.to_mapping(),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BenchmarkResult":
        if not isinstance(value, Mapping):
            raise BenchmarkResultError("benchmark result must be a mapping")
        payload = dict(value)
        payload["parameter_snapshot"] = tuple(
            _coerce_snapshot(item) for item in payload.get("parameter_snapshot", ())
        )
        payload["metrics"] = tuple(
            BenchmarkMetricResult.from_mapping(item)
            for item in payload.get("metrics", ())
        )
        try:
            return cls(**payload)
        except TypeError as exc:
            raise BenchmarkResultError(f"invalid benchmark result: {exc}") from exc


@dataclass(frozen=True)
class BenchmarkRegistry:
    """Stable collection of all five P7.7B results."""

    results: tuple[BenchmarkResult, ...] | Sequence[BenchmarkResult]
    schema_version: str = "v1"
    stage: str = "P7.7B"

    def __post_init__(self) -> None:
        if self.schema_version != "v1":
            raise BenchmarkResultError("schema_version must be v1")
        if self.stage != "P7.7B":
            raise BenchmarkResultError("stage must be P7.7B")
        results = tuple(
            item if isinstance(item, BenchmarkResult) else BenchmarkResult.from_mapping(item)
            for item in self.results
        )
        ids = [item.benchmark_id for item in results]
        if len(ids) != len(set(ids)):
            raise BenchmarkResultError("benchmark_id values must be unique")
        object.__setattr__(self, "results", tuple(sorted(results, key=lambda item: item.benchmark_id)))

    @property
    def status(self) -> str:
        return (
            "PASS_SYNTHETIC_BENCHMARK_VALIDATION"
            if all(can_accept_synthetic_benchmark(item) for item in self.results)
            else "FAIL_SYNTHETIC_BENCHMARK_VALIDATION"
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "status": self.status,
            "results": [item.to_mapping() for item in self.results],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BenchmarkRegistry":
        if not isinstance(value, Mapping):
            raise BenchmarkResultError("benchmark registry must be a mapping")
        if value.get("schema_version") != "v1":
            raise BenchmarkResultError("benchmark registry schema_version must be v1")
        if value.get("stage") != "P7.7B":
            raise BenchmarkResultError("benchmark registry stage must be P7.7B")
        raw_results = value.get("results")
        if not isinstance(raw_results, Sequence) or isinstance(raw_results, (str, bytes)):
            raise BenchmarkResultError("benchmark registry results must be a sequence")
        return cls(results=tuple(BenchmarkResult.from_mapping(item) for item in raw_results))


def can_accept_synthetic_benchmark(result: BenchmarkResult) -> bool:
    """Return the fail-closed P7.7B acceptance decision.

    Passing this gate means only that the synthetic numerical harness is
    stable, closed, restart-equivalent, and deterministic.  It does not open
    physical validation, parameter activation, calibration, or UFOTRI use.
    """

    if not isinstance(result, BenchmarkResult):
        raise BenchmarkResultError("result must be a BenchmarkResult")
    if result.status != "PASS_SYNTHETIC_BENCHMARK_VALIDATION":
        return False
    if any(item.status is not ParameterStatus.TEST_ONLY for item in result.parameter_snapshot):
        return False
    metric_by_name = {item.metric_name: item for item in result.metrics}
    for name in ("numerical_stability", "deterministic"):
        metric = metric_by_name.get(name)
        if metric is None or not metric.pass_fail:
            return False
    return bool(
        result.conservation_result.get("passed")
        and result.restart_result.get("passed")
    )


__all__ = [
    "BenchmarkMetricResult",
    "BenchmarkRegistry",
    "BenchmarkResult",
    "BenchmarkResultError",
    "can_accept_synthetic_benchmark",
]
