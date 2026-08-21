# V3-P6.5 independent plant-to-food boundary review

Review verdict: PASS_FOOD_TRANSFER_BOUNDARY

Review target: codex/v3-p6-5-food-transfer

Review base: 70ff7291a8f12359514107bfb9b17bc1d679f529

## Review method

The review uses the current worktree, the P6.5 architecture test, the
cross-stage architecture tests, and explicit Git path diffs. Software
interface behavior is kept separate from physical, empirical, and regulatory
claims.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| New module is isolated | Source additions are under plant/food_v3 | PASS |
| Required HarvestState exists | All eight required fields are present | PASS |
| State is immutable | HarvestState and FoodInventory are frozen dataclasses | PASS |
| Public product boundary exists | inventory() and product() are exposed | PASS |
| OBT source is public-only | Solver calls obt_state.inventory() | PASS |
| TFWT source is public-only | Solver calls tfwt_state.inventory() | PASS |
| Units are explicit | Bq m^-2 times m^2 produces Bq | PASS |
| Fractions remain provisional | HarvestParameters requires provisional status | PASS |
| Harvest conservation closes | FoodTransferBalance residual is tested at zero | PASS |
| Product boundary is clean | No dose, ingestion, population, or CTEAS-Atmos imports | PASS |
| Dose remains separate | No dose source path changed and no dose state exists | PASS |
| External activation is absent | No UFOTRI database, config, parameter, or registry change | PASS |
| Prior V3 and V1/V2 paths are unchanged | Protected-path architecture checks pass | PASS |

## Boundary disposition

Implemented:

    Plant TFWT / OBT -> HarvestState -> FoodInventory

Not implemented:

    FoodInventory -> ingestion -> dose

FoodTransferSolver emits a product inventory and does not mutate the source
plant states. The optional TFWT food component is explicit; OBT transfer is
the primary required pathway.

## Limitations retained

The harvest area and fractions are design inputs, not validated UFOTRI
parameters. The module does not model crop yield, edible biomass composition,
food processing, animal transfer, ingestion, dose, age groups, or regulatory
quantities. The end-to-end toy pathway is a software and conservation check,
not observational or regulatory validation.

## Acceptance flags

    P6_5_STATUS = PASS_FOOD_TRANSFER_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    FOOD_TRANSFER = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
