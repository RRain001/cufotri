# Independent review of the H2/H3 discriminability design

```text
DISCRIMINABILITY_REVIEW_TARGET_HEAD =
0a9f3e836b7733c02595243a39327378dc5fa83b

INDEPENDENT_REVIEW_BRANCH =
codex/v3-slow-mechanism-discriminability-independent-review

INDEPENDENT_REVIEW_WORKTREE =
CETAS_ufotri_discriminability_independent_review

DISCRIMINABILITY_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_D3_DESIGN

CURRENT_SB1_SB4_DATA =
CONFIRMED_INSUFFICIENT

D3_STATUS =
CONFIRMED_DISCRIMINATING_DESIGN_SUPPORTED

MINIMUM_D3_EXPERIMENT =
24H_EXPOSURE_PLUS_120H_FOLLOWUP

MINIMUM_TOTAL_ELAPSED_DURATION_H = 144
MINIMUM_SAMPLING = 0P2_48_120_H
EXTENDED_120_DAY_FOLLOWUP = OPTIONAL

PARAMETER_REFIT_COUNT = 0
LATENT_POOL_USED_FOR_CLASSIFICATION = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
TRUSTED_REGISTRY_CHANGE_COUNT = 0

MERGE_RECOMMENDATION =
READY_TO_MERGE_DISCRIMINABILITY_RESEARCH

FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Scope and method

The review did not trust the tracked summary tables as decision evidence.
It checked Git chronology, ran the four supported stages (`base`,
`robustness`, `sensitivity`, and `reports`) in a detached local clone of the
target commit, retained the generated files under the ignored
`validation/external_local/discriminability_independent_review/` directory,
and independently recalculated the pointwise distances, lognormal
classification, greedy minimum sampling set, conservation checks and attack
outcomes.

The review branch adds only this report and independent tests. It does not
modify the design runner, protocol, tracked result snapshots, H2/H3 parameter
files, `src/`, root `configs/`, the trusted registry or a physics gate.

## Frozen chronology

| role | commit | chronology finding |
|---|---|---|
| initial protocol | `8ce4777b6ffc49a3dc61814fe19942e5cf9a6348` | Candidate grid, CV levels, seed, thresholds, H2/H3 parameters, no-refit rule and observable contract were committed before execution. |
| wind criterion amendment | `067710877e7b3191cabbe095cd432961d10e2148` | Added required wind robustness before the runner and results existed. |
| runtime boundary amendment | `8d9b993a49bb14fdd51aa6b61f08a016c3d284b3` | Added time origin, timezone, water storage and biomass boundary before the runner and results existed. |
| design runner | `193fae78a77409a2c943dcd1e7367928aeb92d07` | Implemented D0-D5 after the protocol boundary was frozen. |
| base simulation | `1e9c5e02abf78969daa979fafdebf71c9ab02a89` | First tracked D0-D5 outputs. |
| Monte Carlo and sampling | `ef91b76f3b3bc8917fa6b401d7e075e38c1e432d` | Added the frozen-seed classification and minimum sampling outputs. |
| robustness | `406d663d9e69393510d089c29cbfcab79fb6ffa5` | Added one-factor-at-a-time robustness results. |
| sensitivity | `ff3c0890360f58e25f06fbd7788acd90b6a29c5f` | Added bounded local sensitivity diagnostics. |
| report finalization | `b21dafae8d7a5fb7b5c832dbfd9687b9d522b968` | Added the experiment specification and reports. |
| report hardening | `db7ae1f5c781c735bdac4f0dec3a1f78c66615af` | Added acceptance checks without changing the frozen numerical contract. |
| duration clarification | `70f1f275814a4c9c493049ceab813811cd3d558f` | Separated the 144 h minimum experiment from optional 120 d diagnostics. |
| generator hardening | `0a9f3e836b7733c02595243a39327378dc5fa83b` | Prevented report regeneration from restoring the obsolete 120 d minimum wording. |

```text
DISCRIMINABILITY_PROTOCOL_CHRONOLOGY = PASS_FROZEN_BEFORE_D0_D5
SAMPLING_GRID_FREEZE_REVIEW = PASS
MONTE_CARLO_FREEZE_REVIEW = PASS
PARAMETER_SOURCE_REVIEW = PASS_SB1_COMMIT_4B79F627_ZERO_REFIT
FORMAL_DIFF_STATUS = PASS_NO_SRC_OR_ROOT_CONFIG_DIFF
```

The duration clarification occurred after the synthetic outputs, but it
changed only the experimental follow-up interpretation. It did not change a
design forcing, candidate sampling time, noise level, seed, threshold,
parameter, result CSV or model-selection conclusion.

## D0-D5 independent reconstruction

| design | exposure reconstruction | maximum separation (dex) | strong points | review outcome |
|---|---|---:|---:|---|
| D0 | 1 h pulse at 52700 Bq/mL, then strict-zero background | 0.241625 | 0 | no strong separation |
| D1 | 1 h pulse, 24 h washout, second 1 h pulse | 0.242273 | 0 | no strong separation |
| D2 | 1 h pulse, 72 h washout, second 1 h pulse | 0.381611 | 6 | base criteria pass; robustness not evaluated |
| D3 | 24 h step at 5270 Bq/mL, then strict-zero background | 0.464469 | 7 | supported and robust |
| D4 | 72 h step at 5270 Bq/mL, then strict-zero background | 0.674758 | 7 | fails at wind 0.2 m/s |
| D5 | 1 h pulse, 72 h washout, 24 h re-exposure | 0.682925 | 7 | minimum set and robustness fail |

All six schedules, washout intervals, final-exposure reference times,
simulation horizons and strict-zero post-exposure backgrounds were
reconstructed. The D3 minimum is a 24 h exposure plus 120 h observation,
approximately six days total. Follow-up to 120 d remains optional.

## Independent Monte Carlo classification

The independent classifier used only total plant-body TFWT. For each frozen
truth prediction it generated 1000 mean-one lognormal replicates and selected
the lower log10 RMSE to the two frozen predictions. It did not call the
runner's classification or result-selection function.

| D3 sample set | truth | CV10 | CV20 | CV30 | CV30 binomial SE |
|---|---|---:|---:|---:|---:|
| full 14 points | H2 | 1.000 | 1.000 | 1.000 | 0 |
| full 14 points | H3 | 1.000 | 1.000 | 1.000 | 0 |
| 0.2, 48, 120 h | H2 | 1.000 | 1.000 | 0.998 | 0.00141 |
| 0.2, 48, 120 h | H3 | 1.000 | 1.000 | 0.991 | 0.00299 |

The independent deterministic greedy search started from the maximum
pointwise separation, used the original preregistered candidate grid and
optimized the worst bidirectional classification result. It reproduced
`0.2;48;120 h` twice without adding a post-result candidate.

## Robustness and acceptance boundary

For D3, all three levels of each frozen factor passed:

```text
CONCENTRATION_ROBUSTNESS = PASS
RH_ROBUSTNESS = PASS
WIND_ROBUSTNESS = PASS
LEAF_PARAMETER_ROBUSTNESS = PASS
```

D2 is not a final supported design because it was outside the top-three
robustness screen and therefore has no robustness evidence. D4 is not
supported because wind 0.2 m/s leaves only one strong-separation sample,
below the frozen requirement of two. D5 cannot find a passing three-to-eight
point minimum set because it also retains only one strong-separation point;
all 12 reported robustness factor levels consequently fail. Larger D4/D5
maximum separation values do not override these preregistered failures.

## Numerical and conservation review

The detached rerun produced 12 base mechanism runs and 27 unique robustness
simulation configurations. All inventories and concentrations were finite
and nonnegative.

```text
MAXIMUM_FORMAL_CLOSURE_RESIDUAL_BQ_M2 =
1.862645149230957E-09

