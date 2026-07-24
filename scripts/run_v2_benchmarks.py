from __future__ import annotations

import argparse
import json
from pathlib import Path

from cteas_ufotri.benchmarks.v2_cases import (
    benchmark_suite_passes,
    run_v2_benchmark_suite,
)
from cteas_ufotri.benchmarks.independent import benchmark_category_counts
from cteas_ufotri.config import load_configuration


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    results = run_v2_benchmark_suite(config)
    text = json.dumps(
        {
            "pass": benchmark_suite_passes(results),
            "category_counts": benchmark_category_counts(results),
            "cases": results,
        },
        indent=2,
        sort_keys=True,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if benchmark_suite_passes(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
