# V2 physics remediation RC1 independent re-audit

Audit date: 2026-07-25

Audited branch: `codex/v2-physics-remediation-rc1`

Audited commit: `aa6256a12a74dc8913773b0df3e8f30a6e7c7f06`

Pre-remediation V2: `0075708b35baeb6f8b3b5574d5b735316d959097`

V1 baseline/tag commit: `6918440faa3455b848f43589784672f3bfabfe3d`

Auditor stance: independent, read-only physical review. The RC1 self-assessment
was read as a list of claims and was not used as evidence. Expected values were
reconstructed from raw step outputs, explicit equations, or hand arithmetic.

## 1. Executive summary

```text
RC1_INDEPENDENT_VERDICT = REJECT_RC1_REMEDIATION
```

RC1 has genuinely corrected B-01. Across the six formal V2 cases, independent
integration of raw per-step plume losses and independently reconstructed
surface receipt gives exact dry and wet interface equality. In the audited
72 h case:

```text
Q_dry,loss    = 3.2360405975097494e9 Bq
Q_dry,surface = 3.2360405975097494e9 Bq
R_d           = 0 Bq

Q_wet,loss    = 2.763990574195778e10 Bq
Q_wet,surface = 2.763990574195778e10 Bq
R_w           = 0 Bq
```

Segment refinement, pathway on/off controls, zero deposition velocity, zero
rain, and single-path footprint scaling all pass. The old independent
`v_d C_air A` surface-input path no longer participates in inventory updates.

The RC1 cannot, however, be reinstated as a formal V2 candidate because two
new/unresolved HIGH findings remain:

1. The model exposes independent dry and wet footprints but represents their
   combined deposition in one areal surface box and converts all ecological
   inventories with the dry footprint area. When the wet area is 0.1 or 10
   times the dry area, reported globally accounted activity is respectively
   8.688 times too high or 86.9% too low, while the built-in relative residual
   still reports about \(10^{-16}\). Formal cases hide this because both areas
   equal \(10^6\ {\rm m^2}\).
2. The leaf equilibrium term uses ambient actual water-vapour density
   \(RH\,\rho_{v,sat}\), whereas the UFOTRI manual Eq. (27) defines \(\rho\) as
   the water-vapour density in saturated air. At RH 60%, the implementation
   equilibrium-air concentration is 40% low. In a representative numerical
   check this changes net leaf uptake from the manual-consistent
   \(642.54\) to \(1584.29\ {\rm Bq\,m^{-2}\,s^{-1}}\), a factor 2.47.

The conservative beef-product boundary passes. Full-model LHS really reruns
the model and its dominant parameter is stable, but weak ranks remain
seed-sensitive as documented. One of the ten items labelled analytic
benchmarks is not independent because its target rate and equilibrium factor
are read from the leaf function under test. The two-year pasture case preserves
the aggregate plant state and six cuts, but it has no distinct root inventory
and does not test or correctly parameterize all non-leap/cross-year calendars.

## 2. Audit baseline

Stage 0 results:

```text
AUDIT_BASELINE_STATUS = PASS_EXACT_BRANCH_AND_HEAD
V1_TAG_INTEGRITY_STATUS = PASS_6918440FAA3455B848F43589784672F3BFABFE3D
INITIAL_WORKTREE_STATUS = CLEAN
```

- repository root:
  `/Users/rain/Documents/Doctor/Topic/CETAS_ufotri`;
- branch: `codex/v2-physics-remediation-rc1`;
- HEAD: `aa6256a12a74dc8913773b0df3e8f30a6e7c7f06`;
- `main`: `6918440faa3455b848f43589784672f3bfabfe3d`;
- `formal-minimal-baseline-v1^{}`:
  `6918440faa3455b848f43589784672f3bfabfe3d`;
- initial `git status --short`: empty;
- initial `git diff --check`: pass;
- no raw ERA5, generated outputs, virtual environment, cache, or real
  credential was found in tracked paths;
- name-only credential scanning found only the credential example/test paths.

The RC1 diff from pre-remediation V2 contains 63 changed paths and 4765
insertions. No model code, test, YAML, historical report, commit, branch, or tag
was changed by this audit.

## 3. Independent method

The review combined:

- source and configuration tracing from plume depletion through surface,
  plant, food, animal, product, dose, and boundary diagnostics;
- independent integration of raw step rates rather than trusting
  `dry_interface_residual` or `activity_relative_residual`;
- independent implementation of the leaf resistance equations and dimensional
  conversion;
- direct animal/product scenario construction without using formal acceptance
  outputs as targets;
