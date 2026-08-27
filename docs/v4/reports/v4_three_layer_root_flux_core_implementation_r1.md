# V4 three-layer root flux core implementation R1

## Status

`IMPLEMENTED_AWAITING_EXACT_HEAD_CI`

This stage implements the isolated `root_v4` subsystem authorized by the merged three-layer root coupling re-review. It does not integrate the subsystem into a V4 pipeline and does not modify the frozen V3 runtime.

## Implemented equation

For an interval beginning at `t_n`, the root core consumes the authoritative `ThreeLayerSoilState` and an explicit three-layer water-uptake forcing:

`J_root,i = q_w,i * C_w,i(S_n)`

where `q_w,i` is an externally supplied non-negative layer water-uptake flux in m/s and `C_w,i(S_n)` is the authoritative HTO concentration in layer water in Bq/m3 water. The derived HTO flux is in Bq/m2/s.

The interval transfer ledger is:

- water transfer: `q_w,i * Delta t`;
- HTO transfer: `J_root,i * Delta t`.

The core is deliberately non-mutating. It returns a typed transfer plan and does not update soil or TFWT.

## Ownership

The plan exposes the exact per-layer water and HTO sink identity needed by the already implemented `soil_v4` root sink slots. A future TFWT integration must use the same integrated HTO transfer as the receiving plant gain. This stage applies neither side itself, preventing hidden double application.

`soil_v4` remains the sole future owner of applying the soil root sink. Pipeline integration remains unauthorized.

## Time, units and provenance

Every root water-flux forcing requires:

- an explicit UTC interval-start timestamp that exactly matches the soil state timestamp;
- exactly three `q_w` values ordered L1/L2/L3;
- canonical unit `m s^-1`;
- plant identity;
- provenance fields `source_id`, `source_locator`, `revision`, `artifact_sha256`, and `profile_context`.

Missing, malformed, negative, non-finite or incompatible inputs fail closed. The solver also rejects a root-water transfer that would exhaust a layer and rejects an HTO transfer that exceeds the available layer HTO inventory.

## UFOTRI reference evidence

KfK 4605 reference information is retained in `UFOTRIRootReferenceEvidenceV4` only:

- layers 0–5, 5–15 and 15–30 cm;
- long-term water-uptake distribution 20/40/40;
- long-term reference transfer rates about 0.026/0.026/0.017 d^-1;
- short-term transpiration-to-root-uptake delay about 3 h.

The fixture has `runtime_activation = False` and has no API that creates root forcing. The long-term and short-term contexts therefore remain evidence only and cannot silently become defaults.

## Explicitly not implemented

This stage does not implement:

- transpiration calculation;
- generation or partitioning of `q_w,i`;
- a hidden 3 h history buffer;
- Richards/Darcy soil hydrology;
- conversion of an s^-1 transfer rate into m/s;
- activation of 20/40/40 or the reference d^-1 rates;
- V4 pipeline integration;
- selection between post-OBT and pre-OBT root gain ordering;
- calibration or physical validation.

## Next decision

If the exact-head CI and independent review pass, the next stage is a controlled `V4_ROOT_OPERATOR_SPLIT_COMPARISON_R1`. That stage must compare the two already frozen candidates—preserving the V3 post-OBT root gain versus applying the same-interval root gain before OBT formation—using multi-step conservation, timestep refinement, restart equivalence, deterministic repeat, and explicit profile time-basis tests.

```ini
V4_THREE_LAYER_ROOT_FLUX_CORE_IMPLEMENTATION_R1 = IMPLEMENTED_AWAITING_EXACT_HEAD_CI
ROOT_V4_CORE_AVAILABLE = TRUE
ROOT_CORE_MUTATES_SOIL = FALSE
ROOT_CORE_MUTATES_TFWT = FALSE
V4_PIPELINE_INTEGRATION_AUTHORIZED = FALSE
V4_OPERATOR_SPLIT_SELECTED = FALSE
UFOTRI_20_40_40_ACTIVE = FALSE
UFOTRI_REFERENCE_LAYER_RATES_ACTIVE = FALSE
SHORT_TERM_3H_DELAY_ACTIVE = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
PHYSICAL_VALIDATION_COMPLETE = FALSE
```
