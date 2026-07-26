# Independent review of the EMRAS soybean SB1 benchmark

```text
REVIEWED_BRANCH =
codex/v3-emras-soybean-sb1-pdf-era5

REVIEWED_HEAD =
178fb0a3ebae53b20b101000cdbb2b39406088c0

INDEPENDENT_WORKTREE =
/Users/rain/Documents/Doctor/Topic/CETAS_ufotri_sb1_independent_review

INDEPENDENT_REVIEW_BRANCH =
codex/v3-emras-soybean-sb1-independent-review

SB1_REVIEW_BASELINE_STATUS = PASS_EXACT_HEAD
REMOTE_ALIGNMENT_STATUS = PASS_LOCAL_EQUALS_ORIGIN
TAG_INTEGRITY_STATUS = PASS_V1_AND_V2_UNCHANGED
INITIAL_WORKTREE_STATUS = CLEAN

PDF_REVIEW_STATUS = PASS_ALL_REQUESTED_CELLS
ERA5_REVIEW_STATUS = PASS_FIVE_POINTS_3336_HOURS
UNIT_REVIEW_STATUS = PASS
TIME_REVIEW_STATUS = PASS
CALIBRATION_REVIEW_STATUS = PASS_49_POINT_REPRODUCTION
PSEUDO_HOLDOUT_REVIEW_STATUS = PASS_NO_PARAMETER_RECALL
ADAPTER_REVIEW_STATUS = PASS_NO_HIDDEN_PHYSICS
STRUCTURAL_FINDING_STATUS = CONFIRMED_24H_TO_2280H_UNDERPREDICTION

ORIGINAL_TEST_COUNT = 367
INDEPENDENT_TEST_COUNT = 27
TOTAL_TEST_STATUS = PASS_394_ONE_KNOWN_NUMPY_NETCDF_WARNING

INDEPENDENT_SB1_BENCHMARK_REVIEW =
PASS_REPRODUCIBLE_STRUCTURAL_DEFICIT

MERGE_RECOMMENDATION =
READY_TO_MERGE_SB1_BENCHMARK
```

## Independence boundary

The review worktree was created directly from the reviewed SHA. Only the
source PDF and five ERA5 raw responses were copied from the original
worktree. They were made read-only and their SHA-256 values were recomputed.
No processed ERA5 file, generated forcing, prediction, metric or plot was
copied.

The full SB1 processing chain was rebuilt. The source PDF, five raw ERA5
files, 15 processed ERA5 artifacts and 10 generated-forcing artifacts were
byte-identical to the original worktree. The rebuilt manifest differed only
in `generation_commit`: rebuilding at the reviewed HEAD necessarily records
`178fb0a...` rather than the original generation commit `edd8889...`.
All scientific fields and checksums were identical. Therefore:

```text
PDF_SHA256_STATUS = PASS
ERA5_RAW_CHECKSUM_STATUS = PASS_5_OF_5
INDEPENDENT_INPUT_SNAPSHOT_STATUS = PASS_READ_ONLY
DATASET_REBUILD_STATUS = PASS
FORCING_REBUILD_STATUS = PASS_BYTE_IDENTICAL
CHECKSUM_REPRODUCIBILITY_STATUS =
PASS_SCIENTIFIC_CONTENT_WITH_EXPECTED_GENERATION_COMMIT_VARIATION
```

Two unrelated ignored ERA5 golden inputs were later copied read-only so that
the repository-wide V1/V2/V3 verifiers could execute in the isolated
worktree. Their SHA-256 values were checked before use. They were not used by
the SB1 benchmark.

## PDF, time and unit review

Rendered PDF pages 105, 287 and 289 were visually inspected. Independent
tests also parsed the PDF text layer directly and compared it with the
tracked CSVs. The review covered 8 plant-body TFWT values, 3 pods TFWT
values, 6 OBT concentrations, 2 normalized-only OBT entries, 15 chamber
rows, 12 biomass entries and 11 compartment sampling rows.

The dashes at 09:25 and 09:30 remain unreported source values. The zero at
09:30 exists only in the generated primary forcing and is explicitly marked
as an assumption. No digitized curve or invented observation was found.

`Asia/Seoul` gives UTC+09:00 on 2001-07-02. The explicitly reported 0.2 h
sample is at 10:40; the report describes 10-12 minutes and therefore the
decimal value is approximate rather than an exact 12-minute timestamp. All
other elapsed-time mappings, local/UTC round trips and chamber/ERA5 phase
boundaries passed.

