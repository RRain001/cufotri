# EMRAS soybean SB1 benchmark scope

```text
TARGET_EXPERIMENT = EMRAS_SOYBEAN_SB1
TARGET_CASE_ID = EMRAS_SOYBEAN_SB1_PDF_ERA5_V1
TARGET_PROCESS = AIR_HTO_TO_PLANT_BODY_TFWT_UPTAKE_AND_DEPURATION

BENCHMARK_CLASS = HYBRID_LITERATURE_REANALYSIS
EXPERIMENTAL_OBSERVATIONS = PUBLISHED_MEASUREMENTS
CHAMBER_FORCING = PUBLISHED_SB1_TIME_SERIES
OUTDOOR_METEOROLOGY = ERA5_REANALYSIS_SUBSTITUTION
RAW_EXPERIMENT_PACKAGE = INCOMPLETE
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
TRUSTED_REGISTRY_ELIGIBLE = FALSE
```

TFWT, OBT, biomass, sampling times and SB1 chamber values are public
measurements reported by the IAEA from a KAERI experiment. The ERA5 series is
not the original experimental meteorological-tower record. The tracked CSVs
are publication-table transcriptions, not raw sample-level observations.

Missing source evidence includes the original repeated measurements, sample
identifiers, complete compositing details, detection limits, total
measurement uncertainty, original Excel workbooks, source-supplied checksums,
and a quantified chamber fan/mixing rate. These limitations prohibit an
independent empirical holdout claim and production-gate use.

The benchmark may be used for model development, numerical comparison,
bounded parameter screening and explicitly labelled pseudo-holdout analysis.
It does not unlock V3 physics:

```text
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```
