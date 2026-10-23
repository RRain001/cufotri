# P2 R8 — Eq.(28)/(30) conditional algebraic closure discrimination

**Status: SOURCE_LIMITED / NOT_ESTABLISHED.** This is a test-only mathematical audit, not a selection of the original 1993 UFOTRI 4.0 algorithm, an approved crop physiology closure, or an activation of the 1990/1993 runtime.

Primary source: W. Raskob, KfK 5194 (1993), §5.5.1, printed p.20 / PDF zero-based p.29, Eq.(26)–(30), official KIT PDF https://publikationen.bibliothek.kit.edu/270034158/3813483. The original PDF was previously inspected in `P2_R2_EQ28_30_PRIMARY_PDF_AUDIT.md` (SHA256 `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`). No original FORTRAN source/executable is available to identify the historical iteration or evaluation order.

## Two mutually unqualified alternatives

Let `A_print` and `A_integrated` denote the *respiration-free* results of the literal printed Eq.(28) and direct integration of Eq.(26)–(27), respectively. These already disagree due to the additional `k` in the printed Eq.(28) denominator. The literal printed equation subtracts `Rd` once; the leaf-depth integral subtracts `LAI*Rd`. Printed Eq.(30) states `Rd = 0.36*Pc + 1.67e-4*W`, with `W` in g CO2 equivalents/m², not raw dry matter.

**Only under the explicitly unverified assumption** that the Eq.(28) `Rd` and Eq.(30) `Rd` have compatible area bases, two hypothetical simultaneous closures would be:

```text
Pc_print = A_print - Rd
=> Pc_print = (A_print - 1.67e-4 W)/(1 + 0.36)

Pc_integrated = A_integrated - LAI*Rd
=> Pc_integrated = (A_integrated - LAI*1.67e-4 W)/(1 + 0.36*LAI)
```

Both are **conditional algebra**, not source-verified numerical schemes. Eq.(28) and Eq.(30) may in fact be evaluated in a historical sequence or iteration that these simultaneous solutions do not reproduce. A leaf-area vs ground-area respiration basis, the CO2-equivalent biomass conversion, Eq.(29) raw `CO` mg-to-`Pm` g bridge, and original time-stepping are unresolved. Consequently, **neither candidate may be used to drive Eq.(31)/(33), HTO→OBT, or the production solver**.

The new independent test calculates each candidate in closed form and by bisection on its own fixed-point residual, then compares the candidates. At LAI=0 and positive PAR, the literal branch retains a positive canopy rate even with W=0, whereas the direct leaf integral is zero. At zero light and positive W, both simultaneous closures may yield negative net `Pc`; this is a diagnostic, **not** a license to clamp to zero, invent nocturnal photosynthesis, or pass negative values to the existing Eq.(30) API. Test-only numerical agreement proves the conditional algebra, not physical validity.

## Scope and gate

- Added `tests/unit/test_ufotri_1993_p2_r8_eq28_eq30_closure_audit.py` only; no `src/`, `configs/`, model defaults, tolerances, external data, or CI logic changed.
- The 1990 baseline, Eq.(32) empirical opt-in, and R6/R7 synthetic triangular audit are untouched.
- P0 #126 source adjudication, independent expert review, original UFOTRI 4.0 execution, Eq.(29) dimensional reconstruction and real crop/area coupling remain **NOT_RUN/NOT_ESTABLISHED**.
- Draft PR #159 must remain unmerged; do not add `science-validated` or `merge-verified` based on these tests.
