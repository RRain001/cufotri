# V4 root operator-split comparison R1

## Status

`COMPARISON_IMPLEMENTED_AWAITING_MACHINE_GATE`

This stage compares the two root→TFWT→OBT operator orders frozen by the merged coupling rereview. It does not modify a production pipeline.

## Candidates

`PRESERVE_V3_POST_OBT_ROOT_GAIN`

- OBT consumes the interval-start TFWT state.
- The root HTO transfer accumulated during the interval is added to endpoint TFWT after OBT reconciliation.
- A root-only pulse therefore cannot contribute to OBT during its first coarse interval; the lag contracts under timestep refinement.

`ROOT_GAIN_BEFORE_OBT`

- The complete interval-integrated root transfer is first added to TFWT.
- OBT then consumes that augmented TFWT as constant over the same interval.
- A root-only pulse therefore contributes immediately to OBT, but the full transfer accumulated over the interval is treated as available to the OBT source for the entire interval.

## Machine comparison

`scripts/v4/run_root_operator_split_comparison_r1.py` runs both candidates on the same explicit synthetic three-layer root-water forcing. It exercises the merged `root_v4` transfer plan, the `soil_v4` root sink slots, and the existing TFWT/OBT state/solver APIs without changing them.

The machine gate requires:

1. exact soil-root transfer identity and coupled soil+plant conservation;
2. monotonic timestep refinement for both candidates;
3. deterministic repeat;
4. JSON restart equivalence;
5. an explicit pulse test proving the candidate-specific root→OBT lag behavior.

The comparison uses an explicitly common `soil_surface_area` basis. No soil-area/plant-area geometry conversion is inferred.

## Conditional decision

If every machine gate passes, R1 selects `PRESERVE_V3_POST_OBT_ROOT_GAIN` for the next opt-in V4 integration stage. This is based on the frozen interval-start software semantics and continuity with P7.5B, not on a claim that a synthetic benchmark establishes biological truth.

The `ROOT_GAIN_BEFORE_OBT` candidate is then classified as a right-biased Lie split: it exposes the whole interval-integrated root gain to the OBT source for that same full interval. It is not deleted as a concept; it simply is not selected for the current explicit first-order coupling architecture.

If any gate fails, selection remains HOLD and no integration is authorized.

## Explicit exclusions

- UFOTRI 20/40/40 is not active.
- 0.026/0.026/0.017 d^-1 reference rates are not active.
- the short-term ~3 h delay is not active;
- no transpiration or hydrology model is introduced;
- no V3 path is modified;
- no real CTEAS-Atmos forcing is used;
- no physical validation claim is made.

```ini
V4_ROOT_OPERATOR_SPLIT_COMPARISON_R1 = COMPARISON_IMPLEMENTED_AWAITING_MACHINE_GATE
V4_PIPELINE_CHANGED = FALSE
V3_CHANGED = FALSE
UFOTRI_REFERENCE_PROFILE_ACTIVE = FALSE
SHORT_TERM_3H_DELAY_ACTIVE = FALSE
AREA_BASIS_CONVERSION = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
