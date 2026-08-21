# V3-P6.3 independent soil HTO boundary review

Review verdict: `PASS_BOUNDARY_AND_CONSERVATION`

Review target: `codex/v3-p6-3-soil-hto`

Review base: `1b3966d9f5de23fe226c27b50029163dc2c063e9`

## Review method

The P6.3 implementation was checked with a separate architecture-test file
against the execution plan. The review used the current worktree and Git
diff as the source of truth and checked both required behavior and forbidden
cross-module paths.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| New module is isolated | All new source paths are under `plant/soil_v3/` | PASS |
| Required soil state exists | `SoilState` contains all eight required fields | PASS |
| Inventory is authoritative | Concentration is checked as inventory divided by water content | PASS |
| State is immutable | Frozen dataclass and `with_inventory()` return a new state | PASS |
| No root/plant state exists | No root, plant, TFWT, or OBT state fields/imports | PASS |
| Deposition boundary is respected | Solver consumes `deposition_flux_bq_m2_s` only | PASS |
| Layer transport seam exists | Signed `transport_flux_bq_m2_s` supports donor `-F`/receiver `+F` | PASS |
| Decay is explicit | `lambda = ln(2) / tritium_half_life_s` | PASS |
| Conservation is auditable | Balance ledger residual is tested at zero tolerance scale | PASS |
| V1/V2 paths are unchanged | Legacy soil, coupling, plant, and configuration paths have no diff | PASS |
| External activation is absent | No UFOTRI database, trusted registry, foodchain, dose, or CTEAS-Atmos import | PASS |

## Limitations retained by the review

The transport flux is a prescribed interface, not a hydrological calculation.
The solver uses a constant-flux single-layer analytical step and does not
implement root uptake, plant coupling, foodchain, dose, empirical validation,
or production parameterization.

```text
SOIL_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

Review conclusion: the requested P6.3 isolated soil HTO software boundary and
conservation behavior are implemented; no broader environmental or regulatory
claim is supported.
