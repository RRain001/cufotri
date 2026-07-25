# ADR-002: Versioned configuration and result schemas

## Context

Hidden defaults and unversioned fields can change physical semantics without a
visible source change.

## Decision

Require explicit schema/model versions, compatibility mode, module flags,
state definitions, units, hashes, and validation claims. Unknown root fields
fail closed.

## Alternatives

Continue unversioned YAML; infer versions from Git; accept unknown fields.

## Consequences

Migrations are reviewable and results are self-describing, at the cost of
schema maintenance and explicit upgrade work.

## Validation requirement

All JSON schemas parse; representative envelopes pass contract checks; unknown
fields and unsupported modes fail.

## Revisit condition

When schema 3.0.0 cannot express a reviewed requirement without semantic
overloading.
