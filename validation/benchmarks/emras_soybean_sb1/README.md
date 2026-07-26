# EMRAS soybean SB1 PDF + ERA5 benchmark

`CASE_ID = EMRAS_SOYBEAN_SB1_PDF_ERA5_V1`

This directory contains a tracked, redistributable transcription of numeric
tables in the public IAEA report and the code/configuration needed to combine
them with local ERA5 reanalysis files. It is a research benchmark, not a
production-gate evidence package.

```text
BENCHMARK_CLASS = HYBRID_LITERATURE_REANALYSIS
EMPIRICAL_VALIDATION_CLAIM = FALSE
PRODUCTION_GATE_ELIGIBLE = FALSE
TRUSTED_REGISTRY_ELIGIBLE = FALSE
```

The source PDF and all ERA5 raw/processed files remain under
`validation/external_local/emras_soybean_sb1/` and are ignored by Git.
Published values were transcribed only from report tables. No figure was
digitized and no missing observation was invented.

## Reproduction

ERA5 is downloaded through the repository's audited CDS time-series entry
point. Repeat the command for the five coordinates in
`docs/v3/benchmarks/emras_soybean_sb1_site_resolution.md`, changing
`--output-dir` to the matching point identifier:

```bash
.venv/bin/python era5/download_era5_timeseries.py \
  --latitude 36.425 --longitude 127.373611 \
  --start-date 2001-05-20 --end-date 2001-10-06 \
  --variable 2m_temperature,2m_dewpoint_temperature,surface_pressure,10m_u_component_of_wind,10m_v_component_of_wind,total_precipitation,surface_solar_radiation_downwards,surface_thermal_radiation_downwards,total_cloud_cover \
  --format netcdf \
  --output-dir validation/external_local/emras_soybean_sb1/era5_raw/CENTRE \
  --execute
```

The credentials file is local and ignored. Do not copy it into this benchmark
or a log.

```bash
.venv/bin/python validation/benchmarks/emras_soybean_sb1/scripts/build_sb1_dataset.py
.venv/bin/python validation/benchmarks/emras_soybean_sb1/scripts/verify_sb1_dataset.py
.venv/bin/python validation/benchmarks/emras_soybean_sb1/scripts/prepare_sb1_era5.py
.venv/bin/python validation/benchmarks/emras_soybean_sb1/scripts/run_sb1_benchmark.py
```

The last command is permitted only under the frozen research protocol. Its
outputs are ignored and cannot satisfy the V3 empirical-evidence gate.
