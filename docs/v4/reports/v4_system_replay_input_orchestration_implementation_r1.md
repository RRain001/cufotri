# V4 replay-input system orchestration implementation R1

## Status

`IMPLEMENTED_AWAITING_EXACT_HEAD_GATE`

The authorized opt-in replay-input orchestration layer has been implemented on an isolated branch. No production claim is made until exact-head protected/remediation CI and a second governance-closure gate pass.

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

## Required regression evidence

The implementation test suite includes:

- exact zero-leaf equivalence to the frozen four-module V4 integrator;
- same-interval leaf influence on OBT;
- post-OBT root gain;
- signed leaf re-emission conservation;
- total deposition -> L1 mapping;
- precipitation not becoming infiltration;
- explicit non-Atmos soil transport preservation;
- double-ownership rejection;
- interval/spatial/area fail-closed behavior;
- independent root provenance;
- deterministic repeat;
- restart equivalence.

A visible machine harness is added at:

`scripts/v4/run_replay_input_orchestration_r1.py`

The protected gate will execute it explicitly after the existing sensitivity, operator-split, and four-module integration gates.

## Hard boundaries

```ini
V4_SYSTEM_REPLAY_INPUT_ORCHESTRATION_IMPLEMENTATION_R1 = IMPLEMENTED_AWAITING_EXACT_HEAD_GATE
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
```

If the implementation exact head passes both workflows, only a pure governance closure is next. After closure exact-head CI and no-drift merge, the route returns to a system-level post-orchestration review rather than immediately expanding food/dose or other physics.
