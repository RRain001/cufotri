# V4 root operator-split comparison R1

## Status

`PASS_OPERATOR_SPLIT_SELECTION`

This stage compared the two root→TFWT→OBT operator orders frozen by the merged coupling rereview. It did not modify a production pipeline.

## Machine result

The PR exact-head machine gate returned:

- `V4_ROOT_OPERATOR_SPLIT_STATUS=PASS_SELECTION`
- portable suite: `1204 passed, 1 skipped, 57 deselected`
- frozen-boundary suite: `283 passed`
- both candidates monotonic timestep refinement: PASS
- single-application and coupled conservation: PASS
- deterministic repeat: PASS
- JSON restart equivalence: PASS
- root-pulse lag discrimination: PASS

The comparison used explicit synthetic three-layer root-water forcing and one declared `soil_surface_area` basis. No soil-area/plant-area conversion was inferred.

## Selected order

`PRESERVE_V3_POST_OBT_ROOT_GAIN`

OBT consumes interval-start TFWT. The HTO root transfer accumulated during the interval enters endpoint TFWT after OBT reconciliation.

The alternative `ROOT_GAIN_BEFORE_OBT` also converged and conserved mass, but it was not selected because it exposes the complete interval-integrated root transfer to the same interval's OBT source as though that transfer were already available at interval start. Under the current explicit first-order architecture this is a right-biased Lie split.

A root-only pulse made the distinction explicit. In the first coarse interval, the post-OBT candidate had non-zero root transfer but zero OBT formation; the pre-OBT candidate formed OBT immediately. The post-OBT one-step lag contracts under timestep refinement.

The selection is based on numerical time semantics and continuity with frozen P7.5B. Synthetic error ranking is not physical evidence.

## Integration authorization boundary

This decision does **not** itself turn on a V4 pipeline. Only after this PR passes a new exact-head CI and is merged without drift may a new isolated `V4_SOIL_ROOT_TFWT_OBT_INTEGRATION_R1` branch be created.

That next stage must remain opt-in and preserve:

- V3 default path unchanged;
- active parameters = 0;
- no calibration;
- no Leaf R5;
- no UFOTRI 20/40/40 runtime activation;
- no 0.026/0.026/0.017 d^-1 runtime defaults;
- no short-term ~3 h delay activation;
- no transpiration/hydrology generation inside root core;
- no real CTEAS-Atmos binding;
- no silent soil-area/plant-area conversion;
- no physical-validation claim.

```ini
V4_ROOT_OPERATOR_SPLIT_COMPARISON_R1 = PASS_OPERATOR_SPLIT_SELECTION
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
V4_PIPELINE_CHANGED = FALSE
V3_CHANGED = FALSE
UFOTRI_REFERENCE_PROFILE_ACTIVE = FALSE
SHORT_TERM_3H_DELAY_ACTIVE = FALSE
AREA_BASIS_CONVERSION = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
