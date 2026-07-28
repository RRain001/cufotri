# D3 blinded synthetic classification and unblinding report

```text
EVIDENCE_CLASS = SYNTHETIC_PROSPECTIVE_EXPERIMENT_DRY_RUN
REAL_EXTERNAL_EVIDENCE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
PARAMETER_REFIT_COUNT = 0
TRUTH_KEY_HASH_VERIFIED = TRUE
EXPECTED_CLASSIFICATION_PASS_COUNT = 1_OF_3
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

| blind ID | truth | expected | actual | check | H2 RMSE | H3 RMSE | difference |
|---|---|---|---|---|---:|---:|---:|
| A | H2_SB1_FROZEN | H2_SUPPORTED_OVER_H3 | DATA_INCONCLUSIVE | FAIL | 0.030850 | 0.178846 | 0.147996 |
| B | H3_SB1_FROZEN | H3_SUPPORTED_OVER_H2 | DATA_INCONCLUSIVE | FAIL | 0.170728 | 0.028921 | 0.141807 |
| C | SYNTHETIC_OUT_OF_MODEL_CHALLENGE | DATA_INCONCLUSIVE | DATA_INCONCLUSIVE | PASS | 0.137515 | 0.033267 | 0.104248 |

Dataset C confirms that the classifier does not force a binary model
choice. Datasets A and B do not meet their expected selections because
their realized absolute RMSE differences are below the preregistered
0.15 dex threshold. The frozen threshold, aggregation, seeds, and data
were not changed after unblinding.

The dry run therefore fails its H2/H3 positive-control classification
objective while passing its out-of-model fail-closed objective. It cannot
authorize formal H2/H3 selection, trusted-registry promotion, empirical
validation, or V3 physics.
