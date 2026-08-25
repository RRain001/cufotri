# V3-P6.6A independent food-intake boundary review

Review verdict: PASS_INTAKE_PATHWAY_BOUNDARY

Review target: codex/v3-p6-6a-intake-pathway

Review base: be183807d56f0b02f85b67b5276098fcee7bc17e

## Review method

The review uses the current worktree, the P6.6A architecture tests, the
cross-stage typed-boundary suite, and explicit Git path diffs. Software
interface behavior is kept separate from physical, empirical, and regulatory
claims.

## Findings

| Review item | Evidence | Verdict |
|---|---|---|
| New module is isolated | Source additions are under `exposure/intake_v3` | PASS |
| Required `IntakeState` exists | All nine required fields are present | PASS |
| State is immutable | `IntakeState` is a frozen dataclass | PASS |
| Public state boundary exists | `inventory()`, `consumer()`, `food_product()` are exposed | PASS |
| Food source is public-only | Solver calls `FoodInventory.inventory()` and `.product()` | PASS |
| Units are explicit | `Bq/kg` times `kg/year` produces `Bq/year` | PASS |
| Mass basis is explicit | `food_product_mass_kg` is required and positive | PASS |
| Age groups remain separate | Adult and child produce separate states | PASS |
| Parameters remain provisional | Non-provisional status is rejected | PASS |
| Downstream boundary is clean | No downstream-result fields or imports are added | PASS |
| Protected paths are unchanged | No config, parameter, plant, dose, or registry diff | PASS |
| External activation is absent | No UFOTRI database or automatic database loading | PASS |
| V1/V2 defaults remain unchanged | Existing default flags remain off/false | PASS |

## Boundary disposition

Implemented:

    FoodInventory -> FoodIntakeSolver -> IntakeState

Not implemented:

    IntakeState -> downstream radiological result

The solver emits an annual intake activity inventory and does not mutate the
food product state. The annual consumption and product-mass values are
explicit provisional inputs; they are not validated UFOTRI or regulatory
parameters.

## Limitations retained

The food mass basis and consumption amount are design inputs. The stage does
not model food availability, processing, yield, consumption distributions,
dose conversion, committed dose, population risk, regulatory compliance,
observational validation, or CTEAS-Atmos coupling.

## Acceptance flags

    P6_6A_STATUS = PASS_INTAKE_PATHWAY_IMPLEMENTED
    LEAF_RESISTANCE = TRUE
    TFWT_SOLVER = TRUE
    OBT_SOLVER = TRUE
    SOIL_SOLVER = TRUE
    ROOT_UPTAKE = TRUE
    FOOD_TRANSFER = TRUE
    INTAKE_PATHWAY = TRUE
    UFOTRI_PARAMETER_IMPORTED = FALSE
    UFOTRI_ACTIVE_DATABASE = FALSE
    V3_PHYSICS_READY = FALSE
