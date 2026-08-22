# V3-P7.6B-2A parameter candidate construction report

Status: `PASS_PARAMETER_CANDIDATE_CONSTRUCTION`

## Scope

This stage constructs a candidate-preparation layer from the frozen P7.6A
parameter evidence inventory and P7.6B-1 applicability matrix. It does not
resolve a parameter value, perform validation, fit observations, calibrate a
model, or connect the registry to a solver or pipeline.

## Acceptance state

```ini
P7_6B2A_STATUS = PASS_PARAMETER_CANDIDATE_CONSTRUCTION
PARAMETER_CANDIDATE_REGISTRY = TRUE
VALIDATION_CANDIDATES_IDENTIFIED = TRUE
VALIDATION_CANDIDATE_COUNT = 0
VALIDATED_PARAMETERS = 0
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICS_MODULE_CHANGED = FALSE
```

## Construction rule

A record is admitted as `VALIDATION_CANDIDATE` only when its evidence status
is `EVIDENCE_FOUND`, its source is neither `TEST_ONLY` nor
`PROJECT_ASSUMPTION`, and its applicability is one of
`DIRECT_MATCH`, `PARTIAL_MATCH`, or `TRANSFER_REQUIRED`. Every admitted
record retains `validation_required = true` and at least one future
validation-plan item. `UNKNOWN` records remain deferred and
`NOT_APPLICABLE` records are rejected.

The candidate lifecycle is explicit:

```text
PROVISIONAL -> EVIDENCE_FOUND -> APPLICABILITY_REVIEWED
             -> VALIDATION_CANDIDATE -> VALIDATED -> ACTIVE
```

The transition model describes future workflow only. The current registry
rejects `VALIDATED` and `ACTIVE` records, and no candidate record is exposed
to the numerical runtime.

## Screening result

| Screening disposition | Count | Candidate status | Interpretation |
|---|---:|---|---|
| `CANDIDATE` | 0 | `VALIDATION_CANDIDATE` | No current record meets the evidence and applicability gate |
| `DEFERRED` | 26 | `PROVISIONAL` | Source/applicability remains unresolved |
| `REJECTED` | 50 | `REJECTED` | Scenario, numerical-control, or test-only scope |
| **Total** | **76** |  | Complete inventory coverage |

The 50 rejected rows contain 28 `SCENARIO_INPUT` records, 2
`NUMERICAL_CONTROL` records, and 20 `TEST_ONLY_PARAMETER` records. The 20
test-only records are reproducible software fixtures only; they are not
physical, observational, empirical, or calibration evidence.

The candidate lifecycle counts are:

| Candidate status | Count |
|---|---:|
| `PROVISIONAL` | 26 |
| `EVIDENCE_FOUND` | 0 |
| `APPLICABILITY_REVIEWED` | 0 |
| `VALIDATION_CANDIDATE` | 0 |
| `VALIDATED` | 0 |
| `ACTIVE` | 0 |
| `REJECTED` | 50 |

## Subsystem screening

| Subsystem | Candidate | Deferred | Rejected |
|---|---:|---:|---:|
| Atmosphere | 0 | 0 | 9 |
| Leaf exchange | 0 | 5 | 4 |
| TFWT | 0 | 3 | 1 |
| OBT | 0 | 7 | 2 |
| Soil | 0 | 4 | 1 |
| Root | 0 | 1 | 1 |
| Food | 0 | 3 | 2 |
| Intake | 0 | 2 | 4 |
| Dose | 0 | 1 | 3 |
| Pipeline | 0 | 0 | 3 |
| Test fixtures | 0 | 0 | 20 |

Priority tiers are metadata for future validation planning only. The current
inventory assigns 29 records to Tier 1, 5 to Tier 2, and 10 to Tier 3; this
does not imply that any record is validated or active.

## Boundary

The implementation is confined to `parameters_v3/`, the candidate registry,
tests, and documentation. No solver equations, P7.5/P7.5B semantics,
configuration values, real CTEAS-Atmos data, calibration routine, or runtime
parameter database was changed.
