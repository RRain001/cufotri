# V2 external-validation workspace

This directory is intentionally separate from the formal calculation package.
It provides schemas, adapters, metrics, example cases, runners, and report
contracts for evidence that is external to—or independently analytic from—the
model under test.

```text
schemas/   machine-readable case and release-scenario contracts
adapters/  input normalization without model calculations
metrics/   model/reference comparison mathematics
cases/     small public or analytic examples and case manifests
runners/   runner contract documentation
reports/   generated-report contract; large results remain untracked
```

Raw field/site/experimental data, restricted publications, large weather
files, credentials, and generated reports must not be committed. Store only
download instructions, checksums, licences, schemas, small redistributable
snippets, and case manifests.

## Required environmental columns and SI units

| Quantity | Canonical unit |
|---|---|
| `time` | UTC ISO-8601 |
| `air_hto` | Bq m-3 air |
| `precipitation` | m s-1 |
| `wind_speed` | m s-1 |
| `temperature` | K |
| `relative_humidity` | 0-1 |
| `soil_water` | m water |
| `soil_hto` | Bq m-2 |
| `plant_tfwt` | Bq m-2 |
| `plant_obt` | Bq m-2 |
| `food_concentration` | Bq kg-1 fresh |
| `milk_concentration` | Bq L-1 |
| `beef_concentration` | Bq kg-1 |
| `dose` | Sv |
| `uncertainty` | same unit as its observable |

Every case declares units explicitly. Missing values, detection limits,
uncertainty, source/version, licence, checksums, and any unit conversion are
recorded rather than inferred silently.

## Forcing completeness targets

- 72 h validation: 72 consecutive observed hourly records;
- 14 d validation: 336 consecutive observed hourly records;
- 30 d validation: 720 consecutive observed hourly records;
- seasonal validation: declared start/end and complete hourly coverage.

Interpolated, repeated, or extended periods must be labelled and are never
counted as observed.
