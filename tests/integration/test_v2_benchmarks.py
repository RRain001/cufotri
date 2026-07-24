from cteas_ufotri.benchmarks.v2_cases import (
    benchmark_suite_passes,
    run_v2_benchmark_suite,
)
from cteas_ufotri.config import load_configuration


def test_v2_benchmark_matrix_passes_all_fifteen_cases():
    config = load_configuration(
        "configs/default_parameters.yaml", "configs/test_case.yaml"
    )
    results = run_v2_benchmark_suite(config)
    assert len(results) == 15
    assert benchmark_suite_passes(results)
