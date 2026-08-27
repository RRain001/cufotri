# ADR-049: V4 production-case input manifest R1

## Status

Accepted as a fail-closed case-manifest contract, pending exact-head CI and clean merge.

## Context

PR #45 established that the controlled UFOTRI software chain is connected but `PRODUCTION_INPUT_PACKET_READY=FALSE`. The remaining gap is not another solver feature. It is the absence of one case-level record proving that every consumed input has an eligible source, compatible units/time/space semantics, provenance, and an explicit zero policy where zero is scientifically intended.

`FULL_MODEL_PRODUCTION_READY=FALSE` remains an explicit hard boundary. Real CTEAS-Atmos surface deposition remains `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`.

## Decision

Define one machine-readable production-case manifest and JSON Schema, plus a completeness validator. The manifest inventory is anchored to `docs/v4/governance/v4_production_input_readiness_audit_r1.yaml`; that audit remains the authority for which inputs are required and how they are classified.

The validator separates two states:

1. `SCHEMA_VALID`: the case packet has the required structure and legal enum values.
2. `PRODUCTION_COMPLETE`: every required input is present and production-ready under the frozen fail-closed rules.

Schema validity must never imply production readiness.

A required input is production-ready only when it is `READY_CONTROLLED`, `READY_PROVENANCED_SOURCE`, or a fully evidenced `DERIVED_FROM_READY_STATE`. API defaults, synthetic/replay fixtures, silent zeros, silent unit conversions, and silent time/space reconciliation are never accepted as production evidence.

An explicit zero is allowed only when the manifest declares the zero and carries source/revision/rationale evidence for that zero policy. A bare numeric/API zero is not sufficient.

## Current template disposition

The checked-in manifest is deliberately complete as an inventory but incomplete as a production packet. It preserves current unresolved states from PR #45, including `BLOCKED_EXTERNAL` for the real surface-deposition flux. Therefore its expected completeness result is `FAIL_CLOSED_INCOMPLETE`.

No real production value is added by this stage.

## Next stage

After clean merge, proceed to `V4_PRODUCTION_CASE_INPUT_SOURCE_RESOLUTION_R1`: resolve manifest sources and explicit-zero policies one input class at a time without changing solver physics. Real CTEAS-Atmos binding, Leaf R5, full hydrology, multi-pool OBT, calibration, empirical validation, and physical-accuracy claims remain unauthorized.
