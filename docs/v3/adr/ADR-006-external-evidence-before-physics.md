# ADR-006: External evidence before physics

## Context

Numerical references and regression tests do not establish empirical validity
or parameter identifiability.

## Decision

Require a complete licensed external case, committed preregistration,
calibration/holdout separation, identifiability assessment, and executed
holdout before formal V3 physics starts.

## Alternatives

Tune to publication plots; use the independent numerical reference as
experiment evidence; implement first and validate later.

## Consequences

Physics work remains blocked until evidence is available. Architecture and
non-invasive data contracts can progress safely.

## Validation requirement

The physics gate must remain blocked while any empirical prerequisite is
false, regardless of architecture readiness.

## Revisit condition

When a complete, legally usable external case passes the preregistered
workflow.
