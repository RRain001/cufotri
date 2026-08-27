# V4 system replay-input adapter decision R1

## Verdict

`PASS_SYSTEM_REPLAY_ORCHESTRATION_DECISION`

The architecture decision is complete and its first exact-head protected/remediation gate passed. Implementation is still not active; the pure governance closure exact head must pass again and merge without drift.

## Problem resolved

The post-integration review selected the replay-input boundary as the next system priority. Repository audit shows that this boundary cannot be implemented as a simple field mapper:

- the current atmospheric soil adapter produces the V3 one-layer `SoilForcing`, not the V4 `ThreeLayerSoilForcing`;
- the current V4 soil-root-TFWT-OBT integrator contains no leaf-exchange step;
- the frozen numerical semantics require same-interval leaf exchange to affect the TFWT inventory seen by OBT, while root gain remains post-OBT.

Therefore a field-only adapter would leave the complete Atmos -> leaf/soil -> TFWT/OBT chain incomplete.

## Selected architecture

Select a new opt-in higher-level replay-input system orchestrator for the future implementation stage. Keep the existing `V4SoilRootTFWTOBTIntegrator` unchanged as the four-module reference baseline.

The future orchestrator may compose the existing atmospheric record, baseline leaf exchange, TFWT, OBT, three-layer root and three-layer soil components. It may not change their solver equations or replace the V3 default path.

Selected interval order:

1. fail-closed validation/alignment of all records for `[t_n, t_n+1)` UTC;
2. total surface-deposition flux -> L1 atmospheric-deposition boundary only;
3. baseline signed leaf exchange;
4. TFWT leaf intermediate;
5. OBT from the leaf-updated TFWT inventory;
6. layered root plan from interval-start soil `S_n`;
7. three-layer soil advance with that exact root plan applied once;
8. endpoint TFWT reconciliation: leaf intermediate - OBT loss + root gain.

The selected operator split remains `PRESERVE_V3_POST_OBT_ROOT_GAIN`.

## Forcing ownership

Atmos/replay owns only the frozen atmospheric exchange quantities: air HTO concentration, total HTO surface-deposition flux, temperature, relative humidity, wind speed, precipitation rate, time/spatial identity, and provenance.

Three-layer soil transport inputs remain separately owned. Precipitation must not be silently interpreted as infiltration or surface-water input.

Layer root water uptake `q_w,i` remains separately sourced and separately provenanced. It must not inherit Atmos provenance by default and must not be inferred from temperature, humidity, wind, or precipitation in this adapter/orchestration stage.

Biological forcing remains explicit. Baseline leaf resistance state and equilibrium-air concentration remain explicit inputs. Dynamic stomatal Leaf R5 remains HOLD.

## Compatibility gate for the future implementation

The key regression gate is `ZERO_LEAF_EXCHANGE_EQUIVALENCE`.

For identical initial state, soil forcing, root forcing, biological forcing, interval and solver parameters, setting leaf exchange exactly to zero must reproduce the existing four-module V4 integrator endpoint state and ledgers within the established conservation tolerance.

The implementation must additionally prove deterministic repeat, restart equivalence, root-plan single application, soil/root identity closure, plant closure, coupled closure, and fail-closed time/unit/area/provenance handling.

## Timestamp decision

The TFWT solver returns a leaf-updated state stamped at interval end, whereas OBT consumes TFWT inventory without using the TFWT timestamp in its dynamics. This existing composition convention must be preserved explicitly; the new layer must not reset or forge timestamps to force compatibility.

All forcing domains must share the same explicit UTC half-open interval. Silent resampling, nearest-time substitution and hidden temporal reconciliation remain forbidden.

## First exact-head gate evidence

Exact decision head: `45298061c58cbf8f558f4b25de02ca6288dcb104`.

- Protected Gate run `33030199770`: SUCCESS
- Remediation run `33030199769`: SUCCESS
- portable suite: `1226 passed, 1 skipped, 57 deselected`
- frozen-boundary suite: `295 passed`
- sensitivity: `PASS_SOFTWARE_SCREENING`
- operator split: `PASS_SELECTION`
- soil-root-TFWT-OBT integration: `PASS_INTEGRATION`

## Boundaries retained

This closure changes no production source. It does not authorize implementation before the closure merge, and it does not authorize:

- Leaf R5;
- food/intake/dose V4 integration;
- full Richards/Darcy hydrology or hidden hydrology;
- plant-water dynamics;
- parameter activation or calibration;
- real CTEAS-Atmos coupling;
- empirical validation or physical-accuracy claims.

Real CTEAS-Atmos coupling remains blocked on the producer-side true surface-deposition-flux product required by the frozen exchange contract.

## Next-stage authorization rule

If this closure exact head passes both CI workflows and merges with `expected_head_sha` plus no-drift verification, a new isolated branch may start:

`V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1`

Until that merge:

```ini
V4_SYSTEM_REPLAY_INPUT_ADAPTER_DECISION_R1 = PASS_SYSTEM_REPLAY_ORCHESTRATION_DECISION
SELECTED_ARCHITECTURE = OPT_IN_REPLAY_INPUT_SYSTEM_ORCHESTRATOR
FIELD_ONLY_ADAPTER = REJECT_INSUFFICIENT_FOR_COMPLETE_V4_CHAIN
CURRENT_V4_FOUR_MODULE_INTEGRATOR = FREEZE_AS_REFERENCE_BASELINE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
ZERO_LEAF_EXCHANGE_EQUIVALENCE_REQUIRED = TRUE
IMPLEMENTATION_AUTHORIZED_NOW = FALSE
IMPLEMENTATION_AUTHORIZED_AFTER_NO_DRIFT_MERGE = TRUE
LEAF_R5_AUTHORIZED = FALSE
FOOD_INTAKE_DOSE_V4_INTEGRATION_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
```
