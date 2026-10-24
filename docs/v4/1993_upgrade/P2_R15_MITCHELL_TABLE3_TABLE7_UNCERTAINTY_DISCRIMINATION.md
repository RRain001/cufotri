# P2 R15 — Mitchell Table 3/7 coefficient reconciliation: bounded uncertainty, not invented erratum

**Status: PRINTED_CENTRAL_VALUES_DIFFER / MARGINAL_PLUS_MINUS_RECTANGLE_OVERLAPS_TABLE7 / STATISTICAL_RECONCILIATION_NOT_ESTABLISHED / SCIENCE_ACCEPTANCE_NOT_RUN.**

## Scope and primary evidence

Mitchell, Lawlor & Young (1991), *Annals of Botany* 67:7–16, DOI 10.1093/oxfordjournals.aob.a088102, **user-provided ten-page primary PDF SHA256** `d9f6f74b5268c6166407e02e98208dc452f9614002ccdb87a4d045cd4e0229e4`, reviewed in R14. The source PDF is not reproduced, checked into Git, or redistributed. Source lineages and page labels: printed p.7 Eq.(1); p.9 Eqs.(2)–(5); p.12 Table 3; p.14 reported CO2-equivalent factor `k=30/44`; p.15 Table 7/footnote. This R15 packet derives new numerical **conditions** from already-inspected primary source values and independently checks their arithmetic; it does **not** claim an additional unseen Table 3 note or an erratum.

Table 3 shoot Eq.(2): `alpha=0.35 ± 0.04`, `beta0=0.029 ± 0.047` and `beta1=0.010 ± 0.003`, with maintenance normalized to micrograms CO2 per g dry mass per second and `beta1` per degree Celsius. Table 7 shoot: `a=0.36`, `b=0.004 d^-1` **at 10 °C**; KfK5194 Eq.(30) `0.36 Pc + 1.67e-4 W` is a distinct historical model statement.

## Independent conditional calculations

Let `f=(30/44)*(1e-6 g/microgram)*(86400 s/day)=0.0589090909090909`, used solely to convert the printed Eq.(2)/Table 7 footnote's biomass-normalized maintenance. The exact central-value calculation is:

```text
beta10_central = 0.029 + 0.010*10 = 0.129  microgram CO2/(g dry*s)
b10_central = 0.129*f = 0.007599272727272727  day^-1
b_Table7_shoot = 0.004  day^-1
b10_central / b_Table7_shoot = 1.8998181818181814
alpha_Table3_eq2 = 0.35; alpha_Table7 = 0.36
```

Thus **printed central coefficients do not reconstruct** Table 7. However, the separately printed ± values imply a basic **marginal end-point rectangle**, with **no statistical confidence level or covariance asserted**:

```text
beta0 in [-0.018, +0.076]
beta1 in [+0.007, +0.013]  per degree Celsius
beta10_extrema = beta0 + 10*beta1  in [+0.052, +0.206]
b10_endpoint_range = beta10_extrema*f = [0.00306327272727, 0.01213527272727] day^-1
```

Table 7 `0.004/day` **lies inside this rectangle's possible interval**. A specific within-rectangle pair providing exactly that value is:

```text
beta1_example = 0.008
beta0_example = 0.004/f - 10*0.008 = -0.01209876543209876
```

These illustrative coefficients are inside the separately printed intervals. **They are not fitted estimates, a newly established regression, or approved UFOTRI coefficients**. Parameter uncertainties and covariances, the meaning of the reported ±, full unrounded regression data, physiological differences and any author correction are not established, so this calculation cannot legitimately be called a 68%/95% confidence interval or statistical reconciliation.

The shoot growth fraction gap `(0.36-0.35)/0.04=0.25` times the *printed marginal ± magnitude*, but `0.36` is not thereby validated as statistically equivalent to a different model estimator. Table 3 alternative Eq.(5)'s `0.36` must not silently be spliced into Eq.(2) to explain Table 7.

The 10 °C coefficient `0.004/day` would correspond to `T=3.89012345679 °C` if one **held both printed Eq.(2) central coefficients fixed**. That is only an inverse algebraic discriminant, **not** a replacement for the printed Table 7 reference temperature (10 °C) or evidence of the actual temperature used in UFOTRI. Likewise, the two-day photoynthesis average is Mitchell's fitting covariate, not a proven 48-hour model lag.

## Decision table and release boundary

| Question | Auditable disposition |
|---|---|
| Table 7 shoot `0.36`, `0.004/day at 10 °C` vs manual Eq.(30) | Coefficient match at printed precision; established source relationship |
| Table 3 central Eq.(2) reconstructed `b(10 °C)` | **Not equal** to Table 7: `0.00759927` vs `0.004/day` |
| Possible overlap using separate printed ± end points | **Yes, conditional bounded arithmetic**; not a confidence region or formal reconciliation |
| Corrected equation, raw regression data, covariance and erratum | NOT_ESTABLISHED |
| Whether UFOTRI used same-hour, lagged or averaged `Pc` | NOT_ESTABLISHED |
| Production Eq.(30) temperature/area/organ convention | NOT_ESTABLISHED |
| Original UFOTRI executable parity, independent scientific approval | NOT_RUN |

Machine-readable rows in UF93-13 and the independent test use only published numeric summaries and pure arithmetic. No runtime or KfK4605 1990 default is changed; do not replace Table 7 `0.004/day` with the central `0.00759927/day`, average them, infer temperature calibration, modify Eq.(30), or add `science-validated` / `merge-verified`. PR #159 remains Draft and unmerged.
