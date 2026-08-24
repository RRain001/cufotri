# V3-P6.6A food consumption and intake pathway implementation report

Status: PASS_INTAKE_PATHWAY_IMPLEMENTED

Branch: codex/v3-p6-6a-intake-pathway

Base: be183807d56f0b02f85b67b5276098fcee7bc17e

## Scope

This stage establishes the first human exposure inventory boundary:

    FoodInventory
         |
         v
    FoodIntakeSolver
         |
         v
    IntakeState

The package is opt-in and isolated from the V1/V2 runtime. It does not
implement dose coefficients, committed dose, regulatory assessment, UFOTRI
parameter activation, or CTEAS-Atmos coupling.

## intake_v3 package

The package is `src/cteas_ufotri/exposure/intake_v3`:

- `intake_state.py` defines the immutable `IntakeState` record;
- `intake_solver.py` defines immutable `ConsumptionParameters` and
  `FoodIntakeSolver`;
- `validation.py` applies fail-closed identity, timestamp, provenance, unit,
  mass, amount, and provisional-parameter checks;
- `__init__.py` exposes the public boundary.

`IntakeState` contains the required fields:

| Field | Contract |
|---|---|
| `consumer_identifier` | Stable human/consumer identity |
| `age_group_identifier` | Explicit age-group identity; no mixing |
| `food_product_identifier` | Product identity matched against `FoodInventory` |
| `consumption_rate` | Annual consumed food amount |
| `consumption_rate_unit` | Exact `kg/year` contract |
| `intake_inventory_bq` | Annual intake activity |
| `time_period` | Exact `annual` contract |
| `timestamp` | Timezone-aware UTC source time |
| `provenance` | Checked immutable source metadata |

The public methods are `inventory()`, `consumer()`, and `food_product()`.
`FoodIntakeSolver.advance()` returns `IntakeState` and does not mutate the
input `FoodInventory`.

## Consumption equation and explicit mass basis

P6.5 `FoodInventory` stores total product activity in Bq. A product mass is
therefore required to derive the activity concentration; it is an explicit
field of `ConsumptionParameters`, not a default:

    C_food [Bq kg^-1]
      = M_food [Bq] / m_food [kg]

    I_food [Bq year^-1]
      = C_food [Bq kg^-1] * R_consumption [kg year^-1]

The implementation rejects non-positive food mass, negative consumption,
non-matching product identifiers, and unit tokens other than `Bq/kg`, `kg`,
and `kg/year` at their respective boundaries. The annual intake inventory is
checked finite and non-negative.

## Parameter and activation boundary

`ConsumptionParameters` requires `parameter_status = "provisional"` and
checked provenance. The solver imports neither a parameter database nor
configuration values. No configuration, parameter, trusted registry, dose,
legacy V1/V2, or CTEAS-Atmos path was changed.

## Deliberate exclusions

P6.6A does not implement:

- dose coefficients or any dose calculation;
- committed dose or effective-dose aggregation;
- regulatory compliance or regulatory age-group lookup;
- population distributions or risk calculations;
- food processing, yield dynamics, or validated consumption data;
- automatic parameter-database loading;
- CTEAS-Atmos coupling or V3 physics validation.

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
    V1_V2_DEFAULT_PATH_CHANGED = FALSE
