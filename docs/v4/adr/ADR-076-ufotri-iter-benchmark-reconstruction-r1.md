# ADR-076 — UFOTRI ITER benchmark reconstruction R1

## Status

Candidate pending exact-head CI.

Stage: `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`

Base: `main@a78a56cb44a230d33571a194ea0b5375261db86f`

## Context

The replication master plan authorizes the ITER benchmark reconstruction as G2 after the source-limited Canada 1987 contract was closed. KfK 4605 Section 5.3 and Appendix B provide substantially more benchmark information than the Canada case: the release quantity and duration, HT/HTO chemical forms, D/F meteorology, wind-profile exponents, mixing lids, deposition/diffusion/re-emission coefficients, soil/vegetation/site/diet inputs, the Mol diffusion coefficients, and explicit 1 km dose reference tables (Tables 10–13).

The source set nevertheless contains an internal release-height conflict. Appendix B Table 8 specifies `0, 20 and 60 m`, while Section 5.3 discussion, Tables 10–13 and Figures 29–64 use `10 m`, `20 m`, `60 m`, plus a distinct `20 m with building wake` case. R1 must preserve that conflict rather than silently replacing 0 m by 10 m.

The repository contains opt-in manual-compatible HT, HT→HTO, re-emission, food-chain and manual-dose seams, but real CTEAS-Atmos binding and original UFOTRI/MUSEMET numerical equivalence remain outside G2. Therefore G2 can reconstruct and qualify the benchmark contract and tabulated reference outputs without claiming a full atmospheric replay.

## Decision

G2 R1 is a **manual-tabulated ITER benchmark contract and reference-table reconstruction**.

It SHALL:

1. freeze the recoverable Appendix B Table 8 emission, meteorology, building-wake, code-coefficient, soil/vegetation, site/population and human-diet inputs;
2. freeze the Table 9 D/F Mol diffusion coefficients needed by the benchmark;
3. reconstruct Tables 10–13 as four separate authoritative 1 km reference tables: HTO-D, HTO-F, HT-D and HT-F;
4. preserve the Table-8 `0 m` versus Section-5.3/result `10 m` release-height conflict as `ITER_RELEASE_HEIGHT_0_VS_10_M`;
5. preserve `20 m with building wake` as a distinct benchmark case rather than folding it into the ordinary 20 m case;
6. verify internal dose-column identities with tolerances that allow only the rounding visible in the printed tables;
7. verify the robust source-stated ordering at 1 km: 10 m highest, 60 m lowest, and 20 m with wake greater than 20 m without wake for the tabulated total chronic dose in each of Tables 10–13;
8. keep the figure helper tables under Figures 29–64/65 non-authoritative because they are approximate chart transcriptions and contain OCR/series-label loss;
9. leave production `src/`, defaults, workflows and the master roadmap unchanged in the G2 stage PR.

## Recovered benchmark contract

### Emission and meteorology

- release quantity: `100 g` tritium;
- chemical forms: `HT` and `HTO` as separate cases;
- duration: `120 s`;
- Table 8 release heights: `0, 20, 60 m`;
- result-case release heights: `10, 20, 60 m`, plus `20 m with building wake`;
- Pasquill classes: `D` and `F`;
- wind speed at 60 m: `5 m/s` for D, `3 m/s` for F;
- mixing lid: `560 m` for D, `200 m` for F;
- air temperature: `10 °C`;
- no rain and no plume rise;
- wind-profile exponent: `0.34` for D and `0.44` for F.

### Building case

- no building wake for the ordinary release-height cases in Table 8;
- separate 20 m building-wake case;
- building width `100 m`, height `70 m`.

### Code coefficients

- HTO dry deposition velocity: `1.8 cm/s`;
- HT dry deposition velocity: `0.05 cm/s`;
- HTO soil diffusion coefficient: `2.0e-5 cm²/s`;
- HT soil diffusion coefficient: `5.0e-2 cm²/s`;
- HTO soil re-emission rate: `5 %/h`;
- atmospheric oxidation rate: `0.5 %/d`;
- breathing rate: `2.66e-4 m³/s`;
- quality factor: `1`;
- 7-day inhalation dose conversion factor: `6.3e-12 Sv/Bq`;
- 50-year inhalation/ingestion dose conversion factor: `1.7e-11 Sv/Bq`.

### UFOTRI-specific plant additions stated in Section 5.3

- stomatal resistance: `4 s/cm`;
- LAI: `3 m²/m²`;
- under very stable conditions, additional aerodynamic resistance: approximately `10 s/cm`.

These are benchmark evidence only. G2 does not promote them to production defaults.

## Reference outputs

Appendix B Tables 10–13 are treated as authoritative printed reference tables for plume-centreline dose at 1000 m. Each table contains four result cases (`10 m`, `20 m`, `60 m`, `20 m with building wake`) and seven dose columns. Their exact printed values are frozen in the governance record and machine gate.

The figure helper tables under Figures 29–64/65 are not used as numerical oracles because they are chart transcriptions with approximate orders of magnitude and incomplete series identity. They remain useful only as evidence of the observable families and far-range qualitative trends described by Section 5.3.

## Explicit source/numerical boundaries

G2 does not close:

- `ITER_RELEASE_HEIGHT_0_VS_10_M` — Table 8 versus result-case source conflict;
- exact original building-wake numerical implementation;
- original MUSEMET/UFOTRI atmospheric numerical equivalence;
- real CTEAS-Atmos HT/HTO binding;
- exact pointwise reconstruction of Figures 29–64/65 from chart helper tables.

No missing numerical semantics may be supplied by assumption merely to reproduce Tables 10–13.

## Acceptance

R1 passes if and only if:

- the recoverable Table 8/9 benchmark inputs are machine-auditable;
- all four Tables 10–13 are reconstructed exactly as printed;
- early/chronic total-dose identities close within printed-table rounding tolerance;
- the robust 1 km release-height/wake ordering holds for all four tables;
- the 0 m versus 10 m conflict remains explicit and unresolved;
- figure-helper values are not promoted to exact numerical targets;
- no production/default/real-Atmos change is introduced.

A passing R1 means:

`ITER_BENCHMARK_CONTRACT_RECONSTRUCTED = TRUE`

and

`ITER_1KM_TABULATED_REFERENCE_QUALIFIED = TRUE`.

It does **not** mean:

`ITER_FULL_ATMOSPHERIC_NUMERIC_REPLAY_COMPLETE = TRUE`,

`ITER_EMPIRICAL_VALIDATION_COMPLETE = TRUE`,

or

`UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE = TRUE`.

After exact-head CI, merge/no-drift certification and a roadmap-only status sync, the roadmap may proceed only to its next authorized item; G2 itself does not authorize G3 or deferred real-Atmos work ahead of that control-plane update.
