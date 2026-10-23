# P2 R10 — Weir (1984) / Mitchell (1991) bibliography and evidence boundary

**Disposition: PUBLISHER_METADATA_AND_ABSTRACT_VERIFIED / EQUATION_CALIBRATION_NOT_ESTABLISHED / PRODUCTION_COUPLING_BLOCKED.** This audit supplements R9 for P0 #126 and P2 #128. It does not validate KfK5194 Eq.(29)/(30), substitute original UFOTRI code, or modify any solver.

## Publisher-confirmed reference identity

| KfK5194 citation | Publisher bibliographic record | Verified from public publisher abstract | Not established |
|---|---|---|---|
| /39/ Weir et al. | A. H. Weir, P. L. Bragg, J. R. Porter, J. H. Rayner (1984), *A winter wheat crop simulation model without water or nutrient limitations*, *The Journal of Agricultural Science* **102**(2), 371–382. DOI [10.1017/S0021859600042702](https://doi.org/10.1017/S0021859600042702). [Cambridge publisher page](https://www.cambridge.org/core/journals/journal-of-agricultural-science/article/abs/winter-wheat-crop-simulation-model-without-water-or-nutrient-limitations/80C9DA188913CA1E2822FB015215B3E0). | A whole-crop winter-wheat FORTRAN simulation uses daily weather/daylength and canopy radiation to produce dry matter allocated among plant organs; simulations have limits for early-sown crops. | The **full-text** empirical CO calibration, whether KfK5194 Eq.(29) `0.158*CO*10^9` incorporates a unit conversion, and how a Weir-model quantity maps to KfK5194 Eq.(26) `P_m`. |
| /21/ Mitchell et al. | R. A. C. Mitchell, D. W. Lawlor, A. T. Young (1991), *Dark Respiration of Winter Wheat Crops in Relation to Temperature and Simulated Photosynthesis*, *Annals of Botany* **67**(1), 7–16. DOI [10.1093/oxfordjournals.aob.a088102](https://doi.org/10.1093/oxfordjournals.aob.a088102). [Oxford publisher page](https://academic.oup.com/aob/article-abstract/67/1/7/257984). | Shoot and ear dark respiration are examined separately. Respiration per unit **dry mass** varies with season; shoot respiration relates more strongly to the preceding two-day photosynthesis average than the preceding one-day value. The abstract reports growth-respiration assimilation fractions for distinct growth stages. | Whether the KfK5194 Eq.(30) coefficient and biomass term `W` are copied, refitted or transformed from Mitchell, the precise **ground/leaf area** conversion, CO2-equivalent versus dry-matter normalization, and historical solve order. |

Publisher metadata and abstracts were accessed on **2026-10-24**. The papers were published in **1984** and **1991**; Cambridge's later *online posting date* is not their publication year. **Full-text equation review: NOT_RUN; independent scientific review: NOT_RUN.** No full-text mathematical derivation or parameter table has been reviewed in this R10 audit, and no copyrighted paper PDF is committed.

## Implications for Eq.(29)–(30)

1. Weir's publisher abstract establishes crop-level simulation and dry-matter partitioning, **not** a directly reusable numerical coefficient for `CO` or a milligram-to-gram bridge. Retain `eq29_co_to_pm_bridge=NOT_ESTABLISHED`.
2. Mitchell's publisher abstract specifically distinguishes shoot/ear and per-unit-dry-mass respiration. Therefore an unqualified use of Eq.(30) across all crop compartments or an assumption that `W` equals Table 1 dry mass is not justified. Retain `eq30_dry_matter_to_w_bridge=NOT_ESTABLISHED` and `eq30_respiration_area_basis=NOT_ESTABLISHED`.
3. Neither abstract determines whether the KfK5194 Eq.(28) printed denominator/respiration term is an erratum or how original UFOTRI evaluates `Pc` and `Rd`. Do not promote either R8 conditional branch.
4. For a *manual-first* correction, obtain the actual article methods/equations and source-to-target dimensional worksheet, then independent scientific review. For *original executable parity*, additionally obtain original code/executable and same-input numerical evidence.

**No change** to the KfK4605 (1990) default, numerical parameters, protected runtime, `scientific-admission`, or PR #159 Draft status. Source-level provenance is useful, but is **not** independent scientific validation.
