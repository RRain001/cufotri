# Assumptions and provisional defaults

- The default short case uses deterministic synthetic forcing. A 48 h ERA5
  point series was later downloaded and tested. Its returned nearest grid point
  is 117.25 E, 32.00 N rather than the requested stack coordinate.
- The time-series product supplies downward solar and thermal radiation, not
  both net components. The ERA5 case therefore uses absorbed shortwave
  (0.77) minus a provisional fixed 50 W m-2 net longwave loss; downward thermal
  radiation is not incorrectly treated as net thermal radiation.
- The source is 1.0e9 Bq s-1, stack rise is fixed at 15 m, stability is D, and
  the receptor is 1 km downwind. These are finite test values, not site claims.
- Soil depth is 0.05 m; initial/minimum/wilting/maximum water depths are
  0.010/0.0005/0.004/0.020 m.
- LAI is 1.5, plant water is 0.0005 m, and runoff is disabled.
- HTO deposition velocity is 0.005 m s-1. HT oxidation is excluded.
- The Penman aerodynamic SI coefficient (0.001 W m-2 Pa-1) is provisional
  because manual Eq. (38) is dimensionally incomplete in the available scan.
- Basic re-emission \(E_sC_s+T_pC_p\) is the default. Optional REEM/DIFF/ZT is
  an explicit engineering reconstruction calibrated by centralized reference
  evaporation, 10% h-1 radiative, 1% h-1 diffusive, and ZT half-life values.
- Re-emission feedback is midpoint-integrated over a configurable rectangular
  area. The default 1000 m by 1000 m footprint has 12 by 12 quadrature cells.
- `briggs_simple` is a replaceable buoyancy/momentum closure, not a complete
  stable/unstable Briggs implementation. Fixed rise remains the default.
- Mixing-layer reflection, Turner-style stability, rainwater HTO, and a
  three-hour root lag are implemented optional modes.
- Rainwater HTO defaults to zero. Multi-layer soil, dynamic LAI/phenology, HT,
  food chain, and dose remain outside the minimal environmental system.

## Formal minimal baseline v1 contracts

- Eq. (40) shades only the equilibrium-radiation term.
- Feedback uses one 1000 m by 1000 m rectangle and a 3600 s delay.
- The single 0–5 cm layer uses root uptake fraction 1.0; this is not the
  manual's roughly 20% share in a multi-layer root system.
- Winds below 0.5 m s-1 use and record an effective 0.5 m s-1 by default.
- Dry plume depletion is a segment-exponential engineering approximation.
  V2 wet scavenging uses the same competing-rate exponential. Its default mode
  remains `off` for V1 regression. Power-law coefficients are `PROVISIONAL`;
  precipitation is expressed in mm h-1.
- V2 distributes wet plume loss uniformly over a configured representative
  footprint. This is a `PROJECT_EXTENSION`, not the manual's full polar
  deposition field.
- V2 leaf exchange resistance defaults are
  `MANUAL_DERIVED_PROVISIONAL`. They implement the manual's resistance
  structure and day/night order of magnitude, but are not a crop-specific
  calibration. V1 remains `off`.
- V2 crop biomass, edible fraction, water content, seasonal dates, and
  phenology curves are replaceable `PROJECT_EXTENSION` defaults. They are
  deterministic test parameterizations rather than claims about the Hefei
  receptor or a specific agricultural survey.
- Minimal cow water/OBT loss, milk transfer, and 15.5 L d-1 milk production
  use manual Eq. (82)-(105) anchors. The 50 kg fresh feed d-1 and 50 L water
  d-1 defaults are `PROVISIONAL` replaceable screening values. One animal is
  normalized to 4000 m2 from the manual's 250 cows km-2.
