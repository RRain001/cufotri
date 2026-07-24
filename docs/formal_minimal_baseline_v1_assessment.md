# Formal minimal baseline v1 assessment

Assessment date: 2026-07-24

## Verdict

`ACCEPT_WITH_REMAINING_LIMITATIONS`

The repository supports a freezeable and reproducible
`FORMAL_MINIMAL_BASELINE_V1` for the minimal HTO atmosphere–surface
soil–plant TFWT/OBT coupled engineering model. Restoring `complete` is
recommended only with this exact bounded scope.

It is not complete UFOTRI, dynamic whole-domain atmosphere–surface
conservation, food chain, dose, HT oxidation, multi-layer soil, or regulatory
site validation.

## Audit resolution A-01 to A-12

- A-01, A-03, A-04, A-05, A-06, A-08, A-10, and A-11: `RESOLVED`.
- A-02: `RESOLVED` for tested dry project-level source depletion; wet washout
  remains explicitly unimplemented.
- A-07, A-09, and A-12: `DOCUMENTED_LIMITATION`.

The conservation domain is soil HTO + plant TFWT + plant OBT per square metre.
Atmospheric diagnostics are a steady Gaussian source/sink ledger. They do not
define air storage or advective outflow and therefore are not a dynamic
whole-domain balance.

## Frozen contracts

- Rain HTO: only infiltration enters soil; runoff HTO is a boundary bypass.
- Calm wind: default minimum effective wind is 0.5 m s-1 and substitutions are recorded.
- Dry depletion: segment-exponential `PROJECT_SIMPLIFICATION`; source loss and
  deposition match in that discrete ledger.
- Wet scavenging: interface present, disabled, `EXPLICITLY_NOT_IMPLEMENTED`.
- Feedback: one rectangle-derived area and a 3600 s physical delay.
- Eq. (40): `radiation_term_only`.
- Root fraction: 1.0 for the sole modelled 0–5 cm layer; not the manual
  multi-layer top-layer fraction.
- Advanced REEM/DIFF/ZT: `PROVISIONAL`.

## Recomputed acceptance

`scripts/verify_acceptance.py --recompute` used a temporary output directory
and did not overwrite saved artifacts. It recorded Git/worktree state,
configuration and input SHA256, input path, Python/dependency versions, model
modes, internal step, and UTC start/end times.

| Case | Steps | Maximum surface-box relative residual |
|---|---:|---:|
| synthetic_basic_48h | 288 | 4.320656e-16 |
| era5_basic_48h | 288 | 4.040362e-16 |
| advanced_reemission_24h | 144 | 2.478100e-16 |
| runoff_rain_hto_1h | 6 | 1.819981e-16 |
| calm_wind_1h | 6 | 2.092598e-16 |

The rainfall audit counterexample routes 0.6 Bq m-2 into soil and records
5.4 Bq m-2 as runoff bypass for the 60 s step.

## Tests and timestep check

- Test suite: 61 passed, 0 failed.
- Known warning: one NumPy/NetCDF binary-compatibility warning remains.
- 600/300 s final differences: soil HTO 0.02360%, TFWT 0.13859%, OBT
  0.12093%, integrated total re-emission 0.04974%.

## Final fields

```text
FORMAL_BASELINE_VERDICT = ACCEPT_WITH_REMAINING_LIMITATIONS
SURFACE_BOX_CLOSURE_STATUS = PASS
ATMOSPHERIC_BUDGET_STATUS = DOCUMENTED_NOT_DYNAMIC_INVENTORY
RUNOFF_RAIN_HTO_STATUS = PASS
CALM_WIND_STATUS = PASS
DRY_DEPLETION_STATUS = PASS_PROJECT_SIMPLIFICATION
WET_SCAVENGING_STATUS = EXPLICITLY_NOT_IMPLEMENTED
FEEDBACK_DELAY_STATUS = FROZEN_3600S_PASS
FEEDBACK_AREA_STATUS = PASS
ROOT_FRACTION_STATUS = FROZEN_SINGLE_LAYER_1_0
EQ40_SHADING_STATUS = FROZEN_RADIATION_TERM_ONLY
ACCEPTANCE_RECOMPUTE_STATUS = PASS
TEST_STATUS = PASS_61
TIMESTEP_STATUS = PASS
FORMAL_COMPLETE_RECOMMENDATION = RESTORE_COMPLETE_FOR_BOUNDED_FORMAL_MINIMAL_BASELINE_V1_ONLY
```