An independent trapezoidal calculation over 09:30-10:30, excluding 10:35,
gave:

```text
RAW_PROFILE_MEAN = 75612.5 Bq/mL water
REPORTED_MEAN = 77700 Bq/mL water
RELATIVE_DIFFERENCE = -2.6866 percent
MEAN_CONSTRAINED_SCALE = 1.027607869069
```

The air-volume conversion was independently recomputed at 09:40, 10:00 and
10:30 from the published temperature and RH. The project Magnus constants,
degree-Celsius to kelvin conversion, percent-to-fraction conversion and
`1 g liquid water = 1 mL liquid water` dimensional approximation were
applied directly. No factor-of-1000 error was found.

## ERA5 review

For every point, `tp`, `ssrd` and `strd` retain GRIB `stepType=accum` and
one-hour step units. The processor correctly maps:

```text
tp_m * 1000 = precipitation_mm_interval
ssrd_J_m2 / 3600 = shortwave_down_W_m2
strd_J_m2 / 3600 = longwave_down_W_m2
```

No second differencing is applied. Each of CENTRE, NORTH, SOUTH, EAST and
WEST contains exactly 3336 timestamps from 2001-05-20 15:00 UTC through
2001-10-06 14:00 UTC, with zero duplicates, missing values, NaNs or
infinities. The centre precipitation total independently recomputes to
646.781206 mm.

```text
ERA5_PROCESSING_REVIEW = PASS
ERA5_INTERVAL_SEMANTICS_REVIEW = PASS_PREVIOUS_ONE_HOUR
ERA5_SPATIAL_SENSITIVITY_REVIEW = PASS_FIVE_POINTS
```

## Frozen calibration and pseudo-holdout

Git history proves the preregistration commit `edd8889` precedes the
parameter-freeze commit `0e1cb72`, which precedes the pseudo-holdout commit
`9c191f0`. The calibration and both pseudo-holdout partitions are disjoint.

The review reran all 49 combinations without using
`calibration_result.json` to select the optimum. Independent metric
recalculation selected:

```text
leaf_stomatal_resistance_day_s_m = 800
leaf_characteristic_length_m = 0.10
BOUNDARY_HIT = TRUE_BOTH
CALIBRATION_LOG10_RMSE = 1.46637739217
```

The regenerated tracked calibration and pseudo-holdout report files were
byte-identical. Independent recalculation gave:

```text
LATE_PLANT_BODY_LOG10_RMSE = 2.61097196894
LATE_PLANT_BODY_MEDIAN_P_O = 0.00198477512
PODS_LOG10_RMSE = 1.14161890081
PODS_MEDIAN_P_O = 0.07161749527
```

The 24 h, 936 h and 2280 h primary predictions independently reproduce
approximately 10.35, 1.293 and 0.051 Bq/L against observations of 3920,
110 and 60 Bq/L. The structural deficit is therefore confirmed.

```text
PREREGISTRATION_REVIEW = PASS
CALIBRATION_LEAKAGE_REVIEW = PASS_NO_LATE_DATA_IN_SELECTION
PARAMETER_FREEZE_REVIEW = PASS_HISTORY_ORDERED
CALIBRATION_REPRODUCIBILITY_STATUS = PASS
PSEUDO_HOLDOUT_REPRODUCIBILITY_STATUS = PASS
STRUCTURAL_UNDERPREDICTION_STATUS = CONFIRMED
```

## Adapter and repository review

The builder, ERA5 processor, verifier and runner were manually reviewed.
`run_model` has no observation input, nudging term, hidden late inventory,
slow pool or altered leaf flux. Predictions are sampled from model state.
The generic pods mapping remains explicitly provisional.

```text
BENCHMARK_SCOPE_REVIEW = PASS_VALIDATION_ONLY
ADAPTER_NO_HIDDEN_PHYSICS_STATUS = PASS
VALIDATION_ADAPTER_AUDIT = PASS
NO_OBSERVATION_NUDGING_STATUS = PASS
NO_HIDDEN_SLOW_POOL_STATUS = PASS
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
TRUSTED_REGISTRY_CHANGE_COUNT = 0
```

Final checks passed 394 tests, V1 recomputation, V2 recomputation and
validation readiness, V3 deterministic compatibility, V3 architecture
readiness, external-evidence fail-closed verification, compileall and diff
checks. The known NumPy/netCDF ABI warning remains. The production gate is
unchanged:

```text
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
SB1_EMPIRICAL_VALIDATION = NOT_CLAIMED
SB1_PRODUCTION_GATE_ELIGIBLE = FALSE
```
