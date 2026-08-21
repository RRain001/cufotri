# V3-P5.2 UFOTRI Physics Migration Readiness Report

Date: 2026-08-21

## Verdict

```text
P5.2_STATUS = PASS_ARCHITECTURE_READY
UFOTRI_PARAMETERS_IMPORTED = FALSE
UFOTRI_PHYSICS_IMPLEMENTED = FALSE
V3_FORMAL_PHYSICS = NOT_STARTED
MAIN_BEHAVIOR_CHANGED = FALSE
SRC_DIFF = 0
CONFIG_DIFF = 0
TRUSTED_REGISTRY_DIFF = 0
```

`UFOTRI_PARAMETERS_IMPORTED = FALSE` and `UFOTRI_PHYSICS_IMPLEMENTED =
FALSE` are scoped to the V3 P5.1 migration layer and the V3 P1-P4 formal
frameworks audited here. The repository retains a frozen V2 legacy path with
existing manual/UFOTRI equations and defaults; P5.2 neither imports those
values into V3 nor modifies that path.

## Baseline and branch boundary

```text
BASE_MAIN_SHA = 6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
CURRENT_PARAMETER_LAYER_SHA = 92772160a236ee7e0038107038c384c3e74580cb
CURRENT_LEAF_MODULE_SHA = 20a93a6464fd937947c501683b9a27e8ea9e82b2
BRANCH = codex/v3-ufotri-physics-readiness-audit
BRANCH_BASE = CURRENT_PARAMETER_LAYER_SHA
```

`main` predates the already-delivered P1-P5.1 V3 framework. The audit branch
therefore starts from the current P5.1 branch head so the readiness review
sees the actual migration seams. `BASE_MAIN_SHA` is recorded for comparison;
the P5.2 diff contract (`SRC_DIFF = 0`, `CONFIG_DIFF = 0`) means the changes
introduced by this audit branch after its P5.1 base, not the intentional
P1-P5.1 source difference between the current branch and `main`.

## Phase findings

### Leaf Exchange process

The current V3 process has explicit state, forcing, parameter, replaceable
physics, and mass-balance seams. The default physics path fails closed, while
synthetic kernels are test-only. The missing physical capabilities are:

- boundary-layer, stomatal, and cuticular resistance decomposition;
- separate exchange-pathway ownership and flux reporting;
- reviewed TFWT-to-OBT formation and turnover kinetics;
- reference trajectories and an equivalence disposition.

These gaps are recorded in the readiness audit and ADR-009. No interface was
changed.

### Parameter database

P5.1 supports scalar values, units, ranges, source metadata, provenance, and
lifecycle validation. It does not support the typed tables, time/crop/stage
dimensions, interpolation policies, or function parameters likely required by
some UFOTRI relations. A future extension ADR is recorded; the current schema
was not modified.

### Atmospheric forcing

The proposed `AtmosphericHTOForcing` contract separates HTO concentration and
meteorological context from the upstream producer. It defines required time,
concentration, temperature, and humidity fields plus optional precipitation,
radiation, boundary-layer height, and deposition flux. No conversion from
ERA5 or any dispersion product to HTO is introduced.

### Soil and plant coupling

The V3 soil root-zone seam remains read-only and has no root uptake. The future
architecture branches one atmospheric forcing record independently to leaf and
soil/root pathways, then requires an explicit shared ledger to prevent double
counting. No three-layer soil or plant coupling implementation was added.

### Validation contract

Cases A (constant air HTO), B (step/pulse release), and C (diurnal forcing)
are defined with required outputs `TFWT(t)`, `OBT(t)`, and mass-balance
residuals. Concrete tolerances and reference values remain
`TO_BE_FROZEN_IN_P6`.

## Deliverables

- `docs/v3/architecture/leaf_exchange_physics_readiness_audit.md`
- `docs/v3/architecture/ADR-009-leaf-exchange-extension.md`
- `docs/v3/architecture/parameter_database_future_extensions.md`
- `docs/v3/interfaces/atmospheric_hto_forcing_contract.md`
- `docs/v3/architecture/soil_plant_coupling_readiness.md`
- `docs/v3/validation/ufotri_physics_regression_contract.md`
- `tests/architecture/test_ufotri_physics_readiness.py`

The implementation status document is updated with the same P5.2 verdict.

## P6 prerequisites

P6 may begin only after the following are separately frozen: reviewed
equations, typed parameter/database extensions where required, provenance and
reference artifacts, atmospheric forcing semantics, independent leaf/root
coupling ownership, and concrete regression tolerances. P5.2 is not a claim
of physical validation, regulatory suitability, or UFOTRI numerical
equivalence.
