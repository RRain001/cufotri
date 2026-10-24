# P2 R16 — Eq.(28)–(30) area/time/biomass closure, independent coupling discriminants

**Disposition: CONDITIONAL_UNIT_COHERENT_MATH_VALIDATED / ORIGINAL_UFOTRI_ALGORITHM_NOT_IDENTIFIED / NO_PRODUCTION_OBT_FEED / SCIENCE_NOT_RUN.**

## Primary document boundaries

- W. Raskob, KfK5194 (1993), §5.5.1 printed pp.19–21 / PDF0 pp.28–30, Eq.(26)–(31), official source: https://publikationen.bibliothek.kit.edu/270034158/3813483; source hash retained in R9/R13 `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`. Eq.(28) has an extra `k` on its denominator argument and only subtracts `Rd` once relative to literal leaf-depth integration of Eqs.(26)–(27) (R13). Original source/executable does not establish which was used at runtime.
- Mitchell, Lawlor & Young (1991), printed pp.7, 9, 12, 14, 15; user-supplied, visually inspected primary PDF SHA256 `d9f6f74b5268c6166407e02e98208dc452f9614002ccdb87a4d045cd4e0229e4` (R14/R15); `a=.36` and shoot `b=.004/day` at 10°C; paper's `W` as CO2-equivalent biomass, `k=30/44` dry matter per CO2 eq, and paper's fitting-time-averaged photosynthesis do **not** establish UFOTRI's solver update sequence.
- Eq.(29) maximum leaf assimilation `Pm` output units and published `CO`/temperature reference remain unbridged from Weir (1984) (R11). Eq.(33) also uses the symbol `P_m` for a **different** mean *dry matter rate*; never pass Eq.(29) raw Pm directly to Eq.(33).
- Existing isolated 1993 code `kfk5194_1993_photo_r2_audit.py` explicitly labels the printed/integral branches differently, and `kfk5194_1993_photo_obt_rates.py` accepts **externally supplied nonnegative** ground-area `Pc` for Eq.(31) and rate-only Eq.(33); neither is an approved coupled solver. R8's mixed-basis alternative is a useful **negative control**, not an area-certified implementation.

## Dimensional accounting (all below only where explicitly stated)

| Symbol | Hypothetical quantity and dimension | Status |
|---|---|---|
| `P_m` / `p(L)` | maximum/potential leaf CO2 flux, `g CO2 m_leaf^-2 h^-1` | printed manual description; Eq.(29) raw conversion incomplete |
| `I_abs(L)` | absorbed PAR per leaf area; `k I0 exp(-kL)`, L dimensionless m_leaf²/m_ground² | KfK5194 Eqs.(26–27) |
| `G_g` | respiration-free canopy photosynthesis `g CO2 m_ground^-2 h^-1` | **two divergent constructions**, Eq.(28) printed versus exact Eq.(26–27) integral |
| `P_g` | net canopy CO2 uptake per ground area and hour | ***hypothetical*** Eq.(28)/Eq.(30) same-hour joint closure |
| `R_g` | canopy respiration per ground area and hour | only if Eq.(30) shares `P_g`'s basis |
| `R_l` | respiration per leaf area and hour | needs an explicit LAI-dependent integration before comparison with `P_g` |
| `W_g` | canopy dry-matter CO2 equivalent `g CO2 eq m_ground^-2` | Mitchell Eq.(1) source basis; historical UFOTRI W inventory/area not independently confirmed |
| `M_dry,g` | canopy dry matter mass `g dry m_ground^-2` | Mitchell-specific conditional conversion `W_g=(44/30)*M_dry,g`; original UFOTRI fields not identified |
| `P_act,dry` | KfK5194 Eq.(31) **dry-matter production rate**, `g dry m_ground^-2 h^-1` | Eq.(31)'s separate printed factor `1.5` and explicit stomatal stress |

Crucial unit-direction distinction: **KfK5194 Eq.(31) multiplies a CO2 production flux by `1.5` to obtain dry matter** (thus its conversion direction is `g dry/g CO2`), whereas **Mitchell Eq.(3) uses `30/44≈0.681818` g dry per g CO2 equivalent**; its reciprocal `44/30` converts dry matter *to* CO2 equivalents (`g CO2eq/g dry`). Comparing `1.5` directly with `44/30` as if their units agreed is **dimensionally invalid**. Even on the nominal common `g dry/g CO2` orientation, `1.5` and `30/44` differ numerically (`1.5/(30/44)=2.2`) and belong to different source statements/roles. **Neither the ratio nor its difference establishes an actual model, flux, or dose bias.** Never substitute one into the other without a source-based state and dimension adjudication.

