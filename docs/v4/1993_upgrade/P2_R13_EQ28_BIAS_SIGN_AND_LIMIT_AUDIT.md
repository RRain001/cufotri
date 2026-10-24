# P2 R13 — Eq.(28) exact discrepancy, asymptotic bounds and respiration-dependent sign

**Result: CONDITIONAL_MATHEMATICAL_PROOF / SOURCE_INCONSISTENCY_CONFIRMED / ORIGINAL_UFOTRI_PARITY_NOT_ESTABLISHED / PRODUCTION_COUPLING_BLOCKED.**

This packet is a symbolic/numerical consequence of the *visible* KfK 5194 (1993) Eq.(26)–(28), **not** a correction adopted by the original UFOTRI executable. It extends R2/R8/R9 and does not resolve the historical implementation choice, Eq.(29) conversion, Eq.(30) area/bio-equivalent normalization, or independent scientific review.

## Primary printed evidence

W. Raskob, *Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide*, KfK-5194, August 1993, §5.5.1 printed pp.19–20 / PDF pages zero-based 28–29, public KIT source: https://publikationen.bibliothek.kit.edu/270034158/3813483 . Primary PDF SHA256 **previously fixed and locally checked**: `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`. In R13, the same official PDF pages were visually re-inspected from the primary institutional URL (not a new PDF checksum claim).

Eq.(26): `P_pot(L)=Pm * eps * I_abs(L)/(Pm+eps*I_abs(L)) - Rd`.
Eq.(27): `I_abs(L)=k*I0*exp(-k*L)`, for `L in [0,LAI]` and printed `k=0.6`.
Printed Eq.(28): `Pc_print=(Pm/k)*ln((Pm+eps*k*I0)/(Pm+eps*k*I_abs(LAI))) - Rd`.
Exact calculus of Eq.(26)–(27): `Pc_integral=(Pm/k)*ln((Pm+eps*k*I0)/(Pm+eps*I_abs(LAI))) - LAI*Rd`.

The Eq.(28) lower logarithm argument therefore contains an *additional factor k*, and its single respiration subtraction is not the literal integral of the Eq.(26) respiration density unless an additional, still-unknown area/normalization convention was applied.

## New exact analytic discriminants, conditional on a common Pm/eps/k/Rd area basis

Let `G_print` and `G_integral` be the expressions without `Rd`; define `X=eps*I_abs(LAI)>0` and assume finite `Pm>0`, `eps>0`, `I0>0`, `LAI>=0`, `0<k<1`.

The *exact* light-only discrepancy, with identical incident radiation and bottom-of-canopy absorbed radiation, is

```text
D = G_print - G_integral
  = (Pm/k) * ln[(Pm + X)/(Pm + k*X)] > 0 .
```

It obeys the rigorous finite bound `0 < D < (Pm/k)*ln(1/k)`, with `D->0` as `I0->0` and `D->(Pm/k)*ln(1/k)` as `I0->infinity` at any fixed finite LAI. Because `X` already includes `eps`, the derivative with respect to `X` is:

```text
dD/dX = (Pm/k) * Pm*(1-k)/[(Pm+X)*(Pm+k*X)] > 0.
```

Thus for fixed incident radiation the discrepancy **decreases** as LAI increases (`I_abs(LAI)=k*I0*exp(-k*LAI)`). It is largest at LAI=0. The printed light term at LAI=0 is nonzero for k<1, whereas the true integral is necessarily zero; this is a mathematical inconsistency, not a measured bio-physical response.

The low-light slopes (`I0->0`) are

```text
G_integral / I0 -> eps*(1-exp(-k*LAI))
G_print    / I0 -> eps*(1-k*exp(-k*LAI))
D          / I0 -> eps*(1-k)*exp(-k*LAI).
```

At high light (`I0->infinity`), `G_integral -> Pm*LAI` but `G_print -> Pm*LAI - (Pm/k)*ln(k)`. This yields a finite *spurious positive offset* even at saturating incident PAR if the equations share the same definitions.

**Important correction to a blanket overprediction claim:** including the printed `-Rd` vs integral `-LAI*Rd` gives

```text
Pc_print - Pc_integral = D + (LAI-1)*Rd.
```

For `LAI>=1` and `Rd>=0`, the **conditional** print-minus-integral net difference stays positive (strictly if PAR>0 and k<1). For `0<=LAI<1`, its sign can reverse at `Rd_star=D/(1-LAI)`. Thus the printed result is **not** unconditionally larger for *net* assimilation; the area basis and historical evaluation of `Rd` are still unknown. This sign comparison treats `Rd` as the *same externally supplied numerical density* in both hypothetical expressions, **not** as a source-verified Eq.(30) closure.

These deductions provide falsifiable discriminants for independent reviewers; **they do not identify the FORTRAN branch actually used** or justify changing formulas, clamps, extinction `k`, units, `Rd`, the original 1990 default, or OBT coupling.

## Independent numerical audit and acceptance boundary

The source-only R13 test checks a quadrature oracle against `G_integral`, exact discrepancy expression and bound, low/high-light limits, zero-LAI, LAI monotonicity and the `LAI<1` respiration sign reversal. Synthetic dimensional inputs in these tests are mathematical examples only; no experimental data, crop constants or original program outputs are claimed. The registry must keep `eq28_printed_vs_eq26_27_integral=INCONSISTENT_TWO_TERMS`, all `Eq.(29)/(30)` unit/area/solve-order bridges `NOT_ESTABLISHED`, and `production_coupling_allowed=false`. Independent science review `NOT_RUN`, original-executable parity `NOT_RUN`.

Source decision packet for P0 #126 and P2 #128; PR #159 stays Draft and unmerged. No `src/`, `configs/`, production solver, 1990 default, numerical thresholds or CI gate changed. Any future manual-first correction must separately document which convention it chooses and obtain independent scientific review; this R13 analytic demonstration is not such a choice.
