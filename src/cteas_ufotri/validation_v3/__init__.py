"""P7.7A V3 baseline validation framework.

This package is a control and measurement layer.  It is intentionally not
imported by plant, soil, exposure, coupling, pipeline, or parameter-runtime
owners.  Synthetic cases carry explicit test-only values and provenance;
physical validation, calibration, and activation remain later gates.
"""

from .benchmarks import (
    BenchmarkSchemaError,
    DEFAULT_BENCHMARK_CONFIG,
    load_baseline_benchmark_cases,
)
from .validation_case import (
    AcceptanceCriterion,
    ExpectedMetric,
    ObservableSpec,
    ParameterSnapshot,
    ParameterStatus,
    Provenance,
    ReferenceDataSpec,
    ScenarioType,
    ValidationCase,
    ValidationCaseError,
)
from .validation_gate import (
    ValidationGateError,
    ValidationGateResult,
    can_enter_validation,
    evaluate_validation_gate,
)
from .validation_metric import (
    ConservationLedger,
    MetricName,
    ValidationMetricError,
    bias,
    compute_metric,
    conservation_residual,
    decay_error,
    mae,
    relative_error,
    rmse,
    state_difference,
    trajectory_comparison,
)
from .validation_result import ValidationResult, ValidationResultError

__all__ = [
    "AcceptanceCriterion",
    "BenchmarkSchemaError",
    "ConservationLedger",
    "DEFAULT_BENCHMARK_CONFIG",
    "ExpectedMetric",
    "MetricName",
    "ObservableSpec",
    "ParameterSnapshot",
    "ParameterStatus",
    "Provenance",
    "ReferenceDataSpec",
    "ScenarioType",
    "ValidationCase",
    "ValidationCaseError",
    "ValidationGateError",
    "ValidationGateResult",
    "ValidationMetricError",
    "ValidationResult",
    "ValidationResultError",
    "bias",
    "can_enter_validation",
    "compute_metric",
    "conservation_residual",
    "decay_error",
    "evaluate_validation_gate",
    "load_baseline_benchmark_cases",
    "mae",
    "relative_error",
    "rmse",
    "state_difference",
    "trajectory_comparison",
]
