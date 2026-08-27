# V4 system post-orchestration review R1

## Status

`PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_EXACT_HEAD_GATE`

This is a system-level control-plane review after the replay-input orchestration was merged and verified without tree drift. It does not change production source, solver equations, numerical coupling, parameters, calibration, or real CTEAS-Atmos binding.

## What changed since the previous system review

The prior post-integration review selected the replay-input adapter decision as the next stage and deferred food/intake/dose only until the upstream input boundary was decided.

That condition is now resolved:

- PR #29 froze the replay-input architecture;
- PR #30 implemented and merged the opt-in replay-input system orchestration;
- both implementation and governance-closure exact heads passed Protected + Remediation CI;
- post-merge parent/tree audit proved no drift;
- baseline leaf exchange, atmospheric surface deposition, three-layer soil/root, TFWT, and OBT now share one opt-in replay system seam.

The remaining missing connection in the stated north-star chain is therefore the endpoint transition from replay TFWT/OBT to food, intake, and dose.

## Endpoint API audit

The existing downstream modules already have compatible one-way public boundaries:

- `FoodTransferSolver` reads public `OBTState` and `TFWTState`, requires a shared harvest timestamp, multiplies their area-normalized inventories by an explicit harvest area, and creates separate food/harvest outputs;
- `FoodIntakeSolver` converts total food activity to Bq/kg using an explicit `food_product_mass_kg`, then applies an explicit annual consumption amount;
- `DoseSolver` converts annual intake to committed dose with an explicit dose coefficient.

None of these calls currently mutates the replay state. That makes an endpoint adapter architecturally possible without changing upstream dynamics.

## Critical boundary discovered

The existing food transfer is a readout, not a state-depleting crop-harvest dynamics model. It reports transferred and remaining inventory but does not write the remaining plant inventory back into TFWT/OBT state.

Therefore the next V4 decision must freeze R1 as a **terminal diagnostic harvest readout**. It must not automatically harvest every replay interval, and it must not allow the same trajectory to continue after harvest while pretending that the plant source inventory has been depleted.

Repeated harvest, regrowth, crop removal, or post-harvest continuation would require a separate future state-mutation/physics decision.

## Basis and provenance audit

The replay endpoint inventory basis is `soil_surface_area`. Existing food transfer uses an explicit `harvest_area_m2` to convert Bq/m2 into total Bq but does not define a general area conversion layer.

V3.1 already provides the correct governance rule for food concentration basis:

- mass basis is explicit (`fresh_mass`, `dry_mass`, `water_mass`, or `hydrogen_mass`);
- tissue/product scope is explicit;
- area basis is explicit;
- direct comparison requires identical mass/tissue/area basis;
- cross-basis conversion requires separate evidence metadata;
- V3.1 performs no numerical cross-basis conversion.

The next adapter decision must reuse this contract rather than inventing hidden moisture/yield/tissue conversion.

## Sensitivity interpretation

The synthetic screening reported local dose elasticity of approximately `0.8443` for the provisional TFWT harvest fraction and `0.1557` for the OBT harvest fraction in its mixed endpoint profile.

This supports freezing the endpoint definition before implementation. It does **not** validate either fraction, establish physical uncertainty, or authorize calibration. External annual consumption, food mass, harvest area, and dose coefficient remain scenario/exposure scaling inputs rather than environmental-physics priorities.

## Priority decision

Selected next stage:

`V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1`

Scope:

`CONTROL_PLANE_AND_INTERFACE_DECISION_ONLY`

Implementation remains unauthorized until that decision is independently gated and merged.

The next decision must define at minimum:

- explicit terminal harvest trigger and endpoint timestamp semantics;
- OBT-only versus OBT+TFWT endpoint mode;
- explicit mixed TFWT harvest fraction when applicable;
- `soil_surface_area` source ownership and explicit harvest-area handling;
- V3.1 mass/tissue/area-basis contract at the food boundary;
- no numerical cross-basis conversion;
- independent provenance for harvest, product mass/consumption, and dose coefficient;
- fail-closed product/consumer/age/radionuclide/pathway/period identity;
- no upstream state mutation or feedback;
- no continuation of the same replay trajectory after terminal diagnostic harvest;
- composition of existing endpoint solvers rather than equation rewrites.

## What remains HOLD

- Leaf R5 dynamic stomata remains at the R4 evidence checkpoint.
- OBT redesign remains held pending matched evidence.
- full hydrology and plant-water dynamics remain held.
- root `q_w` remains explicit and independently provenanced.
- real CTEAS-Atmos binding remains blocked until the producer-side surface-deposition/flux product is confirmed.
- parameter activation and calibration remain false.

## Current hard state

```ini
V4_SYSTEM_POST_ORCHESTRATION_REVIEW_R1 = PASS_SYSTEM_POST_ORCHESTRATION_REVIEW_AWAITING_EXACT_HEAD_GATE
MAIN_BASE = a03da884eb60b82658c07e0ca57db7058480260f
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
NEXT_STAGE = V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_R1
```

This review requires an exact-head Protected + Remediation gate, followed by a governance-only closure, a second exact-head gate, expected-head merge, and post-merge parent/tree no-drift verification before the next decision stage becomes authorized.
