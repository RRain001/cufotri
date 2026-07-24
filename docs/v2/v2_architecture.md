# V2 architecture

V2 retains the V1 calculation kernel and adds bounded modules around explicit
inventory/flux interfaces:

```text
forcing + configured source
  -> atmospheric plume/depletion ledger
  -> dry + wet surface inputs
  -> soil mode (surface 5 cm | optional three box)
  <-> crop leaf/root exchange and TFWT/OBT inventories
  -> harvested food inventories
  -> optional animal/milk/beef inventories
  -> pathway- and age-resolved research-screening dose
  -> uncertainty/sensitivity runner
```

## Package boundaries

- `atmosphere/`: concentration, dry/wet source depletion, deposited-activity
  ledger. It owns no dynamic air inventory.
- `soil/`: water and HTO inventories and inter-layer transfers.
- `plant/` and `crop/`: leaf exchange, phenology, whole/edible TFWT and OBT.
- `foodchain/`: food and animal inventory transfers and boundary products.
- `dose/`: pure calculations from exposure/concentration inputs and configured
  coefficients; no transport state mutation.
- `analysis/`: deterministic sampling and sensitivity summaries.
- `coupling/`: time ordering, transfer limiting, and combined ledgers.
- `outputs/`: diagnostics and provenance only.

## Interface rules

1. Continuous fluxes are SI per second; inventories are Bq m-2 unless a
   product boundary explicitly uses Bq, Bq kg-1, Bq L-1, or Bq m-3 water.
2. Every internal transfer is computed once and applied with opposite signs.
3. Every external loss is named in a boundary ledger.
4. Mode selection and numerical values are configuration data.
5. V1 states remain readable. V2-only states have zero/default construction
   paths and do not alter an `off`-mode trajectory.
6. Optional experimental soil code cannot change `ufotri_surface_5cm`.

## Time scales

Atmospheric and surface coupling retain the configured internal step and
piecewise forcing. Crop, food, and dose integrations may aggregate to longer
steps only through conservative integration of flux histories. No hourly or
daily rate is used without explicit conversion to s-1.

