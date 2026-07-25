# ADR-007: No dynamic-air implementation yet

## Context

A dynamic air box can double count source, Gaussian transport, deposition, and
re-emission activity.

## Decision

Reserve interfaces only. Defer implementation pending analytic pulse cases,
an independent transport reference, and empirical mixing/ventilation evidence.

## Alternatives

Add storage directly to the Gaussian result; replace the Gaussian plume
without a reference; treat air concentration as inventory.

## Consequences

No dynamic-air claim is possible in this baseline, but the ownership and
ledger questions are explicit.

## Validation requirement

Closed/ventilated pulse identities, no-double-count accounting, external
reference comparison, and global ledger closure.

## Revisit condition

All required reference and empirical evidence exists and the physics-start gate
passes.
