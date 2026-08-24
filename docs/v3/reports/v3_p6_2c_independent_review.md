# V3-P6.2C independent boundary review

Review verdict: `PASS_BOUNDARY_AND_BALANCE`

Review target: `codex/v3-p6-2c-obt-solver`

Review base: `8164b0b4a7e0a32aa34aac130cfb3809d4cbc354`

## Review method

The implementation was checked against the P6.2C execution plan using a
separate architecture-test file and a separate pytest process from the unit
test matrix. The review treated the current worktree and Git diff as the
source of truth. It checked both positive requirements and forbidden paths.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| OBT module is isolated | `src/cteas_ufotri/plant/obt_v3/` contains the new state, solver, validation, and package export | PASS |
| State is inventory-based | `OBTState.obt_inventory_bq_m2` is authoritative and concentration is checked from explicit plant mass | PASS |
| TFWT/OBT ratio is not stored | No `tfwt_obt_ratio` state field; no ratio participates in the solver | PASS |
| TFWT public boundary is respected | Solver calls only `inventory()` and `activity_concentration()`; no TFWT internal field access | PASS |
| Resistance is not recomputed | No resistance-chain import or resistance calculation in `obt_solver.py` | PASS |
| Biological forcing seam exists | `PlantBiologicalForcing` exposes `is_daylight` plus reserved optional fields | PASS |
| Required dynamics are covered | Formation, zero-TFWT loss, conservation, and day/night tests all pass | PASS |
| V1/V2 paths remain unchanged | Legacy plant and coupling files have no diff from the review base | PASS |
| Configs and parameters remain unchanged | Architecture test finds no changed `configs/` or `parameters/` paths | PASS |
| Trusted registry remains unchanged | Architecture test finds no changed trusted-registry file | PASS |
| External activation is absent | No UFOTRI production lookup, `production=True`, foodchain, dose, soil, or CTEAS-Atmos import | PASS |

## Limitations retained by the review

The rates and day/night multipliers are explicit provisional test controls,
not UFOTRI validated parameters. The solver holds TFWT inventory and forcing
constant during a step and has no annual integration, plant growth, soil,
foodchain, dose, or empirical validation. The target therefore remains:

```text
OBT_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

Review conclusion: the requested P6.2C software boundary is implemented and
verified; no broader scientific or production-readiness claim is supported.
