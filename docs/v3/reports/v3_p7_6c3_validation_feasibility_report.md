# V3 P7.6C-3 UFOTRI Validation-Feasibility Assessment

Date: 2026-08-24

Branch: `codex/v3-p7-6c3-validation-feasibility`

Baseline: `codex/v3-integration-review` at
`f0195c77d0521ec4ade9892e88318856934a3243`

## Decision

```ini
P7_6C3_STATUS = PASS_VALIDATION_FEASIBILITY_ASSESSMENT
ALL_PARAMETERS_ASSESSED = TRUE
MAPPED_PARAMETERS_ASSESSED = 26
DERIVED_REVIEW_ITEMS = 1
VALIDATION_FEASIBLE = 4
VALIDATION_FEASIBLE_WITH_LIMITATIONS = 8
PHYSICS_REDESIGN_REQUIRED = 9
NOT_IMPORTABLE = 4
INSUFFICIENT_INFORMATION = 1
NEW_VALIDATION_CANDIDATES = 0
VALIDATED_PARAMETERS = 1
ACTIVE_PARAMETERS = 0
PHYSICS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
CALIBRATION_STARTED = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The result is a feasibility decision, not a parameter search and not a
physics-validation claim. The one validated record remains the P7.6C-1
universal H-3 radioactive half-life. No new candidate or numerical value was
created.

## Scope and completeness

Every one of the 26 records in
`docs/v3/parameter_evidence/ufotri_parameter_mapping.yaml` has exactly one
non-derived feasibility record. The requested derived leaf conductance
`g_ex = 1 / (r_a + r_b + r_c)` is recorded as one additional review item; it
is not a new UFOTRI mapping record or an importable parameter.

The registry cross-checks, for every mapped record:

- mapping ID;
- V3 parameter ID and subsystem;
- current V3 equation;
- P7.6C-2 mapping status;
- current V3 lifecycle status.

## Feasibility interpretation

`VALIDATION_FEASIBLE` means that a future evidence pathway can test the
quantity without changing the current equation. It does not mean that the
quantity is currently validated. `VALIDATION_FEASIBLE_WITH_LIMITATIONS` means
that the future case must freeze a declared state basis, unit transformation,
boundary, timing, or biological scope before evidence admission.

`PHYSICS_REDESIGN_REQUIRED` blocks validation until the V3 representation is
changed through a separate authorized physics-design stage. `NOT_IMPORTABLE`
keeps metadata, exposure assumptions, and dose coefficients out of the
physical-parameter path. `INSUFFICIENT_INFORMATION` blocks the path until the
missing source definition is recovered.

## Main conclusions

- Leaf `r_a`, `r_b`, and `r_c` are feasible for future matched resistance
  validation; `g_ex` is derived from them and is not independently imported.
- OBT `kf` and `kr` are feasible only with explicit biological and compartment
  limitations. No rate is selected.
- Soil transport flux and water-basis records, TFWT transformation/water-loss
  fluxes, TFWT water content, and selected soil-layer geometry are feasible
  with explicit transformations and case contracts.
- OBT day/night multipliers, photosynthetic activity, plant-mass basis, and
  temperature response require physics redesign.
- Root `k_root` requires redesign because the UFOTRI rate and V3 velocity have
  different state, layer, and unit semantics.
- Food harvest fractions require redesign because the recovered UFOTRI model
  uses continuous food-chain rates rather than the V3 harvest event.
- Crop identifiers, annual consumption amount, and dose coefficient are not
  physical parameters to import. The food-product-mass definition remains
  insufficiently specified.

## Runtime and physics boundary

The assessment module and manifest are control-plane only. Production plant,
soil, exposure, coupling, and pipeline modules do not import them. The branch
does not modify plant/soil/TFWT/OBT/root/food/dose solvers, P7.5/P7.5B
coupling, V3 equations, configuration defaults, or a parameter database.
