# Complete 72 h forcing inventory

`FORCING_72H_STATUS = PASS_72_OF_72_OBSERVED`

Here, `observed` means a value retrieved from the external ERA5 reanalysis
product rather than a project deterministic extension. ERA5 is a
data-assimilating reanalysis and is not a point-station observation.

## Source and coverage

- Product: Copernicus/ECMWF `reanalysis-era5-single-levels-timeseries`.
- Catalogue: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries>
- Licence: CC-BY-4.0.
- Point: 32.00 degrees north, 117.25 degrees east on the 0.25 degree
  atmospheric grid.
- UTC interval: 2025-06-01 00:00 through 2025-06-03 23:00.
- Coverage: 72 consecutive hourly rows; 72 external reanalysis, 0
  interpolated, 0 repeated, 0 extended, 0 missing.
- Catalogue check/download: 2026-07-25 UTC.

The raw CSV and archive are under the Git-ignored `data/era5/` directory. The
tracked acquisition manifest records paths and SHA-256 values. No credential
or raw download is committed.

## Variable and unit contract

| Column | Quantity | Raw unit | Time semantics | Model conversion |
|---|---|---|---|---|
| `u10`, `v10` | 10 m wind components | m s-1 | instantaneous | speed and direction |
| `t2m` | 2 m temperature | K | instantaneous | identity |
| `d2m` | 2 m dewpoint | K | instantaneous | identity; RH/VPD derived |
| `tp` | total precipitation | m | preceding 1 h accumulation | divide by 3600 s |
| `ssrd` | downward solar energy | J m-2 | preceding 1 h accumulation | divide by 3600 s and apply documented absorptivity fallback |
| `strd` | downward thermal energy | J m-2 | preceding 1 h accumulation | retained as source metadata; it is not mislabelled as net radiation |

ECMWF documents precipitation in metres and radiation accumulations in
J m-2; for hourly reanalysis the accumulation period is the hour ending at
the validity time. The reader therefore treats the time-series fields as
interval amounts, not forecast values requiring cross-row differencing.

## Integrity

| Artifact | Rows | SHA-256 |
|---|---:|---|
| Existing 2025-06-01 to 2025-06-02 CSV | 48 | `7100f02f3da570098cda4ff5e362d1ffb667fdf685dd29ee1c176d4339c6474c` |
| Added 2025-06-03 CSV | 24 | `e4df65990bb7529d091b539042875c774e526c0633b0c769f31a1c2ffe5eb70b` |
| Added CDS ZIP | n/a | `f186df9ded597e4ce7a23c06d3ebcd9a69c79e1211a159ab724925bc19cc1bb4` |
| Derived 72 h CSV | 72 | `f82f216dcf3550ddcbdf07cbc955850703732945d0b4f4ca86a857d71c41eddd` |

`scripts/prepare_observed_forcing.py` verifies identical column order,
monotonic unique UTC timestamps, a complete hourly grid, one coordinate, and
the exact row count before adding `forcing_status=observed`. It never modifies
the raw inputs.
