# V4 development baseline RC1 report

## Result

`V4_DEVELOPMENT_BASELINE_RC1` is the final mandatory internal V4 development stage.

The preceding completeness review found no remaining mandatory internal software or selected-baseline physics blocker. RC1 therefore performs regression and freeze only; it does not reopen physics selection.

## Entry anchor

- base main: `a9ae81fe1931289c44a860df6eafc6ab2ee16b55`
- base tree: `4b483f427b3aaef0f8bd53f3859815949ce1510e`
- preceding stage: `V4_DEVELOPMENT_COMPLETENESS_REVIEW_R1`
- preceding verdict: `PASS_NO_MANDATORY_INTERNAL_BLOCKERS`
- mandatory internal blockers: `0`
- preceding merge drift: `FALSE`

## Frozen internal baseline

The RC freezes the selected software composition already proven by prior stages:

- controlled atmosphere input: synthetic/replay only;
- three-layer soil: 0–5 / 5–15 / 15–30 cm;
- signed soil transport, conservation ledgers and restart;
- root `J=qC` transfer identity;
- UFOTRI Eq.39 controlled total root-water uptake;
- UFOTRI 20/40/40 layer distribution;
- baseline leaf-resistance exchange;
- TFWT;
- reduced UFOTRI OBT `k_f/k_r` baseline;
- `PRESERVE_V3_POST_OBT_ROOT_GAIN`;
- `KEEP_HARVEST_EVENT`;
- food/intake/dose endpoint.

## RC1 machine gate

The new RC1 runner does not implement physics. It invokes the existing certified runners and requires their established PASS states:

- controlled E2E → `PASS_CONTROLLED_UFOTRI_END_TO_END_NUMERICAL_INTEGRATION`;
- sensitivity → `PASS_SOFTWARE_SCREENING`;
- root operator split → `PASS_SELECTION`;
- soil-root-TFWT-OBT → `PASS_INTEGRATION`;
- replay orchestration → `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`;
- food/intake/dose → `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.

The aggregate target is:

`PASS_V4_DEVELOPMENT_BASELINE_RC1_MACHINE_COMPOSITION`.

The exact-head Protected Integration Gate must also pass the full portable suite, frozen/current-boundary suite and existing machine gates. Remediation CI must independently remain green.

## Completion state if exact-head CI and no-drift merge pass

```ini
V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE=TRUE
MANDATORY_INTERNAL_STAGE_COUNT_REMAINING=0
SELECTED_INTERNAL_BASELINE_FROZEN=TRUE
NEW_PHYSICS_PREAUTHORIZED=FALSE
```

The following remain explicitly false:

```ini
FULL_MODEL_PRODUCTION_READY=FALSE
PRODUCTION_INPUT_PACKET_READY=FALSE
REAL_CTEAS_ATMOS_BINDING=FALSE
EMPIRICAL_VALIDATION=FALSE
PHYSICAL_ACCURACY_CLAIM=FALSE
CALIBRATION_STARTED=FALSE
ACTIVE_PARAMETERS=0
LEAF_R5=FALSE
FULL_RICHARDS_DARCY_HYDROLOGY=FALSE
MULTI_POOL_OBT=FALSE
UFOTRI_SHORT_TERM_3H_DELAY=FALSE
PENMAN_EQ38_AERODYNAMIC_TERM=FALSE
V3_DEFAULT_PATH_CHANGED=FALSE
```

## Release-candidate identity

After a verified no-drift merge, the lightweight tag `v4-development-baseline-rc1` is authorized to point to the RC1 merge commit. The tag denotes the internal software-development baseline only and must not be interpreted as a production or physically validated release.
