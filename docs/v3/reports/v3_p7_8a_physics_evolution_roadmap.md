# V3 P7.8A Physics Evolution Roadmap

## Roadmap status

```ini
ROADMAP_STATUS = DEFINED_NOT_IMPLEMENTED
CURRENT_V3_MODEL = FROZEN
V3.1_SCOPE = BASELINE_CONTRACTS_AND_SMALL_INTERFACES
V3.2_SCOPE = BIOLOGICAL_PHYSICS_EXTENSIONS
V4_SCOPE = NUMERICAL_STATE_AND_COUPLING_REDESIGNS
P7_5_REOPENED = FALSE
P7_5B_REOPENED = FALSE
IMPLEMENTATION_STARTED = FALSE
```

This roadmap is the P7.8A planning output. The stage does not implement any
item, change the solver, or authorize a parameter value. A stage label means
where a separately authorized design and implementation could be evaluated.

## V3.1 — Baseline contracts and small interfaces

### Scope

- Preserve the current leaf resistance chain and its `s m^-1` component
  ownership; define a reproducible growth-stage ontology and forcing-time
  alignment for `R9_LEAF_PHENOLOGY_RESISTANCE`.
- Freeze the OBT plant-mass, fresh/dry/water/hydrogen, concentration, area,
  and plant-product basis contract for `R4_OBT_PLANT_MASS_BASIS`.
- Keep the TFWT storage equation and explicit loss/transformation boundary;
  validate the declared basis and timing before considering dynamic turnover.
- Keep the one-layer soil storage and signed transport interface; do not
  infer a hydraulic model.
- Maintain `kf/kr` only as the scoped reduced OBT baseline while the full OBT
  state decision is prepared.

### Entry conditions

1. P7.6D registry and P7.8A priority registry are unchanged and fail-closed.
2. The stage ontology, mass-basis question, current TFWT/soil contracts, and
   validation data fields are written as reviewable artifacts.
3. No active parameter, calibration, or empirical validation is introduced by
   the stage transition.

### Exit evidence before any V3.1 implementation

- typed stage and mass-basis interface proposal;
- dimensional and provenance audit;
- current-equation baseline validation cases from the P7.7A framework;
- independent review confirming that no stage or mass field silently changes
  a solver equation;
- explicit implementation authorization for only the approved small change.

V3.1 does not activate `R9` or `R4` merely because their interfaces are
  small. The design gate remains mandatory.

## V3.2 — Biological physics extensions

### Scope

Design and, only after a new authorization, evaluate the OBT formation package:

- `R1_OBT_DAYLIGHT_FORMATION_STATE`;
- `R2_OBT_NIGHTTIME_FORMATION_STATE`;
- `R3_OBT_PHOTOSYNTHETIC_FORCING_STATE`;
- `R5_OBT_TEMPERATURE_RESPONSE`.

The four items must be treated as one coupled biological design package for
equation selection, even though their current coupling classification is
internal or interface-only. The package must decide:

1. authoritative TFWT, exchangeable OBT, and non-exchangeable OBT scope;
2. day/night state versus normalized forcing and transition semantics;
3. measured photosynthetic forcing versus a new plant state;
4. fresh/dry/water/hydrogen mass basis and concentration relation;
5. whether temperature affects formation, turnover, or both.

### Dependencies

V3.2 depends on the V3.1 state/unit contracts and on matched time-resolved
TFWT/OBT observations. It must not use the P7.7B synthetic benchmark as
biological validation, and it must not claim full UFOTRI validation from a
reduced `kf/kr` result.

### Exit evidence before implementation

- one reviewed equation decision for the biological package;
- state ownership, units, time basis, and provenance contract;
- dimensional and inventory-conservation tests;
- data and benchmark protocol capable of discriminating the proposed
  mechanism from the reduced baseline;
- independent review and explicit P7.8B implementation authorization.

## V4 — Fundamental state and numerical-coupling redesigns

### Scope

- `R6_ROOT_LAYERED_UPTAKE_STATE`: layer-resolved soil/root states,
  transpiration or water-uptake relation, rate/velocity basis, aggregation,
  signs, and conservation;
- `R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY`: continuous/event or hybrid product
  representation for OBT;
- `R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY`: separate plant-water/product-water
  representation for TFWT;
- `D2_SOIL_HYDRAULIC_TRANSPORT_EVAPORATION`: only if the data and coupling
  review justify reopening hydrology.

These items are not an extension of the current one-layer interfaces by
renaming. They require explicit state diagrams, time-discretization choices,
ownership rules, conservation ledgers, failure behavior, and a P7.5/P7.5B
compatibility review. Root and food work must not be merged into a production
pipeline as isolated coefficient substitutions.

### Dependency order

```text
P7.6D frozen baseline
       |
       +--> V3.1 stage and mass-basis contracts
       |          |
       |          +--> V3.2 OBT biological package
       |                         |
       +--> R6 layered root state + soil-hydrology decision
       |                         |
       +--> R7/R8 product boundary ------> V4 coupling review
```

The OBT package should precede a full food redesign because product transfer
consumes plant OBT/TFWT states. Root-layer and hydrology work must be reviewed
before any soil-plant numerical coupling is reopened. Leaf-stage design can
proceed in parallel at the interface level.

### Exit evidence before V4 implementation

- approved state-ownership and numerical-coupling design;
- unit, sign, time-step, and conservation contracts;
- matched layer/hydrology or harvest/product datasets;
- restart, refinement, failure-isolation, and inventory tests;
- P7.5/P7.5B impact assessment and explicit implementation authorization;
- independent review that confirms no hidden fallback or value import.

## Deferred and rejected paths

`D1_TFWT_WATER_TURNOVER_GROWTH_DILUTION` remains deferred to V3.2 only as a
data/design question; it is not part of the V3.2 OBT implementation package.
It requires a plant water-balance decision first.

`X1` through `X4` are permanently rejected. They are not candidate V3.1,
V3.2, or V4 work:

- no unreviewed UFOTRI parameter import;
- no rate-to-velocity unit shortcut;
- no continuous-rate-to-harvest-fraction shortcut;
- no dose-driven environmental-physics redesign.

## Transition gates

The next implementation stage is P7.8B only after the selected work package
has passed its equation, data, units, conservation, coupling, and independent
review gates. P7.9 parameter validation/calibration remains later and cannot
be started by completing this roadmap.

At the end of P7.8A:

```ini
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
V3_PHYSICS_READY = FALSE
```
