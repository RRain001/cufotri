# ADR-021: V3 Physics Selection and Architecture Decision Policy

- Status: Accepted for P7.8B-2 selection scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository
- Baseline: `codex/v3-p7-8b1-redesign-specification` at `9d3ba09`

## Context

P7.8A prioritized nine physics redesign items and two deferred extensions.
P7.8B-1 converted them into candidate equations, state contracts, parameter
descriptors, validation requirements, and coupling impacts. A further
decision is needed before implementation so that a plausible candidate is not
silently treated as an approved runtime equation or parameter.

## Decision

P7.8B-2 freezes the following future direction:

1. V3.1 prepares an explicit plant/product mass-basis contract and preserves
   the current equations, state serialization, and numerical coupling.
2. V4 selects a precursor plus exchangeable/non-exchangeable OBT package, a
   dynamic stomatal response at the existing leaf resistance boundary, and a
   water-flux-coupled layered root boundary.
3. The existing one-layer signed soil transport, fixed TFWT storage, and
   harvest-event food environmental transfer remain current models.
4. Consumption remains an external scenario input and dose remains an
   external dosimetry/regulatory layer.
5. Full/layered soil hydrology, dynamic TFWT water turnover, and hybrid food
   product states remain insufficient evidence. Organ-specific OBT growth,
   standalone moisture root response, continuous-only food transfer, and
   correction-factor substitutes are rejected for this roadmap.
6. Future implementation order is: data/state contracts, leaf response, OBT
   package, then root water-flux coupling. This order does not authorize code.

The canonical records are:

- `docs/v3/physics/p7_8b2_physics_selection.yaml`;
- `docs/v3/physics/p7_8b2_architecture_roadmap.yaml`;
- `docs/v3/physics/p7_8b2_coupling_decision.yaml`;
- `docs/v3/physics/p7_8b2_validation_dependency.yaml`.

## Decision-state semantics

The selection registry uses exactly these states:

- `SELECTED_FOR_V3_1`: a contract/evidence item selected for V3.1; not a
  numerical equation or active parameter;
- `SELECTED_FOR_V4`: a future architecture selected for a later opt-in profile;
  implementation remains gated;
- `KEEP_CURRENT`: the frozen current boundary remains the selected model;
- `REJECTED`: rejected for this roadmap or as an invalid shortcut, with the
  scope recorded in the reason;
- `INSUFFICIENT_EVIDENCE`: not selected because equation, data, ownership, or
  coupling evidence is incomplete.

These states are decisions about scope and order. None is a runtime lifecycle
state.

## Coupling policy

The current coupling remains unchanged. Future impacts are classified as:

- `NO_IMPACT`;
- `INTERFACE_EXTENSION`;
- `PIPELINE_CHANGE_REQUIRED`;
- `NUMERICAL_COUPLING_CHANGE_REQUIRED`.

Root uptake is explicitly a numerical-coupling change and requires a new
P7.5/P7.5B review. TFWT water turnover would be a pipeline change. Layered
soil hydrology and continuous/hybrid food transfer would be numerical-coupling
changes if later selected. These classifications describe future work and do
not change current semantics.

## Evidence and activation gates

Before P7.8C implementation of a selected future model, the repository must
have:

1. an equation and unit contract with a dimensional audit;
2. explicit state ownership, basis, timestamp, and provenance rules;
3. component and total conservation tests, restart tests, and relevant
   refinement/failure tests;
4. a validation dataset and case contract with pre-registered metrics;
5. a coupling review whenever a pipeline or numerical boundary changes;
6. an independent review; and
7. explicit implementation authorization.

Candidate parameters remain symbolic until their source, applicability,
equation, units, validation plan, and admission decision are independently
reviewed. Unreviewed UFOTRI values and inferred conversions are forbidden.

## Compatibility

`v3_frozen_baseline` remains the default, runnable, and rollback profile.
Future profiles are opt-in and fail closed when required fields are missing.
There is no automatic conversion from current day/night multipliers to future
forcing functions, from scalar root rates to layer fluxes, from activity loss
to water loss, or from harvest fractions to continuous product rates.

## Non-goals

This ADR does not:

- modify plant, soil, food, exposure, pipeline, coupling, solver, or
  parameter-runtime source;
- implement, benchmark, calibrate, or validate a selected candidate;
- import or activate a UFOTRI parameter;
- change P7.5/P7.5B semantics;
- set `V3_PHYSICS_READY = TRUE`.

## Consequences

The repository has a final, traceable future model direction and a frozen
implementation order while retaining a conservative runnable baseline. The
selected V4 items have explicit data and coupling gates; unresolved physics
cannot enter implementation by default. The consequence is that V3 remains
architecture-ready rather than physics-ready until the later evidence and
authorization stages pass.

```ini
P7_8B2_STATUS = PASS_PHYSICS_SELECTION
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```
