# V2 physics remediation RC1 self-assessment

Assessment date: 2026-07-24

Assessed branch: `codex/v2-physics-remediation-rc1`

Assessed source HEAD before this report:
`12ca0d3ac2ec3ff39b3d777ff02a222be68c1bbb`

Independent-audit baseline:
`0075708b35baeb6f8b3b5574d5b735316d959097`

Frozen V1 baseline/tag:
`6918440faa3455b848f43589784672f3bfabfe3d`

## Verdict

```text
RC1_VERDICT = READY_FOR_INDEPENDENT_REAUDIT
B01_DRY_INTERFACE_STATUS = RESOLVED_PASS
H01_LEAF_RESISTANCE_STATUS = RESOLVED_PASS_LITERATURE_PARAMETERIZATION
H02_BENCHMARK_STATUS = RESOLVED_PASS_10_ANALYTIC_7_MANUAL_OR_LITERATURE
H03_LEAF_E2E_STATUS = RESOLVED_PASS
H04_BEEF_BOUNDARY_STATUS = RESOLVED_PASS
H05_WET_PARAMETER_STATUS = RESOLVED_PASS_DOCUMENTED_COMPARISON_AND_BRACKETS
H06_UNCERTAINTY_STATUS = PARTIALLY_RESOLVED_PASS_FULL_MODEL_RANK_LIMITED_WITH_EVIDENCE
PERENNIAL_STATUS = RESOLVED_PASS_TWO_YEAR
V1_REGRESSION_STATUS = PASS
ACTIVITY_PROPAGATION_STATUS = PASS
TEST_STATUS = PASS_158
RECOMPUTE_STATUS = PASS_V1_AND_V2
INDEPENDENT_REAUDIT_RECOMMENDATION = PROCEED_WITH_INDEPENDENT_REAUDIT_BEFORE_FORMAL_ACCEPTANCE
```

This is a self-assessment readiness decision, not independent acceptance.
Current formal status remains:

```text
V2_STATUS = PHYSICS_REMEDIATION_RC1_CANDIDATE
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
```

## Remediation commits

| Stage | Commit | Change |
|---:|---|---|
| 1 | `ecbccaa7ad1d243df1402a9abdc9a29410e60bd1` | unified dry/wet deposition activity ledger |
| 2 | `210ca681d3a770cde4f4c03f190fe54287143bfa` | meteorology-responsive leaf exchange and formal E2E |
| 3 | `08327ec81747c25eb5cd27874c791ac01ec16b74` | conservative beef product and dose boundary |
| 4 | `fdd630e601a0e2efed46360920c3b8dc4f2d0399` | named/bracketed wet parameters |
| 5 | `863f3d1e43ca25807a0216911418aad28bb59562` | independent analytic/manual benchmarks |
| 6 | `554c76395d878f318c3f65b3d25cbfb7fdcc13bf` | full-model mode-aware uncertainty |
| 7 | `03a57958d7a0a46d18fee1d96f3916f9c425d9da` | perennial and multiyear pasture |
| 8 | `1427d94e88920c1a87755457f0d83b32a74ff6df` | experimental multibox scope |
| 9 | `38c9f7655faadc6a98eb7582aefb330e1b122e56` | RC1 status and parameter registry |
| 10 | `12ca0d3ac2ec3ff39b3d777ff02a222be68c1bbb` | expanded activity protocol and verification |

## Numerical remediation evidence

### Dry/wet activity interface

The independent audit found:

```text
dry plume loss = 3.246027849313e9 Bq
dry surface input = 2.901284607250e10 Bq
surface/plume ratio = 8.937953529463
```

Immediately after repair, dry plume loss and surface input were both
`3.246027849313e9 Bq`, ratio 1.0. With the later named wet parameter set, the
current ERA5-plus-extension 72 h allocation is:

```text
dry plume loss = dry surface input = 3.236040597510e9 Bq
wet plume loss = wet surface input = 2.763990574196e10 Bq
dry ratio = 1.0
wet ratio = 1.0
activity relative residual = 5.76e-16
```

### Leaf resistance and formal leaf pathway

At wind 0.5/2/5 m s-1:

| Quantity | 0.5 | 2 | 5 |
|---|---:|---:|---:|
| aerodynamic resistance (s m-1) | 258.019093 | 64.504773 | 25.801909 |
| boundary resistance (s m-1) | 146.972293 | 73.486146 | 46.476720 |
| total conductance (m s-1) | 0.001722596 | 0.003189601 | 0.004035406 |

The formal 72 h air-leaf-food-dose case gives:

```text
plant TFWT = 69957.592224 Bq m-2
plant OBT = 1553.844624 Bq m-2
edible TFWT = 1252.267159 Bq m-2
edible OBT = 19.500811 Bq m-2
leafy TFWT = 2178.002515 Bq kg-1 fresh
leafy OBT = 33.916737 Bq kg-1 fresh
plant ingestion dose = 4.916564067e-9 Sv
mode-off plant ingestion dose = 0 Sv
```

