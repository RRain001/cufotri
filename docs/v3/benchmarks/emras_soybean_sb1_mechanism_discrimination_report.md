# EMRAS soybean SB1 plant-water mechanism discrimination

This report records a preregistered, validation-only mechanism screen. It is
not empirical validation, does not alter formal physics, and cannot unlock the
V3 production gate.

```text
MERGED_SB1_BASELINE_HEAD =
2a56c56d6de3ee79c1069b799a5dab90e10a0097

MECHANISM_BRANCH =
codex/v3-sb1-plant-water-mechanism-discrimination

MECHANISM_BRANCH_HEAD =
744db57e87f8f7e3c202cda070c4ce95fd5c109b
(TESTED_EVIDENCE_HEAD_BEFORE_REPORT_FINALIZATION)

H0_STATUS = REFERENCE_BASELINE
H1_STATUS = NOT_SUPPORTED_LATE_THRESHOLDS_FAIL
H2_STATUS = NOT_SUPPORTED_PARAMETER_BOUNDARY_AND_IDENTIFIABILITY_FAIL
H3_STATUS = NOT_SUPPORTED_FORCING_ROBUSTNESS_4_OF_7
H4_STATUS = NOT_SUPPORTED_LATE_OBT_BOUNDARY_AND_IDENTIFIABILITY_FAIL

BEST_SUPPORTED_MECHANISM = NONE
LATE_RMSE_IMPROVEMENT = NO_CANDIDATE_PASSES_ALL_FROZEN_CRITERIA
LATE_MEDIAN_RATIO_IMPROVEMENT =
NO_CANDIDATE_PASSES_ALL_FROZEN_CRITERIA
EARLY_FIT_STATUS = PASS_ALL_CANDIDATES_WITHIN_FACTOR_3
FORCING_ROBUSTNESS_STATUS =
H1_0_OF_7_H2_7_OF_7_H3_4_OF_7_H4_0_OF_7
PARAMETER_BOUNDARY_STATUS = H2_AND_H4_HIT_BOUND_H3_NO_BOUND_HIT
IDENTIFIABILITY_STATUS =
H2_LIMITED_H3_PASS_BOUNDED_LOCAL_SCREEN_H4_LIMITED
MASS_BALANCE_STATUS = PASS_35_OF_35

MECHANISM_DISCRIMINATION_STATUS =
NO_MINIMAL_MECHANISM_SUPPORTED

FORMAL_V3_DESIGN_RECOMMENDATION = NOT_READY

V3_PHYSICS_IMPLEMENTATION_STATUS =
NOT_STARTED

EMPIRICAL_VALIDATION_CLAIM =
FALSE

PRODUCTION_GATE_ELIGIBLE =
FALSE

V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

`MECHANISM_BRANCH_HEAD` is the tested evidence parent of this report. The
publication commit is necessarily a report-only descendant and is recorded in
the final handoff; a commit cannot contain its own SHA.

## Frozen protocol and candidates

The protocol was committed at `104b1b5264c60b4035f489ad1804f870f94be6c4`
before any candidate run. The selected parameters were committed at
`4b79f62741db4d4b51f4d608df33d2e13c499636` before any late check. The
existing leaf stomatal resistance (`800 s m-1`) and characteristic length
(`0.10 m`) were frozen and never refitted.

| ID | validation-only definition | new fitted parameters |
|---|---|---:|
| H0 | Exact merged SB1 single-pool adapter and frozen leaf parameters | 0 |
| H1 | Preserve H0 TFWT activity inventory and change only the concentration mapping to a time-varying plant-water storage | 0 |
| H2 | Parallel fast/slow TFWT residual; capture from positive leaf uptake and first-order release, both activity-conservative | 2 |
| H3 | Reversible first-order fast/slow TFWT exchange, activity-conservative | 2 |
| H4 | Multipliers on the existing OBT formation and turnover fluxes, with no new state | 2 |

H2 selected `slow_capture_fraction=0.001` and
`slow_release_rate_s=1.0e-6 s-1`. H3 selected
`fast_to_slow_rate_s=1.0e-7 s-1` and
`slow_to_fast_rate_s=1.0e-6 s-1`. H4 selected
`formation_multiplier=2.0` and `turnover_multiplier=2.52`.

## Calibration, late check and descriptive analysis

Only plant-body TFWT at `0.2, 1, 24, 120, 336 h` entered the exhaustive
calibration grids. The `936, 1608, 2280 h` plant-body TFWT values were opened
only after the parameter file was committed. Pods were structural diagnostics;
OBT was a consistency check. Neither entered parameter selection.

The eight-point descriptive analysis was not used to define candidate ranges,
calibrate parameters or select a model. It gave a single-exponential e-folding
time of `275.126 h`; a log-residual double-exponential fit gave fast and slow
e-folding times of `3.36495 h` and `764.522 h` with natural-log SSE `3.46603`;
the best piecewise log-linear break was `24 h` with early and late slopes
`-0.125216` and `-0.000726626 log10 h-1`.

## Frozen results

Primary forcing metrics:

| ID | calibration log10 RMSE | late log10 RMSE | late median P/O | late RMSE improvement | median-ratio closeness improvement | early factor-3 |
|---|---:|---:|---:|---:|---:|---|
| H0 | 1.46638 | 2.61097 | 0.00198478 | reference | reference | reference |
| H1 | 1.50689 | 3.03786 | 0.000742811 | -0.426883 dex | -0.426833 dex | pass |
| H2 | 0.599688 | 0.821221 | 0.556390 | +1.78975 dex | +2.44767 dex | pass |
| H3 | 0.275860 | 1.11834 | 0.172670 | +1.49263 dex | +1.93951 dex | pass |
| H4 | 1.15051 | 5.24874 | 6.99664e-6 | -2.63777 dex | -2.45282 dex | pass |

The frozen primary thresholds required at least `0.75 dex` late-RMSE
improvement, at least `1.0 dex` median-ratio closeness improvement, no more
than `0.25 dex` calibration worsening, early predictions within factor 3,
finite nonnegative states, conservation, no parameter on a bound, acceptable
identifiability, and persistence in at least five of seven forcing scenarios.

H2 passes both late thresholds under all seven forcing scenarios but its
capture fraction is exactly the lower grid bound and its local screen is
limited. H3 has no bound hit and passes the bounded local-identifiability
screen, but persists in only four scenarios; the three background
sensitivities fail. H1 and H4 fail the late thresholds in all seven scenarios.
H4 also worsens the OBT consistency check.

All 35 mechanism-forcing runs were finite and nonnegative. The maximum formal
closure residual was `1.86265e-9 Bq m-2`, below the frozen `1e-6 Bq m-2`
tolerance. H2/H3 maximum internal-transfer residuals were `9.28594e-10` and
`9.24274e-10 Bq m-2`, below the frozen `1e-9 Bq m-2` tolerance.

The correct fail-closed conclusion is therefore:

```text
NO_MINIMAL_MECHANISM_SUPPORTED
```

This result neither rejects all possible slow-process physics nor licenses
parameter expansion. It shows only that none of H1-H4 satisfies every frozen
criterion in this SB1 validation-only screen.

## Verification

The mechanism test module passed `17/17`; the complete repository passed
`411/411` tests with the one previously known NumPy/netCDF ABI warning.
Recomputed V1 acceptance passed five frozen cases. Recomputed V2 acceptance
passed six end-to-end cases and the expanded acceptance suite. V2 validation
readiness, V3 deterministic compatibility, V3 architecture readiness, the
fail-closed external-evidence verifier, the V3 physics-start gate verifier,
Python byte-compilation and Git diff checks passed.

No file under `src/` or formal `configs/` differs from merged `main`. No
trusted-registry entry or V3 tag was created. The mechanism branch is not to be
merged in this work item.
