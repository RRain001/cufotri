# V2 physics remediation RC2 independent re-audit

Date: 2026-07-25
Repository: `/Users/rain/Documents/Doctor/Topic/CETAS_ufotri`
Audited branch: `codex/v2-physics-remediation-rc2`
Audited HEAD: `e74f96b01840b00f9d775d60d0e4a37012dbc105`

## 1. Executive summary

```text
RC2_INDEPENDENT_VERDICT = ACCEPT_RC2_WITH_MINOR_CORRECTIONS
```

RC2 genuinely resolves both HIGH findings from the RC1 independent re-audit.
The result does not rely on the RC2 status document or on the model's reported
combined residual:

- N-01: dry and wet plume losses were independently integrated, local surface
  activity was reconstructed as \(F_dA_d\Delta t\) and \(F_wA_w\Delta t\),
  and the ecological ledger was reconstructed from step inputs, final
  inventory, named boundaries, and decay. Seven independent
  \(A_d,A_w,A_{\rm eco}\) combinations close with a maximum global relative
  residual of \(2.1421\times10^{-16}\); dry and wet interface residuals are
  exactly zero.
- N-02: an independent 24-point
  \(T\times RH\times\alpha\) calculation reproduces the implemented
  saturated-water-vapour Eq. (27) value exactly. At 293.15 K and RH 60%, the
  manual-consistent equilibrium is \(7.8559851\times10^5\ {\rm Bq\,m^{-3}}\)
  and the net flux is \(642.5426\ {\rm Bq\,m^{-2}\,s^{-1}}\), not the RC1
  erroneous value near \(1584.29\).
- The repaired leaf analytic target is assigned before the tested leaf
  function is called. All ten analytic records are independent and pass.
- The perennial representation has a conserved root subinventory and a
  derived shoot inventory, with aggregate `plant_tfwt/plant_obt` as the total
  coordinate. A 50% cut removes 50% of shoots and retains roots. Actual
  365/366-day wrap-around progression, six unique cuts, root continuity, and
  spring shoot regrowth pass.
- Frozen V1 recomputation, V2 recomputation, 162 collected tests, byte
  compilation, and whitespace checks pass.

No BLOCKER or HIGH remains. Five carried research limitations remain MEDIUM.
Three LOW metadata/naming findings remain. The LOW corrections do not change
the physics or require another complete physical audit, but should be made
before merging or creating a candidate tag.

## 2. Audit baseline

```text
AUDIT_BASELINE_STATUS = PASS_EXACT_BRANCH_AND_HEAD
V1_TAG_INTEGRITY_STATUS = PASS_6918440FAA3455B848F43589784672F3BFABFE3D
INITIAL_WORKTREE_STATUS = PASS_ONLY_KNOWN_UNTRACKED_RC1_REPORT
RC2_DIFF_SCOPE_STATUS = PASS_BOUNDED_REMEDIATION_SCOPE
```

- repository root:
  `/Users/rain/Documents/Doctor/Topic/CETAS_ufotri`;
- branch: `codex/v2-physics-remediation-rc2`;
- HEAD: `e74f96b01840b00f9d775d60d0e4a37012dbc105`;
- RC1 HEAD: `aa6256a12a74dc8913773b0df3e8f30a6e7c7f06`;
- pre-remediation V2:
  `0075708b35baeb6f8b3b5574d5b735316d959097`;
- `main` and peeled `formal-minimal-baseline-v1`:
  `6918440faa3455b848f43589784672f3bfabfe3d`;
- initial worktree contained only the known untracked
  `docs/v2/v2_rc1_independent_reaudit.md`;
- `git diff --check` passed;
- tracked-name scanning found only `era5_key.example.txt` and the credential
  test, not a real credential;
- no raw ERA5, output directory, virtual environment, cache, or temporary
  audit result was added to Git.

RC2 relative to RC1 changes 27 paths: configuration and equation/status
documentation, the deposition activity contract, case coupling, leaf Eq. (27),
benchmark target construction, root/calendar state handling, acceptance
checks, and focused tests. This matches the declared remediation scope.