- hand calculation of wet-scavenging rates, half-lives, and one-hour removal;
- source-level classification of every benchmark target;
- a separate ten-sample LHS write/config/output audit;
- independent reconstruction of three ecological ledgers;
- exact V1/V2 recomputation, test, and compilation commands.

Temporary scripts and JSON were placed only in
`audit_tmp/v2_rc1_independent_reaudit/` and were not added to Git.

## 4. Old issue to remediation to independent evidence matrix

| ID | Original issue | Remediation commit and implementation | Independent method | Independent result | Final status |
|---|---|---|---|---|---|
| B-01 | dry plume loss differed from surface input by 8.94x | `ecbccaa`; `surface_deposition_ledger`, `run_short_case`, `advance` | integrate raw loss and flux-area products in six cases and variants | exact dry/wet equality; no inventory use of `v_d C_air` | `CONFIRMED_RESOLVED` |
| H-01 | fixed \(r_a=r_b=50\ {\rm s\,m^{-1}}\) | `210ca68`; Golder/Monin \(r_a\), flat-plate \(r_b\), VPD/LAI \(r_c\) | independent 120-point wind/LAI/RH/day-night grid | wind and meteorology response pass; Eq. (27) saturation density does not | `PARTIALLY_RESOLVED` |
| H-02 | no independent analytic/manual numeric targets | `863f3d1`; `benchmarks/independent.py` | source trace every computed/target pair and hand recompute | 9 independent analytic, 5 manual, 2 literature; 1 self-referential leaf target | `PARTIALLY_RESOLVED` |
| H-03 | all formal end-to-end cases had leaf exchange off | `210ca68`; formal 72 h leaf-food-dose case | run on/off and rebuild leaf input/output | path is non-zero on and exactly zero off; physical equilibrium relation remains wrong | `PARTIALLY_RESOLVED` |
| H-04 | unbounded animal-body beef surrogate | `08327ec`; continuous herd turnover and `BeefProductState` | no/single/continuous production, high demand, no contamination, stop-production cases | transfer, storage, consumption, decay, and dose boundaries close | `CONFIRMED_RESOLVED` |
| H-05 | unsourced wet coefficient | `fdd630e`; named Japanet comparison and project brackets | source/label/unit inspection plus 60 hand combinations and 12 model reruns | correctly labelled comparison/bracket, not UFOTRI or site calibration | `CONFIRMED_RESOLVED` |
| H-06 | toy/small uncertainty exercise | `554c763`; mode-aware full-model LHS | rerun n=64/128/256, four seeds, inspect ten sample configs | full reruns and quantiles pass; only dominant rank stable | `DOCUMENTED_LIMITATION` |
| M-01 | incomplete advanced re-emission fidelity | documentation in RC1 | source/manual inspection | rain-start 3% and concentration-dependent DIFF remain excluded | `DOCUMENTED_LIMITATION` |
| M-02 | perennial state/reset failure | `03a5795`; perennial modes and partial cuts | two-year run, event/state/calendar source inspection | aggregate continuity/cuts pass; root state and calendar handling incomplete | `PARTIALLY_RESOLVED` |
| M-03 | three-box soil not formally coupled | `1427d94`; explicit standalone scope | config/source/test inspection | correctly documented standalone only | `DOCUMENTED_LIMITATION` |
| M-04 | 72 h forcing contains only 48 h ERA5 | documentation retained | inspect hybrid forcing and rerun | still 48 h ERA5 plus dry deterministic 24 h | `DOCUMENTED_LIMITATION` |
| M-05 | uniform area is uncalibrated and concentration-sensitive | `ecbccaa`; separate dry/wet footprint objects | independent pathway and unequal-area variants | single pathways scale correctly; combined unequal areas break global accounting | `NEW_REGRESSION` |
| M-06 | continuous versus accident release interpretation | provenance documentation | inspect all formal YAML | explicit but still a scenario assumption | `DOCUMENTED_LIMITATION` |
| M-07 | habits/crops/hydrology/animal inputs are project assumptions | provenance documentation | parameter-table/config inspection | correctly limited to research screening | `DOCUMENTED_LIMITATION` |

## 5. B-01 dry/wet interface reconstruction

For every time step \(n\), the independent calculation used:

\[
Q_{\mathrm{dry,loss}}=\sum_n
\dot Q_{\mathrm{dry,loss},n}\Delta t_n,
\qquad
Q_{\mathrm{dry,surface}}=\sum_n
F_{\mathrm{dry},n}A_{\mathrm{dry},n}\Delta t_n,
\]

