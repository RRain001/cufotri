# Rural stack short case

From repository root, run the deterministic case:

```bash
.venv/bin/python -m cteas_ufotri.cli
```

Or the ignored local ERA5 sample:

```bash
.venv/bin/python -m cteas_ufotri.cli \
  --era5 data/era5/era5_surface_2025-06-01_2025-06-02.csv \
  --output-directory outputs/rural_stack_short_case_era5
```

The source (117.141610855 E, 31.939774444 N), 70 m stack, 1.0e9 Bq s-1
test release, fixed 15 m plume rise, 600 s internal step, and 48 h duration are
all declared in YAML. The downloaded ERA5 nearest point is 117.25 E, 32.00 N.

Exercise all optional atmospheric/secondary modes:

```bash
.venv/bin/python -m cteas_ufotri.cli \
  --case configs/advanced_test_case.yaml
```

This 24 h case enables simplified Briggs rise, Turner stability, an 800 m
reflecting mixing layer, a three-hour root-uptake delay, and empirical
REEM/DIFF/ZT soil re-emission.
