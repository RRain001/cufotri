"""P7.7B synthetic benchmark execution and result-contract tests."""

from dataclasses import replace
from pathlib import Path

import pytest

from cteas_ufotri.validation_v3 import (
    BenchmarkRegistry,
    BenchmarkResult,
    BenchmarkResultError,
    SyntheticBenchmarkRunner,
    can_accept_synthetic_benchmark,
    read_benchmark_registry,
    write_benchmark_registry,
)


EXPECTED_BENCHMARK_IDS = {
    "v3-p7-7b-end-to-end-pathway",
    "v3-p7-7b-leaf-exchange",
    "v3-p7-7b-radioactive-decay",
    "v3-p7-7b-soil-root",
    "v3-p7-7b-tfwt-obt",
}
ROOT = Path(__file__).resolve().parents[2]
CANONICAL_RESULTS = ROOT / "validation/results/v3/p7_7b_synthetic_benchmark_results.yaml"


def test_all_five_synthetic_benchmarks_execute_and_pass() -> None:
    registry = SyntheticBenchmarkRunner().run_all()

    assert isinstance(registry, BenchmarkRegistry)
    assert registry.status == "PASS_SYNTHETIC_BENCHMARK_VALIDATION"
    assert {item.benchmark_id for item in registry.results} == EXPECTED_BENCHMARK_IDS
    assert all(item.status == "PASS_SYNTHETIC_BENCHMARK_VALIDATION" for item in registry.results)
    assert all(can_accept_synthetic_benchmark(item) for item in registry.results)
    assert all(
        item.conservation_result["passed"] and item.restart_result["passed"]
        for item in registry.results
    )


def test_results_record_zero_active_parameters_and_required_gate_metrics() -> None:
    registry = SyntheticBenchmarkRunner().run_all()

    for result in registry.results:
        assert all(snapshot.status.value == "TEST_ONLY" for snapshot in result.parameter_snapshot)
        metric_names = {metric.metric_name for metric in result.metrics}
        assert {"numerical_stability", "deterministic"} <= metric_names
        assert all(metric.pass_fail for metric in result.metrics)

    first = registry.results[0]
    if first.parameter_snapshot:
        active = replace(first.parameter_snapshot[0], status="ACTIVE")
        with pytest.raises(BenchmarkResultError, match="ACTIVE"):
            replace(first, parameter_snapshot=(active, *first.parameter_snapshot[1:]))


def test_conservation_restart_and_refinement_evidence_are_recorded() -> None:
    registry = SyntheticBenchmarkRunner().run_all()

    for result in registry.results:
        assert result.conservation_result["max_abs_residual"] == pytest.approx(0.0)
        assert result.restart_result["max_abs_difference"] == pytest.approx(0.0)
        stability = next(
            metric for metric in result.metrics
            if metric.metric_name == "numerical_stability"
        )
        assert stability.pass_fail is True
        assert len(stability.details["refinement_differences"]) == 2


def test_execution_ids_and_serialized_registry_are_deterministic(tmp_path: Path) -> None:
    first = SyntheticBenchmarkRunner().run_all()
    second = SyntheticBenchmarkRunner().run_all()

    assert first.to_mapping() == second.to_mapping()
    output = write_benchmark_registry(
        first,
        tmp_path / "p7_7b_synthetic_benchmark_results.yaml",
    )
    restored = read_benchmark_registry(output)
    assert restored == first
    assert restored.to_mapping() == first.to_mapping()


def test_checked_in_result_registry_matches_a_fresh_execution() -> None:
    assert CANONICAL_RESULTS.is_file()
    assert read_benchmark_registry(CANONICAL_RESULTS) == SyntheticBenchmarkRunner().run_all()


def test_result_round_trip_preserves_provenance_and_hashes() -> None:
    result = SyntheticBenchmarkRunner().run_all().results[0]
    restored = BenchmarkResult.from_mapping(result.to_mapping())

    assert restored == result
    assert len(result.input_hash) == 64
    assert result.execution_id.startswith("exec-")
    assert result.provenance.artifact_sha256
