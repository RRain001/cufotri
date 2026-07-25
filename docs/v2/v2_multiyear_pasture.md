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
fraction removed per cut. Perennial plant TFWT/OBT is explicitly partitioned
into root and shoot inventories using the provisional configured root activity
fraction 0.30. A cut removes the configured fraction from shoot and edible
TFWT/OBT only; root activity remains in the plant inventory. Usable edible
activity and removed shoot activity are reported separately as harvested and
cut-plant compatibility boundaries.

For a growing season that crosses 31 December, the phenology fraction uses the
actual length of the applicable year. A season crossing 2025 uses 365 days;
one crossing leap year 2024 uses 366 days. The fraction advances by exactly
one calendar day across each year boundary.

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

The RC2 2025-2026 result contains exactly six cut transitions (DOY 150, 220,
and 290 in each year). The maximum closure residual is `5.27e-16`. At 2025
year end, dormant LAI remains 0.25; root TFWT/OBT are
9.34519/0.931567 Bq m-2 and shoot TFWT/OBT are
2.71066/1.48051 Bq m-2. There is no 31 December reset. On 15 May 2026 LAI has
regrown to 1.7078 and both root and shoot inventories remain positive. Final
cumulative boundaries are:

```text
edible harvested HTO = 1058.666822 Bq m-2
edible harvested OBT = 182.624961 Bq m-2
cut shoot HTO = 131.820827 Bq m-2
cut shoot OBT = 28.284563 Bq m-2
```

The two-year case uses a six-hour audit step and a one-day source release. It
tests continuity, cutting and conservation; it is not a site-calibrated pasture
production forecast.