The worst declared endpoint change between 600 and 60 s is below 1%.

### Beef product boundary

The current 14 d full adult case gives:

```text
stored beef HTO = 0.452490516 Bq m-2
stored beef OBT = 0.030129340 Bq m-2
produced beef HTO = 0.503521507 Bq m-2
consumed beef HTO = 0.050779915 Bq m-2
meat dose = 4.055286257e-9 Sv
combined activity relative residual = 7.68e-16
```

Consumption is limited by produced mass and activity; animal slaughter is an
internal transfer into product storage.

### Benchmark independence

```text
analytic_benchmark = 10
manual_anchor = 5
literature_comparison = 2
physical_invariant = 5
integration_scenario = 9
regression_case = 1
```

The analytic set covers wet exponential removal, competing dry/wet hazards,
leaf equilibrium, re-emission, animal production, one-day/one-year dose, and
food water/fresh/dry conversion. Execution scenarios are not labelled
reference cases.

### Full-model LHS

The real 24 h computational audit derived from `v2_full_adult_dose` samples
n=64/128/256 with primary seed `20260724`, then repeats n=256 with seeds
`20260725`, `20260726`, and `20260727`.

| n | median dose (Sv) | P5 (Sv) | P95 (Sv) | std (Sv) |
|---:|---:|---:|---:|---:|
| 64 | 1.063556e-6 | 9.603677e-7 | 1.169683e-6 | 6.883285e-8 |
| 128 | 1.064500e-6 | 9.581111e-7 | 1.169726e-6 | 6.855520e-8 |
| 256 | 1.064083e-6 | 9.582832e-7 | 1.170620e-6 | 6.841301e-8 |

The largest n=128-to-256 statistic change is 0.208%. All 1280 model runs are
counted, same-seed output is exact, and inactive parameters are excluded with
`inactive_by_mode`. Adult HTO coefficient ranks first under all four seeds.
The remaining weak-parameter order has minimum pairwise Spearman 0.15, so rank
stability remains `LIMITED_WITH_EVIDENCE`.

### Two-year pasture

The 2025-2026 case has six unique 50% cuts, dormant LAI 0.25, and maximum LAI
4.0. At 2025 year end, plant TFWT/OBT remain 4.029408/0.806357 Bq m-2; on
15 May 2026 LAI has regrown to 1.707773. Final boundaries are:

```text
edible harvested HTO = 1012.312962 Bq m-2
edible harvested OBT = 173.519677 Bq m-2
cut whole-plant HTO = 188.488361 Bq m-2
cut whole-plant OBT = 37.719512 Bq m-2
maximum surface closure residual = 4.9241e-16
```

## Verification

The exact Stage 10 command set passed:

```text
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python -m compileall -q src tests era5 scripts
git diff --check
```

Results: 158 tests passed; frozen V1 recomputation passed; expanded V2
recomputation passed; six end-to-end cases, the two-year pasture case, ten
analytic benchmarks, 12 wet-parameter combinations, four leaf time steps,
footprint scaling, zero-source, internal-transfer, and activity-upper-bound
checks passed. One known NumPy/NetCDF binary-compatibility warning remains.

## Remaining limitations

- H-06 is only partially resolved: quantiles converge, but low-influence
  Spearman ranks are seed-sensitive.
- Advanced re-emission still omits the manual rain-start 3% rule and
  concentration-dependent DIFF detail.
- Wet parameters are a Japanet literature comparison plus project brackets,
  not an original UFOTRI or site calibration.
- Dry/wet footprints are uniform project assumptions; local concentration is
  area-sensitive.
- The wet 72 h forcing is 48 h observed ERA5 plus a dry 24 h deterministic
  extension.
- The three-box soil solver remains experimental standalone.
- Crop/yield, hydrology, animal, consumption, and receptor inputs remain
  research-screening assumptions.
- The atmosphere is a steady Gaussian source/sink ledger without dynamic air
  inventory or three-dimensional conservation.
- The chemistry remains HTO-only.

## Readiness rationale

B-01 is resolved and no blocker remains. H-01 through H-05 have direct
remediation evidence. H-06 now exercises the real model, excludes inactive
parameters, demonstrates sample-size/seed behaviour, and explicitly narrows its
remaining claim. A formal leaf pathway, conservative beef boundary,
independent analytic targets, V1/V2 recomputation, and clean pre-report worktree
were all demonstrated.

Therefore:

```text
RC1_VERDICT = READY_FOR_INDEPENDENT_REAUDIT
FORMAL_ACCEPTANCE = PENDING_INDEPENDENT_REAUDIT
```
