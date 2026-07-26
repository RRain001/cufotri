# EMRAS soybean SB1 PDF + ERA5 research benchmark

```text
TARGET_EXPERIMENT = EMRAS_SOYBEAN_SB1
CASE_ID = EMRAS_SOYBEAN_SB1_PDF_ERA5_V1

SITE_COORDINATE = 36.425000 N, 127.373611 E
SITE_COORDINATE_STATUS = PROVISIONAL_INSTITUTIONAL_LOCATION
TIMEZONE_STATUS = ASIA_SEOUL_CONFIRMED_UTC_PLUS_09

PDF_SOURCE_STATUS = LOCAL_SHA256_VERIFIED
PUBLISHED_OBSERVATION_STATUS = VERIFIED_TEXT_LAYER_AND_VISUAL_CELL_REVIEW
CHAMBER_FORCING_STATUS = PUBLISHED_RAW_AND_MEAN_CONSTRAINED
ERA5_DOWNLOAD_STATUS = COMPLETE_FIVE_POINTS
ERA5_TIME_COVERAGE_STATUS = PASS_3336_OF_3336_HOURS
BACKGROUND_HTO_STATUS = REPORTED_MONTHLY_RANGE_SCENARIOS_NOT_HOURLY_MEASUREMENTS

MODEL_INTERFACE_STATUS = RUNNABLE_WITH_VALIDATION_ADAPTER_ONLY
BASELINE_RUN_STATUS = PASS_7_OF_7
CALIBRATION_STATUS = CALIBRATED_MODEL_DEVELOPMENT_ONLY_BOUNDARY_HIT
PSEUDO_HOLDOUT_STATUS = EXECUTED_7_OF_7_NO_PARAMETER_RECALL
IDENTIFIABILITY_STATUS = LIMITED_BOUNDARY_OR_CORRELATION
OBT_STRUCTURAL_CHECK_STATUS = AVERAGES_ONLY_PROVISIONAL_PODS_MAPPING

TARGETED_TEST_STATUS = PASS_16_OF_16
TOTAL_TEST_STATUS = PASS_367_ONE_KNOWN_NUMPY_NETCDF_WARNING
V1_RECOMPUTE_STATUS = PASS_5_OF_5
V2_RECOMPUTE_STATUS = PASS_6_OF_6_AND_EXPANDED_ACCEPTANCE
V3_COMPATIBILITY_STATUS = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE_STATUS = READY_ARCHITECTURE_ONLY
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0

BENCHMARK_CLASS = HYBRID_LITERATURE_REANALYSIS
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
```

## Evidence and forcing

The local 594-page IAEA report has SHA-256
`15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211`.
Tables 5.1, 5.3, I.4.2--I.4.6 and I.4.9 were transcribed from the text layer
and checked cell by cell against rendered pages 105, 287 and 289. No figure
was digitized. The tracked dataset contains 11 TFWT rows, 8 OBT rows
(6 reported concentration values plus 2 normalized-only rows), 12 biomass
rows, 11 sampling rows and 15 chamber-condition rows.

The report identifies KAERI but not the experimental plot coordinate. The
coordinate is therefore an institutional-area proxy, evidence grade C, and a
centre plus north/south/east/west 0.25-degree ERA5 sensitivity is mandatory.
The five downloads cover local 2001-05-21 00:00 through 2001-10-06 23:00
(UTC request 2001-05-20 through 2001-10-06). Each point contains 3336 hourly
records with zero duplicates, missing timestamps, NaNs or infinities.

The chamber profile is integrated trapezoidally over 09:30--10:30 with the
unreported 09:30 boundary explicitly set to zero. Its raw mean is
75,612.5 Bq/mL water versus the reported 77,700 Bq/mL water
(-2.6866%). The sensitivity profile multiplies every chamber value by
1.027607869069. Moisture activity is converted to air-volume activity by
`C_air = C_moisture * rho_v_actual`, using the project saturation-vapour
function, measured temperature/RH and `1 g water = 1 mL water`.

Post-exposure HTO uses four declared boundaries: excess above background,
and the low/mid/high values of the report's monthly ranges. October 1--5
explicitly extends the September 0.040--0.060 Bq/m3 range. These are boundary
scenarios, not hourly measurements.

## Frozen analysis

Calibration uses plant-body TFWT at 0.2, 1, 24, 120 and 336 h. The two
pre-registered adjustable parameters are daytime stomatal resistance
(200--800 s/m) and leaf characteristic length (0.02--0.10 m); bounds come
from `configs/default_parameters.yaml`. A 7-by-7 grid selected 800 s/m and
0.10 m, both at their upper bounds. The frozen parameter-result hash is
`51609eadd468b64d6aff9953b9c316f9ebbad53121ae6e8f50bda76b8ab57687`.

The centre-run calibration log10 RMSE is 1.4664, log10 mean bias is -1.0293,
median predicted/observed is 0.0480, factor-2 coverage is 0.4 and factor-10
coverage is 0.4. Pseudo-holdout uses 936, 1608 and 2280 h without retuning.
Centre-run late plant-body log10 RMSE is 2.6110 with median ratio 0.00198;
pods log10 RMSE is 1.1416 with median ratio 0.0716. All mapped predictions
are finite and nonnegative.

The model approximately follows the first-hour chamber response but removes
TFWT too rapidly after 1 h and cannot sustain the observed late residual
plateau. Generic edible allocation does not transfer plant-body parameters
successfully to pods. The local Jacobian is full rank with parameter-column
correlation 0.307, but both optima hit bounds and residual bias remains large;
the parameters are therefore not accepted as empirically identifiable.
Organ-resolved OBT is unavailable, and pods OBT is only a provisional generic
edible-compartment diagnostic.

ERA5 spatial and background scenarios change the numerical error ranges, but
none changes the underprediction conclusion. This evidence supports a future
bounded investigation of plant-water-storage dynamics, slow exchange or
residual-pool physics; it does not authorize such a V3 change in this branch.

## Reproducibility boundary

The public table transcriptions, schemas, protocol, adapter and compact result
tables are tracked. The source PDF, ERA5 files, unified forcing, full model
outputs and figures remain under ignored `validation/external_local/`.
The benchmark is not an independent external holdout and cannot enter the
trusted registry or unblock V3 production physics.