## 3. RC1 issue to RC2 change to independent evidence matrix

| Issue | RC1 conclusion | RC2 change | Main files/functions | Independent method | Independent conclusion |
|---|---|---|---|---|---|
| N-01 footprint/global accounting | HIGH | explicit dry/wet Bq components and independent ecological reference area | `deposition_activity_components`; `run_short_case` | 7 area combinations, 8 modes, raw step integration, 5 formal ledgers | `CONFIRMED_RESOLVED` |
| N-02 Eq. (27) | HIGH | saturated rather than ambient vapour density | `bidirectional_leaf_exchange` | 4 temperatures, 3 RH, 2 alpha values; independent resistance/flux calculation | `CONFIRMED_RESOLVED` |
| N-03 leaf benchmark | MEDIUM | handwritten resistance, Eq. (27), and analytic target | `_leaf_box_benchmark` | source/AST ordering plus independent numerical target | `CONFIRMED_RESOLVED` |
| N-04 root/calendar | MEDIUM | root subinventory, shoot-only cuts, actual year length | `State`; `_advance_root_component`; `season_fraction_at_time` | isolated cut, leap/non-leap wrap, two-year pasture | `CONFIRMED_RESOLVED` |
| N-05 test metadata | LOW | RC2 status avoids a stale numerical count | status/source scan and actual collection | actual count is 162; current implementation-status header is still RC1-oriented | `PARTIALLY_RESOLVED` |

## 4. RC2 diff and source trace

The activity path is:

```text
stack release
-> competing dry/wet plume loss
-> dry and wet SurfaceDepositionLedger
-> explicit dry/wet activity components
-> division by ecological_reference_area_m2
-> surface soil / plant / edible plant
-> animal / milk / beef where enabled
-> inventory, external boundary, and decay outputs
```

`SurfaceDepositionLedger.surface_input_bq_s` retains the plume loss as the
authoritative activity. `surface_flux_bq_m2_s` is only the local uniform
allocation over its own footprint. `DepositionActivityComponents` divides each
authoritative component by the ecological reference area for the downstream
areal box. Global inventories and boundaries are multiplied by that same
reference area. No remaining calculation sets an activity-accounting area to
the dry footprint or assumes \(A_d=A_w\).

The separate re-emission feedback area remains an atmospheric feedback
geometry; it is not used to reconstruct dry/wet ecological input.

## 5. N-01 independent dry/wet interface reconstruction

For each step, the audit independently calculated:

\[
Q_{d,\mathrm{loss}}=\sum_n\dot Q_{d,n}\Delta t,\qquad
Q_{w,\mathrm{loss}}=\sum_n\dot Q_{w,n}\Delta t,
\]

\[
Q_{d,\mathrm{surface}}=\sum_nF_{d,n}A_d\Delta t,\qquad
Q_{w,\mathrm{surface}}=\sum_nF_{w,n}A_w\Delta t.
\]

Across all seven area combinations:

```text
maximum dry interface relative residual = 0
maximum wet interface relative residual = 0
maximum combined interface relative residual = 0
```

The two-hour combined reference case transfers:

```text
dry activity = 7.33914242866339e9 Bq
wet activity = 3.5605026484867487e11 Bq
total activity = 3.6338940727733826e11 Bq
```

Changing either footprint from \(10^5\) through \(10^7\ {\rm m^2}\) leaves
these Bq values unchanged while its local footprint flux changes inversely
with area.

## 6. Three-area contract and unequal-footprint matrix

The audited combinations were:

