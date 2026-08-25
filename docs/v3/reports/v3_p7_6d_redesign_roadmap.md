# V3 P7.6D Physics Redesign Roadmap

## Roadmap status

```ini
REDESIGN_ROADMAP = COMPLETE
REDESIGN_IMPLEMENTATION = NOT_STARTED
CURRENT_V3_MODEL = FROZEN
P7_5_AND_P7_5B_REOPENED = FALSE
```

This is a design sequence, not an implementation plan with permission to edit
the physics kernel. The nine blocking items are listed in
`docs/v3/physics/p7_6d_redesign_priority_matrix.yaml`.

## Sequence

### R0 — Preserve the P7.6D baseline

Status: complete in P7.6D.

- Keep the current V3 equations, state ownership, and numerical interfaces
  unchanged.
- Keep all parameter values, candidates, active lookups, and calibration
  gates closed.
- Treat P7.6C-3 feasibility as a prerequisite classification, not as an
  implementation requirement.

Exit condition: the decision registry is complete, safe, and isolated from
runtime owners.

### R1 — OBT formation scope and state

Items: `obt.daylight_multiplier`, `obt.nighttime_multiplier`,
`obt.photosynthetic_activity`, `obt.plant_mass`, `obt.temperature`.

Priority: HIGH.  Coupling class: `INTERFACE_ONLY` at this decision stage.

Design questions:

1. What are the authoritative TFWT, exchangeable OBT, and non-exchangeable
   OBT compartments?
2. Is day/night represented by a state, a normalized forcing, or a process
   rate with an explicit time basis?
3. Is photosynthetic activity a measured scalar forcing or a new plant state?
4. What fresh/dry/water/hydrogen mass basis connects inventory and
   concentration?
5. What OBT-specific temperature relation, domain, and units are admissible?

Required outputs before implementation: an equation decision, state and unit
contract, inventory conservation tests, biological-scope definition, and a
dataset/benchmark plan. Until then, `kf`/`kr` may be discussed only as the
scoped reduced first-order baseline.

### R2 — Layered root uptake state

Item: `root.k_root`.

Priority: HIGH.  Coupling class:
`NUMERICAL_COUPLING_CHANGE_REQUIRED`.

Design questions:

1. Which soil and root layers own the state and activity inventory?
2. How does transpiration or water uptake drive the transfer rate?
3. What storage length, concentration basis, and aggregation map a rate to a
   velocity, if a velocity remains the chosen V3 interface?
4. How are signs, layer boundaries, and soil-plant inventory conservation
   tested?

Required outputs before implementation: a soil-root state diagram, numerical
  coupling proposal, unit/dimensional audit, conservation contract, and
  independent review. P7.5/P7.5B remains frozen until a separate coupling
  authorization is granted.

### R3 — Food-chain event/continuous boundary

Items: `food.harvest_fraction`, `food.tfwt_harvest_fraction`.

Priority: HIGH.  Coupling class:
`NUMERICAL_COUPLING_CHANGE_REQUIRED`.

Design questions:

1. Is food represented as a continuous compartment, an event product, or both?
2. How are OBT and TFWT product inventories separated and transferred?
3. What are harvest timing, product mass, harvest loss, and remaining-plant
   balances?
4. Does a continuous food state require time-coupled plant-product integration?

Required outputs before implementation: event/continuous semantics, product
basis, conservation tests, and a coupling-impact decision. No UFOTRI rate is
converted into a V3 harvest fraction during P7.6D.

### R4 — Leaf phenology/resistance relation

Item: `leaf.growth_stage`.

Priority: MEDIUM.  Coupling class: `INTERFACE_ONLY`.

Design questions:

1. What discrete or continuous stage ontology is reproducible across crops?
2. Which canopy geometry and physiology fields are stage-dependent?
3. Does stage alter a resistance equation or only stratify its evidence?
4. How are stage transitions aligned with forcing timestamps?

Required outputs before implementation: stage schema, stage-dependent equation
or explicit decision to keep stage metadata-only, measurement basis, and
validation cases. `r_a`, `r_b`, and `r_c` ownership and units remain frozen.

## Dependency and authorization gates

The proposed dependency order is:

```text
P7.6D freeze
    |
    +--> R1 OBT scope/state --------+
    |                               |
    +--> R2 root layered state -----+--> coupling and conservation review
    |                               |
    +--> R3 food boundary ----------+
    |
    +--> R4 leaf phenology (parallel design possible)
```

R1 should precede a full food-chain redesign because food transfer consumes
plant OBT/TFWT state. R2 must be reviewed before any soil-plant numerical
coupling change. R4 can be designed in parallel, but it cannot import a
vegetation-period quantity as a growth-stage parameter.

Each work package requires a separate authorization before source changes.
The following actions remain forbidden in the roadmap stage:

- editing solver equations or numerical coupling;
- changing P7.5/P7.5B pipeline semantics;
- importing or activating UFOTRI parameters;
- starting calibration or empirical validation;
- replacing the one-layer soil/root interface by assumption;
- converting continuous rates into event fractions by naming or unit scaling.

## Transition to P7.7

After redesign decisions are separately approved, P7.7 may define the
validation framework for the 12 feasible P7.6C-3 items. That framework must
keep feasible current-model validation separate from redesign completion and
must not call a reduced OBT validation a full UFOTRI validation. P7.8 parameter
validation and P7.9 calibration remain later stages.
