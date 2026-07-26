# EMRAS soybean SB4 PDF + ERA5 frozen-transfer benchmark

## Verdict

```text
MERGED_MAIN_BASELINE = d08d9d81f3ef10b11c2431e7bebe2f802c56cd18
SB4_BRANCH = codex/v3-emras-soybean-sb4-transfer-benchmark
SB4_BRANCH_HEAD = FINAL_DELIVERY_HEAD_REPORTED_BY_GIT
TESTED_EVIDENCE_PARENT = 8353611

SB4_DATA_STATUS = PASS_14_TFWT_6_OBT_16_BIOMASS_14_SCHEDULE_ROWS
SB4_CHAMBER_PROFILE_STATUS = PASS_2_RECONSTRUCTED_MEAN_CONSTRAINED
SB4_ERA5_STATUS = PASS_REUSED_5_SB1_RAW_FILES_BY_CHECKSUM

H0_STATUS = REFERENCE_BASELINE_REPRODUCED
H2_SB1_FROZEN_STATUS = SUPPORTED_FOR_BOUNDED_CROSS_EXPERIMENT_DESIGN
H3_SB1_FROZEN_STATUS = SUPPORTED_FOR_BOUNDED_CROSS_EXPERIMENT_DESIGN

H2_PARAMETER_SOURCE_COMMIT = 4b79f62741db4d4b51f4d608df33d2e13c499636
H3_PARAMETER_SOURCE_COMMIT = 4b79f62741db4d4b51f4d608df33d2e13c499636
SB4_PARAMETER_REFIT_COUNT = 0

PLANT_BODY_TRANSFER_STATUS = PASS_H2_AND_H3
PODS_DIAGNOSTIC_STATUS = PASS_VETO_ONLY_PROVISIONAL_MAPPING
OBT_CONSISTENCY_STATUS = PASS_VETO_ONLY
FORCING_ROBUSTNESS_STATUS = PASS_H2_14_OF_14_H3_14_OF_14
MASS_BALANCE_STATUS = PASS_42_OF_42

SB4_TRANSFER_STATUS = MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED
FORMAL_V3_DESIGN_RECOMMENDATION =
BOUNDED_COMPARATIVE_DESIGN_REVIEW_ONLY

EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

`SB4_BRANCH_HEAD` cannot self-reference the commit containing this report.
The final delivery records the literal pushed head; `TESTED_EVIDENCE_PARENT`
identifies the exact code, results and 23 SB4 tests used by the full regression.

## Evidence boundary and data

The public TFWT/OBT, biomass and schedule cells were checked against the PDF
text layer and rendered pages 105, 287 and 290. The source PDF remains ignored
local evidence. The table builder and verifier preserve units and source-cell
traceability.

SB4 publishes only a one-hour mean chamber HTO concentration, not a five-minute
curve. The benchmark therefore declares both chamber profiles
`RECONSTRUCTED`: a constant `52,700 Bq mL-1 water` profile and the published
SB1 curve shape scaled to the same trapezoidal mean. Five checksum-bound SB1
ERA5 raw files are reused without redownload to construct 14 continuous
five-minute forcing files.

This combination is useful for a frozen cross-experiment transfer test but is
not an observed SB4 forcing package and cannot be called empirical validation.

## Frozen protocol and chronology

The SB4 transfer protocol was committed at
`e7ff0d26968a2ae39b332a33e9d88afe355ab064` before the first prediction.
It binds the SB1 parameter source commit, parameter-file checksum,
parameter-result hash, exact H2/H3 values, 42-run matrix, endpoints, thresholds
and failure rules. H2 and H3 were run unchanged; no SB4 result was used for
fitting, selection, bound expansion or parameter optimization.

```text
H2_PARAMETERS =
slow_capture_fraction_0.001_release_rate_1e-6_s-1
H3_PARAMETERS =
fast_to_slow_1e-7_s-1_slow_to_fast_1e-6_s-1
SB4_PARAMETER_REFIT_COUNT = 0
SB4_PARAMETER_SELECTION_COUNT = 0
```

## Primary metrics

RUN_01 plant-body `log10 RMSE / log10 bias / median P/O`:

| profile | H0 | H2 frozen | H3 frozen |
|---|---|---|---|
| constant | 1.536962 / -1.298408 / 0.021175 | 0.354187 / 0.063606 / 0.962755 | 0.367165 / -0.142373 / 0.961340 |
| scaled SB1 | 1.537014 / -1.294400 / 0.021056 | 0.354580 / 0.070107 / 0.991755 | 0.367056 / -0.140051 / 0.990327 |

```text
H0_METRICS =
CONSTANT_1.536962_SCALED_1.537014_LOG10_RMSE
H2_METRICS =
CONSTANT_0.354187_SCALED_0.354580_LOG10_RMSE
H3_METRICS =
CONSTANT_0.367165_SCALED_0.367056_LOG10_RMSE
```

RUN_01 pod `log10 RMSE / log10 bias / median P/O`:

| profile | H0 | H2 frozen | H3 frozen |
|---|---|---|---|
| constant | 1.947616 / -0.745453 / 0.264965 | 1.948069 / -0.745210 / 0.265002 | 1.947787 / -0.745307 / 0.264975 |
| scaled SB1 | 1.956041 / -0.752708 / 0.263421 | 1.956498 / -0.752459 / 0.263461 | 1.956209 / -0.752561 / 0.263431 |

```text
CONSTANT_PROFILE_RESULTS =
H2_OVERALL_PLUS_1.182774_LATE_PLUS_1.680270_7_OF_7;
H3_OVERALL_PLUS_1.169797_LATE_PLUS_1.574313_7_OF_7
SCALED_SB1_PROFILE_RESULTS =
H2_OVERALL_PLUS_1.182434_LATE_PLUS_1.682646_7_OF_7;
H3_OVERALL_PLUS_1.169958_LATE_PLUS_1.575084_7_OF_7
```

Pods and OBT satisfy their frozen non-worsening vetoes, but are not positive
selection evidence. H2 and H3 each pass all seven forcing scenarios under both
profiles. An independent recomputation from point predictions agrees with the
stored metrics and decision rather than trusting the summary JSON.

## Conservation, tests and scope

All 42 runs are finite and nonnegative. The maximum formal closure residual is
`3.725290e-9 Bq m-2`; the paired internal-transfer ledger residual is zero.
The maximum `2.146407e-9 Bq m-2` large-state subtraction roundoff is disclosed
separately and did not cause a tolerance relaxation.

The SB4 suite adds 23 tests, including the 18 required checks and attacks that
alter the H2 parameter, claim SB4 parameter selection, or spoof a reconstructed
profile as an observation. All attacks are rejected. The complete repository
passes 458 tests with the one known NumPy/netCDF ABI warning. V1, V2, V2
validation readiness, V3 deterministic compatibility, V3 architecture,
external-evidence fail-closed and physics-start-gate verifiers all pass.

No formal `src/`, root `configs/`, trusted registry, V1/V2 tag or V3 physics
file is changed. Because both slow mechanisms transfer, SB4 narrows the design
space only to a bounded comparative review; it does not identify a unique
mechanism or authorize implementation.
