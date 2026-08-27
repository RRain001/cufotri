# V4 soil-root-TFWT-OBT integration R1

## Status

`INTEGRATION_IMPLEMENTED_AWAITING_MACHINE_GATE`

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

No area conversion is performed. The current synthetic gate uses `soil_surface_area` for all reservoirs only because that basis is explicitly declared on every state.

## Water interpretation

The root water flux is removed from soil as the carrier associated with the HTO root-transfer plan. It is not added to TFWT water content. R1 therefore preserves the existing fixed TFWT water basis and makes no claim of coupled soil-plant water conservation or plant-water dynamics.

## Machine gate

`scripts/v4/run_soil_root_tfwt_obt_integration_r1.py` uses explicit synthetic forcing and test-only parameter values. It must prove:

- one root transfer identity;
- soil, plant, and coupled HTO conservation;
- deterministic repeat;
- JSON restart equivalence;
- root-only pulse enters endpoint TFWT but not same-interval OBT.

The repository test additionally checks overdraw rejection, area/timestamp identity, duplicate root-slot rejection, V3 pipeline isolation, and absence of runtime use of the UFOTRI root reference fixture.

## Explicit exclusions

- no parameter activation or calibration;
- no UFOTRI 20/40/40 runtime profile;
- no 0.026/0.026/0.017 d^-1 runtime defaults;
- no short-term ~3 h delay;
- no transpiration or hydrology generation;
- no plant-water storage model;
- no Leaf R5;
- no food/intake/dose V4 adapter yet;
- no real CTEAS-Atmos binding;
- no empirical or physical validation claim.

```ini
V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1 = INTEGRATION_IMPLEMENTED_AWAITING_MACHINE_GATE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
V3_DEFAULT_PATH_CHANGED = FALSE
AREA_BASIS_CONVERSION = FALSE
PLANT_WATER_DYNAMICS = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
