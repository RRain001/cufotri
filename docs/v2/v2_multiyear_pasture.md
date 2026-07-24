# V2 perennial pasture and multiyear phenology

Crop configuration distinguishes:

```text
annual_single_harvest
annual_multiple_harvest
perennial_dormant_season
perennial_evergreen
```

The pasture default is `perennial_dormant_season`, with non-zero dormant LAI
0.25, growing-season maximum LAI 4.0, cutting days 150/220/290, and a 0.50
fraction removed per cut. A cut removes the same fraction from whole-plant
TFWT/OBT and edible TFWT/OBT. Remaining plant and edible activity persists;
root/remaining biomass is not reset. Usable edible activity and removed
whole-plant activity are reported separately as harvested and cut-plant
boundaries.

Recompute the formal two-year case:

```bash
.venv/bin/python - <<'PY'
from cteas_ufotri.case import run_short_case
from cteas_ufotri.config import load_configuration

config = load_configuration(
    "configs/default_parameters.yaml",
    "configs/v2/v2_pasture_multiyear_2y.yaml",
)
frame = run_short_case(config)
print(frame.loc[frame["harvest_event"]])
PY
```

The 2025-2026 result contains exactly six cut transitions (DOY 150, 220, and
290 in each year). The maximum closure residual is
`4.9241e-16`. At 2025 year end, dormant LAI remains 0.25 and plant TFWT/OBT
remain 4.0294/0.8064 Bq m-2; there is no 31 December reset. On 15 May 2026 LAI
has regrown to 1.7078. Final cumulative boundaries are:

```text
edible harvested HTO = 1012.312962 Bq m-2
edible harvested OBT = 173.519677 Bq m-2
cut whole-plant HTO = 188.488361 Bq m-2
cut whole-plant OBT = 37.719512 Bq m-2
```

The two-year case uses a six-hour audit step and a one-day source release. It
tests continuity, cutting and conservation; it is not a site-calibrated pasture
production forecast.
