# ADR-018: V3 synthetic benchmark validation policy

Status: Accepted for P7.7B synthetic execution

## Context

P7.7A defined five synthetic cases and an independent-reference vocabulary,
but deliberately did not execute them. P7.7B needs a reproducible execution
layer that can measure numerical behavior and existing solver ledgers without
turning test fixtures into physical parameter evidence.

## Decision

1. `validation_v3/benchmark_runner.py` is the only P7.7B runtime caller. It
   reads the validated YAML case contract and invokes only existing public V3
   solver and pipeline APIs.
2. Execution inputs, timestep schedules, restart split points, and synthetic
   pipeline construction values remain in
   `configs/v3/validation/p7_7a_baseline_benchmarks.yaml` under
   `execution_definition`. No case values are hard-coded in the runner.
3. Each result records a deterministic input hash, execution ID, solver
   version, test-only parameter snapshot, metric outcomes, conservation audit,
   restart audit, status, and case provenance. The registry is written to
   `validation/results/v3/p7_7b_synthetic_benchmark_results.yaml`.
4. Synthetic acceptance requires numerical-stability and deterministic metrics
   to pass, every recorded conservation audit to close, and restart output to
   match the uninterrupted run. This is software/semantic evidence only.
5. No result may import or activate UFOTRI parameters, start calibration, use
   real environmental data, or set V3 physical readiness.

## Consequences

The five frozen interfaces now have an executable, repeatable baseline with
auditable result records. Conservation and restart checks are tied to the
existing ledgers and `V3SimulationState` serialization contract. A passing
registry does not validate half-life, resistance, `kf`, `kr`, root
coefficients, food parameters, dose coefficients, environmental realism, or
UFOTRI equivalence.

## Rejected alternatives

- Duplicating production equations in a second solver would make numerical
  comparison self-referential and could drift from the frozen implementation.
- Loading the parameter evidence/database layer would violate the P7.7A/P7.6D
  activation boundary.
- Replacing the existing pipeline with a benchmark-specific pipeline would
  test a new implementation rather than the current public path.
