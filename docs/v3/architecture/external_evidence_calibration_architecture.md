# External evidence and calibration architecture

Status: `ARCHITECTURE_ONLY`

## Evidence lifecycle

1. Register a complete, legally usable local dataset manifest.
2. Commit a preregistration before inspecting holdout performance.
3. Freeze primary observable, calibration interval/repeats, holdout
   interval/repeats, parameters, priors/bounds, metrics, thresholds, missing
   data, uncertainty, and detection-limit policies.
4. Fit only the calibration partition.
5. Assess parameter identifiability, boundary hits, and correlations.
6. Execute the untouched holdout partition once under the preregistered rule.

Calibration and holdout identifiers cannot overlap. Independent repeats are
preferred; time splits must preserve causal order. Raw licensed or restricted
data remain outside Git; manifests contain local relative identifiers and
checksums, not protected values.

## Statistical contract

Each observation declares unit, uncertainty type/value, detection limit,
censoring policy, sampling time, and replicate ID. Calibration parameters
declare prior, lower/upper bounds, transform, and physical source. The output
reports objective value, confidence/profile interval, boundary hit, parameter
correlation matrix, rank/structural identifiability assessment, and convergence
diagnostics.

A successful optimizer is not evidence of identifiability. Parameters that hit
bounds, remain highly correlated, or are insensitive are reported as
non-identifiable and cannot support a stronger model claim.

`schemas/v3/calibration_case.schema.json` and
`schemas/v3/holdout_case.schema.json` define the machine-readable envelopes.
With no complete case, validators may run only in dry-run mode and must return
`BLOCKED_EXTERNAL_DATA`.
