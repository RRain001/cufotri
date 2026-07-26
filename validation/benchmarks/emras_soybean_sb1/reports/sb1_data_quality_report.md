# SB1 data quality report

```text
PDF_TABLE_TRANSCRIPTION = PASS
SOURCE_CELL_TRACEABILITY = PASS
UNIT_CONVERSION = PASS
CHAMBER_TIME_SERIES = PASS
ERA5_TIME_COVERAGE = PASS
ERA5_MISSING_COUNT = 0
CASE_MANIFEST_SCHEMA = PASS
CHECKSUM_STATUS = PASS
```

## Published observations

| dataset | rows | source |
|---|---:|---|
| TFWT | 11 | Table 5.1 |
| OBT | 8 (6 concentration, 2 normalized-only) | Table 5.3 |
| biomass | 12 | Tables I.4.2--I.4.5 |
| sampling schedule | 11 | Table I.4.9 |
| chamber conditions | 15 | Table I.4.6 |

Every row retains report table, PDF page, printed page, row/column locator,
transcription method and verification status. The 09:25 and 09:30 chamber HTO
dashes remain missing in the source table. Only the generated forcing assigns
the declared zero boundary at exposure start.

## Chamber profile

```text
INTEGRATION = TRAPEZOIDAL_09_30_TO_10_30
RAW_PROFILE_MEAN_BQ_ML_WATER = 75612.5
REPORTED_MEAN_BQ_ML_WATER = 77700
RELATIVE_DIFFERENCE_PERCENT = -2.68661518662
MEAN_CONSTRAINED_SCALE_FACTOR = 1.027607869069
FIVE_PERCENT_STOP_RULE = PASS
```

The conversion to Bq/m3 air multiplies Bq/mL moisture by actual vapour density
in g/m3, with the explicit 1 g/mL liquid-water approximation. TFWT and OBT
canonical values multiply reported Bq/mL water by 1000 to Bq/L water.

## ERA5

Five requested points each contain 3336 unique hourly timestamps. All report
zero duplicates, missing hours, NaNs and infinities. The raw downloads and
processed forcing are checksum-locked in the case manifest. The exact
experiment coordinate, original meteorological-tower files, sample-level
replicates, detection limits and total uncertainty remain unavailable.

```text
DATASET_STATUS = READY_PUBLISHED_TABLES_PLUS_ERA5
EVIDENCE_CLASS = HYBRID_LITERATURE_REANALYSIS
PRODUCTION_GATE_ELIGIBLE = FALSE
```
