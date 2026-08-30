# UFOTRI ITER Benchmark Reconstruction R1

Stage: `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@a78a56cb44a230d33571a194ea0b5375261db86f`

## 1. Scope

G2 reconstructs only the recoverable ITER accident-release benchmark contract from KfK 4605 Section 5.3 and Appendix B. It freezes the benchmark inputs, the D/F Mol diffusion coefficients and the explicitly tabulated 1000 m dose reference values in Tables 10–13. It does not perform or claim a full atmospheric numerical replay.

No production source, default parameter, workflow or roadmap change belongs to this stage.

## 2. Recoverable benchmark inputs

The source provides a 100 g tritium release in separate HT and HTO cases with a 2 min release duration. Appendix B Table 8 specifies release heights 0, 20 and 60 m. Pasquill D/F meteorology is explicit: wind speed at 60 m is 5/3 m/s, mixing lid 560/200 m and wind-profile exponent 0.34/0.44. Air temperature is 10 °C, with no rain and no plume rise.

The separate building-wake case is defined at 20 m with a 100 m wide, 70 m high building. Table 8 also provides HTO/HT dry-deposition velocities, soil diffusion coefficients, a 5 %/h HTO soil re-emission rate, 0.5 %/d atmospheric oxidation, breathing and dose factors. Soil/vegetation, site/population and human-diet inputs are likewise tabulated. Section 5.3 adds stomatal resistance 4 s/cm, LAI 3 m²/m² and approximately 10 s/cm additional aerodynamic resistance under very stable conditions.

Table 9 supplies the Mol diffusion coefficients. G2 freezes the two benchmark classes:

| Class | p_y | q_y | p_z | q_z |
|---|---:|---:|---:|---:|
| D | 0.418 | 0.796 | 0.520 | 0.711 |
| F | 0.235 | 0.796 | 0.311 | 0.711 |

## 3. Release-height source conflict

A source-level conflict is present and is not resolved by assumption:

- Appendix B Table 8: `0, 20, 60 m`;
- Section 5.3 narrative, Tables 10–13 and benchmark figures: `10, 20, 60 m`, with an additional `20 m with building wake` case.

G2 records this as:

`ITER_RELEASE_HEIGHT_0_VS_10_M = PRESERVE_AMBIGUITY`

The 10 m rows in Tables 10–13 are valid printed reference outputs, but they do not authorize rewriting the Table 8 input statement from 0 m to 10 m.

## 4. Tables 10–13 reference qualification

The Appendix B 1000 m plume-centreline dose table is split according to its four captions:

- Table 10 — HTO, category D;
- Table 11 — HTO, category F;
- Table 12 — HT, category D;
- Table 13 — HT, category F.

Each contains four result cases: 10 m, 20 m, 60 m and 20 m with building wake. Seven dose columns are retained exactly as printed: early plume inhalation/skin; early inhalation/skin including re-emission; chronic inhalation/skin including re-emission; early ingestion; chronic ingestion; sum early; sum chronic.

Qualification checks intentionally use only relationships supported by those tables:

1. `sum early = early inhalation/skin with re-emission + early ingestion` within 5% relative tolerance for printed rounding;
2. `sum chronic = chronic inhalation/skin with re-emission + chronic ingestion` within the same tolerance;
3. 10 m has the highest total chronic dose in each table;
4. 60 m has the lowest total chronic dose in each table;
5. 20 m with building wake exceeds ordinary 20 m in total chronic dose in each table;
6. category F total chronic dose exceeds category D for matching 1 km HT and HTO cases;
7. HTO total chronic dose exceeds HT for matching stability/release cases at 1 km.

These checks qualify transcription and benchmark semantics; they are not a substitute for reproducing the atmospheric calculation.

## 5. Figures and far-range evidence

Section 5.3 uses Figures 29 onward for near/far-range concentration and dose behaviour. The Markdown helper tables beneath those figures contain approximate values and occasionally damaged OCR or incomplete series labels. G2 therefore does not use them as exact pointwise targets.

The narrative trends remain evidence-visible for later cross-module qualification, but G2 does not manufacture RMSE, pointwise tolerances or exact far-range arrays from chart transcription.

## 6. Remaining boundaries

The following remain unresolved after a passing G2 contract reconstruction:

- `ITER_RELEASE_HEIGHT_0_VS_10_M`;
- exact original building-wake numerical implementation;
- original MUSEMET/UFOTRI atmospheric numerical equivalence;
- real CTEAS-Atmos HT/HTO binding;
- authoritative pointwise arrays behind the Appendix B figures.

These boundaries do not invalidate Tables 10–13 as printed benchmark reference data, but they prevent G2 from claiming a full atmospheric replay or original-executable equivalence.

## 7. Acceptance and non-claims

Expected machine result:

`PASS_MANUAL_TABULATED_ITER_BENCHMARK_RECONSTRUCTION`

A passing G2 establishes:

- `ITER_BENCHMARK_CONTRACT_RECONSTRUCTED=TRUE`;
- `ITER_1KM_TABULATED_REFERENCE_QUALIFIED=TRUE`.

It leaves:

- `ITER_FULL_ATMOSPHERIC_NUMERIC_REPLAY_COMPLETE=FALSE`;
- `ITER_EMPIRICAL_VALIDATION_COMPLETE=FALSE`;
- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`;
- production readiness and physical accuracy unclaimed.

After exact-head CI and merge/no-drift certification, a separate roadmap-only status PR must decide and authorize the next roadmap item. G2 itself does not skip the control plane.
