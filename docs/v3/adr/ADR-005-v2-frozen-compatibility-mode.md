# ADR-005: V2 frozen compatibility mode

## Context

V2 YAML must be representable inside V3 without new defaults or semantic
guessing.

## Decision

Wrap the exact parsed V2 mapping under
`v2_compatibility.original_config`, record exact-input and canonical-mapping
hashes, and resolve only after anchor/hash/feature checks.

## Alternatives

Rename every field immediately; merge with V3 defaults; convert only resolved
values.

## Consequences

Round-trip semantics are lossless and reviewable. The wrapper is intentionally
not a normalized V3 physics configuration.

## Validation requirement

V1, V2, forcing, and reference configurations round-trip; resolved V2 results
match directly loaded V2 results where executed.

## Revisit condition

After a separately reviewed semantic migration exists with field-level golden
evidence.
