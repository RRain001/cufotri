# V4 soil-root-TFWT-OBT integration R1

## Status

`PASS_SOIL_ROOT_TFWT_OBT_INTEGRATION`

This stage introduces one isolated opt-in orchestration seam connecting the already merged V4 three-layer soil and root cores to the existing TFWT and OBT inventories. It does not replace or modify the frozen V3 default pipeline.

## Implemented order

The selected numerical order is `PRESERVE_V3_POST_OBT_ROOT_GAIN`:

1. root transfer plan from interval-start three-layer soil and explicit `q_w,i`;
2. OBT solve from interval-start TFWT;
3. the exact root-plan fluxes are inserted once into otherwise root-empty soil forcing;
4. soil advances with that root sink;
5. endpoint TFWT is reconciled as start TFWT minus OBT formation plus root HTO transfer.

The integrator checks root-plan/soil-sink identity and plant plus coupled HTO ledgers. OBT is not allowed to consume root HTO that arrives only during the same interval.

## Fail-closed boundaries

- soil, TFWT, and OBT timestamps must match at interval start;
- TFWT and OBT plant/crop/growth-stage identities must match;
- soil, TFWT, and OBT must declare exactly one common area basis;
- base soil root extraction slots must be zero;
- root forcing plant identity and timestamp must match;
- OBT formation cannot exceed interval-start TFWT;
- any non-closing root identity, soil balance, plant balance, or coupled HTO balance rejects the step.

No area conversion is performed. The synthetic gate uses `soil_surface_area` for all reservoirs only because that basis is explicitly declared on every state.

## Water interpretation

The root water flux is removed from soil as the carrier associated with the HTO root-transfer plan. It is not added to TFWT water content. R1 therefore preserves the existing fixed TFWT water basis and makes no claim of coupled soil-plant water conservation or plant-water dynamics.

## Exact-head machine evidence

Implementation head `966ac71c590b8a0e850d9d9ec01b5bdcef285116` passed protected gate run `33028178452`:

- portable suite: `1216 passed`, `1 skipped`, `57 deselected`;
- frozen-boundary suite: `295 passed`;
- sensitivity screening: `PASS_SOFTWARE_SCREENING`;
- operator-split comparison: `PASS_SELECTION`;
- integration machine gate: `PASS_INTEGRATION`;
- deterministic repeat: PASS;
- restart equivalence: PASS;
- root-only pulse post-OBT semantics: PASS;
- maximum root identity residual: `0 Bq/m²`;
- maximum plant residual: `4.44e-16 Bq/m²`;
- maximum soil residual: `4.16e-17 Bq/m²`;
- maximum coupled residual: `4.88e-15 Bq/m²`.

The synthetic H-3-scale half-life used by the machine harness is explicitly `TEST_ONLY` numerical conditioning. It is not a production default, validated parameter, calibration result, or runtime activation.

The governance closure commit changes only this stage's ADR/governance/report assertions. That new exact head must rerun the full protected gate before Ready/merge.

## Explicit exclusions

- no parameter activation or calibration;
- no UFOTRI 20/40/40 runtime profile;
- no 0.026/0.026/0.017 d^-1 runtime defaults;
- no short-term ~3 h delay;
- no transpiration or hydrology generation;
- no plant-water storage model;
- no Leaf R5;
- no food/intake/dose V4 adapter;
- no real CTEAS-Atmos binding;
- no empirical or physical validation claim;
- no next implementation stage is authorized by this closure.

```ini
V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1 = PASS_SOIL_ROOT_TFWT_OBT_INTEGRATION
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
V3_DEFAULT_PATH_CHANGED = FALSE
AREA_BASIS_CONVERSION = FALSE
PLANT_WATER_DYNAMICS = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
NEXT_STAGE_AUTHORIZED = FALSE
```
