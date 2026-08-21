# ADR-011: Future Parameter Database Extension

- Status: proposed for V3-P6
- Decision stage: V3-P5.3 capability freeze
- Current implementation: none

## Context

The P5.1 parameter layer safely carries scalar entries, units, source and
provenance metadata, deterministic hashes, uncertainty, bounds, and lifecycle
status. Several future UFOTRI relations may instead require tables, crop or
growth-stage dimensions, temperature functions, and interpolation.

Representing those relations as a scalar or as an opaque executable would
lose dimensions, applicability, reproducibility, and fail-closed behavior.

## Decision

Do not modify the P5.1 schema during P5.3. Before P6 imports a non-scalar
UFOTRI parameter, evaluate a versioned extension with explicit typed value
kinds, for example:

```text
scalar
table
function
```

The extension must define, at minimum:

- axis names, units, ordering, and valid ranges;
- crop and growth-stage applicability;
- temperature/function representation and allowed operations;
- interpolation and extrapolation policy;
- missing-cell and out-of-domain fail-closed behavior;
- source, uncertainty, artifact hash, and migration lifecycle;
- deterministic serialization and package hashing.

Whether this is a schema version, a validated sidecar package, or another
reviewed representation is a P6 decision. No table, function, interpolation
rule, or UFOTRI numerical value is added by this ADR.

## Consequences

Existing P1-P5.2 parameter interfaces remain stable. P6 must complete the
extension design before activating non-scalar values; otherwise the parameter
must remain a placeholder and physics must fail closed.
