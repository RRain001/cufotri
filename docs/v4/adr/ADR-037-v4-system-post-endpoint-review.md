# ADR-037: V4 system post-endpoint review R1

Status: `PASS_REVIEW_EXACT_HEAD_AWAITING_CLOSURE_GATE`

## Context

PR #33 completed the opt-in terminal diagnostic `food -> intake -> dose` adapter and merged without tree drift. The current V4 software path can therefore connect replay atmospheric forcing through baseline leaf exchange, three-layer soil/root, TFWT, reduced OBT, terminal food transfer, intake and dose. This closes the missing software-wiring gap; it does not make the chain physically validated or production-ready.

The review must now select the next scientific/evidence blocker without reopening frozen work merely because the full software chain exists.

## Decision

After the post-endpoint review, the next selected stage is:

`V4_OBT_FORMATION_EVIDENCE_READINESS_R1`

Its scope is `CONTROL_PLANE_AND_EVIDENCE_READINESS_ONLY`.

This decision does **not** authorize a new OBT solver, precursor or multi-pool runtime state, parameter values, calibration, parameter activation, or a change to the V3/V4 runnable defaults.

## Why OBT is next

The earlier independent physics prioritization ranked OBT daylight formation, nighttime formation and photosynthetic forcing as the three highest `CRITICAL` redesign records. P7.8B-2 subsequently selected the V4 direction as the smallest precursor plus exchangeable/non-exchangeable OBT architecture while explicitly retaining the reduced first-order equation as the runnable baseline until evidence gates are satisfied.

Since then:

- the layered root architecture has been implemented and integrated on the opt-in V4 path;
- the root operator split has been selected and regression-tested;
- food environmental transfer was explicitly retained as the harvest-event boundary;
- the terminal food/intake/dose diagnostic adapter is now merged;
- Leaf R5 remains blocked at the unexecuted R4 prospective-experiment feasibility checkpoint;
- real CTEAS-Atmos binding remains an external prerequisite because the current Atmos `main` still does not establish the required true surface HTO deposition-flux product; its frozen status is `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`;
- full hydrology and plant-water dynamics remain unauthorized.

Accordingly, global parameter activation is still premature. Activating or calibrating the reduced OBT `kf/kr` path before deciding whether matched evidence can discriminate the selected OBT architecture could convert a known structural uncertainty into apparently precise fitted constants.

## Required questions for the next stage

`V4_OBT_FORMATION_EVIDENCE_READINESS_R1` must answer, before any implementation:

1. What biological meanings are assigned to the precursor/activity pool and the exchangeable/non-exchangeable OBT pools?
2. Which proposed states are directly observable, derivable under an explicit contract, or latent?
3. Is there one internally aligned dataset or feasible acquisition plan containing time-resolved TFWT and OBT together with daylight/light state, photosynthetic activity or PAR, temperature, crop/developmental stage, plant mass/tissue/area basis, timestamps and independent biological replicates?
4. Can the reduced first-order baseline and selected multi-pool candidate be compared without mixing incompatible crops, tissues, mass bases, time supports or experiments?
5. What minimum identifiability and holdout conditions must be met before equations or parameter values may be admitted?
6. If the evidence is unavailable, does the selected redesign remain on HOLD while the reduced model stays explicitly labeled as a limited baseline?

Evidence must be classified as `AVAILABLE`, `ACQUIRABLE_WITH_PREREGISTRATION`, or `UNAVAILABLE/INSUFFICIENT`. Literature ranges or synthetic fixtures cannot substitute for matched time-resolved biological evidence.

## Other blocker dispositions

- Root `q_w` production forcing/evidence remains unresolved, but the structural root implementation blocker is closed. It is deferred behind the OBT evidence-readiness decision, not declared solved.
- Post-end-to-end parameter evidence/activation review is deferred. `ACTIVE_PARAMETERS` remains zero.
- Leaf R5 remains at the R4 feasibility/evidence checkpoint; the prospective experiment has not been executed.
- Real CTEAS-Atmos binding remains fail-closed and is not modified by this repository stage.
- Full soil hydrology, plant-water dynamics and TFWT dynamic-water storage remain HOLD.
- The current harvest-event food boundary remains the selected environmental food representation; state-mutating/repeated harvest remains outside R1.

## Stale branch disposition

The pre-existing branch `codex/v4-3-obt-formation-readiness` points only to the old `d4bb2def...` roadmap-reset-era baseline and contains no OBT readiness implementation. It is historical/stale and is not evidence or authority for this decision. A future OBT evidence-readiness stage must start from the then-current certified `main` on a fresh isolated branch.

## First exact-head certification

The first clean review head is `c571a1e6bdf856f76a326f68cb10c304973128c0`.

```text
Protected 33037462292 = SUCCESS
Remediation 33037462279 = SUCCESS
portable = 1284 passed, 1 skipped, 57 deselected
frozen/current-boundary = 346 passed
sensitivity = PASS_SOFTWARE_SCREENING
root operator split = PASS_SELECTION
soil-root-TFWT-OBT = PASS_INTEGRATION
replay orchestration = PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION
food-intake-dose endpoint = PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION
```

The GitHub pull-request workflow checked the synthetic merge ref `eac67ac3ec27d64b32e0a4af54f4fa9533ed88b9`, which merges the exact review head into base `48bb658c...`. This checkout identity is recorded separately from the branch-head identity.

The superseded head `3e788e8f0919e7dc42ed068269c6bcc750575c87` is not certification evidence. Its Protected run `33037232966` failed only because this ADR omitted the exact machine-searchable status token `BLOCKED_SURFACE_FLUX_PRODUCT_UNCONFIRMED`; Remediation `33037233021` succeeded and portable recorded `1283 passed, 1 failed, 1 skipped, 57 deselected`. The correction changed no runtime, model, solver, coupling or roadmap decision.

## Governance closure

This closure is governance-only. Relative to certified review head `c571a1e6...`, it may change only:

- `docs/v4/adr/ADR-037-v4-system-post-endpoint-review.md`;
- `docs/v4/governance/v4_system_post_endpoint_review_r1.yaml`;
- `docs/v4/reports/v4_system_post_endpoint_review_r1.md`;
- `tests/v4/test_v4_system_post_endpoint_review_r1.py`.

It changes no `src/`, workflow, script, runtime semantics, solver equation, parameter, calibration state or scientific decision. The closure exact head must pass Protected + Remediation again before Ready/merge.

## Hard invariants

```ini
V4_SYSTEM_POST_ENDPOINT_REVIEW_R1 = PASS_REVIEW_EXACT_HEAD_AWAITING_CLOSURE_GATE
V3_DEFAULT_CHANGED = FALSE
V4_RUNTIME_CHANGED = FALSE
SOLVER_EQUATIONS_CHANGED = FALSE
NUMERICAL_COUPLING_CHANGED = FALSE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
LEAF_R5_AUTHORIZED = FALSE
OBT_MULTI_POOL_IMPLEMENTATION_AUTHORIZED = FALSE
OBT_PARAMETER_ACTIVATION_AUTHORIZED = FALSE
ROOT_Q_W_PRODUCTION_INPUT_RESOLVED = FALSE
FULL_HYDROLOGY_AUTHORIZED = FALSE
PLANT_WATER_DYNAMICS_AUTHORIZED = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
NEXT_STAGE = V4_OBT_FORMATION_EVIDENCE_READINESS_R1
```

The next stage becomes effective only after this governance closure passes exact-head Protected + Remediation, the PR is merged with `expected_head_sha`, and parent/tree no-drift verification succeeds.