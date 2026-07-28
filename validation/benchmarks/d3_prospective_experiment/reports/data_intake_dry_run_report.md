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

`manifest_sha256 = 5de2522b68a6c8f3e55f1028edb1dfdaa8f22352588e11db4cc451ad0ee21c77`