## Two dimensionally coherent but *unqualified* simultaneous hypotheses

Let `a=0.36` dimensionless and `b=1.67e-4 h^-1`, and choose a common nonnegative canopy-equivalent biomass `W_g`. At one specified instant, **only if** `R_g=a P_g+b W_g` uses the same ground-area/time basis as net `P_g`, and the canopy gross assimilation is `G_g` (either audited but still contested construction), a simultaneous candidate is:

```text
P_g = G_g - R_g
R_g = a*P_g + b*W_g
=> P_g = (G_g - b*W_g) / (1+a)
   R_g = (a*G_g + b*W_g) / (1+a)
   G_g - P_g - R_g = 0.
```

For an **independent leaf-uniform** representation at `LAI>0`, define `P_l=P_g/LAI` and `W_l=W_g/LAI`, and assume each leaf area slice has `R_l=a P_l+b W_l`. Then integrating all leaves gives `R_g=LAI*R_l=a P_g+b W_g`, **exactly the same ground-area candidate** for a chosen gross `G_g`. This is algebraic normalisation, **not a claim of uniformly distributed actual CO2 flux, leaf physiology or UFOTRI historical behavior**. At `LAI=0` the leaf-uniform quantities are undefined: do not divide or extrapolate a canopy with nonzero `W_g`. A missing/zero-LAI canopy must be handled by an independently defined physical branch.

**Explicitly prohibited mixed-basis shortcut:** putting the *same numeric ground-area* `P_g` and `W_g` into the per-leaf `R_l=a P_g+b W_g` and then multiplying it by LAI gives `P_g=(G_g-LAI*bW_g)/(1+LAI*a)`. Although this expression is mathematically solvable (R8's diagnostic scale), it has incompatible area dimensions unless extra explicit conversion assumptions are introduced. It is a **negative control**; do not promote it to a physical closure, replace the unit-coherent result, or feed it to Eq.(31)/Eq.(33).

## Historical evaluation time is another independent ambiguity

The simultaneous candidate above is not the only computation consistent with the *printed algebra*. Under a hypothetical **sequential explicit-lag** decision with an externally established prior driver `P_{g,t-1}`:

```text
R_{g,t} = a*P_{g,t-1} + b*W_{g,t}
P_{g,t} = G_{g,t} - R_{g,t}.
```

The sequential result is generally **not equal** to the simultaneous one, even with identical `G_t` and `W_t`, particularly under changing PAR. Mitchell's two-day regression covariate is not evidence that either hourly step-lag formula or a 48-hour rolling algorithm was used by the UFOTRI executable. No historical order, timestamp convention, temperature-update, soil/root coupling or night continuation is recovered here.

## L2 interfaces, guardrail cases and release constraints

1. **Synthetic daylight discriminants:** compare Eq.(28) printed versus independent integral, and two same-basis simultaneous solutions; require the budget identity `G=P+R`, cross-check against independently evaluated Eq.(30), and show a hypothetical mixed-area solution can disagree for LAI ≠ 1. Record provenance separately for each construction. No automatic selection.
2. **Boundary discriminants:** `LAI=0` invalidates `P_l=P_g/LAI`; printed Eq.(28) yields spurious positive gross flux at positive PAR; zero light with positive biomass gives signed negative `P_g`, which the existing Eq.(31) nonnegative external-input contract must reject instead of converting it to positive OBT production. No invented clipping, negative OBT formation, or nocturnal assimilation.
3. **Time discriminants:** distinguish prior-step from current-hour simultaneous `R` under changing incident PAR. The difference is mathematical evidence of underdetermination, not a source-verified actual lag.
4. **Independent HTO→OBT compartment budget stays separate:** use existing P2 R6/R7 source-labelled transfer rates and strict mass-conserving tests, but **do not inject conditional Eq.(28)/(30) candidate values as an approved Eq.(33) driver**. Eq.(31) `1.5` is separate from Mitchell `44/30`; Eq.(33) `P_m` is a mean dry-matter production denominator, not Eq.(29) leaf `P_m`.
5. **Release fail-closed:** R15 parameter overlap does not resolve Table 3/7 covariance or physiology; Eq.(29) calibration, Eq.(28) implementation branch, W and P area/time/temperature mapping, 1993 executable parity, SB1/SB4/ERA5, private D3 and independent scientific review all remain unqualified. No `src/`, `configs/`, CI required gates, 1990 default or production coupling changed.

**Acceptance category: audited mathematical/contract alternatives only, not a selected calibrated P2 physics solver.** PR #159 remains Draft/unmerged and must not be marked `science-validated` or `merge-verified`. Further physical acceptance requires an independent source-level decision and available original same-input evidence.
