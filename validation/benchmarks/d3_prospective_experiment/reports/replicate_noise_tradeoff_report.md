# D3 replicate and uncertainty sensitivity report

Each cell contains 1,000 synthetic experiments. Replicate means are
classified against the two frozen predictions with the preregistered
0.15/0.50 dex fail-closed thresholds. No parameter is fitted.

```text
EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN
PARAMETER_REFIT_COUNT = 0
CV20_PASSING_REPLICATE_COUNTS = [5, 6]
DEFAULT_PLANNING_REPLICATES = 5
DEFAULT_IS_STATISTICAL_POWER_PROOF = FALSE
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## CV20 decision table

| replicates | H2 correct | H3 correct | challenge false confident | combined target |
|---:|---:|---:|---:|---|
| 3 | 0.869 | 0.846 | 0.067 | FAIL |
| 4 | 0.914 | 0.877 | 0.047 | FAIL |
| 5 | 0.937 | 0.927 | 0.035 | PASS |
| 6 | 0.955 | 0.955 | 0.027 | PASS |

Five replicates remain the operational planning default for sample-loss
and anomaly resistance, but the dry-run Monte Carlo result determines
whether that default satisfies the frozen classification target.