\[
Q_{\mathrm{wet,loss}}=\sum_n
\dot Q_{\mathrm{wet,loss},n}\Delta t_n,
\qquad
Q_{\mathrm{wet,surface}}=\sum_n
F_{\mathrm{wet},n}A_{\mathrm{wet},n}\Delta t_n.
\]

No cumulative interface or residual column was used as the target.

| Formal case | Dry loss/surface (Bq) | Wet loss/surface (Bq) | Dry residual | Wet residual |
|---|---:|---:|---:|---:|
| 72 h ERA5 wet | \(3.236040598\times10^9\) / same | \(2.763990574\times10^{10}\) / same | 0 | 0 |
| accident plant OBT | \(3.908693272\times10^9\) / same | 0 / 0 | 0 | 0 |
| crop ingestion | \(1.331929873\times10^{12}\) / same | 0 / 0 | 0 | 0 |
| pasture milk | \(1.331929873\times10^{12}\) / same | 0 / 0 | 0 | 0 |
| full adult dose | \(1.331929873\times10^{12}\) / same | 0 / 0 | 0 | 0 |
| leaf-food-dose | 0 / 0 | 0 / 0 | 0 | 0 |

For segment counts 1, 2, 10, and 100, total dry and wet losses differ only at
about the \(10^{-15}\) relative floating-point level. Dry and wet losses share
the same remaining source and their sum is below stack input. `vd=0` gives zero
dry loss and `rain=0` gives zero wet loss.

For single-path dry-only and wet-only runs, area factors 0.1/1/10 preserve the
integrated Bq exactly and scale Bq m-2 s-1 by 10/1/0.1. Thus B-01 itself is
resolved.

```text
B01_REAUDIT_STATUS = CONFIRMED_RESOLVED
DRY_INTERFACE_RELATIVE_RESIDUAL = 0
WET_INTERFACE_RELATIVE_RESIDUAL = 0
SEGMENT_INVARIANCE_STATUS = PASS_FLOATING_POINT
```

## 6. Dry/wet competition and footprint behavior

The segment formulas correctly allocate loss by competing hazards:

\[
\Delta Q_d=\Delta Q\frac{\lambda_d}{\lambda_d+\lambda_w},
\qquad
\Delta Q_w=\Delta Q\frac{\lambda_w}{\lambda_d+\lambda_w}.
\]

The independent combined two-hour case gave:

```text
dry loss = 7.418325988e9 Bq
wet loss = 2.067035401e11 Bq
total fraction of stack input = 0.0297391481
```

However, a single areal state cannot simultaneously represent different dry
and wet footprints. `case.py` sets `activity_accounting_area_m2` to the dry
area, even though the surface box receives
\(F_d+F_w=Q_d/A_d+Q_w/A_w\). Independent variants demonstrate the failure:

| Wet area / dry area | True allocated deposition (Bq) | Reported accounted activity (Bq) | Relative error | Built-in residual |
|---:|---:|---:|---:|---:|
| 0.1 | \(4.140161323\times10^{11}\) | \(4.011067737\times10^{12}\) | +8.6882 | \(2.43\times10^{-16}\) |
| 1 | \(4.140161323\times10^{11}\) | \(4.140161323\times10^{11}\) | \(-2.95\times10^{-16}\) | \(3.38\times10^{-16}\) |
| 10 | \(4.140161323\times10^{11}\) | \(5.431097192\times10^{10}\) | -0.8688 | \(6.09\times10^{-17}\) |

This is not a local concentration sensitivity alone: it makes the reported
global Bq ledger wrong while its internal residual remains apparently exact.
The current formal cases pass only because \(A_d=A_w\).

```text
FOOTPRINT_INVARIANCE_STATUS = FAIL_COMBINED_UNEQUAL_FOOTPRINTS
```

## 7. Leaf resistance

The implementation units are dimensionally correct:

\[
[r_a]=[r_b]=[r_c]={\rm s\,m^{-1}},\qquad
[g_c]={\rm m\,s^{-1}}.
\]

An independently coded neutral-stability calculation at 293.15 K, RH 60%,
LAI 3, daytime, and the configured geometry reproduced the implementation to
a maximum relative error of \(1.63\times10^{-15}\).

| Wind (m s-1) | \(r_a\) (s m-1) | \(r_b\) (s m-1) | \(r_c\) (s m-1) | \(g_c\) (m s-1) | implementation half-life (h) |
|---:|---:|---:|---:|---:|---:|
| 0.5 | 258.019 | 146.972 | 195.686 | 0.00166479 | 6.134 |
| 1 | 129.010 | 103.925 | 195.686 | 0.00233307 | 4.377 |
| 2 | 64.505 | 73.486 | 195.686 | 0.00299691 | 3.408 |
| 5 | 25.802 | 46.477 | 195.686 | 0.00373184 | 2.736 |
| 10 | 12.901 | 32.864 | 195.686 | 0.00414163 | 2.466 |

