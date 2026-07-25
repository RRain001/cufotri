# ADR-004: Opt-in V3 physics

## Context

New physics can invalidate V2 defaults and reproducibility if enabled
implicitly.

## Decision

Every V3 candidate has a feature flag, is disabled by default, carries a
version and validation status, and cannot replace V2 silently.

## Alternatives

Enable newest behavior by default; select behavior from field presence; patch
V2 defaults.

## Consequences

Compatibility is stable and experiments are isolated. Users must make a
deliberate, provenance-recorded choice.

## Validation requirement

Registry validation proves unique module IDs, allowed statuses, and all
architecture candidates default off.

## Revisit condition

An accepted V3 release may change its own defaults, never the V2 frozen mode.
