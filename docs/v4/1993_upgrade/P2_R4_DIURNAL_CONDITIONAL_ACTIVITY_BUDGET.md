# P2 R4 — Eq.(32) diurnal reference and conditional HTO→OBT budget

**Scope:** stand-alone opt-in numerical audit, **NOT** the full historical UFOTRI 4.0 physiology, OBT/soil/crop solver, executable-equivalence claim or production activity ledger. Draft PR #159; P0 #126/P2 #128 still OPEN.

## Printed primary authority and non-claims

KfK 5194 (August 1993), §5.5.2, **printed pp.22–23**, original official PDF [KIT 3813483](https://publikationen.bibliothek.kit.edu/270034158/3813483). Eq.(32) sets `T_act=T_m*fact1*fact2` with `T_m` a mean hourly transfer coefficient derived from a daily source value, `fact1` a Figure 11 growing-stage factor and `fact2=1.75` for day / `0.25` for night. The same section reports 12-hour daylight growing periods and explicitly acknowledges empirically approximated night OBT formation. Eq.(33) **does not supply an independently unambiguous advanced night-input algorithm**; R4 therefore *never* calls that mode.

The specific 1993 COMA daily coefficients and printed labels are **R3** source-pinned in `primary_source_transfer_tables_r3.yaml`; this new R4 **does not infer** rates from Eq.(26) canopy maximum CO₂ uptake or reuse historic KfK4605 defaults.

## 12+12-hour coefficient normalization

For a daily source rate `T_m,d` in d⁻¹, an explicit, externally supplied `fact1`, and day/night hours `H_d`, `H_n`, an Eq.(32)-style piecewise constant rate is

```text
k_j = (T_m,d / 24 hours) * fact1 * [1.75 if DAY else 0.25]
K_day = sum_j(k_j * duration_hours_j)
      = T_m,d * fact1 * (1.75*H_d + 0.25*H_n)/24
```

For **H_d=H_n=12 h**, the weighted diurnal factor is exactly `(12*1.75+12*0.25)/24 = 1`. Hence `K_day=T_m,d*fact1`, independently of how the 24 hours are partitioned into smaller explicit durations. For a sample **8 h daylight, 16 h night**, the factor is **0.75**. The R4 default rejects this non-12/12 case instead of silently renormalizing the empirical coefficients. An explicit research-only diagnostic opt-out can *calculate* 0.75 while reporting `historical_reference_matched=False`; it is **not** historical model approval for non-12/12 photoperiods.

Figure 11's true `fact1(t)` curve is still **NOT_RECONSTRUCTED**. R4 takes one explicitly supplied scalar `fact1` for the synthetic 24-hour test; `fact1=1` is a controlled case, not an inferred mature-crop profile. No dates, solar ephemeris, canopy/leaf/soil flux or radiation forcing are fabricated.

## Conservative *conditional* one-way operator

For test-only **isolated fixed areal** HTO and OBT source pools (`H,B`, both in **Bq/m² ground**), use

```text
F_j = H_j * (-expm1(-k_j*Delta_t_hours))   [Bq/m² ground]
H_(j+1) = H_j - F_j                        [Bq/m² ground]
B_(j+1) = B_j + F_j                        [Bq/m² ground]
Residual_j = H_(j+1)+B_(j+1)-H_j-B_j       [Bq/m² ground]
```

Both the signed-step and 24-hour telescoping residual must remain within numerical precision; in this **isolated one-way** operator the transferred activity cannot exceed initial HTO and the two pools remain nonnegative. The method is exact for its declared *piecewise constant first-order* hypothesis, so reducing a day or night segment to 6h, 3h, 1h or 0.5h must not change the end inventory. That invariance **does not prove** the actual atmospheric exchange, tritium incorporation/turnover kinetics, crop anatomy or source-code solve order.

Important exclusions: radioactive decay, outgoing OBT losses (even the distinct R3 documented parent OBT network), environmental inputs, roots, Belot exchange, growing mass, harvested compartments, HTO/OBT bound-organic activity conversion and tissue dilution **are absent**, not implicitly zero in the real 1993 model. For edible wheat/potato the R3 distinct zero-OBT-loss source statement remains a source-specific historical rule, but is **not activated** by R4.

## Preserved source-limited blockers

1. Eq.(28) printed vs direct-integral contradiction, Eq.(29) original mg/g bridge, Eq.(30) historic implicit convention: **not resolved**.
2. Eq.(33) advanced night transfer: **NOT_ESTABLISHED**; a positive quarter-daily empirical simple Eq.(32) night factor must not be passed off as a validated Eq.(33) light-dependent branch.
3. Table 1 crop *g per unspecified source unit* vs Eq.(31)/(33) ground-area-normalized photosynthesis: **not bridged**; printed tuber/seedling dry mass also exceeds corresponding whole-plant dry mass. R4 consumes areal HTO/OBT **activities** as explicit independent synthetic inputs and *does not derive them* from the disputed crop dry masses.
4. Full HTO+OBT coupling to plant, soil, food, cow, ingestion, harvest and radioactive decay requires separate physical contracts and evidence.
5. Independent science review, measured-data qualification and original 1993 FORTRAN numerical parity are **NOT_ESTABLISHED**. Software PASS cannot close those scientific gates.

## Implementation, tests and acceptance

- `src/cteas_ufotri/plant/kfk5194_1993_p2_r4_diurnal_budget.py`: explicit 1993 source profile + R3 pinned crop rate, research-hypothesis enum and 24h typed day/night partitions; rejects unknown crop/mode, incompatible provenance, absent intervals, nonfinite/negative numbers and invalid 12/12 normalization unless requested as an explicitly unqualified diagnostic. No production import.
- `tests/unit/test_ufotri_1993_p2_r4_diurnal_budget.py`: independent closed-form exact-solutions for all four crops, time-step refinement/segmentation and order tests, zero pool/factor and no-creation tests, 8/16 negative/conditional-path controls, wrong profile, invalid type, time and research-hypothesis rejection, no runtime import.
- Required to claim **software scoped PASS**: exact-head Ubuntu Python 3.11 Docker targeted regression, official smoke/full, GitHub protected integration and software-admission checks at unchanged PR head. Not equivalent to independent science acceptance. No production runtime/default changes.
