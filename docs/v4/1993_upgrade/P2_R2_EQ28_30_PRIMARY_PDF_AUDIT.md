# P2 R2 — KfK5194 (1993) printed Eq.(28)–(30) and source discrepancy audit

**Status: SOURCE-LIMITED mathematical diagnostic, not the original UFOTRI 4.0 implementation.**

Authoritative edition: W. Raskob, *Description of the New Version 4.0 of the Tritium Model UFOTRI Including User Guide*, KfK 5194, August 1993, §5.5.1 **printed p.20**, official URL https://publikationen.bibliothek.kit.edu/270034158/3813483, **PDF zero-based page 29**. Actual original PDF inspected with rendered page image, rather than relying solely on incomplete equation text extraction. Original PDF SHA256: `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`. PDF is not vendored to the repository.

## Eq.(28) — printed form vs mathematical integral

The printed page gives:

```text
Pc_print = Pm/k * ln[(Pm + epsilon*k*I_in) / (Pm + epsilon*k*I_abs)] - Rd
```

while its Eq.(27) separately defines `I_abs(L) = I_in*k*exp(-k L)`, `L` running from 0 to LAI, and Eq.(26) gives the single-leaf net rate

```text
P_pot(L) = Pm*[epsilon*I_abs(L)]/[Pm + epsilon*I_abs(L)] - Rd
```

Direct integration of **those two explicitly printed equations** over the leaf-area depth gives:

```text
Pc_integrated = Pm/k * ln[(Pm + epsilon*k*I_in) /
                         (Pm + epsilon*I_abs(LAI))] - Rd*LAI
```

Two independently identifiable differences:

1. The printed Eq.(28) denominator has `epsilon*k*I_abs`, whereas calculus on Eq.(26)–(27) gives `epsilon*I_abs` (Eq.(27) already includes `k`). The source is not presumed typo-free.
2. The printed Eq.(28) subtracts `Rd` once; calculus of the leaf-area distributed respiration term in Eq.(26) subtracts `Rd*LAI`.

Discriminating limiting case: at `LAI=0`, `Rd=0`, the mathematical leaf integral is exactly **0**, while the literal printed expression can be **strictly positive** if `k!=1` and incident PAR is positive. At zero incident PAR and nonzero `Rd`, the printed expression is `-Rd` while the integrated expression is `-Rd*LAI`. Thus the two cannot be silently treated as equivalent by a unit change or an adjusted threshold.

**R2 policy:** `audit_kfk5194_1993_eq28_canopy` returns and labels both diagnostics with their difference and a fail-closed `FORMULAE_NOT_EQUIVALENT_DO_NOT_AUTO_SELECT` disposition. Neither is automatically passed into the Eq.(31) or Eq.(33) production route. This **does not** prove which formula the 1993 FORTRAN actually executed; original executable and independent source validation are still absent.

## Eq.(29) — temperature dependence with unresolved unit bridge

The printed Eq.(29) is:

```text
Pm_raw = [0.158 * CO * 10^9 * T * exp(-DeltaH1/(R*T))]
         / [1 + exp(-DeltaH2/(R*T)) * exp(-DeltaS/R)]
```

The printed source labels `CO` as **mg CO₂ m⁻² h⁻¹** and Eq.(26) `Pm` as **g CO₂ m⁻² h⁻¹**; `DeltaH1/2` in cal/mol, `DeltaS` in cal/(K mol), `R` in cal/(K mol), `T` in Kelvin. Both `CO` and thermochemical constants are plant specific. No source numeric values or universal gas constant are silently injected. The printed `0.158*10^9` is transcribed unchanged; without original code or dimensional reconstruction, `Pm_raw` is intentionally **unconverted** and **prohibited as a qualified Eq.(26) Pm input**.

The implementation evaluates the positive exponential ratio using a log-space stable denominator to avoid overflow; direct-arithmetic independent oracles and stress tests audit this expression. It does **not** propose a Celsius/Kelvin heuristic or crop-specific coefficient values.

## Eq.(30) — respiration with a distinct CO₂-equivalent pool

The printed equation is:

```text
Rd = C1_Rd*Pc + C2_Rd*W
C1_Rd = 0.36
C2_Rd = 1.67e-4 g CO2/h per g CO2 equivalent
```

`Pc` is in g CO₂ m⁻² h⁻¹; `W` is **accumulated plant biomass expressed in g CO₂ equivalents per m²**, **not directly the plant dry matter in g** from Table 1. It is not safe to reuse the same `W` that appears in generic dry-matter crop states without a documented conversion.

Eq.(28) uses `Pc` after subtracting `Rd`, while Eq.(30) itself makes `Rd` depend on `Pc`. This implies an algebraic/iteration relation. The historical code's fixed-point/order convention is **not** known; `audit_kfk5194_1993_eq30_respiration` evaluates the isolated source expression for explicitly supplied nonnegative `Pc` and `W`, **not** a silently fabricated coupled time integrator.

## Implemented R2 and independent tests

- `src/cteas_ufotri/plant/kfk5194_1993_photo_r2_audit.py` provides isolated, typed, externally selectable Eq.(28) discrepancy, raw Eq.(29) and isolated Eq.(30) diagnostics. Must explicitly select immutable `KFK5194_1993_V4` profile. No import into the CLI, legacy 1990 OBT, TFWT or foodchain production modules.
- `tests/unit/test_ufotri_1993_p2_r2_eq28_30_audit.py` independently calculates printed Eq.(28), the exact integral, an explicit midpoint quadrature of Eq.(26)–(27), zero-LAI/zero-PAR discriminants, Eq.(29) raw transcription with numerical stability and Eq.(30) source coefficient/mass basis. Invalid units/source versions and nonfinite inputs fail closed.
- This R2 is deliberately **not** Eq.(28) acceptance, plant-scale canopy parameter calibration, photosynthetic field validation, OBT activity transfer, original-executable equivalence, or independent scientific sign-off. P0 #126 and P2 #128 remain OPEN. Draft PR #159 is **not mergeable scientifically**, even if its software CI passes.

## Next source decision before a production integrator

Request independent review of the Eq.(28) two-factor discrepancy, Eq.(29) raw mg/g unit bridge and the Eq.(28)/(30) coupled numerical convention, using the *printed page image and original FORTRAN if available*. Until clarified, the only source-grounded automated output here is a diagnostic with explicit `NOT_ESTABLISHED` tags, not a closed canopy/OBT physics solver.
