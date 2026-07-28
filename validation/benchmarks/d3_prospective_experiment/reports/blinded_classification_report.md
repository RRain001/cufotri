# D3 blinded synthetic classification and unblinding report

```text
EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN
REAL_EXTERNAL_EVIDENCE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
PARAMETER_REFIT_COUNT = 0
TRUTH_KEY_HASH_VERIFIED = TRUE
EXPECTED_CLASSIFICATION_PASS_COUNT = 3_OF_3
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

| blind ID | truth | expected | actual | check | H2 RMSE | H3 RMSE | difference |
|---|---|---|---|---|---:|---:|---:|
| A | H2_SB1_FROZEN | H2_SUPPORTED_OVER_H3 | H2_SUPPORTED_OVER_H3 | PASS | 0.030850 | 0.242964 | 0.212114 |
| B | H3_SB1_FROZEN | H3_SUPPORTED_OVER_H2 | H3_SUPPORTED_OVER_H2 | PASS | 0.234831 | 0.028921 | 0.205910 |
| C | SYNTHETIC_OUT_OF_MODEL_CHALLENGE | DATA_INCONCLUSIVE | DATA_INCONCLUSIVE | PASS | 0.169511 | 0.064171 | 0.105341 |

The corrected V2 dry run selected H2 for its H2 positive control,
selected H3 for its H3 positive control and returned
`DATA_INCONCLUSIVE` for the out-of-model challenge. The V1 failure
remains preserved under the benchmark archive and in Git history.

Neither result authorizes formal H2/H3 selection, trusted-registry
promotion, empirical validation, or V3 physics.
