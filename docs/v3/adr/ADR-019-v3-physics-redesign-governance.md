# ADR-019: V3 physics redesign governance

- Status: Accepted for P7.8A planning scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository
- Baseline: `codex/v3-p7-7b-synthetic-benchmark` at `9490c21`

## Context

P7.6C-3 separated future validation feasibility from missing V3 equations.
P7.6D then froze the current V3 model and identified nine
`REDESIGN_REQUIRED` records. P7.7A supplied a validation framework and P7.7B
demonstrated synthetic software behavior, but neither stage established
environmental realism, empirical validation, calibration, or UFOTRI
equivalence.

Without a separate prioritization stage, a high-impact gap could be turned
into an implementation request by selecting a plausible parameter, silently
changing a state basis, or treating a synthetic benchmark as evidence. Root
and food redesigns can additionally reopen numerical boundaries that were
explicitly frozen by P7.5/P7.5B.

## Decision

P7.8A establishes a control-plane-only redesign governance process:

1. The current V3 equations, interfaces, and numerical coupling remain
   frozen while redesigns are ranked.
2. Every P7.6D `REDESIGN_REQUIRED` record receives a scientific-impact,
   dose-pathway, uncertainty, validation-availability, engineering-cost, and
   coupling-impact assessment.
3. Every redesign records its required validation data, prerequisites,
   forbidden shortcut, recommended V3.1/V3.2/V4 stage, and exit evidence.
4. Coupling impact is classified before implementation using the four frozen
   states `NO_IMPACT`, `INTERFACE_CHANGE_ONLY`,
   `PIPELINE_CHANGE_REQUIRED`, and
   `NUMERICAL_COUPLING_REDESIGN_REQUIRED`.
5. A redesign cannot enter validation or become active directly. It requires
   an equation/state/data design, conservation and coupling review where
   applicable, independent review, and explicit implementation
   authorization.
6. Unreviewed parameter import, rate-to-velocity scaling, continuous-rate to
   event-fraction scaling, and dose-driven environmental-physics redesign are
   permanently rejected.

The canonical records are:

- `docs/v3/physics/p7_8a_redesign_priority_registry.yaml`;
- `docs/v3/physics/p7_8a_coupling_impact_matrix.yaml`;
- `docs/v3/reports/v3_p7_8a_redesign_prioritization_report.md`;
- `docs/v3/reports/v3_p7_8a_physics_evolution_roadmap.md`;
- `docs/v3/reports/v3_p7_8a_coupling_impact_report.md`.

## Roadmap decision

### V3.1 — contracts and small interfaces

V3.1 may prepare the leaf growth-stage ontology and OBT mass-basis contract,
while preserving the current equations. It may also close the current TFWT
and soil basis/timing contracts. No parameter value or physical extension is
activated by a contract-only artifact.

### V3.2 — biological extensions

V3.2 is the candidate stage for the OBT day/night, photosynthetic activity,
and temperature package after the mass/state contracts are frozen. The
reduced `kf/kr` equation remains a scoped baseline until a new equation and
matched validation dataset pass review.

### V4 — state and numerical-coupling redesigns

V4 is the candidate stage for layered root uptake, continuous/event food
boundaries, and any justified soil hydrology redesign. These items require a
new state diagram and P7.5/P7.5B compatibility review before implementation.

## Gate invariants

P7.8A must preserve:

```ini
CURRENT_V3_MODEL = FROZEN
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The following direct transitions are forbidden:

```text
REDESIGN_REQUIRED  -> ACTIVE
REDESIGN_REQUIRED  -> VALIDATED
DEFERRED           -> ACTIVE
DEFERRED           -> VALIDATED
```

`REDESIGN_REQUIRED` means that the current representation is insufficient for
the intended mechanism. It is not a parameter status and it is not a
validation result.

## Non-goals

This ADR does not:

- modify plant, soil, exposure, coupling, pipeline, or parameter-runtime
  source;
- import or activate UFOTRI parameters;
- select a new equation or calibration value;
- start empirical validation or calibration;
- reopen P7.5/P7.5B numerical semantics;
- change `V3_PHYSICS_READY`.

## Consequences

The repository now has a reviewable answer to what must be redesigned, what
can wait, what affects coupling, and what is permanently out of scope. The
cost is that the nine blocking records remain blocked until their individual
design and evidence requirements are met. This is intentional: planning
completeness does not substitute for physical evidence or implementation
authorization.