LAI 0 gives exactly zero conductance and flux. At wind 2 m s-1 and RH 60%,
LAI 1/3/6 gives \(r_c=587.06/195.69/97.84\ {\rm s\,m^{-1}}\); LAI is not
multiplied a second time after conductance. Night increases \(r_c\) from
195.69 to 2935.29 s m-1 and lowers \(g_c\) from \(2.997\times10^{-3}\) to
\(3.254\times10^{-4}\ {\rm m\,s^{-1}}\). Raising VPD from the RH 90% to RH
30% condition raises \(r_c\) from 148.92 to 242.45 s m-1 and lowers
conductance.

The resistance response is therefore real and non-negative. It is correctly
labelled as a manual structure plus a Golder and flat-plate literature
parameterization, rather than an exact UFOTRI parameter set.

## 8. Air-water equilibrium and formal leaf path

The implemented form is structurally:

\[
C_{a,eq}=C_{p,w}\frac{\rho_v}{\alpha\rho_w}.
\]

It correctly avoids direct subtraction of liquid-water Bq m-3 from air
Bq m-3. The physical fidelity problem is the definition of \(\rho_v\).
UFOTRI manual Eq. (27) explicitly defines \(\rho\) as the weight of water
vapour in saturated air. The code instead uses:

\[
\rho_v=RH\frac{e_{sat}(T)}{R_vT}.
\]

At RH 60%, \(C_{p,w}=5\times10^{10}\ {\rm Bq\,m^{-3}}\), and 293.15 K:

```text
implementation C_a,eq = 4.713591e5 Bq m-3
manual-saturated C_a,eq = 7.855985e5 Bq m-3
implementation/manual ratio = 0.6
```

For \(C_a=10^6\ {\rm Bq\,m^{-3}}\), wind 2 m s-1, and LAI 3, the resulting
net uptake is 1584.29 rather than 642.54 Bq m-2 s-1. This is a model-physics
error in the newly formalized leaf pathway, not merely a missing citation.

The on/off end-to-end isolation itself works:

| Endpoint | leaf on | leaf off |
|---|---:|---:|
| integrated air-to-leaf (Bq m-2) | 397689.401 | 0 |
| final plant TFWT (Bq m-2) | 69957.592 | 0 |
| final plant OBT (Bq m-2) | 1553.845 | 0 |
| edible TFWT (Bq m-2) | 1252.267 | 0 |
| edible OBT (Bq m-2) | 19.501 | 0 |
| plant ingestion dose (Sv) | \(4.91656\times10^{-9}\) | 0 |

The leaf/ecological activity ledger closes at \(4.37\times10^{-16}\) or
better, so the issue is the equilibrium physics, not numerical conservation.

```text
H01_REAUDIT_STATUS = PARTIALLY_RESOLVED_EQ27_FIDELITY_FAIL
H03_REAUDIT_STATUS = PARTIALLY_RESOLVED_PATH_ACTIVE_PHYSICS_FAIL
LEAF_METEOROLOGY_RESPONSE_STATUS = PASS
LAI_DOUBLE_COUNT_STATUS = PASS_NO_DOUBLE_COUNT
LEAF_ACTIVITY_LEDGER_STATUS = PASS
```

## 9. Beef product and dose boundary

The formal mode is:

```text
continuous_herd_turnover
```

Independent boundary cases gave:

- no slaughter: zero product transfer and animal closure residual
  \(2.84\times10^{-14}\) Bq;
- single slaughter: 150 Bq removed from animal, 150 Bq entered product,
  zero animal remainder, zero product residual;
- high consumption: a 15 Bq/1 kg product inventory permitted exactly 15 Bq
  and 1 kg consumption, never more;
- production without consumption: 5 Bq/1 kg remained stored;
- after production stopped: 1.25 Bq/0.25 kg was consumed and 3.75 Bq/0.75 kg
  remained;
- uncontaminated production and consumption produced zero activity and dose;
- HTO and OBT are tracked separately.

The formal full-dose result is:

```text
animal slaughter transfer = 0.536039201392 Bq m-2
beef product input         = 0.536039201392 Bq m-2
consumed HTO/OBT           = 0.050779914944 / 0.002375787979 Bq m-2
stored HTO/OBT             = 0.452490515526 / 0.030129339561 Bq m-2
decay                      = 0.000263643381 Bq m-2
meat dose                  = 4.055286257e-9 Sv
```

