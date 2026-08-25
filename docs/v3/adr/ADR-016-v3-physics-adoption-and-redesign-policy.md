# ADR-016: V3 physics adoption and redesign policy

- Status: Accepted for P7.6D decision scope
- Date: 2026-08-24
- Decision owner: CTEAS_UFOTRI repository
- Baseline: `codex/v3-p7-6c3-validation-feasibility` at
  `e27badfe7aabb5a030607e8604c73e0598322a0f`

## Context

P7.6C-3 assessed every 26 P7.6C-2 mapping records and one requested derived
leaf conductance item. Feasibility is not model adoption: a feasible record
only says that a future evidence pathway can be designed under the stated
equation and scope. It does not select a value, create a candidate, or make
the current V3 model equivalent to UFOTRI.

The P7.6D decision must therefore separate six outcomes:

- `KEEP_CURRENT_V3`: freeze the current equation or derived relation as the
  baseline.
- `VALIDATE_CURRENT_MODEL`: retain the equation and permit a separately
  governed future validation contract.
- `EXTEND_V3_PHYSICS`: retain a scoped reduced baseline while reserving a
  backward-compatible extension for missing process scope.
- `REDESIGN_REQUIRED`: the current state/equation cannot represent the target
  mechanism without an unsupported assumption.
- `DO_NOT_IMPORT`: the item is metadata, an exposure assumption, or an
  external dosimetry coefficient rather than environmental physics.
- `WAIT_FOR_EVIDENCE`: the source definition or state basis is incomplete.

## Decision

The canonical decision registry is
`docs/v3/physics/p7_6d_physics_adoption_decision.yaml`. It covers all 27
P7.6C-3 assessment records exactly once and freezes the following disposition:

| Adoption decision | Count | Interpretation |
| --- | ---: | --- |
| `KEEP_CURRENT_V3` | 2 | Existing H-3 decay role and derived leaf conductance relation remain frozen |
| `VALIDATE_CURRENT_MODEL` | 9 | Leaf resistance components, selected soil quantities, and TFWT quantities may enter a future scoped validation path |
| `EXTEND_V3_PHYSICS` | 2 | OBT `kf`/`kr` remain a reduced first-order baseline; full compartment scope is deferred |
| `REDESIGN_REQUIRED` | 9 | OBT mechanism fields, root uptake, food harvest representation, and stage-dependent resistance are blocked |
| `DO_NOT_IMPORT` | 4 | Crop metadata, consumption habit, and dose coefficient stay outside UFOTRI physics |
| `WAIT_FOR_EVIDENCE` | 1 | Food-product mass semantics must be recovered or independently defined |

The current V3 model remains frozen. In particular:

1. The existing resistance chain and derived `g_ex` relation remain the
   baseline; no UFOTRI resistance value is imported.
2. TFWT storage and explicit transformation/water-loss boundary interfaces
   remain the baseline. Unit, area, timing, water-basis, and boundary
   contracts must be declared before future validation.
3. OBT `kf`/`kr` are retained only as a scoped first-order reduced model. The
   decision does not validate a rate or authorize a value.
4. Root `k_root` is not converted from a UFOTRI rate into a V3 velocity.
5. Continuous UFOTRI food-chain rates are not converted into V3 harvest
   fractions.
6. Dose coefficients, crop identifiers, and consumption amounts do not enter
   the environmental-physics validation path.

## Redesign policy

The nine blocking items are grouped in
`docs/v3/physics/p7_6d_redesign_priority_matrix.yaml`:

1. OBT formation scope and state: daylight/nighttime treatment,
   photosynthetic activity, plant-mass basis, and temperature response.
2. Layered root uptake state: root rate, water uptake, layer aggregation, and
   conservation boundary.
3. Food-chain event/continuous boundary: organic and TFWT harvest
   representations.
4. Leaf phenology/resistance relation: stage ontology and stage-dependent
   resistance equation.

These are design work packages only. A future implementation stage must first
freeze equations, state ownership, units, conservation tests, validation
requirements, and provenance. The priority matrix does not authorize any of
those implementations.

## Numerical-coupling decision

P7.6D makes no current numerical-coupling change. The redesign records classify
future impact as follows:

- `NO_IMPACT`: OBT day/night fields remain internal design questions until a
  new state is approved.
- `INTERFACE_ONLY`: stage, photosynthesis, plant-mass, and temperature
  redesigns may require typed forcing or basis interfaces.
- `NUMERICAL_COUPLING_CHANGE_REQUIRED`: layered root uptake and a continuous
  food-chain representation would change a future soil-plant or plant-product
  time boundary.

P7.5/P7.5B interfaces, equations, and numerical semantics are not reopened by
this ADR.

## Gates and non-goals

The P7.6D registry is control-plane only. Its gate has these invariants:

- a `REDESIGN_REQUIRED` record cannot enter validation;
- `DO_NOT_IMPORT` and `WAIT_FOR_EVIDENCE` records cannot enter physical
  validation;
- no record can become `ACTIVE`;
- no parameter value, active database, runtime lookup, calibration, solver
  equation, or numerical-coupling implementation is created;
- `IMPLEMENTATION_STARTED = FALSE`, `ACTIVE_PARAMETERS = 0`,
  `CALIBRATION_STARTED = FALSE`, `UFOTRI_ACTIVE_DATABASE = FALSE`, and
  `V3_PHYSICS_READY = FALSE` remain mandatory.

The gate tests and architecture tests are in
`tests/unit/test_p7_6d_physics_adoption.py` and
`tests/architecture/test_p7_6d_physics_adoption_boundary.py`.

## Consequences

The next valid activity for the 12 feasible P7.6C-3 items is a separately
reviewed P7.7 validation framework with explicit dataset and benchmark
contracts. The nine redesign items must first pass their future design gates.
P7.6D does not imply that any parameter is validated, calibrated, or ready for
production use.
