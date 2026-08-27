# V4 replay-input system orchestration implementation R1

## Status

`PASS_IMPLEMENTATION_EXACT_HEAD_AWAITING_CLOSURE_GATE`

The authorized opt-in replay-input orchestration layer has passed its first exact-head software integration gate. A governance-only closure has now been written; merge remains blocked until the closure exact head passes Protected + Remediation CI again.

## Implemented boundary

The new module is:

`src/cteas_ufotri/v4_integration/replay_input_orchestration.py`

It adds:

- `ReplayDomainProvenance` for soil-external, biological, and leaf-input provenance carried outside the frozen component solvers;
- `V4ReplayIntervalInput` as one explicit UTC replay interval;
- `V4ReplayInputSystemOrchestrator` as a higher-level opt-in composition layer;
- `V4ReplaySystemBalance` for signed leaf + soil + root + OBT coupled conservation;
- `V4ReplaySystemStepResult` for auditable per-interval outputs.

The existing `V4SoilRootTFWTOBTIntegrator` is not modified.

## Selected runtime composition

For one interval `[t_n, t_n+1)`:

1. validate all input domains, common time, spatial support, area basis, and provenance;
2. map atmospheric total HTO surface deposition to the V4 L1 surface-deposition slot only;
3. compute the existing baseline signed leaf-exchange flux;
4. advance TFWT with leaf exchange;
5. advance OBT from the leaf-updated TFWT inventory;
6. plan root transfer from the original interval-start three-layer soil state;
7. apply that exact root plan once to the three-layer soil solver;
8. create endpoint TFWT as leaf-updated TFWT minus OBT transfer plus root gain.

The operator split remains `PRESERVE_V3_POST_OBT_ROOT_GAIN`.

## Fail-closed ownership

The base soil input is forbidden from pre-populating atmospheric deposition or root extraction slots. Atmospheric replay exclusively owns total surface deposition; root_v4 exclusively owns the root transfer plan.

Precipitation is retained as atmospheric metadata/co-forcing only. It does not generate infiltration, soil water input, inter-layer transport, or root `q_w`.

Root water uptake keeps `RootWaterFluxProvenanceV4`; it is not overwritten by atmospheric provenance. Soil-external, biological, and leaf-parameter provenance are explicit envelope fields.

R1 permits only identical spatial support. Silent spatial reconciliation or area conversion fails closed.

## Conservation

Leaf exchange is treated as a signed external plant/coupled-system transfer. This allows both air-to-leaf uptake and leaf-to-air re-emission to close the same ledger.

The implementation checks:

- soil/root water identity;
- soil/root HTO identity;
- plant storage closure;
- combined soil+plant HTO closure;
- underlying three-layer soil water and HTO closure.

## First exact-head evidence

Implementation head:

`dc309089d667fbd4ca0ab5ca4498b75b02a909d1`

Required workflows:

- V3 Remediation CI `33031238565`: `SUCCESS`;
- V3 Protected Integration Gate `33031238577`: `SUCCESS`.

Observed test/machine evidence:

```text
portable = 1245 passed, 1 skipped, 57 deselected
frozen/current-boundary = 313 passed
sensitivity = PASS_SOFTWARE_SCREENING
root operator split = PASS_SELECTION
soil-root-TFWT-OBT = PASS_INTEGRATION
replay orchestration = PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION
```

The replay machine harness explicitly returned all required invariants as true:

- `atmos_deposition_mapped_to_l1_surface`;
- `coupled_balance_closed`;
- `deterministic_repeat`;
- `plant_balance_closed`;
- `precipitation_not_inferred_as_soil_water`;
- `restart_equivalence`;
- `root_gain_post_obt`;
- `root_provenance_independent`;
- `same_interval_leaf_exchange_reaches_obt`;
- `zero_leaf_exchange_equivalence`.

The driven synthetic check reported a coupled residual of approximately `4.44e-15 Bq m^-2` and a plant residual of approximately `4.44e-16 Bq m^-2`. These are software/numerical closure checks only and are not empirical validation.

## Governance closure

No corrective implementation commit was needed. The closure changes only this report, ADR-034, the machine-readable governance record, and the governance test that asserts the recorded gate state.

The closure deliberately does **not** modify:

- `src/cteas_ufotri/v4_integration/replay_input_orchestration.py`;
- the frozen `V4SoilRootTFWTOBTIntegrator`;
- any V3 source;
- functional replay tests;
- the machine harness;
- workflow execution semantics;
- solver equations or operator order.

Therefore the runtime implementation proven by the first exact-head gate is unchanged. A second exact-head gate is still mandatory because governance metadata is part of the auditable branch head.

## Hard boundaries

```ini
V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1 = PASS_IMPLEMENTATION_EXACT_HEAD_AWAITING_CLOSURE_GATE
V3_DEFAULT_CHANGED = FALSE
EXISTING_V4_FOUR_MODULE_INTEGRATOR_CHANGED = FALSE
COMPONENT_SOLVER_EQUATIONS_CHANGED = FALSE
SELECTED_OPERATOR_SPLIT = PRESERVE_V3_POST_OBT_ROOT_GAIN
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
LEAF_R5 = FALSE
FOOD_INTAKE_DOSE_V4_INTEGRATION = FALSE
FULL_HYDROLOGY = FALSE
PLANT_WATER_DYNAMICS = FALSE
ROOT_Q_W_FROM_ATMOS = FALSE
REAL_CTEAS_ATMOS_BINDING = FALSE
EMPIRICAL_VALIDATION = FALSE
PHYSICAL_ACCURACY_CLAIM = FALSE
CLOSURE_EXACT_HEAD_GATE = PENDING
MERGE_AUTHORIZED = FALSE
```

After closure exact-head CI succeeds, the PR may be marked Ready and merged only with `expected_head_sha`, followed by parent/tree no-drift verification. The next stage after a verified merge remains `SYSTEM_LEVEL_POST_ORCHESTRATION_REVIEW`; this closure does not authorize immediate food/intake/dose integration or any other physics expansion.
