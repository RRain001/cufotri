# UFOTRI Canada 1987 benchmark reconstruction R1

## Executive result

Candidate result:

`G1_CANADA_1987_STATUS=PASS_SOURCE_LIMITED_CANADA_1987_BENCHMARK_RECONSTRUCTION`

This result means that the Canada 1987 benchmark **contract** has been reconstructed from recoverable KfK 4605 evidence without filling missing inputs. It is not an empirical replay or a numerical-equivalence claim.

```text
CANADA_1987_BENCHMARK_CONTRACT_RECONSTRUCTED = TRUE
CANADA_1987_FULL_NUMERIC_REPLAY_READY = FALSE
CANADA_1987_EMPIRICAL_VALIDATION_COMPLETE = FALSE
UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE = NOT_ESTABLISHED
```

## Evidence basis

Primary repository evidence is KfK 4605 Section 5.2 in `ufotri_manual.md`.

The manual identifies the underlying experiment report as:

G.L. Ogram, *The Canadian HT Dispersion Experiment at Chalk River - June 1987: Summary Report*, Canadian Fusion Fuels Technology Project, CFFTP-G-88027 (1988), reference /44.

The raw CFFTP-G-88027 data are not present as repository benchmark inputs. Therefore this stage uses only values and semantics recoverable from the available manual transcription.

## Recovered experiment/site semantics

The experiment was conducted at Chalk River Nuclear Laboratories. The manual describes a central circular field of about 100 m radius, a sparsely vegetated extension of about 200 m, and sampling out toward approximately 400 m. The open-area soils vary strongly in texture, organic fraction and water content; the benchmark model nevertheless used a controlled 20% starting soil-water content for the vegetated area.

The meteorological variables described as hourly averaged are wind direction, wind speed, temperature, net solar radiation and relative humidity, covering nearly every hour from June 9 to June 26. The numerical series are not tabulated in the manual transcription. Precipitation is described only as the sum of one several-hour rain event.

## Recovered static benchmark inputs

| Item | Recovered value | Qualification |
|---|---:|---|
| Chemical form | HT | Manual Section 5.2 |
| Release rate | `1.9e9 Bq/s` | Manual Table 3 |
| Release duration | `1800 s` | Half-hour release |
| Integrated release | `3.42e12 Bq` | Exact rate × duration conversion |
| Release height | `1 m` | Manual prose |
| Stability | PG class `B` | Manual prose |
| Meteorological instrument height | `2.75 m` | Manual prose |
| HT deposition velocity | `0.055 cm/s = 5.5e-4 m/s` | Arithmetic-mean value selected by UFOTRI |
| Re-emitted HTO deposition velocity | `0.5 cm/s = 5.0e-3 m/s` | Manual prose |
| Initial soil-water fraction | `0.20` | Starting point; updated hourly by model |
| Plant inorganic water | `200 g` | Manual Table 3 |
| Plant organic matter | `100 g` | Manual Table 3 |
| LAI | `3 m²/m²` | Manual Table 3 |
| Leaf diffusion resistance, day | `4 s/cm = 400 s/m` | Single-leaf value |
| Leaf diffusion resistance, night | `60 s/cm = 6000 s/m` | Single-leaf value |
| Soil re-emission, day | recalculated hourly except rain | Manual Table 3 |
| Soil re-emission, night | starts at `1%`, decreases with time | Manual Table 3 |
| Soil re-emission, rain | starts at `3%`, decreases with time | Manual Table 3 |

These values are evidence for this benchmark only. No project production default is changed.

## Observable contract

The manual comparison covers eight observable families:

| Figure | Observable | Location/time semantics |
|---:|---|---|
| 21 | HT air concentration during plume passage | plume-centreline distance series |
| 22 | HT soil concentration after plume passage | plume-centreline distance series |
| 23 | HTO soil concentration vs time | about 50 m |
| 24 | HTO soil concentration vs time | about 180 m |
| 25 | HTO air concentration vs time | 50 m; first 30 h include measurements at about 0.4–1 m height |
| 26 | HTO air concentration vs time | 400 m; measurements at 1 m height |
| 27 | HTO vegetation-water concentration vs time | 40 m |
| 28 | HTO vegetation-water concentration vs time | **ambiguous: prose 175 m; caption/TOC 180 m** |

