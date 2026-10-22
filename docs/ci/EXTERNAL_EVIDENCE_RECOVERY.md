# External evidence recovery and cloud-runner qualification

Status: **SOURCE IDENTIFIED / INPUT PACKETS NOT RECOVERED** (2026-10-22).

The public Git repository and a green portable CI run do **not** contain the experiment/ERA5 input files or original D3 reblinding secret. A previously existing local-only archive was deleted and must not be assumed recoverable. This document only records authoritative *candidate sources*, file contracts and how to avoid falsely claiming empirical validation.

## Inventory and provenance

| Dataset gate | Primary upstream source | Current repository contract | Present in public Git? | Permitted claim |
|---|---|---|---|---|
| `SB1` | IAEA EMRAS Tritium/C-14 Working Group report + CDS ERA5; KAERI soybean experiment | `validation/benchmarks/emras_soybean_sb1/source_inventory.yaml`; `validation/external_input_requirements.py` | **No**, required raw/external files absent | `HYBRID_LITERATURE_REANALYSIS`; **not empirical validation** |
| `SB4` | Same IAEA report and checksum-verified SB1 ERA5 data | `validation/benchmarks/emras_soybean_sb4/source_inventory.yaml`; `validation/external_input_requirements.py` | **No**, raw and prepared external files absent | `HYBRID_LITERATURE_REANALYSIS_RECONSTRUCTED_CHAMBER`; **not empirical validation** |
| `ERA5_ACCEPTANCE` | Copernicus CDS ERA5 hourly single levels | `validation/external_input_requirements.py` requires exactly `data/era5/era5_surface_2025-06-01_2025-06-02.csv` | **No** | Reanalysis meteorology input; not independent tritium observations |
| `D3_PRIVATE_REBLIND_SECRET` | Controlled historical blind/truth key material | `validation/external_input_requirements.py` declares two restricted JSON inputs | **No** and must not be made public | Original reblinding qualification blocked without exact original keys |

IAEA official publication candidate:

`https://www-pub.iaea.org/MTCD/publications/PDF/TE_1678_CD/Reports/Theme_1_WorkingGroup2%28Tritium%26C-14%29/ModellingtheEnvironmentalTransferofTritiumandCarbon-14toBiotaandMan.pdf`

Repository historical local PDF SHA-256:

`15b2591d82d8276c83030327d6a65d3f5a2e2ec3b11429d63b7c39461f50d211`

**The historical SHA is not a verified checksum of the currently hosted IAEA URL.** Retrieve the official file in an ephemeral or access-controlled location and compute its SHA-256. If it differs, stop and record the precise file/version/page and table-content equivalence rather than silently replacing the reference. The IAEA page/PDF link confirms a candidate public source, not permission to redistribute the entire document in this repository. The existing repo permits only the independently reviewed published numeric-table transcription.

ERA5 official dataset:

`https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview`

Dataset DOI: `10.24381/cds.adbb2d47`.

The existing SB1 reproduction instructions cover **2001-05-20 through 2001-10-06**, and a five-point spatial sensitivity at `CENTRE`, `NORTH_0P25`, `SOUTH_0P25`, `EAST_0P25`, `WEST_0P25`. The centre coordinates are `36.425 N, 127.373611 E`. Required ERA5 fields are temperature/dew point, pressure, U/V wind, total precipitation, shortwave/thermal radiation and total cloud cover. Consult `validation/benchmarks/emras_soybean_sb1/README.md` and `docs/v3/benchmarks/emras_soybean_sb1_site_resolution.md` for the complete existing case contract. The separate `ERA5_ACCEPTANCE` 2025-06-01/02 file is a distinct software acceptance input, not a substitute for the 2001 experiment reanalysis.

## Recovery order

1. **Public source verification only:** verify official IAEA source file version, expected page/table mapping, source provenance and byte hash; keep the original report untracked unless reuse and redistribution are independently authorized.
2. **ERA5 reproducibility:** use the repository's audited `era5/download_era5_timeseries.py` interface with a user-authorized CDS account/credentials and the exact declared coordinates/time windows. Check downloads and NetCDF coordinate/time variables, preserve checksums and CDS source metadata. Do not log the CDS token or upload the raw NetCDF files as public Actions artifacts.
3. **SB1:** run existing tracked table validation and then construct documented forcing in an ephemeral authorized environment. Do not invent missing measurements or treat gridded ERA5 as an in-situ chamber measurement.
4. **SB4:** reuse independently checked SB1 ERA5, and retain explicit labels that the chamber profiles are reconstructed (constant reported mean or scaled SB1 profile); do not claim real five-minute SB4 time series were observed.
5. **D3:** if original blind key material cannot be recovered, state `ORIGINAL_PRIVATE_REBLINDING_NOT_REPRODUCIBLE`. A **new**, prospectively sealed and preregistered reblinding experiment may be conducted, but cannot be substituted for the original historical D3 run or its SHA.
6. **Dataset-specific strict qualification:** manually run `.github/workflows/external-evidence.yml` with `mode=strict`, `dataset=SB1`, `SB4`, `ERA5_ACCEPTANCE` or `D3_PRIVATE_REBLIND_SECRET`, but only after that dataset has been securely provisioned and validated. The default `mode=audit` reports readiness only. `dataset=ALL` requires every declared dataset, including private D3 material.

GitHub hosted runners are ephemeral. Repository secrets protect *access tokens*, not large datasets. Using a private object store or controlled runner to supply approved data requires its own licensing, threat-model and checksum audit. A PASS on a selected dataset is not a PASS on unselected datasets.

## Criteria to close issue #119

- Document official source/version/license and redistribution ruling for each input.
- Record exact raw-byte SHA-256 and independently validated processing hashes against existing test contracts.
- Demonstrate independent calibration/holdout discipline, no secret disclosure and no model-prediction substitution.
- Obtain and archive a successful strict run for **each** required dataset actually available; classify unrecoverable historical D3 evidence explicitly rather than inventing secrets.
- Only then reconsider external scientific readiness. Keep empirical, site, regulatory and original executable equivalence claims disabled until independently supported.