| \(A_d\) (m2) | \(A_w\) (m2) | \(A_{\rm eco}\) (m2) | Total deposition (Bq) | Independent global relative residual |
|---:|---:|---:|---:|---:|
| \(10^6\) | \(10^6\) | \(10^6\) | \(3.633894073\times10^{11}\) | \(2.1421\times10^{-16}\) |
| \(10^6\) | \(10^5\) | \(10^6\) | same | \(2.1421\times10^{-16}\) |
| \(10^6\) | \(10^7\) | \(10^6\) | same | \(2.1421\times10^{-16}\) |
| \(10^5\) | \(10^6\) | \(10^6\) | same | \(2.1421\times10^{-16}\) |
| \(10^7\) | \(10^5\) | \(10^6\) | same | \(2.1421\times10^{-16}\) |
| \(10^6\) | \(10^5\) | \(10^5\) | same | \(1.6734\times10^{-17}\) |
| \(10^6\) | \(10^7\) | \(10^7\) | same | \(2.5257\times10^{-17}\) |

The reconstructed ecological input equals
\((Q_d+Q_w)\), and multiplication of the areal inventory, boundary, and decay
by \(A_{\rm eco}\) recovers the same global total. Changing
\(A_{\rm eco}\) changes per-area inventories and concentrations inversely but
does not create or destroy Bq.

Dry-only, wet-only, dry+wet, both-off, dry-off, wet-off, `vd=0`, and `rain=0`
cases also close. Disabled/zero pathways are exactly zero.

```text
N01_REAUDIT_STATUS = CONFIRMED_RESOLVED
DRY_INTERFACE_RELATIVE_RESIDUAL = 0
WET_INTERFACE_RELATIVE_RESIDUAL = 0
ECOLOGICAL_GLOBAL_RELATIVE_RESIDUAL = 2.1421235832565863E-16_MAX
UNEQUAL_FOOTPRINT_STATUS = PASS
REFERENCE_AREA_INVARIANCE_STATUS = PASS
```

## 7. Formal and end-to-end activity ledgers

The following values were rebuilt without using
`activity_relative_residual` as an expected value.

| Case | Stack input (Bq) | Dry loss/surface (Bq) | Wet loss/surface (Bq) | Ecological input (Bq) | Final global inventory (Bq) | Global boundary (Bq) | Decay (Bq) | Independent relative residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 72 h wet, 48 h ERA5 + 24 h extension | \(3.6000\times10^{12}\) | \(3.236040598\times10^9\) / same | \(2.763990574\times10^{10}\) / same | \(3.087594634\times10^{10}\) | \(1.730270885\times10^{10}\) | \(1.356244153\times10^{10}\) | \(1.079596278\times10^7\) | \(7.4130\times10^{-16}\) |
| crop ingestion | \(1.2096\times10^{15}\) | \(1.331929873\times10^{12}\) / same | 0 / 0 | \(1.331929873\times10^{12}\) | \(9.999135694\times10^{11}\) | \(3.311452706\times10^{11}\) | \(8.710329023\times10^8\) | \(1.8330\times10^{-16}\) |
| pasture milk | \(1.2096\times10^{15}\) | \(1.331929873\times10^{12}\) / same | 0 / 0 | \(1.331929873\times10^{12}\) | \(9.317987503\times10^{11}\) | \(3.993330640\times10^{11}\) | \(7.980586686\times10^8\) | \(3.6660\times10^{-16}\) |
| full adult dose | \(1.2096\times10^{15}\) | \(1.331929873\times10^{12}\) / same | 0 / 0 | \(1.331929873\times10^{12}\) | \(9.317986971\times10^{11}\) | \(3.993331172\times10^{11}\) | \(7.980586417\times10^8\) | \(3.6660\times10^{-16}\) |
| leaf food dose | \(2.5920\times10^{14}\) | 0 / 0 | 0 / 0 | \(3.467249821\times10^{11}\) leaf input | \(5.930389275\times10^{10}\) | \(2.874039782\times10^{11}\) | \(1.711113325\times10^7\) | 0 |

Named boundary diagnostics in the wet case include
\(7.535743946\times10^9\) Bq deep loss. Pasture/full-dose cases report
\(9.852812958\times10^6\) Bq milk and
\(4.031423822\times10^7\) Bq excretion. The full-dose case additionally
reports \(5.315570292\times10^4\) Bq consumed beef. Feed and
animal-to-product transfers cancel internally rather than appearing twice as
external inputs.

