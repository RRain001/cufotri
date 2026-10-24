"""Run optional existing CUFOTRI parameter studies without duplicating CLI wrappers.

These subcommands call the same already-tested model functions as the archived
V2 uncertainty and wet-deposition sensitivity entrypoints. Their outputs are
software/research diagnostics, not external UFOTRI parity or field validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cteas_ufotri.config import load_configuration

ROOT = Path(__file__).resolve().parents[1]


def run_v2_uncertainty(output: Path | None) -> int:
    from cteas_ufotri.analysis.full_model_uncertainty import (
        run_full_model_lhs_convergence,
    )

    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_full_adult_dose.yaml",
    )
    result = run_full_model_lhs_convergence(
        config, config["uncertainty"]["parameters"]
    )
    result_text = json.dumps(result, indent=2, sort_keys=True)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result_text + "\n", encoding="utf-8")
    print(result_text)
    return 0 if result["status"] == "PASS" else 1


def run_wet_sensitivity(output: Path) -> int:
    from cteas_ufotri.analysis.wet_sensitivity import wet_parameter_sensitivity

    config = load_configuration(
        ROOT / "configs/default_parameters.yaml",
        ROOT / "configs/test_case.yaml",
    )
    records = wet_parameter_sensitivity(config)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: wrote {len(records)} wet-parameter sensitivity records")
    return 0


def run_synthetic_benchmarks() -> int:
    from cteas_ufotri.validation_v3 import (
        run_baseline_synthetic_benchmarks,
        write_benchmark_registry,
    )

    registry = run_baseline_synthetic_benchmarks()
    output = write_benchmark_registry(
        registry, ROOT / "validation/results/v3/p7_7b_synthetic_benchmark_results.yaml"
    )
    print(f"status={registry.status}")
    print(f"results={output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="study", required=True)
    lhs = subcommands.add_parser(
        "v2-uncertainty", help="Reproduce the V2 full-dose LHS convergence study"
    )
    lhs.add_argument("--output", type=Path)
    wet = subcommands.add_parser(
        "wet-sensitivity", help="Reproduce the wet scavenging parameter grid"
    )
    wet.add_argument("--output", type=Path, required=True)
    subcommands.add_parser(
        "synthetic-benchmarks", help="Regenerate the P7.7B synthetic benchmark registry"
    )
    args = parser.parse_args(argv)
    if args.study == "v2-uncertainty":
        return run_v2_uncertainty(args.output)
    if args.study == "wet-sensitivity":
        return run_wet_sensitivity(args.output)
    if args.study == "synthetic-benchmarks":
        return run_synthetic_benchmarks()
    parser.error("Unknown study")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
