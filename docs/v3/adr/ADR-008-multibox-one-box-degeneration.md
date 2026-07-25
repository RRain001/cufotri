# ADR-008: Multibox one-box degeneration

## Context

A layered soil implementation can conserve internally yet fail to reproduce
the accepted one-box boundary under equivalent assumptions.

## Decision

One-box degeneration is a mandatory acceptance property. V2 one-box remains
the default; three-box coupling is opt-in and architecture-only.

## Alternatives

Accept layer-local conservation alone; replace V2 by the experimental solver;
calibrate layers before checking the limit.

## Consequences

Formal coupling must demonstrate compatibility and refinement behavior before
external calibration.

## Validation requirement

One-box degeneration, refinement convergence, layer/global ledgers, and
external soil evidence must all pass.

## Revisit condition

Only after a reviewed mathematical relation proves a different compatibility
limit and independent tests confirm it.
