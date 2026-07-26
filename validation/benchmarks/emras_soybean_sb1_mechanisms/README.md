# SB1 plant-water mechanism discrimination

This directory contains validation-only prototypes used to distinguish a
small set of plant-water mechanisms against the merged EMRAS soybean SB1
research benchmark.

```text
FORMAL_MODEL_CHANGE = FALSE
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
V3_PHYSICS_IMPLEMENTATION_STATUS = NOT_STARTED
```

The preregistration protocol was committed before any candidate was run.
H0-H4 reuse the frozen SB1 forcing adapter and existing calculation kernel.
No file in `src/` or formal `configs/` is modified.

## Staged execution

```bash
.venv/bin/python \
  validation/benchmarks/emras_soybean_sb1_mechanisms/scripts/run_mechanism_discrimination.py \
  --stage calibrate
```

Commit `frozen_mechanism_parameters.yaml` and
`mechanism_calibration_result.json` before running:

```bash
.venv/bin/python \
  validation/benchmarks/emras_soybean_sb1_mechanisms/scripts/run_mechanism_discrimination.py \
  --stage late
```

Generated full time series and figures remain under the ignored SB1 local
output directory. Compact parameter, prediction, metric, identifiability and
mass-balance tables are tracked here.
