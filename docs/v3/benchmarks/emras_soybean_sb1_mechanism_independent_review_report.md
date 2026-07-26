# Independent review of the SB1 mechanism screen

```text
REVIEWED_BRANCH =
codex/v3-sb1-plant-water-mechanism-discrimination

REVIEWED_HEAD =
5c1d4bf39415be9b6e7960efeda23af50570f518

INDEPENDENT_WORKTREE =
/Users/rain/Documents/Doctor/Topic/CETAS_ufotri_sb1_mechanism_independent_review

INDEPENDENT_REVIEW_BRANCH =
codex/v3-sb1-mechanism-independent-review

PROTOCOL_CHRONOLOGY_REVIEW = PASS
PARAMETER_FREEZE_CHRONOLOGY_REVIEW = PASS
LATE_DATA_LEAKAGE_REVIEW = PASS_NO_LATE_DATA_IN_SEARCH
REPORT_FINALIZATION_REVIEW = PASS_DOCS_ONLY_AFTER_TESTED_EVIDENCE

SB1_MECHANISM_INDEPENDENT_REVIEW =
PASS_REPRODUCIBLE_FAIL_CLOSED_SCREEN

H1_STATUS = CONFIRMED_NOT_SUPPORTED
H2_STATUS = CONFIRMED_IMPROVES_BUT_NOT_IDENTIFIABLE
H3_STATUS = CONFIRMED_IMPROVES_BUT_NOT_ROBUST
H4_STATUS = CONFIRMED_NOT_SUPPORTED

MECHANISM_DISCRIMINATION_STATUS =
CONFIRMED_NO_MINIMAL_MECHANISM_SUPPORTED

MERGE_RECOMMENDATION =
READY_TO_MERGE_RESEARCH_SCREEN

EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
V3_PHYSICS_START_GATE =
BLOCKED_EXTERNAL_EXPERIMENT_OR_FIELD_DATA
```

## Independent boundary and chronology

The review worktree was created at the exact reviewed head. Only the source
PDF and five ERA5 raw NetCDF responses were copied from the original
worktree, made read-only and checksum-verified. Processed ERA5, generated
forcing, mechanism predictions, metrics, selections and mass-balance outputs
were not copied.

The PDF dataset builder, dataset verifier and ERA5 processor rebuilt all local
inputs. The only temporary tracked difference was the expected manifest
generation commit and unset processed-forcing checksum during the rebuild;
the committed manifest was restored after the regenerated primary forcing
reproduced checksum
`7b4c3bc649211c67a0498028e7d8981a53547102cf1a13fc11988b874ee136f6`.

Git ancestry independently confirms:

```text
104b1b5  protocol freeze
868680f  candidate implementation
4b79f62  parameter freeze
83980e5  frozen late checks
744db57  tested evidence parent
c26bb7a  report-only finalization
5c1d4bf  implementation-status-only refresh
```

The calibration predictions contain only `0.2, 1, 24, 120, 336 h`. The late
hours `936, 1608, 2280 h` are disjoint. The frozen leaf parameters remain
`800 s m-1` and `0.10 m`; H2, H3 and H4 each retain two new parameters.

## Independent rebuild and parameter selection

The mechanism calibration entry point was rerun against the independently
rebuilt forcing. It performed one H0 evaluation, one primary H1 evaluation
plus its predefined square-root storage sensitivity, and `49` evaluations
each for H2, H3 and H4. A separate review calculation sorted the 149
point-evaluation rows by calibration log10 RMSE and the frozen tie-breakers,
without reading `mechanism_calibration_result.json` or
`mechanism_selection.json`.

The independent optima are:

| mechanism | parameter 1 | parameter 2 | calibration log10 RMSE |
|---|---:|---:|---:|
| H2 | slow capture fraction `0.001` | release `1.0e-6 s-1` | 0.599687748 |
| H3 | fast-to-slow `1.0e-7 s-1` | slow-to-fast `1.0e-6 s-1` | 0.275859965 |
| H4 | formation multiplier `2.0` | turnover multiplier `2.52` | 1.150505134 |

The independently regenerated parameter-result hash is
`f95f27fe6ce601af688c1a40d3b23619d11374e0c4151d8c1a702d0c6a2160a9`,
identical to the committed frozen contract. H2 is on the capture-fraction
lower bound. H3 is interior, has rank 2, maximum absolute local parameter
correlation `0.744824`, and passes the bounded local screen. H4 is on its
formation-multiplier bound.

## Independent metrics and mechanism checks

H0 calibration and late predictions are strictly equal to the merged SB1
benchmark predictions. H1 changes only the inventory-to-concentration water
storage mapping and has no fitted parameter. H2 and H3 internal transfers are
activity-conservative at every reported run. H4 modifies only existing OBT
formation and turnover rates and its harvest OBT error is worse than H0.

Primary late metrics independently recomputed from point predictions:

| mechanism | log10 RMSE | log10 bias | median P/O | factor 2 | factor 10 |
|---|---:|---:|---:|---:|---:|
| H0 | 2.610972 | -2.567386 | 0.00198478 | 0 | 0 |
| H1 | 3.037855 | -2.983964 | 0.000742811 | 0 | 0 |
| H2 | 0.821221 | -0.337592 | 0.556390 | 0.333333 | 0.666667 |
| H3 | 1.118339 | -0.840530 | 0.172670 | 0.333333 | 0.666667 |
| H4 | 5.248745 | -5.016970 | 6.99664e-6 | 0 | 0 |

Frozen forcing-persistence counts independently recompute to H1 `0/7`, H2
`7/7`, H3 `4/7` and H4 `0/7`. H3 fails exactly `RUN_05`, `RUN_06` and
`RUN_07`, the low/mid/high background scenarios, because neither scenario may
be counted unless both late-improvement thresholds pass relative to the
corresponding H0 scenario.

All 35 mechanism-forcing runs are finite, nonnegative and pass the frozen
mass-balance criteria. Maximum internal-transfer residuals are
`9.285941e-10 Bq m-2` for H2 and `9.242740e-10 Bq m-2` for H3. Maximum formal
mass-closure residual is `1.862645e-9 Bq m-2`.

Two adversarial summaries were tested. Changing the reported H3 forcing count
from 4 to 5 is rejected by recomputation from per-scenario predictions.
Changing the reported H2 boundary flag to false is rejected by the frozen grid
coordinates. Therefore selection is fail-closed on detailed evidence rather
than trusting summaries.

## Regression

The review adds 24 independent tests. The first full-repository attempt
correctly exposed a missing ignored `outputs/calibration_grid.csv` from the
earlier SB1 review. The review regenerated that 49-point auxiliary grid from
the rebuilt forcing rather than copying it. The final isolated run passed all
435 tests with the one known NumPy/netCDF ABI warning.

V1 recomputation, V2 recomputation, V2 validation readiness, V3 deterministic
compatibility, V3 architecture readiness, external-evidence fail-closed
verification, the V3 physics-start gate, byte-compilation and Git diff checks
all pass.

```text
INDEPENDENT_TEST_STATUS = PASS_24
FULL_REGRESSION_STATUS =
PASS_435_ONE_KNOWN_NUMPY_NETCDF_WARNING
FORMAL_PHYSICS_CHANGE_COUNT = 0
FORMAL_CONFIG_CHANGE_COUNT = 0
TRUSTED_REGISTRY_CHANGE_COUNT = 0
```
