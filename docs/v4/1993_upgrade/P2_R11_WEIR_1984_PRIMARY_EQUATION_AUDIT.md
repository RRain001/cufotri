# P2 R11 — Weir (1984) primary-equation dimensional audit

**Disposition: WEIR_PRIMARY_PDF_VISUALLY_CHECKED / UFOTRI_EQ29_BRIDGE_NOT_ESTABLISHED / PRODUCTION_COUPLING_BLOCKED.** This supplements R9/R10 on P0 #126 and P2 #128. It is not a reproduction of the original UFOTRI executable, an empirical validation, or independent scientific approval.

## Original paper and reproducibility

- A. H. Weir, P. L. Bragg, J. R. Porter, J. H. Rayner (1984), *A winter wheat crop simulation model without water or nutrient limitations*, *Journal of Agricultural Science* 102(2), pp. 371–382. DOI: `10.1017/S0021859600042702`.
- Institutional full-text source (Rothamsted Research): https://repository.rothamsted.ac.uk/id/eprint/20642/1/Weir-1984-A-winter-wheat-crop-simulation-mode.pdf .
- Downloaded and inspected locally on 2026-10-24; PDF SHA256 `0558e6c38f9efb2d7fe9f3af1b862c096cfcd6c1e35619b233a09d39609d17e4`, 13 pages. Original article PDF is **not committed**. Page 374 = local PDF page 5 (zero-based 4); p.375 = PDF page 6 (zero-based 5). The page images for these two pages were visually checked against extracted text.
- Primary UFOTRI target remains KfK 5194 (1993) §5.5.1 printed p.20 / PDF zero-based 29, original source SHA256 `9a75292bc7289969db7175e17003c3dd777de72a30b52993264662dbc5c62ff5` (previously checked R9). Earlier 1990 default KfK 4605 remains frozen.

## Source-visible mathematical facts (do not conflate units or models)

| Direct source | Printed fact | Inference limit |
|---|---|---|
| Weir 1984 p.374 Eq.(19)–(20) | Light-response quadratic with `P_max = 0.995 C_a/r_p`; the printed rate is `mg CO2 m^-2 s^-1`. `C_a` is `mg CO2 m^-3`; `r_p` is `s m^-1`. | The paper's `P_max` is **not established** as KfK5194 Eq.(29) `P_m`. |
| Weir 1984 p.374 Eq.(21)–(22) | `r_p = r_a + r_s + r_m`, in `s m^-1`; the paper uses a radiation/vapor-deficit stomatal closure. | Cannot transfer these resistance or maximum-rate conventions to KfK5194 without an explicit derivation. |
| Weir 1984 p.374 and p.375 Eq.(25) | Daylight leaf-area layer photosynthesis is aggregated to crop production; growth and maintenance respiration are treated separately. Total respiration is expressed in `g m^-2 day^-1`, and depends on crop weight `W` in `g m^-2`. | Leaf-area/ground-area aggregation and daily-vs-hourly conversion are not a validated bridge into KfK5194 Eq.(30) `W` or `Rd`. |
| Weir 1984 p.375 Eq.(25)–(26) | Photosynthate in `CH2O` equivalent is given using the paper's empirical factor `0.65` multiplying `CO2` photosynthesis; daily net assimilate is production minus respiration in `g m^-2 day^-1`. | This is not a license to substitute `0.65` for KfK5194 Eq.(31) `COA=1.5` or to equate the two models' biomass pools. |
| KfK5194 1993 §5.5.1 Eq.(26)/(29) | The printed Eq.(26) `P_m` is `g CO2 m^-2 h^-1`, whereas Eq.(29) `CO` is labelled `mg CO2 m^-2 h^-1`. | The empirical Eq.(29) `0.158 * CO * 10^9 * T * exp(...)` calibration and implied mass bridge remain **NOT_ESTABLISHED**. |

The pure dimensional identity `1 mg m^-2 s^-1 = 3.6 g m^-2 h^-1` is valid irrespective of the models (multiply by 3600 s/h and divide by 1000 mg/g). **It must not be inserted into Eq.(29) as a conversion correction without verifying the empirical prefactor's calibration and the area basis.** Weir's `P_max` is in per-second units, whereas KfK5194 Eq.(29) explicitly prints a per-hour `CO` label: identical abbreviations are not evidence of identical state definitions.

## Open questions and release gate

1. Establish where, if anywhere, Weir's maximum-rate/resistance formulation actually enters KfK5194 Eq.(29); confirm `0.158` and `10^9` calibration from the 1993 primary text or an original implementation. **NOT_ESTABLISHED**.
2. Reconcile KfK5194 Eq.(28) printed expression with Eq.(26)–(27), including LAI and leaf/ground area. **NOT_ESTABLISHED**.
3. Obtain and visually check Mitchell et al. (1991) complete methods/equations before assessing KfK5194 Eq.(30) respiration and CO2-equivalent biomass. Mitchell **FULL_TEXT_NOT_RUN**.
4. Obtain genuine independent scientific sign-off at the exact commit SHA and original UFOTRI same-input outputs before claiming original-executable equivalence. Both **NOT_RUN**.

This source audit changes **only documentation, provenance registry and regression tests**. No `src/`, `configs/`, 1990 default, 1993 runtime solver, test threshold, or CI gate is changed. `scientific-admission` remains blocked; PR #159 must remain Draft, unmerged, with no `science-validated` or `merge-verified`.
