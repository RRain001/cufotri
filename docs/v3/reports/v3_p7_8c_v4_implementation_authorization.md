# V3 P7.8C — V4 Implementation Authorization Gate

## Decision

```ini
P7_8C_STATUS = PASS_CONTRACT_PREPARATION_AUTHORIZATION
V3_1_EXIT_GATE = PASS_MAIN_MERGED
V4_DATA_AND_STATE_CONTRACTS = AUTHORIZED_CONTROL_PLANE_ONLY
V4_SELECTED_MODEL_IMPLEMENTATION = HOLD_PREREQUISITES_INCOMPLETE
LEAF_DYNAMIC_STOMATAL_RESPONSE_IMPLEMENTATION = NOT_AUTHORIZED
OBT_FORMATION_PACKAGE_IMPLEMENTATION = NOT_AUTHORIZED
ROOT_WATER_FLUX_IMPLEMENTATION = NOT_AUTHORIZED
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```

P7.8C is opened after V3.1 closed on `main` at
`3103d82c5cad3ead37a827f4970e8d649a1107dc`. V3.1 implementation
`95f78801d0fa3b507e6bd76249b192adf8b107cb` passed the independent Luna R2
review at `7a06733f3201cc60c4c6599799892899cdb61d7f` and was merged without tree
drift. The V3.1 contract therefore no longer blocks the roadmap.

This P7.8C decision does **not** authorize a future solver model. It authorizes
only the first roadmap item, `V4_DATA_AND_STATE_CONTRACTS`, as control-plane
preparation required to make later implementation decisions auditable.

## Why this is not a contradiction with P7.8B-2

ADR-021 and the P7.8B-2 selection registry require a selected future model to
have, before implementation, an equation/unit contract, state ownership,
dimensional/conservation/restart evidence, a validation dataset/case contract,
applicable coupling review, independent review, and explicit implementation
authorization.

The roadmap's first V4 item is not a selected physical model. Its purpose is to
produce those contracts while leaving equations, runtime states, coupling and
parameters unchanged. Therefore P7.8C can authorize that preparation without
waiving any prerequisite for the leaf, OBT, or root models.

## Current readiness matrix

| Roadmap item | P7.8C decision | Reason |
| --- | --- | --- |
| V4 Data & State Contracts | AUTHORIZED_CONTROL_PLANE_ONLY | V3.1 is complete; contract preparation changes no solver/coupling/runtime state |
| Dynamic leaf stomatal response | HOLD | item-specific equation/unit, forcing ownership, validation case, compatibility and independent-review gates remain open |
| OBT precursor + two-pool package | HOLD | mass basis is ready, but pool ownership, equation/unit, conservation/restart, matched biological validation and independent review remain open |
| Root water-flux boundary | HOLD | layer ownership, conservation/restart/refinement, validation and mandatory P7.5/P7.5B coupling review remain open |
| Full soil hydrology | NOT SELECTED | insufficient evidence |
| Dynamic TFWT water turnover | NOT SELECTED | insufficient evidence |
| Continuous/hybrid food transfer | NOT SELECTED | insufficient evidence |
| Organ-specific OBT growth | REJECTED | not the selected first OBT direction |

## Authorized V4-1 work

`V4_DATA_AND_STATE_CONTRACTS` may create documents, schemas and control-plane
tests for:

1. candidate equation and unit definitions;
2. state ownership, scope, mass/area basis and aggregate-readout rules;
3. forcing units, timestamps, provenance and missing-data behavior;
4. validation dataset/case schemas and pre-registered metrics;
5. conservation identities and failure-contract tests;
6. restart/compatibility schema design;
7. coupling-impact classifications and review packets.

The work must remain value-free where evidence is not admitted. A schema or
contract may name a candidate parameter but may not assign a production value,
calibrate it, or make it runtime admissible.

## Explicitly forbidden in V4-1

The authorization does not permit:

- modifications to production solver equations;
- new candidate runtime state activation;
- changes to the default `v3_frozen_baseline` profile;
- changes to existing V3 state serialization;
- P7.5/P7.5B ordering, endpoint, ledger or restart changes;
- numerical-coupling changes;
- dynamic stomatal-response implementation;
- precursor/two-pool OBT implementation;
- layer water-flux root implementation;
- full soil hydrology or TFWT water-turnover implementation;
- parameter activation or calibration;
- a claim of physical validation or `V3_PHYSICS_READY`.

## Item-specific gates still required

### Leaf dynamic stomatal response

Before implementation the repository needs a reviewed response equation/unit
contract, explicit light/VPD/leaf-temperature/stage forcing ownership,
response-domain and failure tests, restart/compatibility rules, matched
conductance/resistance validation cases, independent review, and a later
item-level implementation authorization.

### OBT formation package

V3.1 now supplies the mass-basis prerequisite, but implementation still needs a
reviewed `P/B_x/B_n` equation/unit and state-ownership contract, aggregate OBT
readout semantics, component/total conservation and restart tests, matched
TFWT/exchangeable/non-exchangeable OBT validation cases, pre-registered metrics,
independent review, and later item-level authorization.

### Root water-flux boundary

Implementation remains additionally blocked by the numerical-coupling gate.
The layer water/activity basis, `q_w,i` ownership, soil/root/TFWT extraction
signs, layer/global conservation, restart/refinement/failure tests, matched
layer-resolved validation cases, and a fresh P7.5/P7.5B coupling review are all
required first.

## Compatibility

`v3_frozen_baseline` remains the default runnable profile and rollback target.
Missing V4 fields fail closed. No current scalar, rate, loss term, harvest
fraction or synthetic benchmark is reinterpreted as a future physical model.

## Next stage

The only authorized next implementation activity is:

```ini
NEXT = V4_DATA_AND_STATE_CONTRACTS
SCOPE = CONTROL_PLANE_ONLY
PRODUCTION_RUNTIME_CHANGES = FORBIDDEN
V4_PHYSICS_IMPLEMENTATION_AUTHORIZED = FALSE
```

This P7.8C gate itself does not complete physical validation and does not make
any future candidate parameter admissible.
