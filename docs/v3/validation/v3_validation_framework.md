# V3 P7.7A Baseline Validation Framework

Status: `FRAMEWORK_ONLY`

P7.7A establishes the validation control plane for the frozen V3 baseline. It
defines how a case names its forcing, initial state, parameter snapshot,
outputs, reference data, metrics, thresholds, and provenance. It does not
decide whether a parameter is physically true and it does not run a solver.

## Boundary

The implementation is isolated under
`src/cteas_ufotri/validation_v3/`. Plant, soil, exposure, coupling, pipeline,
and parameter-runtime owners do not import this package. Case values are
declared in `configs/v3/validation/p7_7a_baseline_benchmarks.yaml`; the Python
loader does not contain benchmark numbers.

The current repository state remains:

```ini
P7_7A_STATUS = PASS_VALIDATION_FRAMEWORK
VALIDATION_SCHEMA = TRUE
VALIDATION_METRICS = TRUE
BASELINE_BENCHMARKS_DEFINED = TRUE
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
```

The one existing validated record from P7.6C-1 remains a separate physical
constant record. P7.7A adds no parameter validation result and no new
candidate.

## Components

| Component | Responsibility | Explicit non-responsibility |
| --- | --- | --- |
| `validation_case.py` | Freeze named case inputs, output specifications, reference data, thresholds, and provenance | No solver call, parameter lookup, or unit conversion |
| `validation_metric.py` | Compute deterministic comparisons and inventory closure from supplied values | No reference-data generation or ledger mutation |
| `validation_result.py` | Record metric value, threshold, decision, uncertainty, execution hash, solver version, and parameter snapshot | No activation or calibration transition |
| `validation_gate.py` | Admit software/analytical/synthetic baseline cases only | No empirical or parameter-validation admission |
| `benchmarks.py` | Load the YAML benchmark manifest | No benchmark arithmetic |

## Metric contract

The framework supports:

- `RMSE`, `MAE`, `relative_error`, and signed `bias` for aligned numerical
  values;
- `conservation_residual = input_inventory - output_inventory -
  storage_change` and a `ConservationLedger` adapter that preserves the
  recorded residual;
- `trajectory_comparison` as aligned trajectory RMSE;
- `decay_error` as the absolute error in net trajectory decrease;
- `state_difference` as the maximum aligned absolute state difference.

Non-finite values, unequal trajectory lengths, missing references, and hidden
mapping-valued parameters fail closed. No NaN filtering or silent repair is
performed.

## Gate policy

`can_enter_validation()` permits only `SYNTHETIC_BENCHMARK`,
`SOFTWARE_REGRESSION`, or `ANALYTICAL_SEMANTIC` cases whose parameter entries
are explicit `TEST_ONLY` snapshots. It rejects evaluated physical constants,
empirical observations, `ACTIVE` or non-test-only parameter snapshots,
non-zero active-parameter counts, calibration, UFOTRI database import or
activation, and `V3_PHYSICS_READY = TRUE`.

An allowed case is therefore eligible for a software/semantic baseline check;
it is not a physical validation result.
