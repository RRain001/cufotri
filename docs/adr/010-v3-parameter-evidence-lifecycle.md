# ADR-010: V3 parameter evidence and provenance lifecycle

Status: Accepted for the P7.6A control-plane boundary

## Context

P7.5/P7.5B already provide a controlled synthetic V3 execution path. Their
explicit coefficients and case inputs must be governed before any validation
or calibration discussion. A governance layer must not become a runtime
parameter database or alter existing solver APIs.

## Decision

P7.6A freezes an immutable `ParameterEvidenceRecord` and a deterministic
`ParameterEvidenceRegistry` under `src/cteas_ufotri/parameters_v3/`.

Each record must carry:

- one primary parameter class;
- canonical, reported, and normalized units as separate fields;
- a lifecycle status;
- an allowed source type and non-empty source identifier;
- explicit applicability coordinates;
- evidence notes and repository/file/location provenance;
- review status.

The lifecycle is:

```text
PROVISIONAL -> EVIDENCE_FOUND -> VALIDATED -> ACTIVE
       \             \
        -> REJECTED    -> REJECTED
```

Only adjacent transitions are legal. P7.6A rejects `VALIDATED` and `ACTIVE`
records at the stage registry gate. `REJECTED` is retained as an explicit
fail-closed disposition. No value is resolved or converted by the registry.

## Gap categories

The inventory uses six mutually exclusive categories: evidence sufficient for
future validation, evidence with unresolved applicability, conflicting
evidence, no evidence, scenario input, and test-only parameter. Test-only
records may be `EVIDENCE_FOUND` only in the narrow sense of reproducible
software-fixture evidence; this status never implies physical validation.

## Consequences

The control plane can be audited and serialized without coupling to a solver.
Missing sources, units, applicability, or provenance fail closed. P6/P7
modules remain explicit-parameter consumers, and V1/V2/default behavior is
unchanged.

P7.6B must define any validation/calibration contract. Real CTEAS-Atmos data,
UFOTRI parameter activation, regulatory values, and production use remain
outside this decision.
