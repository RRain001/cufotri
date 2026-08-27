# ADR-035: V4 system post-orchestration review R1

## Status

`PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_CLOSURE_GATE`

## Context

The project north star is a traceable chain from atmospheric HTO forcing and deposition through soil/plant HTO, TFWT/OBT, food, intake, and dose. The replay-input orchestration merged in PR #30 closes the previously missing opt-in upstream system seam from atmospheric replay through leaf exchange, three-layer soil/root coupling, TFWT, and OBT without changing the frozen V3 default or component equations.

The previous post-integration review ranked `FOOD_INTAKE_DOSE_V4_ADAPTER_DECISION` second and deferred it only until the upstream input boundary was decided. That blocker is now resolved. This review therefore re-evaluates the next system-level gap rather than reopening already-frozen subsystem physics.

## Evidence reviewed

This decision is based on the merged repository state at `a03da884eb60b82658c07e0ca57db7058480260f`, including:

- the previous system post-integration review;
- the structural physics-gap/sensitivity audit;
- the synthetic sensitivity execution;
- the merged replay-input orchestration and its two exact-head CI gates;
- the current V3 food, intake, and dose public APIs;
- the V3.1 mass-basis/tissue/area-basis contract.

The sensitivity screen remains computational, not physical. In particular, the mixed endpoint's high local dependence on `food.tfwt_harvest_fraction` demonstrates that endpoint definition matters; it does not validate a transfer fraction or authorize parameter fitting.

## Current system state

After PR #30:

- atmospheric replay can drive total surface deposition and baseline leaf exchange into the opt-in V4 system seam;
- three-layer soil/root, TFWT, and reduced OBT are integrated under the frozen `PRESERVE_V3_POST_OBT_ROOT_GAIN` split;
- the replay endpoint exposes the existing public `OBTState` and `TFWTState` at the interval endpoint;
- `FoodTransferSolver` already consumes those public state types, but it is not part of the V4 replay system;
- `FoodIntakeSolver` converts a food-product inventory plus explicit product mass/annual consumption into annual intake;
- `DoseSolver` converts annual intake plus an explicit dose coefficient into dose;
- all three downstream stages are one-way endpoint/readout operations and do not currently feed back into the replay dynamics;
- the V3.1 mass-basis contract is metadata/fail-closed governance only and implements no numerical fresh/dry/water/hydrogen conversion.

## Priority decision

Select `V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1` as the next control-plane stage.

This is the smallest next step that can connect the now-merged replay system to the complete north-star endpoint without changing upstream physics. It is a decision stage only. No adapter implementation is authorized by this review.

## Required decisions for the next stage

The next adapter decision must freeze all of the following before code is written.

### 1. Terminal harvest semantics

R1 must use an explicit **terminal diagnostic harvest readout**. A harvest is not automatically executed every replay interval. It occurs only when the caller supplies an explicit terminal harvest request against a completed replay endpoint.

The current V3 food solver calculates transferred and remaining inventories but does not mutate the source OBT/TFWT states. Therefore R1 must not allow the same dynamic trajectory to continue after a diagnostic harvest while pretending that the source plant inventory has been depleted. Any state-mutating or repeated-harvest model is a separate future physics/coupling decision.

### 2. Time semantics

The harvest source states must share the exact replay endpoint timestamp. Food, intake, and dose outputs may carry that event timestamp as their provenance anchor. The annual intake period is an exposure-period transform, not a claim that food transfer or plant dynamics were continuously simulated for one year.

### 3. Area ownership

Replay TFWT/OBT inventories are authoritative on `soil_surface_area`. The adapter decision must define the harvest-area mapping explicitly and must forbid silent conversion to leaf area, plant area, or any other area basis. A numerical area conversion outside the already-explicit `harvest_area_m2` multiplication is not authorized.

### 4. Mass/tissue/product basis