The largest step product residual is \(1.11\times10^{-16}\ {\rm Bq\,m^{-2}}\);
the cumulative animal/product residual is \(4.53\times10^{-14}\ {\rm
Bq\,m^{-2}}\). No unlimited body-concentration food source remains in the
formal dose path.

```text
H04_REAUDIT_STATUS = CONFIRMED_RESOLVED
BEEF_PRODUCT_LEDGER_STATUS = PASS
MEAT_CONSUMPTION_LIMIT_STATUS = PASS
MEAT_DOSE_STATUS = PASS_PRODUCT_ACTIVITY_ONLY
```

## 10. Wet-scavenging parameters

The named research default is:

```text
iaea_emras_japanet_comparison
a = 5.0e-5
b = 0.8
P unit = mm h-1
status = LITERATURE_COMPARISON_NOT_UFOTRI
```

This is correctly kept separate from project low/central/high brackets and from
the dry/wet footprint assumptions. The 12 formal sensitivity cases each deep
copy configuration and call the complete model; their distinct soil, plant,
food, and dose outputs are not algebraic rescaling.

The table gives independent one-hour removal for all 12 \((a,b)\) combinations
at \(P=0.1,1,5,10,50\ {\rm mm\,h^{-1}}\). The final column is the half-life at
50 mm h-1.

| \(a\) | \(b\) | 0.1 | 1 | 5 | 10 | 50 | \(t_{1/2}\) at 50 (h) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1e-5 | 0.6 | 0.900% | 3.536% | 9.022% | 13.352% | 31.369% | 1.841 |
| 1e-5 | 0.8 | 0.569% | 3.536% | 12.231% | 20.319% | 56.095% | 0.842 |
| 1e-5 | 1.0 | 0.359% | 3.536% | 16.473% | 30.232% | 83.470% | 0.385 |
| 2e-5 | 0.6 | 1.792% | 6.947% | 17.230% | 24.922% | 52.898% | 0.921 |
| 2e-5 | 0.8 | 1.135% | 6.947% | 22.966% | 36.510% | 80.724% | 0.421 |
| 2e-5 | 1.0 | 0.717% | 6.947% | 30.232% | 51.325% | 97.268% | 0.193 |
| 5e-5 | 0.6 | 4.421% | 16.473% | 37.673% | 51.159% | 84.774% | 0.368 |
| 5e-5 | 0.8 | 2.812% | 16.473% | 47.915% | 67.881% | 98.369% | 0.168 |
| 5e-5 | 1.0 | 1.784% | 16.473% | 59.343% | 83.470% | 99.988% | 0.077 |
| 1e-4 | 0.6 | 8.646% | 30.232% | 61.153% | 76.145% | 97.682% | 0.184 |
| 1e-4 | 0.8 | 5.546% | 30.232% | 72.872% | 89.684% | 99.973% | 0.084 |
| 1e-4 | 1.0 | 3.536% | 30.232% | 83.470% | 97.268% | 99.999998% | 0.0385 |

The most aggressive bracket has a 2.31 minute half-life at 50 mm h-1 and
should be interpreted as an uncertainty stress bound. It is finite and does
not create an exact algebraic all-removal singularity.

```text
H05_REAUDIT_STATUS = CONFIRMED_RESOLVED
WET_PARAMETER_SOURCE_STATUS = PASS_LITERATURE_COMPARISON_PROJECT_BRACKET
WET_PARAMETER_RANGE_STATUS = PASS_WITH_EXTREME_BOUND_NOTE
WET_MAGNITUDE_STATUS = PASS_RECOMPUTED
```

## 11. Benchmark independence

The full suite labels 10 analytic, 5 manual, 2 literature, 5 physical-invariant,
9 integration-scenario, and 1 regression case. Numerical values pass their
declared tolerances.

Nine analytic targets are independently derived: wet exponential removal,
dry and wet competing-hazard allocation, re-emission first-order loss, animal
first-order production, one-day dose, one-year dose, water-to-fresh conversion,
and dry-to-fresh conversion.

`analytic_leaf_fixed_conductance_box` is not independent. It calls
`bidirectional_leaf_exchange` and reads both
`exchange.conductance_m_s` and
`exchange.equilibrium_air_concentration_bq_m3` to construct the expected
first-order rate and equilibrium. The subsequent one-second Euler loop only
checks integration against values supplied by the function under test. This
cannot validate leaf conductance or equilibrium and must not be counted as an
independent analytic leaf benchmark.