## 8. N-02 Eq. (27) hand calculation

The independent calculation used:

\[
e_{\rm sat}=610.78\exp\left[
\frac{17.2694(T-273.15)}{T-273.15+237.29}\right],
\quad
\rho_{v,\rm sat}=\frac{e_{\rm sat}}{461.5T},
\]

\[
C_{a,\rm eq}=C_{\rm plant}
\frac{\rho_{v,\rm sat}}{\alpha\rho_w}.
\]

For default \(\alpha=1.1\), \(C_{\rm plant}=5\times10^{10}\) Bq m-3 water:

| T (K) | \(C_{a,\rm eq}\) (Bq m-3), identical at RH 30/60/90% |
|---:|---:|
| 273.15 | 220236.4594 |
| 283.15 | 427131.5983 |
| 293.15 | 785598.5068 |
| 303.15 | 1378528.5278 |

The alternate \(\alpha=1.25\) grid also matched exactly. Maximum relative
error across all 24 combinations was zero at displayed floating-point
precision.

## 9. RH, VPD, resistance, and representative leaf flux

At 293.15 K, RH 60%, \(C_{\rm plant}=5\times10^{10}\) Bq m-3 water,
\(C_a=10^6\) Bq m-3 air, wind 2 m s-1, LAI 3, and the default geometry:

```text
saturated vapour density = 0.0172831671497 kg m-3
equilibrium air concentration = 785598.506802 Bq m-3
r_a = 64.5047733706 s m-1
r_b = 73.4861463396 s m-1
r_c = 195.685803937 s m-1
conductance = 0.00299691266765 m s-1
net leaf flux = 642.542550928 Bq m-2 s-1
```

The independently implemented values and production function values agree to
floating-point precision. At fixed temperature, changing RH from 30% to 90%
does not change the equilibrium term, but it changes VPD,
\(r_c\), conductance, and the net flux. Thus RC2 correctly separates the
equilibrium term from the conductance term.

```text
N02_REAUDIT_STATUS = CONFIRMED_RESOLVED
EQ27_SATURATED_DENSITY_STATUS = PASS
RH_EQUILIBRIUM_INDEPENDENCE_STATUS = PASS
RH_RESISTANCE_RESPONSE_STATUS = PASS
```

## 10. Formal leaf end-to-end path

With leaf exchange enabled:

```text
final plant TFWT = 56875.9530065 Bq m-2
final plant OBT = 1330.82122645 Bq m-2
final edible TFWT = 1079.94899636 Bq m-2
final edible OBT = 17.1695171503 Bq m-2
plant ingestion dose = 4.34629712971e-9 Sv
independent activity residual = 2.7151e-17
```

With leaf exchange off, every listed plant/edible endpoint and the plant
ingestion dose are exactly zero. The on-case activity propagates:

```text
air -> leaf TFWT -> plant OBT -> edible TFWT/OBT -> ingestion dose
```

```text
LEAF_END_TO_END_STATUS = PASS
LEAF_ACTIVITY_LEDGER_STATUS = PASS
```

## 11. Analytic benchmark independence

The leaf benchmark now constructs aerodynamic, boundary, and canopy
resistances, Eq. (27), the first-order rate, and
\(C(t)=C_{\rm eq}+(C_0-C_{\rm eq})e^{-kt}\) before the first call to
`bidirectional_leaf_exchange`. No tested-function result is used to construct
the target.

The leaf target is \(1.8469355203\times10^7\) Bq m-3; the independent-target
versus 0.1 s numerical integration relative difference is
\(5.2630\times10^{-6}\), within the declared \(5\times10^{-5}\) integration
tolerance.

Full suite classification:

