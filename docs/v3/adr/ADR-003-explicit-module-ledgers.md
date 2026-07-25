# ADR-003: Explicit module ledgers

## Context

A single residual can hide mismatched cross-module areas, units, or transfer
amounts.

## Decision

Every future module reports external input, internal input/output, boundary
output, decay, final inventory, numerical residual, and relative residual.
Internal transfers reconcile globally by transfer ID.

## Alternatives

Use only local box residuals; infer transfers from state deltas; report one
whole-model residual.

## Consequences

Interface conservation is testable. More metadata and reconciliation tests are
required.

## Validation requirement

Local identities and cross-module transfer equality must pass for equal and
unequal footprint cases.

## Revisit condition

Only if a stronger typed conservation protocol supersedes every field without
losing cross-module evidence.
