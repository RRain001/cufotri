# ADR-075 — UFOTRI Canada 1987 benchmark reconstruction R1

## Status

Candidate pending exact-head CI.

Stage: `UFOTRI_CANADA_1987_BENCHMARK_RECONSTRUCTION_R1`

Base: `main@9b1d6ff34b7306175601e9257fdddf393a4e8d3c`

## Context

The replication master plan requires the Canada 1987 HT release comparison as G1 validation evidence. KfK 4605 Section 5.2 contains a useful but incomplete reconstruction basis: site description, a set of static model inputs, the observable families in Figures 21–28, and a qualitative interpretation of calculated-versus-measured behaviour.

The manual also states that the underlying hourly meteorological variables existed for nearly every hour from June 9 to June 26, while precipitation was available only as an event total. Those numerical hourly series are not tabulated in the repository transcription. Reference /44 is identified as G.L. Ogram, `The Canadian HT Dispersion Experiment at Chalk River - June 1987: Summary Report`, CFFTP-G-88027 (1988), but its raw field/model data are not present as repository benchmark inputs.

The current repository now contains manual-compatible seams for the HT branch, HT→HTO soil conversion and secondary re-emission area-source handoff. This is enough to define a benchmark contract, but not enough to claim a numerically faithful replay of the 1987 experiment.

## Decision

G1 R1 is a **source-limited benchmark-contract reconstruction**.

It SHALL:

1. freeze only static Canada inputs explicitly recoverable from KfK 4605 Section 5.2;
2. enumerate the eight observable families represented by Figures 21–28;
3. preserve the internal Figure 28 distance conflict: the prose says 175 m while the caption/table-of-contents says 180 m;
4. record every missing item that prevents a full numeric replay;
5. use the manual's own stated validation intent — qualitative reproduction of the time dependence in air, soil and vegetation over several days — as the historical comparison objective;
6. fail closed against invented hourly meteorology, invented precipitation timing, invented raw measurement/calculation arrays, an assumed Canada sigma table, or a promoted Eq. (44) rate;
7. leave `src/`, defaults, workflows and the master roadmap unchanged in the stage PR.

The embedded chart-transcription helper tables under Figures 21–28 are NOT authoritative benchmark point arrays. They do not preserve an unambiguous mapping between measured points (asterisks in the original figures) and calculated curves. They therefore SHALL NOT be used to manufacture RMSE, bias, correlation, or pointwise pass/fail tolerances.

## Recovered static contract

The R1 contract freezes the following manual values:

- HT release rate: `1.9e9 Bq/s`;
- duration: `1800 s`;
- integrated release activity: `3.42e12 Bq`;
- release height: `1 m`;
- Pasquill-Gifford stability: `B`;
- meteorological measurement height: `2.75 m`;
- HT deposition velocity: `0.055 cm/s = 5.5e-4 m/s`;
- deposition velocity of re-emitted HTO: `0.5 cm/s = 5.0e-3 m/s`;
- starting soil water content: `20%`;
- plant inorganic water: `200 g`;
- plant organic matter: `100 g`;
- LAI: `3 m²/m²`;
- single-leaf diffusion resistance: `4 s/cm` day and `60 s/cm` night;
- soil re-emission: recalculated hourly by day except rain, starting at `1%` at night and `3%` during rain, with the latter rates decreasing with time.

These values are benchmark evidence, not production defaults.

## Explicit replay blockers

A full numerical Canada replay remains blocked by at least:

- absence of the raw CFFTP-G-88027 report/data set in repository benchmark inputs;
- missing hourly wind direction, wind speed, temperature, net solar radiation and relative humidity values;
- missing exact release clock alignment to those hourly data;
- precipitation available in the manual only as an event-total description, not an hourly allocation;
- missing authoritative measured/calculated point arrays for Figures 21–28;
- no Canada-specific numerical sigma-parameter table explicitly recoverable from Section 5.2;
- incomplete exact recovery of the historical Eq. (44) re-emission-rate generation;
- unavailable original MUSEMET/UFOTRI executable numerical equivalence and deferred real CTEAS-Atmos HT binding.

## Acceptance

R1 passes if and only if the recoverable contract, observable inventory, unit conversions, repository seam mapping, Figure 28 ambiguity and all replay blockers are machine-auditable and no missing value is silently supplied.

A passing R1 means:

`CANADA_1987_BENCHMARK_CONTRACT_RECONSTRUCTED = TRUE`

It does **not** mean:

`CANADA_1987_EMPIRICAL_VALIDATION_COMPLETE = TRUE`

or:

`UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE = TRUE`.

After exact-head CI, merge/no-drift certification and a roadmap-only sync, the planned next reconstruction stage is `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`. Any future Canada numerical replay must consume newly recovered primary evidence or an explicitly qualified atmospheric forcing/binding; it may not back-fill the R1 blockers by assumption.