```text
ANALYTIC_BENCHMARK_COUNT = 10
INDEPENDENT_ANALYTIC_COUNT = 10
SELF_REFERENTIAL_BENCHMARK_COUNT = 0
MANUAL_ANCHOR_COUNT = 5
LITERATURE_COMPARISON_COUNT = 2
PHYSICAL_INVARIANT_COUNT = 5
INTEGRATION_SCENARIO_COUNT = 9
REGRESSION_CASE_COUNT = 1
TOTAL_BENCHMARK_RECORD_COUNT = 32
N03_REAUDIT_STATUS = CONFIRMED_RESOLVED
```

## 12. Root/shoot inventory semantics and cuts

`State` uses total plant TFWT/OBT plus explicit root TFWT/OBT as the stored
coordinates; shoot TFWT/OBT is the exact non-negative difference. This is
mathematically equivalent to storing root and shoot directly while retaining
the old total fields as the aggregate compatibility interface. Positive
inputs are partitioned by `root_activity_fraction`; non-cut losses follow the
current root share. Root and aggregate are not added as separate inventories.

An isolated 50% cut starting from:

```text
TFWT: root 40, shoot 60 Bq m-2
OBT: root 20, shoot 30 Bq m-2
```

produced:

```text
TFWT: root 40 retained, shoot 30 retained, 30 cut
OBT: root 20 retained, shoot 15 retained, 15 cut
closure relative error = 0
```

Edible compartments and vegetative shoot inventories are distinct. A cut may
remove configured edible harvest and configured vegetative shoot activity at
the same event, but neither inventory is removed twice.

```text
ROOT_SHOOT_LEDGER_STATUS = PASS_TOTAL_PLUS_ROOT_COORDINATES
CUT_ROOT_RETENTION_STATUS = PASS
CUT_BOUNDARY_STATUS = PASS
```

## 13. Actual calendar and two-year pasture

For a wrap-around season DOY 300 to 60:

```text
2023-12-31 -> 2024-01-01 phase step = 1/125 = 0.008
2024-12-31 -> 2025-01-01 phase step = 1/126 = 0.00793650793651
2025-12-31 -> 2026-01-01 phase step = 1/125 = 0.008
```

Python's actual calendar supplies DOY 366 only in leap years. The transition
logic produces one event per date boundary; non-leap years cannot create a
DOY-366 event.

The formal two-year pasture case has six unique cuts. At 2025 year end:

```text
root TFWT = 9.34518930466 Bq m-2
root OBT = 0.931566957130 Bq m-2
LAI = 0.25
```

On 2026-05-15:

```text
root TFWT = 2.36858057160 Bq m-2
shoot TFWT = 0.687029652740 Bq m-2
LAI = 1.70777324883
```

The maximum step surface relative residual is
\(5.2666\times10^{-16}\), and the independently reconstructed two-year
surface ledger closes at \(2.6655\times10^{-16}\).

```text
N04_REAUDIT_STATUS = CONFIRMED_RESOLVED
ACTUAL_YEAR_LENGTH_STATUS = PASS
WRAPAROUND_CALENDAR_STATUS = PASS
MULTIYEAR_CONTINUITY_STATUS = PASS
```

## 14. Regression and new-problem scan

No evidence was found for:

- reference-area double scaling;
- dry/wet activity being added twice;
- Eq. (27) flux-sign inversion;
- removal of RH from VPD resistance;
- root plus aggregate double counting;
- cut/edible inventory double subtraction;
- root activity being presented as edible concentration;
- V1 default-mode changes;
- a benchmark relabelled without an independent target.

The following LOW issues remain:

| ID | Severity | Finding | Consequence |
|---|---|---|---|
| L-RC2-01 | LOW | end-to-end `provenance.json` records the merged-config hash and leaf mode but does not expose `ecological_reference_area_m2`, an Eq. (27) formula/version identifier, or `root_activity_fraction` as named fields | values remain recoverable from hashed configuration and result rows, but field-level auditability is weaker than requested |
| L-RC2-02 | LOW | `docs/implementation_status.md` still opens with RC1 branch/status and `PASS_158`; RC2 is appended without the actual 162-test count | current implementation-status metadata is not self-contained |
| L-CARRIED-01 | LOW | coupled `AnimalState` names ending `_bq` represent normalized Bq m-2 | arithmetic is consistent, but internal names remain misleading |

