# Independent review of the SB4 frozen transfer benchmark

```text
REVIEWED_BRANCH =
codex/v3-emras-soybean-sb4-transfer-benchmark

REVIEWED_HEAD =
b540387087cecedee2a3d2a078657e0b313a2c8e

TESTED_EVIDENCE_PARENT =
8353611

INDEPENDENT_WORKTREE =
/Users/rain/Documents/Doctor/Topic/CETAS_ufotri_sb4_independent_review

INDEPENDENT_REVIEW_BRANCH =
codex/v3-emras-soybean-sb4-independent-review

SB4_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_FROZEN_TRANSFER

H2_TRANSFER_STATUS =
CONFIRMED_14_OF_14

H3_TRANSFER_STATUS =
CONFIRMED_14_OF_14

SB4_TRANSFER_STATUS =
CONFIRMED_MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED

MERGE_RECOMMENDATION =
READY_TO_MERGE_SB4_RESEARCH_BENCHMARK

EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
FORMAL_V3_PHYSICS = NOT_STARTED
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Independent boundary and chronology

The review worktree was created at the exact final SB4 head. It did not copy
any SB4 processed ERA5, generated forcing, predictions, metrics, selection or
mass-balance result. The only copied inputs were the IAEA source PDF and the
five shared SB1/SB4 ERA5 raw responses. All six copies were made read-only
before use.

The independently recomputed input checksums are:

| input | bytes | SHA-256 |
|---|---:|---|
| IAEA EMRAS tritium working-group PDF | 8,944,588 | `15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211` |
| CENTRE ERA5 raw response | 213,284 | `f01366f54fc14735ae28ea8e2e75e87bd2acbe129fc5d8096dab50589b44d290` |
| NORTH_0P25 ERA5 raw response | 213,284 | `ae0f7596ffab190382e97f8c26a3f937bed2dea057f888254d79cce5bccc1868` |
| SOUTH_0P25 ERA5 raw response | 213,284 | `2e93bca85b6eac020a96d21926b393bdc3eb7871e3511f8310a7c8641ab5b1d1` |
| EAST_0P25 ERA5 raw response | 213,284 | `5bdc10883c8edb9953a811e3441897076ad591df8c5da63a3569c2a648e9bea6` |
| WEST_0P25 ERA5 raw response | 213,284 | `c889a7002074c0c3abf97158d7e11d69abbaf5634db701dd572add0a5682740f` |

The PDF checksum matches both the SB1 and SB4 source inventory. All five raw
checksums match the frozen SB1 case manifest and the independently regenerated
SB4 forcing manifest.

The branch is eight commits ahead of and zero commits behind baseline
`d08d9d81f3ef10b11c2431e7bebe2f802c56cd18`. The observed sequence is:

```text
c6eb07e  SB4 data transcription
b1c81d8  reconstructed chamber and ERA5 forcing
e7ff0d2  frozen SB1-to-SB4 transfer protocol
efb6e85  frozen transfer runner
ed253e0  paired-transfer ledger stabilization
31df826  42-run result generation
8353611  transfer and conservation tests
b540387  final report and status
```

Git ancestry confirms that protocol commit
`e7ff0d26968a2ae39b332a33e9d88afe355ab064` precedes the runner and every
SB4 prediction commit.

```text
SB4_REVIEW_BASELINE_STATUS = PASS_EXACT_FROZEN_HEADS
REMOTE_ALIGNMENT_STATUS = PASS_LOCAL_EQUALS_REMOTE
TAG_INTEGRITY_STATUS = PASS_V1_V2_UNCHANGED
INITIAL_WORKTREE_STATUS = PASS_CLEAN
SB4_SCOPE_REVIEW = PASS_VALIDATION_RESEARCH_ONLY
SB4_PROTOCOL_CHRONOLOGY_REVIEW = PASS_FROZEN_BEFORE_PREDICTION
FORMAL_DIFF_STATUS = PASS_ZERO_SRC_CONFIG_REGISTRY_CHANGES
```

## Direct PDF transcription review

PDF pages 105, 287 and 290 were rendered to PNG and inspected visually. Their
text layers were also extracted independently. The review tests parse the PDF
text directly and then compare the parsed values to the tracked tables; they
do not merely compare a second hard-coded array to the CSV.

The review reproduced:

- 14 TFWT values: seven plant-body and seven pod observations at
  `0.2, 1, 24, 120, 336, 768, 1368 h`;
- six SB4 harvest OBT values: stem `19.8`, leaves `8.8`, body average `14.3`,
  shell `74.7`, seeds `200.0`, and pod average `137.4 Bq/mL` combustion water;
- 16 SB4 biomass component cells across exposure/harvest and fresh/dry mass;
- 14 sampling rows after expanding the seven published sampling times to the
  two requested compartments;
- exposure on 2001-08-09 and harvest on 2001-10-05; and
- the reported mean chamber air-moisture HTO of
  `5.27 x 10^4 Bq/mL water`.

The tracked `Bq/L` fields equal the PDF `Bq/mL` values multiplied by exactly
1000. Biomass units retain their fresh/dry basis and `m-2` area basis.

```text
SB4_PDF_TRANSCRIPTION_REVIEW = PASS_14_TFWT_6_OBT_16_BIOMASS
SB4_SOURCE_TRACEABILITY_REVIEW = PASS_TEXT_AND_RENDERED_PAGE
SB4_UNIT_REVIEW = PASS_EXPLICIT_1000_CONVERSION
```

## Chamber profiles and ERA5 reconstruction

Both chamber profiles were rebuilt after confirming that the independent
worktree contained no SB4 generated directory.

The constant profile is `52,700 Bq/mL water` from 09:30 through 10:30 and its
trapezoid mean is exactly `52,700`. The scaled profile starts from the
published SB1 five-minute shape, retains the unreported 09:30 boundary as the
explicit zero reconstruction assumption, and applies one uniform scale factor
of `0.6969747065630683`. Its source mean is `75,612.5 Bq/mL` and its resulting
trapezoid mean is exactly `52,700`. Ratios between each nonzero scaled value
and the corresponding SB1 source value are constant.

Every profile row and all 14 forcing-manifest entries are marked
`RECONSTRUCTED`; none claims an observed or published SB4 five-minute curve.

The five raw inputs have ZIP file signatures despite their `.nc` names. The
tracked extraction logic found one NetCDF member in each response and wrote
new processed files in the independent worktree. Each point contains 3,336
consecutive hourly records from 2001-05-20 15:00 UTC through
2001-10-06 14:00 UTC, with zero duplicate, missing, NaN and Inf counts.

A separate review calculation compared every processed interval to the
extracted NetCDF:

```text
tp [m]       x 1000 = precipitation_mm_interval
ssrd [J/m2]  / 3600 = shortwave_down_W_m2
strd [J/m2]  / 3600 = longwave_down_W_m2
```

The comparison is exact within `1e-12`; no second differencing is present.
Five processed point families and 14 profile/scenario forcing files were
regenerated.

```text
SB4_INPUT_SNAPSHOT_STATUS = PASS_SIX_READ_ONLY_INPUTS
PDF_CHECKSUM_STATUS = PASS
ERA5_RAW_CHECKSUM_STATUS = PASS_5_OF_5
READ_ONLY_INPUT_STATUS = PASS
SB4_CONSTANT_PROFILE_REVIEW = PASS_EXACT_MEAN
SB4_SCALED_PROFILE_REVIEW = PASS_ONE_FACTOR_SHAPE_PRESERVED
SB4_PROFILE_PROVENANCE_REVIEW = PASS_RECONSTRUCTED_ONLY
SB4_ERA5_REBUILD_STATUS = PASS_5_OF_5
SB4_ERA5_INTERVAL_REVIEW = PASS_PREVIOUS_ONE_HOUR_NO_SECOND_DIFF
SB4_FORCING_REBUILD_STATUS = PASS_14_FILES
```

## Frozen parameter contract

The SB4 protocol binds the parameter source to commit
`4b79f62741db4d4b51f4d608df33d2e13c499636`. The file at that commit and
the current frozen file both have SHA-256
`9224d4019d1e71f28f653699125c09328ae95af8bfc39a71442dc9dc355dc2d9`.
The contained parameter-result hash is
`f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9`.

The values match exactly:

| mechanism | frozen parameters |
|---|---|
| H2 | `slow_capture_fraction=0.001`; `slow_release_rate_s=1.0e-6` |
| H3 | `fast_to_slow_rate_s=1.0e-7`; `slow_to_fast_rate_s=1.0e-6` |

There is no SB4 parameter file, optimization mode, command-line override or
environment override. Every prediction row records
`selected_from_sb4=false` and `sb4_parameter_refit_count=0`.

```text
SB1_PARAMETER_SOURCE_COMMIT = 4b79f62741db4d4b51f4d608df33d2e13c499636
SB1_PARAMETER_FILE_SHA256 = 9224d4019d1e71f28f653699125c09328ae95af8bfc39a71442dc9dc355dc2d9
SB1_PARAMETER_RESULT_HASH = f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9
SB4_PARAMETER_REFIT_COUNT = 0
SB4_PARAMETER_SELECTION = FALSE
```

## Independent 42-run result and selector review

The runner regenerated the complete Cartesian product:

```text
3 mechanisms x 2 profiles x 7 forcing scenarios = 42 runs
MISSING_COMBINATION_COUNT = 0
DUPLICATE_COMBINATION_COUNT = 0
```

A review-side metric implementation recomputed all overall, early, mid and
late metrics from 588 point predictions without calling the SB4 metric or
selection functions. Primary RUN_01 log10 RMSE values are:

| profile | H0 plant body | H2 plant body | H3 plant body | H0 pods | H2 pods | H3 pods |
|---|---:|---:|---:|---:|---:|---:|
| constant | 1.536962 | 0.354187 | 0.367165 | 1.947616 | 1.948069 | 1.947787 |
| scaled | 1.537014 | 0.354580 | 0.367056 | 1.956041 | 1.956498 | 1.956209 |

The independently reconstructed forcing pass counts are:

| mechanism | constant | scaled |
|---|---:|---:|
| H2 | 7/7 | 7/7 |
| H3 | 7/7 | 7/7 |

Primary pod RMSE worsening is only `0.000453/0.000457 dex` for H2 and
`0.000171/0.000168 dex` for H3 under constant/scaled profiles. Primary OBT
absolute-log-error worsening is negative for both mechanisms and profiles.
Pods and OBT are nevertheless used only as veto/consistency checks and never
as positive selection evidence.

The review selector derived from detailed predictions, independently
recomputed metrics and independently rerun mass checks returns:

```text
MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED
```

This is a bounded cross-experiment transfer result. It does not select H2 or
H3, validate either mechanism empirically, or authorize production physics.

## Independent conservation and adversarial checks

The review test imports the frozen SB1 mechanism implementation directly and
reruns all 42 forcing/mechanism cases without calling the SB4 runner,
mass-summary function or selector. Its results are:

```text
FINITE_NONNEGATIVE_STATUS = PASS_42_OF_42
FORMAL_MASS_BALANCE_STATUS = PASS_42_OF_42
MAXIMUM_FORMAL_RESIDUAL_BQ_M2 = 3.725290298461914E-9
PAIRED_INTERNAL_TRANSFER_LEDGER = ZERO
MAXIMUM_INTERNAL_LEDGER_RESIDUAL_BQ_M2 = 0
MAXIMUM_STATE_SUM_ROUNDOFF_BQ_M2 = 2.1464074961841102E-9
```

The paired flux ledger uses `math.fsum` over equal and opposite entries. Its
exact zero is the internal transfer acceptance quantity. The separately
reported state-sum subtraction roundoff exceeds `1e-9` in some large-inventory
states, but it is not represented as a ledger residual and was not used to
relax the frozen `1e-9 Bq/m2` internal-transfer tolerance.

The independent review adds 37 tests. Five explicit attacks are rejected:

1. changing the H2 capture fraction;
2. setting `selected_from_sb4=true`;
3. relabelling a reconstructed profile as `OBSERVED`;
4. forging an H3 forcing pass count from 7 to 6; and
5. making pods positive parameter-selection evidence.

The last two are new review-side attacks beyond the original branch tests.

## Regression and gate status

The original SB4 suite passes 23/23 tests. The independent review suite passes
37/37 tests. The repository collects 495 tests.

The first full-repository attempt found seven existing SB1 independent-review
tests without their ignored local `generated_forcing` and
`outputs/calibration_grid.csv` inputs. The review did not copy those outputs.
It regenerated the SB1 dataset, five-point ERA5 forcing, seven baseline runs,
49-point frozen calibration grid and pseudo-holdout outputs from the copied,
read-only PDF and raw ERA5 inputs. The SB1 independent suite then passed
27/27, and the full repository passed 494 tests with one existing skip and one
known NumPy/netCDF ABI warning.

The V1/V2/V3 calculation verifiers require a separate ignored 48-hour ERA5
input that Phase C did not authorize copying into the review worktree. Its
SHA-256 was independently checked as
`7100f02f3da570098cda4ff5e362d1ffb667fdf685dd29ee1c176d4339c6474c`,
matching the tracked acquisition manifest. The verifiers were then executed
in the original SB4 worktree at the identical reviewed head `b540387...`.
Review additions are tests and this report only and are not imported by those
calculation paths.

```text
INDEPENDENT_TEST_STATUS = PASS_37
ORIGINAL_SB4_TEST_STATUS = PASS_23
FULL_REGRESSION_STATUS =
PASS_494_ONE_EXISTING_SKIP_ONE_KNOWN_NUMPY_NETCDF_WARNING