A downstream V4 adapter must carry an explicit V3.1 `MassBasisContract` for the food product/measurement boundary. Direct comparison is allowed only for identical mass, tissue, and area bases. Cross-basis conversion remains blocked unless separately evidenced under the V3.1 contract; this stage must not invent a numerical fresh/dry/water/hydrogen conversion.

`food_product_mass_kg` must describe the same declared food product whose total activity inventory is consumed by the intake solver. It is not a hidden biomass, yield, moisture, or tissue conversion parameter.

### 5. OBT/TFWT harvest mode

The next decision must make the endpoint mode explicit: OBT-only or OBT+TFWT. Mixed-mode TFWT harvest fraction must be explicit and separately provenanced. The adapter must not silently infer it from sensitivity results, crop identity, water content, or other state fields.

### 6. Provenance and identity

Harvest parameters, food-product mass/consumption parameters, and dose coefficients must retain independent provenance. Food-product identity, age group, consumer, radionuclide, pathway, and period semantics must fail closed on mismatch. No value may be promoted from provisional/test/scenario status to active merely because the adapter can execute.

### 7. No upstream side effects

The endpoint adapter must be composition/readout only. With identical replay endpoint state, evaluating food/intake/dose must leave soil, TFWT, OBT, root plan, replay balances, and restart state unchanged. The adapter must not be imported by the frozen V3 default path.

## Candidate ranking after orchestration

1. `V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1` — **SELECT NEXT CONTROL-PLANE STAGE**.
2. Parameter/evidence prioritization after complete endpoint wiring — **DEFER until endpoint boundary is frozen**.
3. Real CTEAS-Atmos binding — **BLOCKED** until the producer-side surface-deposition/flux product and matching provenance are confirmed.
4. Leaf R5 dynamic stomata — **HOLD** at the R4 evidence checkpoint.
5. OBT physics redesign — **HOLD** pending matched evidence; current reduced solver remains the software baseline.
6. Full soil hydrology / plant-water dynamics — **HOLD**; explicit forcing remains the selected boundary.

## First exact-head gate

Review head `baf27ed33348e44ecb9ff04b8b633deecfbfa3c2` passed both required workflows:

- V3 Protected Integration Gate run `33032403498`: `SUCCESS`;
- V3 Remediation CI run `33032403623`: `SUCCESS`;
- portable suite: `1253 passed, 1 skipped, 57 deselected`;
- frozen/current-boundary suite: `321 passed`;
- sensitivity gate: `PASS_SOFTWARE_SCREENING`;
- root operator-split gate: `PASS_SELECTION`;
- soil-root-TFWT-OBT gate: `PASS_INTEGRATION`;
- replay orchestration gate: `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`.

No corrective review commit was required. The first gate therefore closes the review decision itself; the present follow-up is governance-only.

## Governance closure rule

This closure may update only ADR-035, the machine-readable governance record, the review report, and its governance test. It must not change `src/`, scripts, replay functional tests, workflow execution semantics, component equations, endpoint APIs, or runtime coupling.

Merge remains unauthorized until the governance-closure exact head independently passes both Protected and Remediation workflows. The eventual merge must use `expected_head_sha` and must be followed by parent/tree no-drift verification.

## Non-authorization

This review does not authorize:

- food/intake/dose adapter implementation;
- continuous or state-mutating harvest physics;
- parameter activation or calibration;
- any mass-, tissue-, moisture-, or area-basis numerical conversion;
- Leaf R5;
- OBT redesign;
- full hydrology or plant-water dynamics;
- root `q_w` inference from atmospheric meteorology;
- real CTEAS-Atmos binding;
- empirical validation or physical-accuracy claims.

The frozen V3 default, current replay orchestration, component solver equations, `PRESERVE_V3_POST_OBT_ROOT_GAIN`, and `ACTIVE_PARAMETERS=0` remain unchanged. After a successful closure gate and no-drift merge, only `V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1` becomes authorized, still as a control-plane/interface decision stage rather than implementation.