N-05 is therefore only partially resolved: RC2's own status does not claim an
incorrect test count, but the repository-wide implementation-status document
has not been promoted to a current RC2 header/count.

## 15. Remaining research limitations

Five carried MEDIUM limitations remain documented rather than newly introduced:

1. advanced re-emission omits the manual rain-start 3% rule and
   concentration-dependent DIFF detail;
2. three-box soil remains experimental standalone;
3. the 72 h wet case is 48 h ERA5 plus a deterministic dry 24 h extension;
4. continuous versus accident release duration remains scenario-specific;
5. crop, hydrology, footprint, animal, and intake parameters remain
   replaceable research-screening assumptions.

Wet parameters remain a literature comparison/project bracket rather than
site calibration; weak LHS ranks remain limited with evidence; the atmosphere
is steady Gaussian; chemistry is HTO-only. These are declared scope and
parameter limits, not RC2 regressions.

## 16. V1 regression

`.venv/bin/python scripts/verify_acceptance.py --recompute` passed all five
frozen cases:

- synthetic basic 48 h;
- ERA5 basic 48 h;
- advanced re-emission 24 h;
- runoff/rain HTO 1 h;
- calm wind 1 h.

V1 defaults remain wet off and leaf off. The new reference-area and root
coordinates do not alter the frozen V1 behavior. The V1 tag remains unchanged.

```text
V1_RECOMPUTE_STATUS = PASS_5_FROZEN_CASES
V1_COMPATIBILITY_STATUS = PASS
```

## 17. V2 recomputation and tests

`.venv/bin/python scripts/verify_v2_acceptance.py --recompute` passed:

- frozen V1 recomputation;
- wet, leaf, food, dose, and conservative beef paths;
- analytic LHS and full-model n=64/128/256 convergence with four seeds;
- the 12-case wet-parameter grid;
- RC2 unequal-footprint, Eq. (27), time-step, root/shoot, actual-calendar,
  and activity-protocol checks;
- 10 analytic, 5 manual, and 2 literature numeric records;
- six end-to-end cases and required temporary artifacts;
- temporary provenance and hashes.

Actual test collection and execution:

```text
TEST_STATUS = PASS_162_ONE_WARNING
```

All 162 tests passed. The single existing warning is the NumPy/NetCDF binary
compatibility warning in `tests/unit/test_era5_reader.py`.

```text
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END
COMPILE_STATUS = PASS_SRC_TESTS_ERA5_SCRIPTS
DIFF_CHECK_STATUS = PASS
```

## 18. Verdict, merge, and tag recommendation

The two former HIGH defects and the two associated MEDIUM implementation gaps
are physically resolved. No new BLOCKER or HIGH was found. The only new work
required is field-level provenance/current-status metadata, plus the carried
LOW naming issue if maintainers choose to address it.

Accordingly:

```text
MERGE_TO_MAIN_RECOMMENDATION = YES_AFTER_MINOR_DOC_PROVENANCE_CORRECTIONS
V2_TAG_RECOMMENDATION = YES_AFTER_MERGE_AND_LIGHTWEIGHT_REVERIFY
NEXT_STAGE_RECOMMENDATION = CORRECT_LOW_METADATA_THEN_MERGE_NO_FULL_REAUDIT
```

Do not merge or tag from this audit session. A focused review of the metadata
patch plus tests/acceptance rerun is sufficient; another complete physics
re-audit is not required unless model code or configuration semantics change.

## 19. Commands executed

