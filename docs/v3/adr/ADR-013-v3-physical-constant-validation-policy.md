# ADR-013: V3 physical-constant validation and evidence reconciliation

## Status

Accepted for V3 P7.6C-1. This ADR authorizes validation of a physical constant
in the control plane only; it does not authorize runtime import, calibration,
or V3 physics readiness.

## Context

P7.6B-2B identified one and only one physical validation candidate:
`soil.tritium_half_life`. The existing V3 soil equation consumes an explicit
half-life in seconds and derives the decay constant as

```text
lambda_T = ln(2) / T_half
```

The candidate needs a source comparison that keeps reported source values,
uncertainties, lineage, and the selected value auditable. A second webpage or
database copy of the same evaluation is not a second independent confirmation.

## Decision

### Evidence independence

Every source is stored as an immutable `PhysicalConstantEvidenceRecord` with
the evaluation authority, evaluation date, measurement/evaluation basis,
source locator, reported value and uncertainty, explicit SI conversion,
uncertainty convention, and lineage disposition:

```text
INDEPENDENT_EVALUATION
DERIVED_FROM_EXISTING_EVALUATION
DUPLICATE_REPRESENTATION
UNKNOWN
```

Derived and duplicate records remain visible but do not increase the count of
independent evidence streams. `UNKNOWN` lineage blocks validation.

### Reconciliation hierarchy

The decision order is:

1. exact physical quantity and equation semantics;
2. recognized evaluated nuclear-data or metrology authority;
3. explicit uncertainty and convention;
4. transparent evaluation method and source lineage;
5. later/current recommendation when it supersedes an earlier evaluation;
6. traceable original measurements.

Sources are compared after explicit unit normalization. A pair is consistent
when its difference is no more than two combined standard uncertainties. This
comparison is a consistency check only. Arithmetic averaging and
inverse-variance weighting are forbidden unless a future ADR explicitly
authorizes them for a different stage.

### Uncertainty and units

Reported values and uncertainties are never overwritten. Each source retains
`reported_value`, `reported_uncertainty`, `reported_unit`,
`uncertainty_convention`, `conversion_path`, `normalized_value`,
`normalized_uncertainty`, and `normalized_unit`. The validation record stores
the selected source value and uncertainty separately in canonical SI seconds.

### Lifecycle

P7.6C-1 permits only:

```text
VALIDATION_CANDIDATE -> VALIDATED
```

and only when the typed record is `PASS`, source reconciliation is resolved,
equation/unit/applicability matches are true, the half-life semantic benchmark
passes, and independent review is complete. `PROVISIONAL -> VALIDATED` and any
transition to `ACTIVE` are rejected. A conflict or unresolved lineage produces
`HOLD` and leaves the candidate unvalidated.

The validation manifest separates the candidate snapshot from the decision:

```text
candidate_status = VALIDATION_CANDIDATE
validation_status = PASS
parameter_status = VALIDATED
```

`parameter_status = ACTIVE` is forbidden in this stage.

### Runtime isolation

The validation registry is control-plane-only. `SoilStorageSolver`, V3
pipeline modules, and protected soil/plant/exposure modules continue to receive
explicit parameter objects and do not import or resolve the validation
registry. The validated value is knowledge evidence, not a runtime default.

## Consequences

- P7.6C-1 can close the physical radioactive-decay constant without claiming
  soil transport, plant transfer, OBT, exposure, dose, or calibration validity.
- A later source update must create a new evidence record and a new explicit
  reconciliation decision; it must not overwrite the existing source record.
- `V3_PHYSICS_READY`, `UFOTRI_ACTIVE_DATABASE`, calibration, and runtime import
  remain false.
