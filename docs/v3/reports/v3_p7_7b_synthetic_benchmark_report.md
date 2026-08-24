# V3 P7.7B Synthetic Benchmark Execution Report

Date: 2026-08-24
Branch: `codex/v3-p7-7b-synthetic-benchmark`

## Disposition

```ini
P7_7B_STATUS = PASS_SYNTHETIC_BENCHMARK_VALIDATION
BENCHMARKS_EXECUTED = TRUE
DECAY_TEST = PASS
LEAF_TFWT_TEST = PASS
TFWT_OBT_TEST = PASS
SOIL_ROOT_TEST = PASS
END_TO_END_TEST = PASS
CONSERVATION = PASS
RESTART_EQUIVALENCE = PASS
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## Executed cases

| Case | Executed path | Primary result | Conservation | Restart | Determinism |
| --- | --- | ---: | ---: | ---: | ---: |
| radioactive decay | `SoilStorageSolver` | `decay_error = 0` | max residual `0` | max difference `0` | PASS |
| leaf exchange → TFWT | `TFWTStorageSolver` with explicit `LeafExchangeFlux` | `state_difference = 0` | max residual `0` | max difference `0` | PASS |
| TFWT → OBT | `OBTSolver` | `trajectory_comparison = 0` | max residual `0` | max difference `0` | PASS |
| Soil → Root | `RootUptakeSolver` plus explicit source-state reconciliation | `relative_error = 0` | max residual `0` | max difference `0` | PASS |
| end-to-end pathway | frozen `V3PipelineRunner` | `trajectory_comparison = 0` | max residual `0` | max difference `0` | PASS |

The executable registry is
`validation/results/v3/p7_7b_synthetic_benchmark_results.yaml`. All five
results carry deterministic input hashes, execution IDs, solver version
`v3-p7-7b-existing-solvers-v1`, and only `TEST_ONLY` parameter snapshots.

## Scope boundary

The run verifies numerical/interface behavior of the current code paths:
analytic semantic agreement, non-negative state propagation, ledger closure,
timestep refinement trend, deterministic repeatability, and restart
equivalence. It does not establish environmental realism, parameter accuracy,
field validation, calibration, regulatory dose validity, or UFOTRI equivalence.
No real atmospheric, soil, plant, food, or dose dataset was used.

## Verification command

```text
PYTHONPATH=. .venv/bin/python \
  scripts/validation/run_p7_7b_synthetic_benchmarks.py

PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/v3/test_p7_7b_synthetic_benchmarks.py \
  tests/v3/test_p7_7a_validation_framework.py \
  tests/architecture/test_p7_7a_validation_framework_boundary.py
```

Result: `19 passed`.
