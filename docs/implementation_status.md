# Implementation status

Updated: 2026-07-24

Overall status: **COMPLETE — planned minimal HTO environmental system**

This completion statement applies to the requested atmosphere–topsoil–TFWT/OBT–
re-emission coupled system and its replaceable interfaces. It does not claim
equivalence to every UFOTRI food-chain or dose equation.

| Item | Status | Evidence / limitation |
|---|---|---|
| REPOSITORY_STRUCTURE_STATUS | PASS | package, configs, docs, tests, example output |
| UFOTRI_SPEC_EXTRACTION_STATUS | PASS_SCOPE | manual states/inputs/units/symbol conflicts/HT boundary extracted |
| ERA5_READER_STATUS | PASS_PROVISIONAL | CSV/NetCDF, UTC, actual intervals, cumulative resets, real 48 h data |
| PET_MODULE_STATUS | PASS_PROVISIONAL | Eq. 38-43 route tested; aerodynamic coefficient provisional |
| GAUSSIAN_ATMOSPHERE_STATUS | PASS | point/rectangular area, PG, wind rotation/profile, fixed/simple Briggs, mixing layer |
| SOIL_WATER_STATUS | PASS | 5 cm bucket, drainage, optional runoff |
| SOIL_HTO_STATUS | PASS | deposition/rain input/evap/root/drainage/decay and concentration identity |
| PLANT_TFWT_STATUS | PASS | root/transpiration, optional 3 h lag, disabled leaf interface |
| OBT_STATUS | PASS | formation/turnover, day/night option, internal conservation |
| REEMISSION_STATUS | PASS_PROVISIONAL | basic mass flux plus optional reconstructed REEM/DIFF/ZT |
| COUPLING_STATUS | PASS | explicit split, lagged rectangular area feedback, strict forcing validation |
| UNIT_TEST_STATUS | PASS | 43 tests passed |
| MASS_BALANCE_STATUS | PASS | all acceptance cases below 4.5e-16 relative error |
| END_TO_END_CASE_STATUS | PASS | synthetic/ERA5 48 h and advanced 24 h; CSV/grid + 6 plots + report |

## Resolved failed commands

1. `.venv/bin/python -m pytest -vv` initially returned 4 failures:
   YAML exponent parsed as text, `WaterBalance` field mismatch, and a moisture
   test point in the saturated reduction range. Fixed and rerun.
2. The second run returned 1 failure because a signed mass-balance residual was
   included in a non-negative physical-output check. Fixed and rerun.
3. `.venv/bin/python -m cteas_ufotri.cli` completed but emitted non-fatal
   Matplotlib/Fontconfig cache warnings. `MPLCONFIGDIR` and `XDG_CACHE_HOME` now
   point to writable temporary directories.
4. The first real-ERA5 chained validation stopped at 1/13 failed tests because
   the miniature CSV fixture used net-field headers (`ssr/str`) while asserting
   the downloaded-field fallback (`ssrd/strd`). The fixture headers were aligned
   with the real product and the chain was rerun.
5. The first accumulated-field test run returned two failures because pandas 3
   exposed the timestamp-difference array as read-only. `_interval_seconds`
   now requests a writable copy before setting the first interval, and the full
   suite is rerun after the fix.
6. Adding credential-source tests initially caused collection to fail because
   the legacy downloader only supported direct-script sibling imports. The ERA5
   utilities are now a package and the downloader supports both package-relative
   and direct-script imports.

## Known non-fatal warning

The first NetCDF fixture test emitted `numpy.ndarray size changed` once while
loading a compiled backend. The NetCDF test passed, and isolated `netCDF4`,
`cftime`, and `xarray` imports also pass with `RuntimeWarning` promoted to an
error. Retest this after dependency upgrades; it is not currently reproducible
as an import failure.

## Deliberately deferred extensions

These are outside the requested minimal HTO environmental system and are not
silently represented as implemented:

- multi-layer Richards/Darcy soil transport and spatially distributed land cells;
- full stability-specific regulatory Briggs formula variants;
- dynamic LAI/phenology and explicit plant-water storage dynamics;
- HT chemistry/oxidation, animals, food chains, ingestion, and dose;
- calibration/validation of provisional Penman aerodynamic, net-radiation
  fallback, and empirical REEM/DIFF/ZT coefficients against observations.

Next command:

```bash
.venv/bin/python scripts/verify_acceptance.py
```
