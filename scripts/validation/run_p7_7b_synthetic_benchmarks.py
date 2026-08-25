"""Regenerate the committed P7.7B synthetic benchmark result registry."""

from __future__ import annotations

from pathlib import Path

from cteas_ufotri.validation_v3 import (
    run_baseline_synthetic_benchmarks,
    write_benchmark_registry,
)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    registry = run_baseline_synthetic_benchmarks()
    output = write_benchmark_registry(
        registry,
        root / "validation/results/v3/p7_7b_synthetic_benchmark_results.yaml",
    )
    print(f"status={registry.status}")
    print(f"results={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