```bash
pwd
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse main
git rev-parse formal-minimal-baseline-v1^{}
git log --oneline --decorate -25
git diff --check
git diff aa6256a12a74dc8913773b0df3e8f30a6e7c7f06...HEAD --stat
git diff aa6256a12a74dc8913773b0df3e8f30a6e7c7f06...HEAD --name-status
git ls-files | grep -Ei 'key|token|secret|credential|cdsapirc'
rg -n "activity_accounting_area|ecological_reference_area|dry_footprint|wet_footprint|dry_surface|wet_surface|surface_deposition|activity_component" src tests configs scripts
rg -n "rho_v|rho_v_sat|vapour_density|vapor_density|relative_humidity|equilibrium_air_concentration|Eq. \\(27\\)" src tests docs configs
.venv/bin/python audit_tmp/v2_rc2_independent_reaudit/independent_checks.py
.venv/bin/python -m pytest --collect-only -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_acceptance.py --recompute
.venv/bin/python scripts/verify_v2_acceptance.py --recompute
.venv/bin/python -m compileall -q src tests era5 scripts
git diff --check
```

The temporary independent diagnostic implemented plume/surface/ecological
integration, Eq. (27), resistance, benchmark-source, root/cut, calendar, and
formal-case calculations. It was not used to modify model code or
configuration.

## 20. Final status fields

```text
RC2_INDEPENDENT_VERDICT = ACCEPT_RC2_WITH_MINOR_CORRECTIONS
N01_REAUDIT_STATUS = CONFIRMED_RESOLVED
DRY_INTERFACE_STATUS = PASS_INDEPENDENT_RAW_INTEGRATION_ZERO_RESIDUAL
WET_INTERFACE_STATUS = PASS_INDEPENDENT_RAW_INTEGRATION_ZERO_RESIDUAL
UNEQUAL_FOOTPRINT_STATUS = PASS
ECOLOGICAL_REFERENCE_AREA_STATUS = PASS_GLOBAL_BQ_INVARIANT
GLOBAL_ACTIVITY_LEDGER_STATUS = PASS_MAX_RELATIVE_RESIDUAL_7.4130E-16_FORMAL
N02_REAUDIT_STATUS = CONFIRMED_RESOLVED
EQ27_STATUS = PASS_SATURATED_WATER_VAPOUR_DENSITY
RH_EQUILIBRIUM_STATUS = PASS_INDEPENDENT_OF_RH
LEAF_RESISTANCE_STATUS = PASS_RH_REMAINS_IN_VPD
LEAF_END_TO_END_STATUS = PASS_ON_NONZERO_OFF_ZERO
LEAF_BENCHMARK_STATUS = PASS_INDEPENDENT_TARGET
ANALYTIC_BENCHMARK_COUNT = 10
SELF_REFERENTIAL_BENCHMARK_COUNT = 0
ROOT_SHOOT_STATUS = PASS_TOTAL_PLUS_ROOT_CONSERVED_COORDINATES
CUT_BOUNDARY_STATUS = PASS_SHOOT_ONLY_ROOT_RETAINED
CALENDAR_STATUS = PASS_ACTUAL_365_366_DAY_YEARS
MULTIYEAR_STATUS = PASS_6_UNIQUE_CUTS_ROOT_CONTINUITY_REGROWTH
V1_REGRESSION_STATUS = PASS_5_FROZEN_CASES
V2_RECOMPUTE_STATUS = PASS_6_END_TO_END
TEST_STATUS = PASS_162_ONE_WARNING
BLOCKER_COUNT = 0
HIGH_COUNT = 0
MEDIUM_COUNT = 5
LOW_COUNT = 3
HIGHEST_SEVERITY = MEDIUM_DOCUMENTED_LIMITATION
MERGE_TO_MAIN_RECOMMENDATION = YES_AFTER_MINOR_DOC_PROVENANCE_CORRECTIONS
V2_TAG_RECOMMENDATION = YES_AFTER_MERGE_AND_LIGHTWEIGHT_REVERIFY
NEXT_STAGE_RECOMMENDATION = CORRECT_LOW_METADATA_THEN_MERGE_NO_FULL_REAUDIT
```
