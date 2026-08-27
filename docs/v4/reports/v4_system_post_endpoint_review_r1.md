# V4 system post-endpoint review R1

## Status

`READY_FOR_FIRST_EXACT_HEAD_CI`

This is a system-level control-plane review only. PR #33 has closed the missing terminal diagnostic `food -> intake -> dose` software seam; the purpose of this review is to choose the next evidence/physics blocker without changing runtime behavior.

## Verified entry state

PR #33 merged at `48bb658c986d4ca1f355991e4e298a16863fec3b` with parent1 `f13a36d2...`, parent2 `269dd5f2...`, and tree `bb7fe7a7...`. The PR closure head and merge commit have identical trees and the head-to-merge comparison contains no changed files. `MERGE_TREE_DRIFT=FALSE`.

The closure exact-head gate recorded:

```text
Protected 33036005017 = SUCCESS
Remediation 33036005021 = SUCCESS
portable = 1275 passed, 1 skipped, 57 deselected
frozen/current-boundary = 337 passed
endpoint = PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION
```

The opt-in software chain now reaches dose from normalized replay forcing. That is software integration evidence only; `ACTIVE_PARAMETERS=0`, empirical validation is false, and real CTEAS-Atmos binding remains false.

## External Atmos prerequisite re-check

The current `RRain001/CTEAS-Atmos` `main` is still `341d9d6b3b45b6e2416e09aec0b381adf137fd3e`, exactly the snapshot used by the frozen exchange-contract audit. That audit proved receptor concentration compatibility but did not prove a true surface deposition-flux product in `Bq m^-2 s^-1`; Stage18 ledger Bq amounts cannot be relabeled as flux.

Therefore:

```ini
REAL_CTEAS_ATMOS_BINDING = BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED
ATMOS_ACTION_IN_THIS_STAGE = NONE_READ_ONLY_RECHECK_ONLY
```

The unfinished Atmos module remains an external prerequisite and is intentionally skipped here rather than becoming a reason to modify the separate project from UFOTRI.

## What changed since the earlier system priority review

Three major software/architecture blockers have been closed or narrowed:

1. Layered root uptake is no longer merely a candidate. A three-layer root core exists, the operator split has been selected, and soil/root/TFWT/OBT integration is merged on the opt-in V4 path.
2. Food environmental transfer was explicitly retained as the harvest-event representation for this roadmap; the terminal diagnostic adapter now composes food, intake and dose without upstream mutation.
3. Replay orchestration and terminal endpoint wiring are both merged, so missing software connectivity is no longer the dominant internal blocker.

Important scientific gaps remain. Root `q_w` is still an explicit external production input rather than an activated parameterization; the UFOTRI 20/40/40 fractions, reference layer rates and short-term 3 h delay remain non-active evidence. Leaf R5 remains at the unexecuted R4 experiment-feasibility checkpoint.

## Why OBT evidence readiness is selected

The independent P7.8A ranking placed these records first, second and third and marked all three `CRITICAL`:

- `R1_OBT_DAYLIGHT_FORMATION_STATE`;
- `R2_OBT_NIGHTTIME_FORMATION_STATE`;
- `R3_OBT_PHOTOSYNTHETIC_FORCING_STATE`.

P7.8B-2 then selected the future V4 OBT direction as a precursor/activity pool plus exchangeable and non-exchangeable OBT pools, while keeping the reduced

`dB/dt = kf*T - kr*B`

model as the runnable baseline until evidence gates are passed.

The later synthetic system screen reinforces the structural question without resolving it: OBT photosynthetic-activity, temperature-response and growth-stage extension fields are exact structural zeros in the current call graph. That is not proof those processes matter physically, but it confirms the reduced implementation cannot currently express the selected mechanisms.

Root was the next `CRITICAL` structural item in the old ranking and its architecture/integration has now been addressed. Food was subsequently selected to stay event-based. Leaf phenology was only `MEDIUM` in that ranking and remains independently evidence-blocked. This leaves OBT as the highest-priority unresolved internal physics question that can be advanced without waiting for Atmos.

## Why parameter activation is not next

The full software chain being runnable does not justify turning on a production parameter database. In particular, calibrating current reduced OBT `kf/kr` before determining whether matched data can distinguish the selected OBT formation architecture risks letting effective constants absorb unresolved daylight/activity/temperature biology.

The next stage must therefore decide evidence readiness before equation implementation or value selection. A later whole-chain parameter-evidence review remains necessary, but it is deferred until this critical structural evidence gate is resolved.

## Selected next stage

`V4_OBT_FORMATION_EVIDENCE_READINESS_R1`

Scope: `CONTROL_PLANE_AND_EVIDENCE_READINESS_ONLY`.

It must determine whether one internally compatible evidence packet already exists or can realistically be acquired. At minimum it must review time-resolved TFWT and OBT together with daylight/light state, photosynthetic activity or PAR, temperature, crop/stage, plant mass/tissue/area basis, timestamps/time support, provenance and independent biological replication.

The stage must freeze biological meanings for the proposed precursor, exchangeable OBT and non-exchangeable OBT states; classify proposed states as directly observed, explicitly derived or latent; define identifiability and holdout requirements; and compare evidence compatibility for the reduced baseline versus selected multi-pool candidate.

Allowed evidence dispositions are:

- `AVAILABLE`;
- `ACQUIRABLE_WITH_PREREGISTRATION`;
- `UNAVAILABLE_OR_INSUFFICIENT`.

If evidence is insufficient, the multi-pool redesign stays HOLD. The stage may not fill the gap with literature ranges, cross-dataset composition, synthetic fixtures or guessed parameter values.

## Candidate disposition after review

| Candidate | Disposition |
| --- | --- |
| OBT formation evidence readiness | `SELECT_NEXT_CONTROL_PLANE_STAGE` |
| Root `q_w` production-input evidence | `DEFER_ONE_STAGE_STRUCTURE_READY_INPUT_UNRESOLVED` |
| Whole-chain parameter evidence/activation | `DEFER_UNTIL_CRITICAL_OBT_EVIDENCE_DECISION` |
| Leaf R5 dynamic stomata | `HOLD_R4_FEASIBILITY_NOT_EXECUTED` |
| Real CTEAS-Atmos binding | `EXTERNAL_BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED` |
| Full hydrology / plant-water dynamics | `HOLD` |

## Stale branch note

`codex/v4-3-obt-formation-readiness` is not an unfinished OBT implementation worth resuming. It still points to `d4bb2def...`, the early roadmap-reset-era baseline, and contains no OBT readiness work. It is treated as a stale empty anchor. Any next OBT stage must start fresh from the then-current certified `main`.

## Hard state

```ini
V4_SYSTEM_POST_ENDPOINT_REVIEW_R1 = READY_FOR_FIRST_EXACT_HEAD_CI
BASE_MAIN = 48bb658c986d4ca1f355991e4e298a16863fec3b
CONTROL_PLANE_ONLY = TRUE
V3_DEFAULT_CHANGED = FALSE
V4_RUNTIME_CHANGED = FALSE
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5 = FALSE
OBT_MULTI_POOL_IMPLEMENTATION = FALSE
OBT_PARAMETER_ACTIVATION = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY = FALSE
PLANT_WATER_DYNAMICS = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
NEXT_STAGE = V4_OBT_FORMATION_EVIDENCE_READINESS_R1
```

Exact-head Protected + Remediation must pass before a governance-only closure is written. The closure head must then pass both workflows again before Ready/`expected_head_sha` merge and parent/tree no-drift audit.