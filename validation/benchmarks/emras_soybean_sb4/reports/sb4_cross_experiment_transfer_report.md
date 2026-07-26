# Frozen SB1-to-SB4 cross-experiment transfer

```text
PROTOCOL_ID = SB1_TO_SB4_FROZEN_MECHANISM_TRANSFER_V1
PROTOCOL_COMMIT = e7ff0d26968a2ae39b332a33e9d88afe355ab064
PARAMETER_SOURCE_COMMIT = 4b79f62741db4d4b51f4d608df33d2e13c499636
SB4_PARAMETER_REFIT_COUNT = 0
RUN_COUNT = 42
```

The protocol was committed before any SB4 prediction. H2 transfers
`slow_capture_fraction=0.001` and `slow_release_rate=1.0e-6 s-1`; H3
transfers `fast_to_slow_rate=1.0e-7 s-1` and
`slow_to_fast_rate=1.0e-6 s-1`. The frozen parameter file checksum and
parameter-result hash are verified before execution. No SB4 calibration,
optimization, bound expansion or slow-pool fitting is permitted.

Primary RUN_01 plant-body metrics are:

| profile | model | log10 RMSE | log10 bias | median P/O | factor 2 | factor 10 |
|---|---|---:|---:|---:|---:|---:|
| constant | H0 | 1.536962 | -1.298408 | 0.021175 | 0.285714 | 0.285714 |
| constant | H2 frozen | 0.354187 | 0.063606 | 0.962755 | 0.285714 | 1.000000 |
| constant | H3 frozen | 0.367165 | -0.142373 | 0.961340 | 0.714286 | 1.000000 |
| scaled SB1 | H0 | 1.537014 | -1.294400 | 0.021056 | 0.285714 | 0.285714 |
| scaled SB1 | H2 frozen | 0.354580 | 0.070107 | 0.991755 | 0.285714 | 1.000000 |
| scaled SB1 | H3 frozen | 0.367056 | -0.140051 | 0.990327 | 0.714286 | 1.000000 |

Primary RUN_01 pod metrics are:

| profile | model | log10 RMSE | log10 bias | median P/O |
|---|---|---:|---:|---:|
| constant | H0 | 1.947616 | -0.745453 | 0.264965 |
| constant | H2 frozen | 1.948069 | -0.745210 | 0.265002 |
| constant | H3 frozen | 1.947787 | -0.745307 | 0.264975 |
| scaled SB1 | H0 | 1.956041 | -0.752708 | 0.263421 |
| scaled SB1 | H2 frozen | 1.956498 | -0.752459 | 0.263461 |
| scaled SB1 | H3 frozen | 1.956209 | -0.752561 | 0.263431 |

The independently recomputed profile decisions are:

| candidate | profile | primary overall improvement | primary late improvement | forcing passes | supported |
|---|---|---:|---:|---:|---|
| H2 frozen | constant | 1.182774 dex | 1.680270 dex | 7/7 | yes |
| H2 frozen | scaled SB1 | 1.182434 dex | 1.682646 dex | 7/7 | yes |
| H3 frozen | constant | 1.169797 dex | 1.574313 dex | 7/7 | yes |
| H3 frozen | scaled SB1 | 1.169958 dex | 1.575084 dex | 7/7 | yes |

Pod RMSE worsening is at most `0.000458 dex`, below the frozen `0.50 dex`
veto. OBT absolute-log-error worsening is negative for both candidates and
profiles, also below its `0.50 dex` veto. Pods remain a provisional structural
diagnostic and OBT remains a consistency check; neither is positive parameter
selection evidence.

Both transferred slow mechanisms pass the frozen criteria on both chamber
profiles. This supports retaining both as bounded comparative design
candidates, but does not distinguish H2 from H3:

```text
PLANT_BODY_TRANSFER_STATUS = PASS_H2_AND_H3
PODS_DIAGNOSTIC_STATUS = PASS_VETO_ONLY_PROVISIONAL_MAPPING
OBT_CONSISTENCY_STATUS = PASS_VETO_ONLY
FORCING_ROBUSTNESS_STATUS = PASS_H2_14_OF_14_H3_14_OF_14
SB4_TRANSFER_STATUS = MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED
FORMAL_V3_DESIGN_RECOMMENDATION =
BOUNDED_COMPARATIVE_DESIGN_REVIEW_ONLY
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