```text
H02_REAUDIT_STATUS = PARTIALLY_RESOLVED
ANALYTIC_BENCHMARK_COUNT = 9
MANUAL_ANCHOR_COUNT = 5
LITERATURE_COMPARISON_COUNT = 2
NONINDEPENDENT_BENCHMARK_COUNT = 1
```

## 12. Full-model uncertainty and H-06

The full-model audit used nine active parameters and recorded seven
`inactive_by_mode` parameters. A separate ten-sample inspection confirmed:

- each sample starts from a deep-copied configuration;
- all nine requested values equal the actual written configuration values;
- all ten model output triplets are distinct;
- outputs came from complete `run_short_case` calls, not post-processing
  scaling.

The complete convergence run made 1280 model calls:

| n | median total dose (Sv) | P5 | P95 | mean | std |
|---:|---:|---:|---:|---:|---:|
| 64 | \(1.063555\times10^{-6}\) | \(9.603673\times10^{-7}\) | \(1.169681\times10^{-6}\) | \(1.064443\times10^{-6}\) | \(6.883277\times10^{-8}\) |
| 128 | \(1.064500\times10^{-6}\) | \(9.581109\times10^{-7}\) | \(1.169720\times10^{-6}\) | \(1.064387\times10^{-6}\) | \(6.855467\times10^{-8}\) |
| 256 | \(1.064083\times10^{-6}\) | \(9.582806\times10^{-7}\) | \(1.170620\times10^{-6}\) | \(1.064405\times10^{-6}\) | \(6.841295\times10^{-8}\) |

The maximum n=128-to-256 statistic change is 0.2072%. Same-seed output is
bitwise reproducible. Adult HTO dose coefficient is the dominant parameter in
all four n=256 seeds. The minimum pairwise full-rank Spearman is 0.15 and
minimum top-three Jaccard is 0.2. At the 24 h horizon, inhalation and skin dose
dominate while milk/meat are about \(10^{-13}\) to \(10^{-14}\) Sv, so
non-dominant total-dose ranks are largely noise-sensitive.

The current narrow statement is acceptable: dominant parameter and quantiles
are stable; weak parameter order is not.

```text
H06_REAUDIT_STATUS = DOCUMENTED_LIMITATION
FULL_MODEL_RERUN_STATUS = PASS_1280_RUNS
QUANTILE_CONVERGENCE_STATUS = PASS_MAX_CHANGE_0.2072_PERCENT
DOMINANT_RANK_STABILITY_STATUS = PASS
WEAK_RANK_LIMITATION_STATUS = LIMITED_WITH_EVIDENCE_MIN_SPEARMAN_0.15
```

## 13. Perennial pasture and calendar behavior

The 2025-2026 run has exactly six unique cut events at DOY
150/220/290 in each year. Dormant LAI is 0.25. At 2025 year end, TFWT and OBT
remain 4.029408 and 0.806357 Bq m-2, and spring 2026 regrowth is non-zero. Final
cut/harvest boundaries match the recorded RC1 values and the maximum surface
closure residual is \(4.92\times10^{-16}\).

Two limitations prevent full Stage-8 confirmation:

1. There is no separate root inventory. A 50% cut removes 50% of the aggregate
   `plant_tfwt` and `plant_obt` pools, labelled as a whole-plant cut. Therefore
   the requested invariant “roots retained while only configured aboveground
   fraction is removed” cannot be demonstrated.
2. `_season_fraction` hard-codes 366 days for every wrap-around season. In a
   non-leap year, a season spanning DOY 300 to 60 advances from 65/126 on
   December 31 to 67/126 on January 1, skipping one day of phase. DOY 366
   events are impossible in non-leap years. The formal 2025-2026 pasture case
   has start < harvest and therefore does not exercise this defect or a leap
   year.

```text
PERENNIAL_REAUDIT_STATUS = PARTIALLY_RESOLVED
MULTIYEAR_CONTINUITY_STATUS = PASS_FORMAL_AGGREGATE_POOL
CUT_BOUNDARY_STATUS = PASS_AGGREGATE_ROOT_RETENTION_NOT_REPRESENTED
```

## 14. Activity propagation protocol

Three formal ledgers were reconstructed from raw deposition/leaf rates,
inventories, cumulative named boundary terms, and decay, without using the
reported activity residual as the target:

| Case | External ecological input (Bq) | Final inventory (Bq) | Boundary outputs (Bq) | Decay (Bq) | Independent relative residual |
|---|---:|---:|---:|---:|---:|
| 72 h wet | \(3.087594634\times10^{10}\) | \(1.730270885\times10^{10}\) | \(1.356244153\times10^{10}\) | \(1.079596278\times10^7\) | \(7.27\times10^{-16}\) |
| leaf-food-dose | \(3.976894006\times10^{11}\) | \(7.278320482\times10^{10}\) | \(3.248863667\times10^{11}\) | \(1.982914620\times10^7\) | \(3.05\times10^{-16}\) |
| full adult dose | \(1.331929873\times10^{12}\) | \(9.317986971\times10^{11}\) | \(3.993331172\times10^{11}\) | \(7.980586417\times10^8\) | \(4.19\times10^{-16}\) |

Each formal case is below its stack-input upper bound. Internal feed, slaughter,
OBT formation/turnover, and product storage are not double-counted as external
sources. The steady Gaussian air concentration is not treated as a dynamic
inventory.

This pass is conditional on equal dry and wet footprints. The independently
demonstrated unequal-footprint failure means the published global protocol is
not valid across the configuration interface it exposes.

```text
ACTIVITY_PROPAGATION_REAUDIT_STATUS = FAIL_CONFIGURED_UNEQUAL_FOOTPRINTS
GLOBAL_INTERFACE_STATUS = DRY_WET_PASS_EQUAL_AREAS_FAIL_UNEQUAL_AREAS
ECOLOGICAL_LEDGER_STATUS = PASS_FORMAL_CASES
ACTIVITY_UPPER_BOUND_STATUS = PASS_FORMAL_CASES
```

## 15. V1 regression and default modes

The exact V1 recomputation command passed all five frozen cases:

- synthetic basic 48 h;
- ERA5 basic 48 h;
- advanced re-emission 24 h;
- runoff/rain HTO 1 h;
- calm wind 1 h.

The V1 tag has not moved. Default wet scavenging is off, leaf exchange is off,
and V1 does not use the new beef-product boundary. V1 baseline compatibility
therefore passes.

```text
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V1_DEFAULT_MODE_STATUS = PASS
V1_COMPATIBILITY_STATUS = PASS
```

## 16. Formal tests and recomputation

Baseline and independent-diagnostic commands actually executed included:

```text
pwd
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse main
git rev-parse formal-minimal-baseline-v1^{}
git log --oneline --decorate -20
git diff --check
git diff 0075708b35baeb6f8b3b5574d5b735316d959097...HEAD --stat
git diff 0075708b35baeb6f8b3b5574d5b735316d959097...HEAD --name-status
git ls-files | rg -i 'key|token|secret|credential|cdsapirc'

.venv/bin/python audit_tmp/v2_rc1_independent_reaudit/independent_reaudit.py
.venv/bin/python scripts/run_v2_benchmarks.py \
  --output audit_tmp/v2_rc1_independent_reaudit/benchmarks.json
.venv/bin/python scripts/run_v2_uncertainty_convergence.py \
  --output audit_tmp/v2_rc1_independent_reaudit/lhs_convergence.json
.venv/bin/python -m pytest --collect-only -q
```

The independent script was an audit-only reconstruction of deposition,
leaf, beef, wet-magnitude, benchmark, LHS-sample, perennial, and global
activity checks. It and its JSON outputs were removed after their numerical
evidence was incorporated into this report.

Formal commands and results:

```text
.venv/bin/python -m pytest -q
  PASS: 150 collected/passed, 0 failed, 1 warning

.venv/bin/python scripts/verify_acceptance.py --recompute
  PASS: five V1 frozen cases and provenance

.venv/bin/python scripts/verify_v2_acceptance.py --recompute
  PASS: six end-to-end cases, wet/leaf/food/dose, beef, LHS,
        wet grid, activity protocol, footprint, time step,
        zero-source, internal transfer, two-year pasture,
        artifacts, provenance and hashes

.venv/bin/python -m compileall -q src tests era5 scripts
  PASS

git diff --check
  PASS
```

The warning is the existing NumPy/NetCDF binary-compatibility warning in
`tests/unit/test_era5_reader.py::test_netcdf_mapping`.

RC1 documentation states `PASS_158`, but current HEAD actually collects 150
tests. This is a LOW documentation/provenance mismatch; all 150 collected
tests pass.

## 17. New findings

