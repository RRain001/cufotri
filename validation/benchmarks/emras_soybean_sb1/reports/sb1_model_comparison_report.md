# SB1 model comparison report

```text
MODEL_INTERFACE_STATUS = RUNNABLE_WITH_VALIDATION_ADAPTER_ONLY
BASELINE_RUN_COUNT = 7
CALIBRATED_SENSITIVITY_RUN_COUNT = 7
NAN_COUNT = 0
INF_COUNT = 0
NEGATIVE_CONCENTRATION_COUNT = 0
TIME_ALIGNMENT_STATUS = PASS
OBSERVATION_MAPPING_STATUS = PASS
REPRODUCIBLE_RERUN_STATUS = PASS
```

## Primary numerical results

| partition | log10 RMSE | log10 bias | median P/O | factor 2 | factor 10 |
|---|---:|---:|---:|---:|---:|
| calibration plant body | 1.4664 | -1.0293 | 0.0480 | 0.400 | 0.400 |
| pseudo-holdout A plant body | 2.6110 | -2.5674 | 0.00198 | 0.000 | 0.000 |
| pseudo-holdout B pods | 1.1416 | -1.1351 | 0.0716 | 0.000 | 0.333 |

Across all seven forcing runs, calibration log10 RMSE spans
1.4084--1.5215, late plant-body 1.4524--2.6110, and pods 1.0281--1.1417.
Thus meteorology/background choices influence magnitude but do not reverse
the underprediction.

## Scientific diagnosis

1. At 0.2 h the primary prediction is 8.99e6 versus 9.58e6 Bq/L; at 1 h it
   is 2.04e6 versus 1.05e6. The first-hour fall is represented only roughly.
2. At 24 h the model reaches 10.35 versus 3920 Bq/L. The 1--24 h fall is far
   too fast.
3. Predictions at 120 and 336 h are 63.37 and 10.20 versus 1320 and 330 Bq/L.
   The observed slow phase is underrepresented.
4. At 936, 1608 and 2280 h, plant-body predictions are 1.293, 0.119 and
   0.051 Bq/L versus 110, 60 and 60. The residual platform is not reproduced.
5. Pods predictions are 11.03, 6.27 and 4.30 versus 210, 60 and 60 Bq/L.
   Plant-body calibration does not transfer successfully.
6. Five-point ERA5 sensitivity changes error magnitude, not the diagnosis.
7. Mean-constrained chamber scaling is only +2.7608%, with correspondingly
   small early-result changes.
8. Background HTO matters mainly at late times, but even the high boundary
   does not restore the plant-body plateau.
9. The two calibrated leaf-resistance parameters are locally distinguishable,
   but boundary hits and residual bias make their empirical identifiability
   limited.
10. The adapter cannot represent dynamic plant-water storage, a distinct
    slow residual pool, chamber mixing measurements, soybean-specific pod
    allocation, or organ-resolved OBT.
11. Harvest plant-body average OBT is 3.50 versus 16,000 Bq/L combustion
    water, while provisional pods average is 624 versus 670 Bq/L. Pods are
    of similar magnitude, but the plant-body result has a severe systematic
    deficit and the generic edible mapping prevents validation of the pods
    agreement.
12. A future finite V3 plant-physics investigation is scientifically
    motivated, but this benchmark does not authorize or validate it.

The pseudo-holdout was evaluated only after the calibrated parameter set and
hash were committed. No parameter or bound was changed afterward.

```text
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
```
