# V3-P7.6B-2B evidence recovery report

## Decision

`P7_6B2B_STATUS = PASS_EVIDENCE_RECOVERY`

One physical evidence record was recovered with complete source metadata,
explicit applicability, equation role, and unit conversion. It is retained in
the control-plane inventory and exposed only as a future validation candidate;
no solver or pipeline value was changed.

## Accepted evidence

| parameter | source | reported quantity | normalized quantity | disposition |
| --- | --- | --- | --- | --- |
| `soil.tritium_half_life` | Lucas and Unterweger (2000), [NIST JRES 105, 541–549](https://doi.org/10.6028/jres.105.043) | `4500 +/- 8 d` | `388800000 s` | `EVIDENCE_FOUND`; direct decay-term candidate |

The source metadata records the title, authors, year, journal, volume, pages,
DOI, locator, stable URL, reported uncertainty, and the conversion path
`4500 d x 86400 s d^-1 = 388800000 s`. The record also states its equation
role: the existing V3 soil decay term derives `lambda_T = ln(2) / T_half`.
The normalized value is evidence-layer provenance only; it is not a runtime
lookup or an activation.

The half-life is a universal H-3 nuclear property. Its applicability is
therefore limited to the radioactive-decay term. It is not evidence for soil
transport, soil water content, retention, or any plant-transfer coefficient.

## Targeted negative screening

The priority Tier-1 materials were screened against the current V3 equations
before any candidate was created.

| target | screened evidence | reason it remains deferred |
| --- | --- | --- |
| `obt.kf` | Barescut et al. (2009), [Radioprotection 44, 671–676](https://doi.org/10.1051/radiopro/20095123); the accessible formulation reports a TFWT-to-OBT formation relation | the source does not provide the complete current `dOBT/dt = kf*TFWT - kr*OBT` parameterization and the rate varies with plant growth stage |
| `obt.kr` | Kirchmann, Gerber and Fagniart (1986), [Radiation Protection Dosimetry 16, 107–110](https://doi.org/10.1093/rpd/16.1-2.107) | a reported leaf-loss timescale is not by itself a complete V3 turnover-equation record with a closed OBT definition and uncertainty |
| `obt.kf` / `obt.kr` model structure | Ota and Nagai (2011), [Journal of Environmental Radioactivity 102, 813–823](https://doi.org/10.1016/j.jenvrad.2011.05.007) | the model uses a dynamic carbohydrate/respiration representation rather than one directly interchangeable pair of V3 first-order coefficients |
| `root.k_root` | the [OSTI tritium re-emission report](https://www.osti.gov/servlets/purl/598776) contains effective soil/root rate formulations | the reviewed quantity is a rate in a soil-concentration formulation, not an explicit effective transfer velocity in `m s^-1` for `J_root = k_root * C_soil` |
| `leaf.r_a`, `leaf.r_b`, `leaf.r_c` | Belot et al. (1979), [Health Physics 37, 575–583](https://doi.org/10.1097/00004032-197910000-00009) | a complete mapping to the V3 `r_total = r_a + r_b + r_c` chain, environmental regime, crop/leaf type, and unit basis was not recovered |
| soil transport terms | UFOTRI soil descriptions and the external soil/root materials | no source-compatible coefficient for the current signed interface flux was established; interface flux is not silently converted into a transport parameter |

These negative screens are not evidence records and do not change the model.
No values were averaged, reconstructed, or replaced with assumptions.

## Lifecycle and boundary

The recovered record is `EVIDENCE_FOUND`, not `VALIDATED` or `ACTIVE`.
`source_metadata` is mandatory for non-test physical evidence, and the schema
requires the source identifier to match the metadata identifier. The evidence
registry remains control-plane-only and continues to reject validated/active
records.
