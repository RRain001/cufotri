# V3-P7.6B-2A validation-preparation gate report

Status: `PASS_PARAMETER_CANDIDATE_CONSTRUCTION`

## Gate API

`parameters_v3/validation_gate.py` now exposes:

```python
can_enter_validation(candidate)
```

The predicate returns true only for an immutable
`ParameterCandidateRecord` with:

- `candidate_status = VALIDATION_CANDIDATE`;
- `candidate_screening = CANDIDATE`;
- a non-empty evidence link;
- `validation_required = true`; and
- applicability other than `UNKNOWN` or `NOT_APPLICABLE`.

This is admission to a future validation protocol, not a claim of validity.
It never performs optimization, observation fitting, Bayesian inference,
calibration, parameter replacement, or runtime lookup.

## Current gate result

The canonical registry evaluates to:

```ini
VALIDATION_CANDIDATES_IDENTIFIED = TRUE
CANDIDATE_COUNT = 0
BLOCKED_RECORDS = 76
VALIDATED_PARAMETERS = 0
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

All 26 deferred records are blocked by provisional/deferred status. All 50
rejected records are blocked by rejected status. No record is silently
promoted by the gate.

## Lifecycle safety

The lifecycle validator rejects a direct
`VALIDATION_CANDIDATE -> ACTIVE` transition; `VALIDATED` is an explicit
intermediate state. The lifecycle representation can describe a future
validated record, but `ParameterCandidateRegistry` rejects both
`VALIDATED` and `ACTIVE` records while the stage is P7.6B-2A. This preserves
the separation between candidate preparation and activation.

## Test evidence

The focused candidate suite contains 20 passing tests covering direct,
partial, and transfer candidate construction; unknown and not-applicable
blocking; lifecycle transitions; duplicate and reference checks; value-free
registry serialization; protected paths; and fresh-process solver isolation.
The existing P7.6B-1 applicability suite was rerun separately with 12
passing tests.
