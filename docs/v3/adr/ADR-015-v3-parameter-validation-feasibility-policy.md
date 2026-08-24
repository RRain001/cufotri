# ADR-015: V3 UFOTRI Parameter Validation-Feasibility Policy

- Status: Accepted for P7.6C-3 control-plane scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository

## Context

P7.6C-2 completed a semantic comparison for 26 V3 quantities against the
recovered UFOTRI manual. A semantic match is not automatically a validation
candidate: several records are exposure assumptions, metadata, incompatible
state bases, or mechanisms that the current V3 equations do not represent.
The original UFOTRI source implementation is still unavailable.

## Decision

P7.6C-3 freezes five feasibility states:

- `VALIDATION_FEASIBLE`: the physical quantity, equation role, unit, and
  compartment align; a future evidence path can be defined without changing
  the current V3 equation.
- `VALIDATION_FEASIBLE_WITH_LIMITATIONS`: the current equation can be tested
  under explicit state, unit, timing, or scope assumptions; those limitations
  must be documented before a future candidate is admitted.
- `PHYSICS_REDESIGN_REQUIRED`: the UFOTRI mechanism or state basis cannot be
  represented by the current V3 equation without an unsupported assumption.
- `NOT_IMPORTABLE`: the record is metadata, a scenario/exposure assumption,
  a regulatory coefficient, or another quantity outside UFOTRI environmental
  physics.
- `INSUFFICIENT_INFORMATION`: the source definition or quantity semantics are
  incomplete, so feasibility cannot be established.

The canonical decision matrix is
`docs/v3/parameter_evidence/parameter_validation_feasibility.yaml`, with its
immutable record type in
`src/cteas_ufotri/parameters_v3/validation_feasibility.py`.

## Gate

Only the first two states return `can_enter_validation = true`:

```text
VALIDATION_FEASIBLE
VALIDATION_FEASIBLE_WITH_LIMITATIONS
```

The other three states fail closed. `can_activate` is always false in this
stage, and an activation request raises a lifecycle error. A feasibility
decision never creates a candidate, selects a value, or changes a solver.

## Decision rules

1. Exact resistance components `r_a`, `r_b`, and `r_c` may receive a future
   validation dataset because their roles and units match. `g_ex` is reviewed
   only as a derived quantity from those components.
2. OBT `kf` and `kr` are potentially testable under explicit biological-scope
   and compartment limitations. Day/night multipliers, photosynthetic forcing,
   plant-mass basis, and temperature response require model redesign first.
3. A UFOTRI root rate is not a V3 root velocity without a declared state,
   length, and layer aggregation; `root.k_root` therefore requires redesign.
4. Soil flux and water-basis transformations are feasible only with declared
   sign, boundary, layer, density, and state-basis contracts. The universal
   H-3 half-life remains the one existing validated constant.
5. Continuous UFOTRI food-chain rates cannot be converted into V3 harvest
   fractions by naming or arithmetic alone; food harvest fractions require
   redesign.
6. Crop identifiers, consumption habits, and dose coefficients remain outside
   physical-parameter validation. An unrecovered product-mass definition is
   `INSUFFICIENT_INFORMATION`.

## Safeguards and non-goals

This ADR does not add a validated-value database, an active database, a
runtime lookup, a calibration routine, a new equation, or a numerical-coupling
change. `ACTIVE_PARAMETERS = 0`, `CALIBRATION_STARTED = FALSE`,
`UFOTRI_ACTIVE_DATABASE = FALSE`, and `V3_PHYSICS_READY = FALSE` remain
mandatory. A future physics redesign must use a separate stage and ADR.
