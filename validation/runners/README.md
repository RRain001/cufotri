# Validation runner contract

The executable runner is `scripts/run_v2_validation_case.py`. It resolves a
case from source configuration, recomputes the model, verifies reference
checksums, applies declared comparison metrics, and writes:

```text
resolved_config.yaml
provenance.json
model_output.csv
reference_output.csv
metrics.json
validation_report.md
plots/
```

`--dry-run` validates the case, scenario taxonomy, reference availability,
checksum, observable columns, metrics, units, and thresholds without running
the model. A missing reference returns `BLOCKED_EXTERNAL_DATA`; it never
becomes an automatic pass.
