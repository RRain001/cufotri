# ADR-012: V3 parameter candidate construction and validation-preparation gate

Status: Accepted for the P7.6B-2A control-plane boundary

## Context

P7.6A freezes evidence and provenance records, and P7.6B-1 records a complete
source-to-model applicability review. Those layers identify why a parameter
is unresolved or inapplicable, but they do not provide a lifecycle state for
records that a later validation protocol may consider. A separate candidate
layer is required without importing a parameter value into the solver path.

## Decision

P7.6B-2A adds `ParameterCandidateRecord` and
`ParameterCandidateRegistry` under `src/cteas_ufotri/parameters_v3/`. The
candidate record preserves:

- the P7.6A parameter identity, class, evidence identifier, and provenance;
- the P7.6B-1 applicability disposition and review notes;
- an explicit candidate lifecycle status and screening disposition;
- a reason, uncertainty source, future validation plan, and priority tier.

The screening rule is:

```text
evidence.status == EVIDENCE_FOUND
AND source is not TEST_ONLY or PROJECT_ASSUMPTION
AND applicability not in {UNKNOWN, NOT_APPLICABLE}
```

`DIRECT_MATCH`, `PARTIAL_MATCH`, and `TRANSFER_REQUIRED` may produce a
`VALIDATION_CANDIDATE`, but the record must retain
`validation_required = true`. `UNKNOWN` remains `PROVISIONAL`/`DEFERRED`,
and `NOT_APPLICABLE` becomes `REJECTED`. The registry covers all 76 reviewed
records in deterministic `parameter_id` order and contains no parameter
values.

The lifecycle permits `VALIDATION_CANDIDATE -> VALIDATED -> ACTIVE` only as a
future record transition. The P7.6B-2A registry and gate reject
`VALIDATED`/`ACTIVE` records, so that future lifecycle is not executable in
this stage. `can_enter_validation()` is a preparation predicate only; it does
not validate, calibrate, activate, or provide a runtime lookup.

## Consequences

The current P7.6A/P7.6B-1 inputs yield 0 candidates, 26 deferred records, and
50 rejected records. This is an auditable empty candidate set, not a claim
that all V3 mechanisms lack scientific literature. Physical candidate
construction remains blocked until source evidence and applicability are
resolved.

The candidate package is control-plane-only and has no imports from V3 plant,
soil, food, dose, coupling, or pipeline modules. P7.5/P7.5B numerical
semantics, solver equations, configurations, and runtime parameter lookup
remain unchanged. Calibration, UFOTRI database activation, and production
use remain forbidden.
