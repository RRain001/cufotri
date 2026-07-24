# V2 end-to-end cases

Run all five cases and the uncertainty/sensitivity sample in a chosen output
directory:

```bash
.venv/bin/python scripts/run_v2_end_to_end.py --output /tmp/cteas_v2_e2e
```

All cases inherit the frozen stack at 117.141610855 E, 31.939774444 N,
70 m, rural land use, HTO.

| Case | Duration / purpose |
|---|---|
| `v2_era5_72h_wet_deposition` | one-hour release, 72 h wet-deposition follow-up |
| `v2_accident_plant_obt_14d` | one-hour accident and 14 d plant OBT |
| `v2_crop_ingestion_season` | 14 d leafy-crop ingestion |
| `v2_pasture_milk_pathway` | 14 d pasture-cow-milk transfer |
| `v2_full_adult_dose` | 14 d full adult screening dose |

The repository contains only 48 h of matching ERA5. The 72 h case therefore
uses those 48 h followed by an explicit 24 h deterministic configured
extension. The extension is named in provenance; no forcing row is silently
repeated. This is a remaining limitation, not a 72 h ERA5 observational claim.

Each case writes `results.csv`, eight required pathway/diagnostic figures, and
`provenance.json` with Git/worktree, Python/dependencies, config and input
hashes, modes, runtime timestamps, and output hashes. The suite additionally
writes fixed-seed LHS uncertainty and OAT sensitivity JSON/figures.

The 2026-07-24 temporary-directory recomputation produced 432 steps for the
72 h case and 336 steps for each 14 d case. Maximum surface-box relative
residuals were between 4.17e-16 and 6.04e-16. Wet depletion was non-zero in the
ERA5/hybrid case; plant OBT, crop dose, milk concentration, and full adult dose
were non-zero in their corresponding cases.
