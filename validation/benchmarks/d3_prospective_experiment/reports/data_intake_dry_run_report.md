# D3 synthetic data intake dry-run report

```text
INTAKE_CLASS = SYNTHETIC_INTERNAL_TEST_DATA
RAW_SNAPSHOT_READ_ONLY = TRUE
SHA256_MANIFEST = PASS
LICENCE_REVIEW = SYNTHETIC_INTERNAL_TEST_DATA
REGISTRY_ELIGIBILITY = FALSE
PRODUCTION_ELIGIBILITY = FALSE
REAL_EXTERNAL_VALIDATION = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

| blind ID | rows | schema | units | missing | nonfinite | mass errors | detection mismatches |
|---|---:|---|---|---:|---:|---:|---:|
| A | 35 | PASS | PASS | 0 | 0 | 0 | 0 |
| B | 35 | PASS | PASS | 0 | 0 | 0 | 0 |
| C | 35 | PASS | PASS | 0 | 0 | 0 | 0 |

The read-only snapshot is a local ignored copy of the synthetic
blinded files, not an external raw-data package. The review proves
only that the intake workflow detects schema, unit, missing-value,
mass, detection-limit, licence, and eligibility boundaries.

`manifest_sha256 = 4357a9fafc6fb1ed6d2097e795c37bc8af02d82167d04c4afb510f62345371b4`
