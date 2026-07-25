from cteas_ufotri.benchmarks.v2_cases import (
    benchmark_suite_passes,
    run_v2_benchmark_suite,
)
from cteas_ufotri.benchmarks.independent import benchmark_category_counts
from cteas_ufotri.config import load_configuration


def test_v2_benchmark_matrix_passes_scenarios_and_independent_checks():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    results = run_v2_benchmark_suite(config)
    counts = benchmark_category_counts(results)
    assert counts["analytic_benchmark"] >= 10
    assert counts["manual_anchor"] + counts["literature_comparison"] >= 4
    assert counts["integration_scenario"] == 9
    assert counts["physical_invariant"] == 5
    assert counts["regression_case"] == 1
    assert all(
        result.get("independent") is True
        for result in results.values()
        if result.get("category") == "analytic_benchmark"
    )
    assert benchmark_suite_passes(results)
