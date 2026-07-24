# V2 scope

Status: `V2_SCOPE_STATUS = FROZEN`

Primary physical source: `ufotri_manual.md`.
Implementation contract: reviewed equations in `docs/equations/`.
Baseline: `formal-minimal-baseline-v1` at
`6918440faa3455b848f43589784672f3bfabfe3d`.

## Claim boundary

The V2 candidate is an:

```text
HTO atmosphere-soil-plant-food pathway-dose research prototype
```

It includes HTO Gaussian transport, dry and wet plume depletion and deposition,
formal single-layer surface soil plus a standalone experimental three-box API,
bidirectional leaf exchange, TFWT and OBT,
crop phenology and edible compartments, minimal plant/milk/beef pathways,
research-screening public dose, uncertainty/sensitivity analysis, benchmarks,
and recomputable acceptance.

It is not a line-by-line reproduction of all UFOTRI; it excludes HT oxidation
and HT-specific soil chemistry, regulatory validation, dynamic three-dimensional
atmospheric mass conservation, multi-nuclide use, and medical dosimetry.

## Frozen compatibility contracts

- V1's single 0-5 cm soil, 3600 s feedback delay, Eq. (40) radiation-only
  shading, steady Gaussian atmospheric ledger, and 61-test regression remain
  available and unchanged.
- Every V2 process is selected by configuration; disabling it reproduces the
  corresponding V1 path.
- Internal inventories and fluxes use SI units. Fresh mass, dry mass, water
  volume, activity, and dose conversions are explicit.
- Case values and empirical parameters live in YAML and carry one of:
  `MANUAL_EXACT`, `MANUAL_DERIVED`, `LITERATURE_PARAMETERIZATION`,
  `PROJECT_EXTENSION`, or `PROVISIONAL`.
- `formal-minimal-baseline-v1` is immutable. V2 status never changes the claim
  attached to that tag.

## Required subsystem disposition

| Subsystem | V2 disposition |
|---|---|
| Atmospheric HTO transport | implement, preserving V1 Gaussian contract |
| Fallout / dry depletion | retain tested project simplification |
| Washout / wet deposition | implement source-loss and surface ledger |
| Air-soil exchange | retain deposition and conservative re-emission |
| Soil re-release | retain basic mode; audit empirical Eq. (44) mode |
| Air-leaf exchange | implement configurable bidirectional resistance |
| Root uptake / TFWT / OBT | extend to crop and edible compartments |
| Crop growth / food chain | project extension with explicit inventories |
| Inhalation / skin / ingestion / dose | research-screening implementation |
| Age groups | adult, child, infant configuration |
| Probability / uncertainty | reproducible MC, LHS, and OAT |
| Three-box soil | experimental standalone project extension; not formal RC1 coupling |
