# ERA5 input audit

Audit date: 2026-07-24

## Local product

- Dataset: `reanalysis-era5-single-levels-timeseries`
- Requested point: 117.141610855 E, 31.939774444 N
- Returned nearest grid point: 117.25 E, 32.00 N
- Period: 2025-06-01 00:00 through 2025-06-02 23:00 UTC
- Rows: 48 hourly records
- Local raw files: ignored CSV plus preserved CDS ZIP under `data/era5/`

The CSV has no embedded unit attributes, so units are controlled by the ERA5
mapping contract and dataset definitions:

| CSV | Mapped field | Unit / sign | Handling |
|---|---|---|---|
| `t2m` | temperature | K | retained in K internally; Celsius helper available |
| `d2m` | dew point | K | used for RH and VPD |
| `u10`,`v10` | 10 m wind components | m s-1 | speed/direction; rural power profile for stack wind |
| `tp` | hourly precipitation | m interval-1 | divided by actual interval seconds |
| `ssrd` | downward solar energy | J m-2 interval-1 | divided by interval; not treated as net |
| `strd` | downward thermal energy | J m-2 interval-1 | retained as downward; not treated as net thermal |

The time-series product delivered per-hour interval accumulations for this
request. `configs/era5_mapping.yaml` therefore selects `interval`. The reader
also supports `cumulative_with_resets`, converting differences and treating a
negative difference as a new accumulation cycle.

Because this product lacks both net shortwave and net longwave components, the
test case uses the documented provisional radiation fallback: absorbed
shortwave (`0.77 * ssrd/dt`) minus 50 W m-2 net longwave loss. Replacing that
provider does not alter the water or HTO balance equations.

`scripts/verify_acceptance.py --recompute` reads this ignored CSV without
modifying it, records path and SHA256 in temporary provenance, and recomputes
the 48 h ERA5 case without downloading ERA5.
