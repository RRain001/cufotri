"""Loading interfaces for the P7.7A synthetic benchmark suite."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from .validation_case import ScenarioType, ValidationCase, ValidationCaseError


class BenchmarkSchemaError(ValidationCaseError):
    """The benchmark manifest is not a P7.7A case collection."""


DEFAULT_BENCHMARK_CONFIG = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "v3"
    / "validation"
    / "p7_7a_baseline_benchmarks.yaml"
)


def load_baseline_benchmark_cases(
    path: str | Path = DEFAULT_BENCHMARK_CONFIG,
) -> tuple[ValidationCase, ...]:
    """Decode and validate the repository's five synthetic case definitions."""

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise BenchmarkSchemaError(f"benchmark manifest does not exist: {manifest_path}")
    try:
        payload: Any = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkSchemaError(f"cannot read benchmark manifest: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise BenchmarkSchemaError("benchmark manifest must be a mapping")
    if payload.get("schema_version") != "v1":
        raise BenchmarkSchemaError("benchmark manifest schema_version must be v1")
    if payload.get("stage") != "P7.7A":
        raise BenchmarkSchemaError("benchmark manifest stage must be P7.7A")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise BenchmarkSchemaError("benchmark manifest cases must be a non-empty list")

    cases: list[ValidationCase] = []
    for index, raw_case in enumerate(raw_cases):
        try:
            case = ValidationCase.from_mapping(raw_case)
        except ValidationCaseError as exc:
            raise BenchmarkSchemaError(
                f"invalid benchmark case at index {index}: {exc}"
            ) from exc
        if case.scenario_type is not ScenarioType.SYNTHETIC_BENCHMARK:
            raise BenchmarkSchemaError(
                f"baseline benchmark {case.case_id} must be SYNTHETIC_BENCHMARK"
            )
        cases.append(case)

    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise BenchmarkSchemaError("benchmark case_id values must be unique")
    return tuple(sorted(cases, key=lambda case: case.case_id))


__all__ = [
    "BenchmarkSchemaError",
    "DEFAULT_BENCHMARK_CONFIG",
    "load_baseline_benchmark_cases",
]