| ID | Severity | Finding | Consequence |
|---|---|---|---|
| N-01 | HIGH | unequal dry/wet footprints make the global Bq ledger wrong while its residual reports closure | activity protocol is not valid across declared configuration |
| N-02 | HIGH | leaf Eq. (27) uses ambient actual rather than manual saturated water-vapour density | formal leaf flux and food dose use a physically different equilibrium |
| N-03 | MEDIUM | leaf analytic benchmark derives target rate/equilibrium from the function under test | independent analytic count is 9, not 10 |
| N-04 | MEDIUM | aggregate pasture has no root state and wrap-year phenology hard-codes 366 days | root retention and non-leap/leap behavior are not verified |
| N-05 | LOW | RC1 reports 158 tests but current HEAD collects 150 | verification metadata is stale |

Carried documented limitations remain M-01, M-03, M-04, M-06, and M-07.
The internal `AnimalState` `_bq` names continue to represent normalized
Bq m-2 in the coupled model; this is the carried LOW naming limitation.

Current severity accounting:

```text
BLOCKER = 0
HIGH = 2
MEDIUM = 7
LOW = 2
```

The MEDIUM count includes N-03, N-04, and the five carried documented
limitations. The LOW count includes N-05 and the carried animal-state naming
limitation.

## 18. Remaining limitations

- advanced re-emission omits the manual rain-start 3% and
  concentration-dependent DIFF detail;
- three-box soil remains experimental standalone;
- the wet 72 h case is 48 h ERA5 plus a dry 24 h deterministic extension;
- routine/accident source duration remains a scenario assumption;
- crop, hydrology, footprint, animal, and intake parameters remain research
  assumptions;
- wet parameters remain literature comparison/project brackets, not UFOTRI or
  site calibration;
- weak LHS ranks are not stable;
- atmosphere remains a steady Gaussian source/sink ledger;
- chemistry remains HTO-only.

These documented research limits could coexist with a candidate status. The
two HIGH findings cannot.

## 19. Merge and tag recommendation

Do not merge RC1 to `main` as the formal V2 candidate and do not create a V2
candidate tag. The next stage should be a bounded remediation of:

1. the dry/wet footprint geometry and global activity-accounting contract;
2. the Eq. (27) saturated-water-vapour equilibrium definition and affected
   leaf benchmarks/end-to-end evidence;
3. benchmark independence;
4. perennial root-boundary semantics and calendar handling.

After correction, rerun focused independent deposition, leaf, benchmark, and
perennial checks before a full acceptance rerun. This audit does not authorize
or perform those fixes.

## 20. Final status fields

```text
RC1_INDEPENDENT_VERDICT = REJECT_RC1_REMEDIATION
B01_REAUDIT_STATUS = CONFIRMED_RESOLVED
DRY_INTERFACE_STATUS = PASS_INDEPENDENT_RAW_INTEGRATION
WET_INTERFACE_STATUS = PASS_INDEPENDENT_RAW_INTEGRATION
DRY_WET_COMPETITION_STATUS = PASS
FOOTPRINT_INVARIANCE_STATUS = FAIL_COMBINED_UNEQUAL_FOOTPRINTS
LEAF_RESISTANCE_STATUS = PARTIAL_RESPONSE_PASS_EQ27_FIDELITY_FAIL
LEAF_END_TO_END_STATUS = PATH_ACTIVE_LEDGER_CLOSED_PHYSICAL_EQUILIBRIUM_FAIL
BEEF_BOUNDARY_STATUS = PASS_CONTINUOUS_HERD_TURNOVER
WET_PARAMETER_STATUS = PASS_LITERATURE_COMPARISON_PROJECT_BRACKET
BENCHMARK_INDEPENDENCE_STATUS = FAIL_ONE_NONINDEPENDENT_ANALYTIC_LABEL
FULL_MODEL_UNCERTAINTY_STATUS = PASS_FULL_MODEL_RERUN
RANK_STABILITY_STATUS = DOMINANT_PASS_WEAK_LIMITED_WITH_EVIDENCE
PERENNIAL_STATUS = PARTIAL_AGGREGATE_PASS_ROOT_CALENDAR_GAPS
ACTIVITY_PROPAGATION_STATUS = PASS_FORMAL_EQUAL_AREAS_FAIL_UNEQUAL_AREAS
V1_REGRESSION_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END
TEST_STATUS = PASS_150_ONE_WARNING
BLOCKER_COUNT = 0
HIGH_COUNT = 2
MEDIUM_COUNT = 7
LOW_COUNT = 2
HIGHEST_SEVERITY = HIGH
MERGE_TO_MAIN_RECOMMENDATION = NO
V2_TAG_RECOMMENDATION = NO
NEXT_STAGE_RECOMMENDATION = TARGETED_REMEDIATION_THEN_FOCUSED_REAUDIT
```
