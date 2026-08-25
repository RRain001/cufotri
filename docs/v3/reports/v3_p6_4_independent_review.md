# V3-P6.4 independent root uptake boundary review

Review verdict: PASS_ROOT_UPTAKE_BOUNDARY

Review target: codex/v3-p6-4-root-uptake

Review base: d38ae03536b5e9fd027012f0b2e68402310551c7

## Review method

The review uses the current worktree, the P6.4 architecture test, the
cross-stage architecture tests, and the explicit Git path diff as evidence.
The review separates software-interface behavior from physical or empirical
validation.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| New root module is isolated | Source additions are under plant/root_v3 | PASS |
| Required RootState exists | All six required fields are present | PASS |
| State is immutable | RootState is a frozen dataclass | PASS |
| Root output is typed | RootFlux alias and TFWT validation are explicit | PASS |
| Soil input uses public API | Solver calls inventory() and concentration() | PASS |
| Equation units are explicit | k_root m s^-1 times C_soil Bq m^-3 gives flux Bq m^-2 s^-1 | PASS |
| Coefficient remains provisional | Explicit parameter status is required | PASS |
| Source inventory is protected | Excess transfer fails closed and ledger residual is tested | PASS |
| TFWT remains storage owner | Only TFWTStorageSolver updates TFWT inventory | PASS |
| Forbidden pathways are absent | No OBT, foodchain, dose, or CTEAS-Atmos solver import | PASS |
| External activation is absent | No UFOTRI database, configs, parameters, or trusted registry change | PASS |
| Legacy runtime is unchanged | V1/V2 plant, soil, coupling, and defaults have no diff | PASS |

## Boundary disposition

The implemented pathway is:

    SoilState -> RootUptakeSolver -> RootFlux -> TFWTStorageSolver -> TFWTState

The root solver is not allowed to create or mutate TFWTState. The TFWT solver
is the sole owner of TFWT storage update and records the root input in its
balance. OBT, foodchain, dose, and CTEAS-Atmos remain outside the pathway.

## Limitations retained

The uptake coefficient is an explicit provisional test parameter, not a
validated UFOTRI value. The equation uses soil-water concentration and an
effective coefficient; it does not model root geometry, transpiration,
advection, diffusion, competition, or field conditions. The root boundary
ledger is non-mutating and does not claim a complete soil transport update.
The tests are software and conservation checks, not observational or
regulatory validation.

## Acceptance flags

    P6_4_STATUS = PASS_ROOT_UPTAKE_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
