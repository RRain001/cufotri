# V3 P7.6D Coupling Impact Report

## Decision

```ini
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_REOPENED = FALSE
P7_5B_REOPENED = FALSE
CURRENT_V3_MODEL = FROZEN
```

P7.6D classifies the future impact of every redesign item without changing
the current numerical coupling. The canonical per-item decisions are in
`docs/v3/physics/p7_6d_physics_adoption_decision.yaml`; the grouped priority
matrix is in `docs/v3/physics/p7_6d_redesign_priority_matrix.yaml`.

## Impact classes

| Class | P7.6D meaning |
| --- | --- |
| `NO_IMPACT` | A future equation/state decision is internal to the current subsystem boundary; no coupling change is identified yet |
| `INTERFACE_ONLY` | A future design may add or refine a typed forcing, state-basis, or event interface, but no time-coupling change is authorized |
| `NUMERICAL_COUPLING_CHANGE_REQUIRED` | The future representation would alter a time/state boundary and must receive a separate numerical-coupling design and authorization |

## Redesign-item assessment

| Item | Future impact | Reason |
| --- | --- | --- |
| `obt.daylight_multiplier` | `NO_IMPACT` | Daylight treatment is an internal OBT formation decision until a new state or forcing boundary is approved |
| `obt.nighttime_multiplier` | `NO_IMPACT` | Nighttime treatment is likewise internal to the OBT design boundary |
| `obt.photosynthetic_activity` | `INTERFACE_ONLY` | A scalar forcing or plant-state contract may be needed, but no new numerical link is selected |
| `obt.plant_mass` | `INTERFACE_ONLY` | The mass/hydrogen basis affects state diagnostics and plant-product interpretation |
| `obt.temperature` | `INTERFACE_ONLY` | Temperature is already an optional biological forcing field; the missing relation is not a coupling authorization |
| `root.k_root` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | Layered root uptake changes soil-root state ownership, water uptake, and aggregation |
| `food.harvest_fraction` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | A continuous food representation could change the plant-product time boundary |
| `food.tfwt_harvest_fraction` | `NUMERICAL_COUPLING_CHANGE_REQUIRED` | TFWT product transfer must be redesigned with the plant-product event/continuous contract |
| `leaf.growth_stage` | `INTERFACE_ONLY` | Stage ontology and stage-dependent resistance can be represented at the forcing/resistance interface |

The matrix therefore contains 2 `NO_IMPACT`, 4 `INTERFACE_ONLY`, and 3
`NUMERICAL_COUPLING_CHANGE_REQUIRED` redesign items.

## Current interface preservation

No source file under `src/cteas_ufotri/plant/`, `src/cteas_ufotri/exposure/`,
`src/cteas_ufotri/coupling/`, or `src/cteas_ufotri/v3_pipeline/` is changed by
P7.6D. The control-plane registry is not imported by runtime owners. Existing
TFWT, OBT, soil, root, food, and atmospheric interfaces remain the current V3
baseline.

The classification does not imply that the listed future changes are easy or
already designed. In particular, `root.k_root` and the food-chain records are
explicit blockers for any future numerical-coupling implementation. A future
coupling proposal must include state ownership, time discretization, sign and
unit contracts, conservation tests, failure behavior, and independent review.

## Authorization boundary

P7.6D does not implement any item in this report. A future stage may reopen a
coupling boundary only after the corresponding physics redesign is accepted,
the P7.5/P7.5B compatibility impact is reviewed, and an explicit implementation
authorization is recorded. Until then:

- no solver equations change;
- no numerical coupling changes;
- no parameter is imported or activated;
- no calibration or production validation starts.
