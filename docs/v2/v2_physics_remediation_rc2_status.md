# V2 RC2 directed physics remediation status

```text
RC2_STATUS=FORMAL_UFOTRI_ENVIRONMENTAL_PATHWAYS_V2_CANDIDATE_READY
N01_FOOTPRINT_STATUS=PASS_EXPLICIT_DRY_WET_COMPONENTS
N02_LEAF_EQ27_STATUS=PASS_SATURATED_WATER_VAPOUR_DENSITY
BENCHMARK_STATUS=PASS_10_ANALYTIC_ALL_INDEPENDENT
PERENNIAL_STATUS=PASS_ROOT_SHOOT_AND_ACTUAL_CALENDAR
V1_STATUS=PASS_5_FROZEN_CASES
V2_STATUS=PASS_6_END_TO_END_CASES
TEST_STATUS=PASS
BLOCKER_COUNT=0
HIGH_COUNT=0
MERGE_RECOMMENDATION=HOLD_FOR_INDEPENDENT_REAUDIT
```

## Scope and baseline

- development branch: `codex/v2-physics-remediation-rc2`;
- RC1 source HEAD: `aa6256a12a74dc8913773b0df3e8f30a6e7c7f06`;
- frozen V1 baseline: `6918440faa3455b848f43589784672f3bfabfe3d`;
- HTO-only V2 scope is unchanged;
- no main merge, push, or tag is part of RC2.

## N-01 footprint contract

Dry and wet deposition retain independent local footprints and explicit
activity components:

\[
M_d=F_dA_d,\qquad M_w=F_wA_w,\qquad M_{\rm total}=M_d+M_w.
\]

The downstream areal ecology uses the configured
`ecological_reference_area_m2`; it receives each component activity divided by
that same reference area. Global inventories and boundaries are converted back
with the reference area. No equality between \(A_d\) and \(A_w\) is used.

Cases with \(A_w/A_d=0.1,1,10\) preserve dry/wet Bq, retain inverse-area local
flux scaling, and close
`input = inventory + boundary + decay` below \(10^{-12}\).

## N-02 UFOTRI Eq. (27)

The leaf equilibrium is:

\[
C_{a,eq}=C_{plant}\frac{\rho_{v,sat}}{\alpha\rho_w},
\qquad
\rho_{v,sat}=\frac{e_{sat}(T)}{R_vT}.
\]

At 293.15 K, RH 30%, 60%, and 90% give the same equilibrium concentration.
RH remains active in VPD-dependent canopy resistance. The formal leaf case
continues through HTO flux, TFWT, OBT, edible plant, and ingestion dose with
activity closure below \(10^{-12}\).

## Independent benchmark

`analytic_leaf_fixed_conductance_box` now uses handwritten neutral
aerodynamic, flat-plate boundary, canopy-resistance, Eq. (27), and first-order
solution calculations for its target. The expected value does not call the
leaf exchange module. The suite contains ten analytic benchmarks and requires
`independent=true` for every analytic record.

## Perennial root and calendar

Perennial TFWT and OBT expose root and shoot components. Positive plant inputs
use the provisional configured root activity fraction; non-cut losses follow
the current root share. Cuts remove shoot activity only and retain roots.
Annual crops retain zero root fraction compatibility.

Wrap-around growing seasons use the actual 365- or 366-day year. The two-year
pasture case retains roots across the year boundary, produces positive
second-spring shoots and regrowth LAI, executes six unique cuts, and closes
below \(10^{-12}\).

The root fraction, cutting schedule, footprint geometry, and ecological
reference area remain explicit provisional project assumptions, not
site-calibrated parameters.

## Verification

The required commands pass:

```text
pytest -q
python scripts/verify_acceptance.py --recompute
python scripts/verify_v2_acceptance.py --recompute
python -m compileall -q src tests era5 scripts
git diff --check
```

`verify_v2_acceptance.py` reports:

```text
PASS: V1 recompute acceptance
PASS: RC2 unequal-footprint, Eq. (27), root/shoot, actual-calendar,
      time-step, and activity-protocol checks
PASS: categorized V2 evidence (10 analytic, 5 manual, 2 literature)
PASS: six end-to-end cases and required artifacts recomputed
```

One pre-existing NumPy/NetCDF binary-compatibility warning remains in
`tests/unit/test_era5_reader.py`; it does not fail the suite.

RC2 stops at candidate-ready status. A new independent audit is required
before any merge or release decision.
