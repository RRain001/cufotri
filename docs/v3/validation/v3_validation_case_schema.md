# V3 P7.7A ValidationCase Schema

The machine-readable schema is
`schemas/v3/validation_case.schema.json`; the typed decoder is
`src/cteas_ufotri/validation_v3/validation_case.py`.

## Required top-level fields

| Field | Contract |
| --- | --- |
| `case_id` | Stable lower-case identifier; anonymous cases are rejected |
| `description` | Human-readable purpose and scope |
| `scenario_type` | Synthetic/software/analytical case or a later physical/empirical class |
| `forcing_definition` | Named forcing block containing `forcing_id`, variables, units, and time basis |
| `initial_state` | Named state block containing `state_id`, variables, units, and basis |
| `execution_definition` | Optional explicit execution adapter inputs such as benchmark kind, timestep refinement, restart split, and synthetic fixture construction values |
| `parameter_context` | List of explicit parameter snapshots; an empty list is valid when no parameter is under test |
| `model_outputs` | Named output observables with quantity, unit, time basis, and output reference |
| `reference_data` | Independent reference definition or values with method and provenance |
| `expected_metric` | Primary metric and observable identity |
| `acceptance_criteria` | One or more explicit threshold/comparison/rationale records |
| `provenance` | Source kind, identifier, artifact SHA-256, access basis, and locator |

## Parameter and evidence rules

Every parameter snapshot contains `parameter_id`, scalar `value`, `unit`,
status, and its own provenance. A mapping-valued parameter is rejected so a
hidden bundle of unnamed parameters cannot enter a case.

Reference data must provide either explicit values or a declared independent
reference expression. `independent: true` is a declaration to be reviewed; it
does not turn a synthetic expression into an observation. Reconstructed,
synthetic, reanalysis, evaluated, and empirical inputs retain their source
kind and are never relabelled by the decoder.

All artifacts use a lower-case 64-character SHA-256 field. The P7.7A built-in
benchmark manifest identifies repository-controlled synthetic fixtures; these
digests are fixture provenance, not physical-data evidence.

## Result relation

`ValidationResult` repeats the case and metric identity and records the
computed `value`, `threshold`, `pass_fail`, optional `uncertainty`,
`execution_hash`, `solver_version`, and the exact parameter snapshot. The
boolean decision is checked against the value, threshold, and comparison
operator during construction, so a manually inconsistent pass/fail record is
rejected.

P7.7B adds `BenchmarkResult` and `BenchmarkRegistry` as execution records. A
benchmark result also carries a deterministic input hash and execution ID,
conservation and restart audits, a deterministic-repeatability metric, and a
synthetic-only status. `execution_definition` is configuration data, not a
physical parameter source; active parameter snapshots are rejected.