V1_ACCEPTANCE = PASS_RECOMPUTED_5_OF_5
V2_ACCEPTANCE = PASS_RECOMPUTED
V2_VALIDATION_READINESS = PASS
V3_COMPATIBILITY = PASS_BITWISE_WHERE_DETERMINISTIC
V3_ARCHITECTURE = READY_ARCHITECTURE_ONLY
V3_EXTERNAL_EVIDENCE = READY_FAIL_CLOSED_BLOCKED_EXTERNAL_DATA
V3_PHYSICS_START_GATE = BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA

FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
TRUSTED_REGISTRY_CHANGE_COUNT = 0
V3_TAG_CREATED = FALSE
```

## Review decision

No stop condition in the frozen review protocol was triggered. The SB4
transcription, forcing reconstruction, frozen parameter transfer, detailed
metrics, 42-run completeness, veto roles and conservation checks are
independently reproducible.

The branch is ready to merge as a research benchmark only. Its valid claim is
that both H2 and H3 transfer across the SB1/SB4 reconstructed comparison under
the frozen criteria. Current evidence cannot uniquely select either mechanism.

```text
SB4_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_FROZEN_TRANSFER

H2_TRANSFER_STATUS =
CONFIRMED_14_OF_14

H3_TRANSFER_STATUS =
CONFIRMED_14_OF_14

SB4_TRANSFER_STATUS =
CONFIRMED_MULTIPLE_SLOW_MECHANISMS_TRANSFER_SUPPORTED

MERGE_RECOMMENDATION =
READY_TO_MERGE_SB4_RESEARCH_BENCHMARK
```
