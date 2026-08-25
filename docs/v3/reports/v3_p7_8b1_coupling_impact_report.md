# V3 P7.8B-1 Coupling Impact Report

## Disposition

```ini
COUPLING_IMPACT_STATUS = COMPLETE
CURRENT_V3_MODEL = FROZEN
P7_5_SEMANTICS_CHANGED = FALSE
P7_5B_SEMANTICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
PIPELINE_CHANGED = FALSE
IMPLEMENTATION_AUTHORIZED = FALSE
```

The machine-readable specification is
`docs/v3/physics/p7_8b1_redesign_specification.yaml`. P7.8B-1 uses the
following future-impact states:

| State | Meaning |
|---|---|
| `NO_INTERFACE_CHANGE` | The frozen baseline continues with no new field, state, or boundary |
| `INTERFACE_EXTENSION` | A future opt-in profile may add typed forcing, state-basis, or metadata fields without changing the current numerical composition |
| `PIPELINE_CHANGE` | A future design changes forcing/state ownership or endpoint preparation and requires a pipeline review |
| `NUMERICAL_COUPLING_CHANGE` | A future design changes state/time ownership or conservation boundaries and requires P7.5/P7.5B review |

## Matrix

| Specification | Impact | Affected modules | Migration strategy |
|---|---|---|---|
| R1 OBT daylight | `INTERFACE_EXTENSION` | OBT biological forcing; validation case schema | Keep reduced profile; require explicit day/night contract in future profile |
| R2 OBT nighttime | `INTERFACE_EXTENSION` | OBT biological forcing; light-state adapter | No automatic mapping from current nighttime multiplier |
| R3 OBT activity | `INTERFACE_EXTENSION` | OBT forcing/state; validation schema | Optional activity is inert under baseline |
| R4 OBT mass basis | `INTERFACE_EXTENSION` | OBT state diagnostics; food/intake basis metadata | Existing fresh basis continues; non-fresh basis requires explicit contract |
| R5 OBT temperature | `INTERFACE_EXTENSION` | OBT biological forcing; meteorology adapter | Baseline ignores response; future profile declares affected process |
| R6 layered root | `NUMERICAL_COUPLING_CHANGE` | Soil, root, TFWT, coupling ledger | No scalar-to-layer conversion; P7.5/P7.5B review mandatory |
| R7 OBT food boundary | `NUMERICAL_COUPLING_CHANGE` | OBT, food, coupling event/state boundary | Event profile remains default; continuous/hybrid is opt-in |
| R8 TFWT food boundary | `NUMERICAL_COUPLING_CHANGE` | TFWT, food, product water, intake denominator | Separate TFWT product state; no OBT fraction reuse |
| R9 leaf stage | `INTERFACE_EXTENSION` | Leaf coordinates/forcing; meteorology adapter | Stage remains metadata in baseline |
| D1 TFWT water turnover | `PIPELINE_CHANGE` | Plant-water forcing, TFWT, OBT input | Deferred until water-balance ownership review |
| D2 soil hydrology | `NUMERICAL_COUPLING_CHANGE` | Soil, root, water forcing, coupling ledger | Deferred; no scalar signed-flux inference |

## P7.5/P7.5B protection

P7.5B freezes interval-start forcing labels, endpoint semantics, root source
snapshot behavior, plant operation order, soil reconciliation, and food/
intake/dose endpoint readout. None of those decisions changes in P7.8B-1.

In particular:

- OBT candidate states do not alter the current TFWT-to-OBT call order;
- root candidates do not alter the current soil snapshot or TFWT input;
- soil candidates do not replace signed transport in the baseline;
- food candidates do not turn endpoint food/intake/dose assessment into a
  production consumption process;
- TFWT water turnover is not added to the current activity-flux interface.

## Backward compatibility

The compatibility contract is profile-based:

```text
v3_frozen_baseline
    -> existing cases, equations, state serialization, and outputs unchanged

future_opt_in_profile
    -> explicit new fields/states
    -> missing fields fail closed
    -> separate validation/coupling authorization
```

There is no implicit migration from:

- a day/night multiplier to a biological forcing function;
- a scalar root velocity to a layered root rate;
- a signed soil flux to a hydrologic transport model;
- an event harvest fraction to a continuous product rate;
- an activity loss flux to a water-mass loss flux.

## Required future reviews

Before P7.8B2 implementation:

1. OBT interface extensions require a state/unit and biological-scope review.
2. Root, layered soil, and food designs require numerical-coupling review,
   conservation tests, restart/refinement tests, and P7.5/P7.5B compatibility
   review.
3. TFWT water turnover requires pipeline ownership and a separate water-mass
   ledger.
4. Every candidate requires independent review and explicit implementation
   authorization.

P7.8B-1 therefore defines future coupling impact without changing current
coupling.
