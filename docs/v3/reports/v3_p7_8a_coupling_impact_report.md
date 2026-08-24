# V3 P7.8A Coupling Impact Report

## Decision

```ini
COUPLING_MATRIX_STATUS = COMPLETE
CURRENT_V3_MODEL = FROZEN
NUMERICAL_COUPLING_CHANGED = FALSE
P7_5_REOPENED = FALSE
P7_5B_REOPENED = FALSE
PIPELINE_CHANGED = FALSE
IMPLEMENTATION_AUTHORIZED = FALSE
```

The machine-readable matrix is
`docs/v3/physics/p7_8a_coupling_impact_matrix.yaml`. It classifies future
impact; it does not make any current impact real.

## Impact states

| State | P7.8A meaning |
|---|---|
| `NO_IMPACT` | The design question remains internal to the current subsystem boundary; no coupling change is identified at this stage |
| `INTERFACE_CHANGE_ONLY` | A typed forcing, state-basis, or metadata interface may be required, without a new time-coupled numerical link |
| `PIPELINE_CHANGE_REQUIRED` | A future change would alter forcing/state ownership or pipeline semantics and needs a separate pipeline review |
| `NUMERICAL_COUPLING_REDESIGN_REQUIRED` | A future change alters a state/time boundary and requires explicit numerical-coupling design and P7.5/P7.5B review |

The matrix contains 15 governed records: 9 redesign items, 2 deferred
extensions, and 4 rejected proposals.

| Impact state | Count | Representative items |
|---|---:|---|
| `NO_IMPACT` | 2 | OBT daylight and nighttime state questions |
| `INTERFACE_CHANGE_ONLY` | 4 | OBT activity/mass/temperature and leaf phenology |
| `PIPELINE_CHANGE_REQUIRED` | 3 | TFWT water balance and rejected parameter/dose boundary expansions |
| `NUMERICAL_COUPLING_REDESIGN_REQUIRED` | 6 | Root, food, deferred soil hydrology, and rejected shortcuts |

## Redesign assessment

### No current coupling impact

`R1_OBT_DAYLIGHT_FORMATION_STATE` and
`R2_OBT_NIGHTTIME_FORMATION_STATE` are currently internal OBT design
questions. A future decision could add a state or forcing boundary, but P7.8A
does not assume one and does not modify the OBT solver.

### Interface-only impact

`R3_OBT_PHOTOSYNTHETIC_FORCING_STATE`, `R4_OBT_PLANT_MASS_BASIS`,
`R5_OBT_TEMPERATURE_RESPONSE`, and `R9_LEAF_PHENOLOGY_RESISTANCE` may require
typed forcing, coordinate, or basis metadata. No new numerical link, default,
or runtime parameter is selected. The existing `r_a + r_b + r_c` chain,
TFWT/OBT public state boundaries, and provenance contracts remain unchanged.

### Pipeline change required

`D1_TFWT_WATER_TURNOVER_GROWTH_DILUTION` would require explicit water-balance
forcing/state ownership and pipeline semantics. It is deferred until data and
the boundary are defined. The rejected `X1` and `X4` proposals would also
cross the parameter or external dose boundary, so they are rejected rather
than implemented as pipeline changes.

### Numerical-coupling redesign required

`R6_ROOT_LAYERED_UPTAKE_STATE` changes soil/root layer ownership, water uptake,
aggregation, and conservation. `R7` and `R8` change the plant-product time
boundary and must keep OBT and TFWT product states separate. `D2` would reopen
hydrologic and soil-root state ownership. `X2` and `X3` are classified by the
boundary they would silently corrupt, but remain permanently rejected.

These items require, at minimum, a state diagram, unit and sign contract,
time-discretization decision, conservation ledger, restart/refinement tests,
failure behavior, P7.5/P7.5B compatibility assessment, and independent
review before any implementation authorization.

## Current boundary preservation

No file under the following runtime owners is changed by P7.8A:

- `src/cteas_ufotri/plant/`;
- `src/cteas_ufotri/soil/`;
- `src/cteas_ufotri/exposure/`;
- `src/cteas_ufotri/coupling/`;
- `src/cteas_ufotri/v3_pipeline/`;
- `src/cteas_ufotri/parameters_v3/`.

The P7.8A registry and matrix are documentation/control-plane artifacts and
are not imported by production owners. Synthetic benchmark success does not
relax this isolation.

## Coupling gate

The following transitions remain forbidden:

```text
REDESIGN_REQUIRED  -> ACTIVE
REDESIGN_REQUIRED  -> VALIDATED
DEFERRED           -> ACTIVE
DEFERRED           -> VALIDATED
```

The only valid future route is:

```text
planning
  -> equation/state/data design
  -> coupling and conservation review when applicable
  -> independent review
  -> explicit implementation authorization
  -> separately gated implementation
```

P7.8A stops at the planning node.
