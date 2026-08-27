# V4 system post-orchestration review R1

## Status

`PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_CLOSURE_GATE`

The system-level review after replay-input orchestration has passed its first exact-head Protected + Remediation gate. A governance-only closure is now recorded; merge remains blocked until the closure exact head passes both workflows again.

## Review conclusion

The previous reason for deferring downstream endpoint wiring is resolved. PR #30 merged the opt-in replay-input orchestration and passed both its implementation and closure gates without tree drift. Atmospheric replay, baseline leaf exchange, three-layer soil/root, TFWT, and OBT are therefore connected on the current opt-in V4 path.

The selected next stage is:

`V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1`

Its scope remains `CONTROL_PLANE_AND_INTERFACE_DECISION_ONLY`. No endpoint adapter implementation is authorized by this review.

## Why this is next

The current food/intake/dose modules already form one-way readout APIs compatible with replay endpoint TFWT/OBT types. Connecting them is the smallest remaining step toward the stated Atmos-to-dose chain that does not require new upstream physics.

The synthetic sensitivity screen shows that endpoint definition can materially alter computed dose, especially the provisional mixed TFWT harvest fraction. That is used only to justify freezing endpoint semantics first. It is not parameter evidence, physical uncertainty, calibration evidence, or an activation decision.

## Terminal diagnostic harvest boundary

The existing food solver does not mutate source TFWT/OBT state after calculating transferred and remaining inventory. R1 must therefore use a **terminal diagnostic harvest readout**:

- harvest only on explicit caller request;
- harvest source timestamp must equal the replay endpoint timestamp;
- no automatic per-step harvest;
- no continuation of the same replay trajectory after harvest while claiming source depletion;
- repeated harvest, regrowth, crop removal, or state-mutating harvest require a separate future decision.

This avoids introducing a hidden conservation/state-semantic gap merely to make the chain appear end-to-end.

## Basis, area, identity, and provenance boundary

The next decision must freeze:

- source inventory area basis `soil_surface_area`;
- explicit `harvest_area_m2` only, with no hidden leaf/plant/field area conversion;
- V3.1 `MassBasisContract` at the product boundary;
- direct comparison only for identical mass/tissue/area basis;
- no numerical fresh/dry/water/hydrogen cross-basis conversion;
- explicit `OBT_ONLY` versus `OBT_PLUS_TFWT` mode;
- explicit, independently provenanced TFWT harvest fraction for mixed mode;
- independent provenance for harvest, food-product mass/consumption, and dose coefficient;
- fail-closed food-product, consumer, age-group, radionuclide, pathway, and exposure-period identity;
- no upstream state mutation or feedback;
- composition of existing endpoint solvers rather than equation rewrites.

## First exact-head evidence

Review head:

`baf27ed33348e44ecb9ff04b8b633deecfbfa3c2`

Evidence:

```text
Protected Gate 33032403498 = SUCCESS
Remediation 33032403623 = SUCCESS
portable = 1253 passed, 1 skipped, 57 deselected
frozen/current-boundary = 321 passed
sensitivity = PASS_SOFTWARE_SCREENING
root operator split = PASS_SELECTION
soil-root-TFWT-OBT = PASS_INTEGRATION
replay orchestration = PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION
```

No corrective review commit was required. Existing replay invariants remained green, including zero-leaf equivalence, same-interval leaf-to-OBT semantics, post-OBT root gain, deposition-to-L1 ownership, independent root provenance, no precipitation-to-infiltration inference, restart equivalence, deterministic repeat, and coupled conservation.

## Governance closure

The closure changes only:

- ADR-035;
- the post-orchestration governance YAML;
- this review report;
- the review governance test.

It does not modify production source, workflow execution semantics, scripts, endpoint APIs, replay functional tests, solver equations, parameters, or runtime coupling.

A second exact-head Protected + Remediation gate remains mandatory before Ready/merge. The merge must use `expected_head_sha` and be followed by parent/tree no-drift verification.

## What remains HOLD

- Leaf R5 dynamic stomata: R4 evidence checkpoint.
- OBT physics redesign: matched evidence required.
- full hydrology and plant-water dynamics: HOLD.
- root `q_w`: explicit, independently provenanced; not inferred from Atmos.
- real CTEAS-Atmos binding: blocked until producer-side surface-deposition/flux product is confirmed.
- parameter activation: false.
- calibration: false.

## Current hard state

```ini
V4_SYSTEM_POST_ORCHESTRATION_REVIEW_R1 = PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_CLOSURE_GATE
BASE_MAIN = a03da884eb60b82658c07e0ca57db7058480260f
FIRST_EXACT_HEAD = baf27ed33348e44ecb9ff04b8b633deecfbfa3c2
FIRST_PROTECTED_GATE = SUCCESS
FIRST_REMEDIATION = SUCCESS
V3_DEFAULT_CHANGED = FALSE
REPLAY_ORCHESTRATION_CHANGED = FALSE
COMPONENT_SOLVER_EQUATIONS_CHANGED = FALSE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5 = FALSE
OBT_REDESIGN = FALSE
FULL_HYDROLOGY = FALSE
PLANT_WATER_DYNAMICS = FALSE
ROOT_Q_W_FROM_ATMOS = FALSE
FOOD_INTAKE_DOSE_V4_IMPLEMENTATION = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
CLOSURE_EXACT_HEAD_GATE = PENDING
MERGE_AUTHORIZED = FALSE
NEXT_AFTER_VERIFIED_MERGE = V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1
```
