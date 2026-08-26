# ADR-023 — P7.8C V4 authorization boundary

## Status

Accepted for P7.8C gate review.

## Context

P7.8B-2 selected future leaf, OBT and root directions but explicitly withheld
implementation authorization. ADR-021 requires each selected future model to
close equation/unit, ownership, dimensional/conservation/restart, validation,
coupling and independent-review gates before implementation.

The same roadmap places `V4_DATA_AND_STATE_CONTRACTS` first. That item is
control-plane preparation: it exists to define the contracts needed by later
item-level implementation decisions and is not itself a physical model.

V3.1 has now closed its mass-basis contract, passed independent Luna R2 review,
and merged to main without changing the frozen runtime.

## Decision

P7.8C authorizes `V4_DATA_AND_STATE_CONTRACTS` as **control-plane-only** work.
It does not authorize implementation of any selected future physical model.

This is a one-way fail-closed boundary:

- contract/schema/test preparation may proceed;
- production solver equations may not change;
- candidate runtime states may not be activated;
- candidate parameter values may not be admitted;
- the frozen baseline remains default and rollback target;
- every selected model still needs a later item-level authorization after its
  P7.8B-2 prerequisites and independent review are complete.

## Authorized control-plane outputs

V4-1 may define:

- equation and unit contracts;
- state ownership and aggregate readout contracts;
- forcing unit/timestamp/provenance contracts;
- validation dataset/case schemas and pre-registered metrics;
- conservation identities and negative/failure contracts;
- restart/compatibility schema designs;
- coupling-impact and review packets.

These outputs may be symbolic and value-free. They may not create production
runtime behavior.

## Model decisions at this gate

- `LEAF_DYNAMIC_STOMATAL_RESPONSE`: implementation HOLD.
- `OBT_FORMATION_PACKAGE`: implementation HOLD.
- `ROOT_UPTAKE_WATER_FLUX_BOUNDARY`: implementation HOLD, including mandatory
  future P7.5/P7.5B numerical-coupling review.
- Full soil hydrology, dynamic TFWT turnover and continuous/hybrid food transfer
  remain insufficient evidence.
- Organ-specific OBT growth remains rejected for this roadmap.

## Consequences

The next repository work may build V4-1 contracts but not V4 solver physics.
Completion of V4-1 will create evidence for later item-level readiness reviews;
it will not by itself activate leaf, OBT or root candidates.

```ini
P7_8C_STATUS = PASS_CONTRACT_PREPARATION_AUTHORIZATION
V4_DATA_AND_STATE_CONTRACTS_AUTHORIZED = TRUE
V4_SELECTED_MODEL_IMPLEMENTATION_AUTHORIZED = FALSE
SOLVER_CHANGES_AUTHORIZED = FALSE
NUMERICAL_COUPLING_CHANGES_AUTHORIZED = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```
