# P7.7 Physics Validation Preparation

Status: `PREPARATION_ONLY`

Date: 2026-08-24

This document defines the next validation boundary after the V3 integration
review. It prepares interfaces, schemas, and review gates only. It does not
import a dataset, run calibration, change a solver, or activate a parameter.

## Entry state

```ini
V3_INTEGRATION_REVIEW = PASS
PHYSICS_MODULE_CHANGES = 0
ACTIVE_PARAMETERS = 0
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The only currently validated record is the universal H-3 radioactive
half-life. All plant, soil-transport, food, intake, dose, and leaf-parameter
validation remains open or provisional.

## 1. Validation dataset interface

Define a machine-readable adapter contract without importing external data.
Each future dataset record must carry, at minimum:

```yaml
dataset_id: stable identifier
source_kind: CONTROLLED_EXPERIMENT | FIELD_OBSERVATION | EVALUATED_REFERENCE
source_identifier: DOI, accession, report, or controlled local reference
artifact_sha256: immutable artifact digest
license_or_access_basis: provenance and reuse basis
observation_time:
  timezone: explicit timezone or UTC
  start: ISO-8601 timestamp
  end: ISO-8601 timestamp
spatial_reference:
  coordinate_system: explicit CRS or local frame
  coordinates: source coordinates and uncertainty when applicable
variables:
  - variable_id: canonical model quantity
    value: numeric or missing
    unit: canonical or explicitly convertible unit
    uncertainty: numeric or declared unavailable
    uncertainty_convention: stated convention
    provenance: source column/table/figure locator
quality_status: PROVISIONAL | REVIEWED | ACCEPTED | REJECTED
```

The adapter must preserve source values, units, timestamps, coordinates,
missingness, uncertainty, and provenance. Reconstructed, synthetic, or
reanalysis inputs must retain those labels and cannot be relabelled as direct
observations.

## 2. Benchmark case schema

Define a validation case independently of production arithmetic:

```yaml
case_id: stable case identifier
dataset_id: source dataset reference
forcing_reference: immutable forcing artifact or declared synthetic fixture
initial_state_reference: explicit initial conditions and units
parameter_snapshot_reference: reviewed candidate/validation snapshot
pathways_under_test: explicit model pathways
observables: quantity, unit, time basis, and observation mapping
expected_invariants:
  - conservation or boundary invariant
reference_outputs:
  - independent reference method and artifact digest
tolerances:
  - observable_id: absolute/relative tolerance with rationale
independent_review_status: PENDING | PASS | HOLD | REJECT
execution_status: NOT_RUN | PASS | FAIL | BLOCKED
```

Benchmark cases must distinguish software regression, analytical semantic
checks, evaluated physical constants, and empirical/observational validation.
Production model arithmetic cannot be used to manufacture its own independent
expected values.

## 3. Parameter validation workflow

The future workflow is:

```text
dataset/evidence intake
        -> provenance and independence review
        -> quantity, equation, unit, and time-basis match
        -> applicability review
        -> validation candidate record
        -> independent benchmark and uncertainty review
        -> PASS / HOLD / REJECT decision
```

Only a `PASS` validation record may transition a candidate to `VALIDATED`.
This preparation stage adds no transition from `VALIDATED` to `ACTIVE`.
Runtime ownership remains explicit: solvers continue to receive their
parameter objects from their existing callers.

## 4. Required review questions

Before any future validation decision, reviewers must be able to answer:

1. Is the quantity exactly the quantity used by the equation?
2. Are unit, time basis, coordinate basis, and chemical/biological scope
   compatible?
3. Is the evidence independent, derived, duplicate, or unknown?
4. Are reported values and uncertainties preserved without blind averaging?
5. Is applicability to the specific V3 pathway demonstrated?
6. Is the benchmark independent of production arithmetic?
7. Does the result remain isolated from runtime activation?

## 5. Explicit non-goals

P7.7 preparation must not:

- begin calibration, fitting, Bayesian inference, or parameter optimization;
- add real atmospheric or field data to the production workflow;
- replace provisional values in `configs/` or legacy parameter stores;
- modify V3 physics equations, numerical coupling, or solver defaults;
- set `ACTIVE_PARAMETERS > 0` or enable `UFOTRI_ACTIVE_DATABASE`;
- claim `V3_PHYSICS_READY = TRUE`.

## Exit criteria for preparation

The preparation stage may close only when the dataset adapter schema,
benchmark schema, provenance/uncertainty rules, independent-reference rule,
and candidate-to-validation workflow have each received an independent review.
Closure still leaves parameter activation and calibration as separate future
gates.
