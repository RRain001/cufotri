# P2 R9 — KfK5194 Eq.(28)–(30) source-adjudication gate

**Disposition: SOURCE_LIMITED / PRODUCTION_COUPLING_BLOCKED / INDEPENDENT_REVIEW_NOT_RUN.** This is a decision packet for P0 #126 and P2 #128, not a corrected UFOTRI equation, an original-FORTRAN reconstruction, or a scientific approval. It updates the machine-readable `UF93-13.p2_r9_source_gate` registry without changing any numerical solver.

## Frozen primary-source identity

- W. Raskob, KfK 5194 (August 1993), §5.5.1, printed p.20 / PDF zero-based p.29, [KIT original PDF](https://publikationen.bibliothek.kit.edu/270034158/3813483).
- Locally inspected official PDF SHA256: `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5`. The PDF itself is private host evidence, not committed to this repository.
- The printed-page image was re-inspected in R9. R2 documents the transcription in [P2_R2_EQ28_30_PRIMARY_PDF_AUDIT.md](P2_R2_EQ28_30_PRIMARY_PDF_AUDIT.md); R8 independently tests two *hypothetical* Eq.(28)/(30) closures in [P2_R8_EQ28_EQ30_CONDITIONAL_CLOSURE.md](P2_R8_EQ28_EQ30_CONDITIONAL_CLOSURE.md).

## Independent decisions required before coupling

| ID | Source-visible fact | Unresolved decision / required evidence | Current disposition |
|---|---|---|---|
| A: Eq.(28) | The printed denominator uses `epsilon*k*I_abs`; Eq.(27) already defines `I_abs(L)=I_in*k*exp(-k*L)`. Eq.(28) subtracts `Rd` once, while integrating Eq.(26) over leaf depth subtracts `Rd*LAI`. | Decide whether to follow the literal print, the mathematical integral, or a separately documented manual-first correction. Provide a defensible leaf-vs-ground area basis, independent scientific review and numerical discriminants (LAI=0, LAI≠1, PAR=0). Original FORTRAN is needed only to claim historical executable parity. | `INCONSISTENT_TWO_TERMS` |
| B: Eq.(29) | The printed numerator is `0.158*CO*10^9*T*exp(-DeltaH1/(R*T))`. `CO` is labelled mg CO2 m^-2 h^-1, while Eq.(26) `P_m` is labelled g CO2 m^-2 h^-1. The constants are plant-specific. | Establish the empirical constant's unit convention, reference /39/, and any explicit mg-to-g normalization **before** using the raw result as Eq.(26) `P_m`. Do not assume that multiplying/dividing by 1000 is sufficient: the printed prefactor may already encode a calibration convention. | `NOT_ESTABLISHED` |
| C: Eq.(30) | `Rd=0.36*Pc+1.67e-4*W`, where `Pc` is CO2 assimilation per area per hour and `W` is plant biomass in g CO2 equivalents per m². | Determine the respiration leaf/ground-area basis relative to Eq.(26)/(28); establish a documented bridge from Table 1 dry matter to `W` and the evaluation/iteration order of `Pc` and `Rd`. R8 simultaneous fixed points are conditional arithmetic only. | `NOT_ESTABLISHED` |
| D: downstream | Eq.(31) uses a CO2-to-dry-matter factor `COA=1.5`; Eq.(33) uses `P_m` for *mean hourly dry matter production*, distinct from Eq.(26) maximum CO2 assimilation. Night transfer is empirical, not positive nighttime photosynthesis. | Keep the CO2-equivalent biomass and dry-matter states distinct, and require source-supported nighttime and crop-organ branch decisions before any HTO→OBT integration. | `NOT_ESTABLISHED` |

## Decision rules and evidence package

1. **Permitted now:** source-labelled R1–R8 isolated diagnostics, conditional synthetic budgets, independent numerical oracles, and a separately reviewed manual-first *proposal*. No automatic interpretation of ambiguous printed symbols.
2. **Blocked:** feeding raw Eq.(29) into Eq.(26); choosing either Eq.(28) branch as historically correct; using the R8 conditional closure as a validated production scheme; reusing dry matter as `W`; or connecting these to Eq.(31)/(33), TFWT/OBT inventories, CLI, or the frozen 1990 path.
3. **Minimum review packet:** original printed p.19–23 images and hash; unit table for leaf/ground area, CO2, CO2 equivalents, dry matter and time; explicit alternative equations and assumptions; discriminating LAI/PAR/night/crop tests; reviewer name, dated verdict, and exact commit SHA. For **original UFOTRI executable parity**, additionally require original FORTRAN/executable, compiler/runtime and same-input outputs.
4. **Release gate:** `UF93-13.p2_r9_source_gate.production_coupling_allowed=false`; P0 #126 and P2 #128 remain open; independent scientific review and original executable comparison are `NOT_RUN`. Scoped Docker software PASS does not override these blockers. Draft PR #159 must not be merged or marked `science-validated` / `merge-verified`.

**Scope:** documentation and machine-readable governance plus focused tests only. No `src/`, `configs/`, original PDF, 1990 default, physical thresholds, or production runtime changes.