The Figure 28 conflict is preserved, not resolved by preference.

The `<details>` chart helper tables embedded in the Markdown transcription are not accepted as authoritative raw series. The original figures distinguish measurements by asterisks and calculations by curves, but the helper tables do not preserve a reliable series identity. Using those values to manufacture RMSE, correlation or a pointwise tolerance would create false precision.

## Historical comparison objective

The manual explicitly cautions that a more precise reproduction of individual measurements could be accidental because of simplified diffusion resistance, root-distribution uncertainty, plant mass uncertainty and spatial averaging of input parameters.

Its stated purpose is instead to test whether UFOTRI qualitatively reproduces the time dependence — increase and decrease of HTO concentrations in air, soil and vegetation over several days after an HT release.

Therefore R1 freezes the historical comparison objective as:

`QUALITATIVE_TIME_DEPENDENCE_OF_AIR_SOIL_AND_VEGETATION_CONCENTRATIONS_OVER_SEVERAL_DAYS`

This does not create a new numerical tolerance. A quantitative tolerance policy can be added only after authoritative input and measured/calculated arrays are recovered.

## Repository compatibility mapping

The current post-F1 repository already contains opt-in/manual-compatible seams for the parts needed by a future Canada replay:

- `src/cteas_ufotri/coupling/ht_v4.py` — HT forcing/branch contract;
- `src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py` — HT deposition/conversion ownership seam;
- `src/cteas_ufotri/coupling/reemission_area_source_v4.py` — secondary HTO area-source handoff and hour-N→N+1 semantics.

This compatibility mapping is structural only. It does not establish original MUSEMET/UFOTRI numerical equivalence or a real CTEAS-Atmos replay.

## Explicit blockers to a full numeric replay

1. `CAN1987_REFERENCE_44_RAW_REPORT_AND_DATA` — CFFTP-G-88027 raw data are not repository benchmark inputs.
2. `CAN1987_RAW_HOURLY_MET_SERIES` — the hourly numerical weather sequence is absent.
3. `CAN1987_RELEASE_CLOCK_ALIGNMENT` — exact release timestamp alignment to the weather sequence is absent.
4. `CAN1987_PRECIPITATION_EVENT_TIMING` — only an event total is described, not hourly precipitation.
5. `CAN1987_RAW_MEASURED_AND_CALCULATED_SERIES` — authoritative point arrays and series identities for Figures 21–28 are absent.
6. `CAN1987_SIGMA_PARAMETER_NUMERIC_PROVENANCE` — the Canada section names the S.C.K./C.E.N. Mol set but does not provide a Canada-specific numerical table that can be adopted without inference.
7. `CAN1987_COMPLETE_EQ44_REEMISSION_RATE_RECOVERY` — exact historical Eq. (44) generation remains source-limited.
8. `CAN1987_PRIMARY_ATMOS_NUMERICAL_EQUIVALENCE` — original MUSEMET/UFOTRI executable equivalence is unavailable and real CTEAS-Atmos HT binding remains deferred.

All eight blockers are intentionally machine-visible. `full_numeric_replay_ready` must stay `false` while any of them remains unresolved.

## Qualification

Machine gate:

`python scripts/v4/check_ufotri_canada_1987_benchmark_reconstruction_r1.py`

Focused tests:

`pytest -q tests/v4/test_ufotri_canada_1987_benchmark_reconstruction_r1.py`

The machine gate validates manual anchors, exact unit conversions, all eight observable families, the Figure 28 ambiguity, current repository seam availability and fail-closed blocker/acceptance semantics.

## Boundary and next step

This stage adds no production source, changes no default parameter, changes no workflow and does not edit the master roadmap. Exact-head CI and merge/no-drift evidence are required before G1 R1 can be recorded as complete in the roadmap.

After that roadmap-only sync, the planned next reconstruction stage is `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`.

Canada 1987 numerical replay remains an explicitly unclosed empirical-validation action until the missing primary evidence and qualified atmospheric forcing are available. Nothing in this report authorizes silent parameter completion or an original-executable-equivalence claim.
