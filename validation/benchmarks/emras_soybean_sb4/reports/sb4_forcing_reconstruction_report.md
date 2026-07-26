# SB4 forcing-reconstruction report

```text
SB4_CHAMBER_PROFILE_STATUS =
PASS_TWO_TRANSPARENT_RECONSTRUCTED_PROFILES
SB4_ERA5_STATUS = PASS_REUSED_SB1_RAW_BY_CHECKSUM
SB4_OBSERVED_CHAMBER_CURVE_CLAIM = FALSE
```

Both chamber profiles satisfy the published one-hour mean of
`52,700 Bq mL-1 water` by trapezoidal integration over 13 five-minute points:

| profile | construction | mean |
|---|---|---:|
| `CONSTANT_REPORTED_MEAN` | constant at the reported mean | 52,700 |
| `SCALED_SB1_OBSERVED_SHAPE` | SB1 published shape scaled by 0.6969747065630683; unreported SB1 start boundary transparently assumed zero | 52,700 |

Every chamber row and every forcing-manifest entry is labelled
`RECONSTRUCTED`; `sb4_observed_curve_claim` is false. RUN_02 is a predefined
SB1 chamber temperature, humidity and illuminance-shape sensitivity, also
reconstructed rather than observed.

The workflow reuses the five read-only SB1 ERA5 raw responses without
redownloading them. Their checksums are bound in the generated manifest for
CENTRE, NORTH, SOUTH, EAST and WEST. Fourteen forcing files cover
`2001-08-09 09:25 +09:00` through `2001-10-05 23:00 +09:00` at continuous
five-minute spacing, with 16,580 rows per file.

For each profile, the seven predefined scenarios are the centre primary,
SB1-chamber-meteorology sensitivity, north/south meteorological sensitivities,
and low/mid/high background HTO cases. These scenarios assess forcing
robustness; none upgrades the evidence class.