MAXIMUM_PAIRED_INTERNAL_TRANSFER_RESIDUAL_BQ_M2 =
0.0

MAXIMUM_INTERNAL_STATE_SUM_ROUNDOFF_BQ_M2 =
1.061380316969007E-09

FORMAL_MASS_TOLERANCE_BQ_M2 = 1.0E-06
INTERNAL_LEDGER_TOLERANCE_BQ_M2 = 1.0E-09
TOLERANCE_RELAXATION_COUNT = 0
```

The review treats the paired-transfer ledger, formal closure and large-state
subtraction roundoff as different quantities. It does not use state-sum
roundoff as a ledger residual.

All 12 regenerated result CSV files were byte-identical to the tracked
snapshots. Report regeneration preserved the six-day minimum and optional
120-day extension; its only substantive tracked-report difference was the
current source HEAD metadata.

## Attacks

The independent tests rejected or overrode each required attack:

- a forged D3 minimum-set CV30 accuracy of 1.000 was replaced by independently
  recalculated H2/H3 values of 0.998/0.991;
- changing CV30 to 25% violated the frozen noise contract;
- changing the proposed set to 0.2/72/120 h did not reproduce the frozen
  independent optimum;
- enabling parameter refit violated the contract;
- using a latent slow-pool state violated the observable contract;
- setting an empirical-validation claim violated the design-only scope; and
- changing the minimum follow-up to 120 d violated the duration contract.

```text
INDEPENDENT_REVIEW_TEST_COUNT = 35
INDEPENDENT_REVIEW_TEST_RESULT = 35_PASS_0_FAIL
RECOMPUTED_RESULT_SNAPSHOT_MATCH_COUNT = 12_OF_12
FULL_REPOSITORY_COLLECTED_TEST_COUNT = 566
FULL_REPOSITORY_PYTEST_EXIT = PASS
COMPILEALL_STATUS = PASS
V1_RECOMPUTE_ACCEPTANCE = PASS
V2_RECOMPUTE_ACCEPTANCE = PASS
V2_VALIDATION_READINESS = PASS
V3_COMPATIBILITY = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE = READY_ARCHITECTURE_ONLY
V3_EXTERNAL_EVIDENCE = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE_VERIFICATION =
PASS_BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Verdict

The evidence supports a reproducible synthetic experimental design, not
selection of H2 versus H3 from current observations and not empirical
validation. The reviewed D3 research is ready for a conditional fast-forward
merge. Real external evidence must still pass separate intake, licence,
trusted-registry and independent validation gates before any production
physics authorization.
