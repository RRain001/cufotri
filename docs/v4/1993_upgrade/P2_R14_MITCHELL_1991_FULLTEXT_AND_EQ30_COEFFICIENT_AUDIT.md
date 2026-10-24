# P2 R14 — Mitchell (1991) complete original equations / KfK5194 Eq.(30) source bridge

**Disposition: MITCHELL_PRIMARY_FULLTEXT_VISUALLY_REVIEWED / TABLE7_EQ30_COEFFICIENT_MATCH / TABLE3_TABLE7_INTERNAL_NUMERIC_UNRESOLVED / ORIGINAL_FORTRAN_PARITY_NOT_RUN / PRODUCTION_COUPLING_BLOCKED.**

This document supersedes the **access limitation only** from R12: a user-supplied legitimate ten-page PDF is now available for review. R12's contemporaneous institutional HTTP 401 observation remains historically true; it must not be rewritten to claim that the archive became open access. The PDF is *not committed*, transmitted to GitHub, or copied to public test fixtures. This document quotes only short parameter/equation fragments necessary for independent source identification.

## Frozen source evidence

Mitchell, R. A. C., Lawlor, D. W. & Young, A. T. (1991), *Dark Respiration of Winter Wheat Crops in Relation to Temperature and Simulated Photosynthesis*, *Annals of Botany* 67:7–16, DOI `10.1093/oxfordjournals.aob.a088102`.

- User-attached source `mitchell1991.pdf`: 10 pages; visually inspected page images for printed pp.7, 9, 12, 13, 14, 15 (PDF zero-based pages 0, 2, 5, 6, 7, 8). Local uploaded-file SHA256: `d9f6f74b5268c6166407e02e98208dc452f9614002ccdb87a4d045cd4e0229e4`. This fingerprint identifies the *specific reviewed uploaded PDF*, not an archive copy.
- Printed p.7 Eq.(1): `R' = a P' + b W'` where `W'` is dry mass expressed in CO2 equivalents, not raw grams of dry matter; `a` growth, `b` maintenance.
- Printed p.9 Eqs.(2),(3): dry-mass-normalized `R = alpha P + beta0 + beta1 T`; to convert to CO2-equivalent biomass maintenance, `b = k(beta0+beta1 T)`, where `k` converts dry mass to CO2 equivalents. Paper also studies Eq.(5), a separate *per-ground-area* maintenance variant. Its discussion explicitly does not use the Eq.(5) parameter set to estimate growth/maintenance physiological coefficients because it lacks a physiological basis (printed p.14).
- Printed p.14 prose fixes `k = 30/44 g dry mass per g CO2` for Table 7 estimates. Therefore **only under this paper's stated biomass representation** `W_CO2eq [g CO2 eq/m2] = M_dry [g dry/m2] * (44/30)`. This is a source-supported *unit bridge*, but it does not identify the actual input arrays/buffers or conversion implementation inside UFOTRI 1993 FORTRAN, which remains unavailable.
- Printed p.15 Table 7 gives **shoot** `a=0.36`, `b=0.004 day^-1` at **10 °C**, and **ear** `a=0.42`, `b=0.006 day^-1` at **13 °C**. Table 7 footnote shows `b = (beta0+beta1 T)*(30/44)*(10^-6 g/microgram)*(86400 s/day)` using regression units. The 1993 KfK5194 printed Eq.(30) `Rd=0.36 Pc+1.67e-4 W` has an **exact printed shoot growth coefficient** and `0.004/24 = 0.000166666... h^-1`, agreeing with the printed `1.67e-4 h^-1` within the last displayed digits (difference `3.333e-7 h^-1`, ≈0.2%). This is **parameter-provenance evidence, not proof of original runtime behavior**, and is specific to the shoot parameter estimate and its stated temperature.
- Time-basis evidence: printed p.12 states the fitted shoot `P` averaged **the day of respiration measurement and the preceding day** (the two days preceding the night); p.14 interprets decoupling/assimilate storage. This describes the **paper's regression input**, not evidence that UFOTRI's hourly Eq.(30) used a mandatory two-day rolling buffer. Historical `Pc/Rd` evaluation order and crop-hour time averaging remain **NOT_ESTABLISHED**.
- Physiological scope: paper's *shoot* parameters were assumed representative of entire crop on a per-dry-mass basis, whereas the *ear* stage required separate interpretation and exclusion of early-ear observations. These are empirical conditional assumptions, not a universally verified crop-specific constant.

## New internal numerical consistency gate — **do not silently repair primary data**

The **printed Table 3** (p.12) has shoot **Eq.(2)** central parameters `alpha=0.35 ±0.04`, `beta1=+0.010 ±0.003 microgram CO2/(g dry mass °C s)`, `beta0=+0.029 ±0.047 microgram CO2/(g dry mass s)`. By direct *central-value-only* substitution at the Table 7 shoot reference of 10 °C:

```text
beta(10 C) = +0.029 + (+0.010)*(10) = 0.129 microgram CO2/(g dry mass s)
b_reconstructed = 0.129 * (30/44) * 1e-6 * 86400
                = 0.00759927 day^-1
b_Table7_shoot = 0.004 day^-1
```

Thus the **printed rounded central values in Table 3 do not reproduce the Table 7 shoot `b`** when the paper's own Eq.(3) and Table 7 footnote are applied. Table 3 also prints `alpha=0.35` for Eq.(2) whereas Table 7 lists `a=0.36`; its alternative Eq.(5) regression separately lists `alpha=0.36`. These observations are not a license to change signs, mix Eq.(2) and Eq.(5), invent a correction/erratum, or assert scientific invalidity: regression uncertainties, underlying unrounded data, covariances or other undocumented choices cannot be resolved from the printed page alone.

**Science classification:** `TABLE7_EQ30_NUMERIC_MATCH` is established as a specific parameter relationship; `TABLE3_EQ2_TO_TABLE7_B_REPRODUCIBILITY` is `NOT_ESTABLISHED_PRINTED_CENTRAL_VALUES_DIFFER`. One may not cite an internally inconsistent regression chain as fully independently verified. KfK5194's selection of fixed temperature vs dynamically variable `b(T)`, LAI/ground vs leaf-area normalization, tissue partition and original iteration order are still not independently established.

## Independent software checks and scientific release boundary

R14 checks Table 7 → Eq.(30) unit conversion and matching, the dry-matter-to-CO2-equivalent factor and round-trip, Table 3 central-value mismatch, separately shoot/ear coefficient identities, and strict `NOT_RUN` release gates. Checks run on **synthetic arithmetic only** and do not calibrate/model a physical field trial. R12 access restriction remains historical, R14 provides newer actual full-text evidence. Do not alter `src/`, runtime configuration, 1990 default, numerical tolerances, GitHub required checks or external-data scientific admission.

Required before production: independent scientific review of the Table 3/7 mismatch, manual Eq.(28) inconsistency, Eq.(29) Weir bridge, identification of the hourly state convention for `Pc/Rd/W`, full external SB1/SB4/ERA5/private D3 input evidence and original UFOTRI same-input parity. Draft PR #159 unmerged until independent review and scientific admission actually pass. **No `science-validated` or `merge-verified`**.
