# ADR-001: V2 immutable anchor

## Context

V2 is identified by the candidate tag and has frozen numerical behavior,
configuration semantics, states, ledgers, and provenance.

## Decision

Use peeled commit `f097115cbfc052baa18f1e49a1207fa6b3523cff` as the V2
compatibility anchor. V3 work cannot move the tag or modify tagged artifacts.

## Alternatives

Use moving `main`; duplicate V2 code inside V3; silently migrate cases.

## Consequences

Compatibility is auditable and old cases remain reproducible. Improvements
require opt-in V3 modules rather than edits to the anchor.

## Validation requirement

Verify tag identity plus V1/V2 recomputation and golden migration cases.

## Revisit condition

Never for the existing tag; a separately named release may establish a new
anchor.
