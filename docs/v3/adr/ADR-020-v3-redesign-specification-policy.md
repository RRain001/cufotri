# ADR-020: V3 redesign specification policy

- Status: Accepted for P7.8B-1 specification scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository
- Baseline: `codex/v3-p7-8a-physics-redesign-prioritization` at `986e375`

## Context

P7.8A ranked nine physics redesign items and separated two deferred
extensions from four permanently rejected shortcuts. The next stage needs a
scientific design record before any solver or coupling source is changed.
Without that record, a plausible parameter or a unit conversion could be
mistaken for a model decision, and a root/soil/food change could silently
reopen the P7.5/P7.5B numerical boundary.

## Decision

P7.8B-1 freezes the following specification policy:

1. Every redesign specification must state the current model/equation, the
   identified gap, scientific requirement, candidate model, new states,
   candidate parameters, interface changes, coupling impact, validation data,
   complexity, priority, decision, compatibility, and migration strategy.
2. Candidate equations are design forms only. They are not implemented,
   validated, calibrated, or equivalent to UFOTRI by being written down.
3. Candidate parameters are symbolic, unit-labelled, and value-free. No
   UFOTRI value may enter runtime or calibration before a separately reviewed
   equation, applicability, provenance, and validation record exists.
4. The `v3_frozen_baseline` remains the default and all existing cases must
   continue to run without implicit state or parameter conversion.
5. Future redesigns use opt-in profiles. Missing future fields fail closed;
   current baseline fields are not reinterpreted as new mechanisms.
6. Root, layered soil, and food event/continuous candidates are
   `NUMERICAL_COUPLING_CHANGE` designs and require a future P7.5/P7.5B review.
7. OBT, leaf, and TFWT candidates may extend interfaces, but interface scope
   does not authorize a solver equation change.

The canonical specification is
`docs/v3/physics/p7_8b1_redesign_specification.yaml`. Supporting reports are:

- `docs/v3/reports/v3_p7_8b1_redesign_specification_report.md`;
- `docs/v3/reports/v3_p7_8b1_equation_gap_analysis.md`;
- `docs/v3/reports/v3_p7_8b1_coupling_impact_report.md`;
- `docs/v3/reports/v3_p7_8b1_independent_review.md`.

## Frozen decision states

The specification registry uses exactly these states:

- `APPROVED_FOR_FUTURE_IMPLEMENTATION`: a future implementation may be
  prepared after its remaining gates; this is not runtime activation;
- `REQUIRES_MORE_RESEARCH`: evidence, equation choice, or coupling design is
  insufficient for implementation selection;
- `KEEP_CURRENT_MODEL`: the frozen baseline remains the correct model for the
  current scope;
- `REJECT_REDESIGN`: the proposed redesign violates the evidence or scope
  boundary and must not be implemented.

P7.8B-1 uses `APPROVED_FOR_FUTURE_IMPLEMENTATION` only for the OBT mass-basis
contract, not for a new numerical OBT equation. The OBT biological package,
root, soil, leaf, TFWT, and food candidate physics remain
`REQUIRES_MORE_RESEARCH`.

## Coupling decision states

Future impact is classified as:

- `NO_INTERFACE_CHANGE`;
- `INTERFACE_EXTENSION`;
- `PIPELINE_CHANGE`;
- `NUMERICAL_COUPLING_CHANGE`.

These are impact classifications, not current changes. P7.5/P7.5B semantics
remain frozen in this ADR.

## Gate invariants

```ini
SPECIFICATION_ONLY = TRUE
CANDIDATE_EQUATIONS_IMPLEMENTED = FALSE
CANDIDATE_PARAMETERS_HAVE_VALUES = FALSE
IMPLEMENTATION_AUTHORIZED = FALSE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
NUMERICAL_COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The following transitions are forbidden:

```text
SPECIFICATION_ONLY              -> ACTIVE_PARAMETER
REQUIRES_MORE_RESEARCH          -> ACTIVE_PARAMETER
APPROVED_FOR_FUTURE_IMPLEMENTATION -> ACTIVE_PARAMETER
```

Before P7.8B2, the selected candidate must receive equation selection,
dimensional/unit audit, state ownership, conservation/restart tests,
validation case/data contract, coupling review where applicable, independent
review, and explicit implementation authorization.

## Non-goals

This ADR does not:

- modify plant, soil, exposure, pipeline, coupling, or parameter-runtime
  source;
- implement or benchmark a candidate equation;
- import or activate UFOTRI parameters;
- start calibration or empirical validation;
- change P7.5/P7.5B semantics;
- change `V3_PHYSICS_READY`.

## Consequences

The repository now has an auditable bridge from prioritization to future
implementation. Existing cases remain stable, while future work must carry
its own equation, evidence, state, and coupling contract. Some candidates
remain deliberately unresolved; this is a required scientific outcome, not a
missing implementation.
