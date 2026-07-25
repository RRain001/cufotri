# Deterministic forcing extension bias

`FORCING_EXTENSION_BIAS_STATUS = PASS_COMPARISON_EXECUTED_NOT_SITE_VALIDATION`

The frozen V2 72 h wet case was rerun twice with the same model configuration:

1. 72/72 externally retrieved ERA5 reanalysis hours; and
2. the candidate baseline of 48 ERA5 hours followed by the documented
   deterministic dry 24 h extension.

This isolates forcing substitution. It is an internal sensitivity comparison,
not an independent model reference and not site validation.

## Primary results

| Observable | Observed-forcing versus extension result |
|---|---:|
| cumulative wet deposition | 0.000% final difference |
| cumulative dry deposition | 0.000% final difference |
| final soil HTO | -5.668% |
| final plant TFWT | +0.105% |
| final plant OBT | +3.198% |
| TFWT peak time | 8 h earlier |
| total/pathway dose | zero in both runs because dose is disabled in this case |

Wet and dry deposition are unchanged because the configured release lasts one
hour, entirely inside the shared first 48 h. The new third day changes
post-release water/plant redistribution: final soil HTO decreases, final OBT
increases modestly, and the TFWT peak timing changes. These differences do not
reverse the candidate's activity-ledger conclusion, but they demonstrate that
the deterministic extension is not neutral for downstream inventories.

The original hybrid case remains a transparent integration/regression
scenario. It must not be relabelled as 72 h external forcing or field
validation.

Execution:

```bash
.venv/bin/python scripts/run_v2_validation_case.py \
  --case validation/cases/full_observed_72h.yaml \
  --output validation/reports/full_observed_72h
```

The generated, untracked report directory contains the resolved configuration,
provenance, both full time series, metrics, report, and plots.
