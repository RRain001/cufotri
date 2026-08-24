"""Deterministic serialization for the P7.7B benchmark registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .benchmark_registry import BenchmarkRegistry, BenchmarkResultError


class BenchmarkResultWriterError(ValueError):
    """A result registry cannot be read or written safely."""


def write_benchmark_registry(
    registry: BenchmarkRegistry,
    path: str | Path,
) -> Path:
    """Write one stable YAML registry and return its explicit path."""

    if not isinstance(registry, BenchmarkRegistry):
        raise BenchmarkResultWriterError("registry must be a BenchmarkRegistry")
    output_path = Path(path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            yaml.safe_dump(
                registry.to_mapping(),
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            ),
            encoding="utf-8",
        )
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkResultWriterError(
            f"cannot write benchmark registry {output_path}: {exc}"
        ) from exc
    return output_path


def read_benchmark_registry(path: str | Path) -> BenchmarkRegistry:
    """Read and revalidate one P7.7B YAML registry."""

    input_path = Path(path)
    try:
        payload: Any = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkResultWriterError(
            f"cannot read benchmark registry {input_path}: {exc}"
        ) from exc
    try:
        return BenchmarkRegistry.from_mapping(payload)
    except BenchmarkResultError as exc:
        raise BenchmarkResultWriterError(
            f"invalid benchmark registry {input_path}: {exc}"
        ) from exc


__all__ = [
    "BenchmarkResultWriterError",
    "read_benchmark_registry",
    "write_benchmark_registry",
]
