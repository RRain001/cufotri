# V3-P6.5 plant harvest and food-transfer implementation report

Status: PASS_FOOD_TRANSFER_IMPLEMENTED

Branch: codex/v3-p6-5-food-transfer

Base: 70ff7291a8f12359514107bfb9b17bc1d679f529

## Scope

This stage establishes the plant-to-food inventory boundary:

    TFWT / OBT
         |
         v
    HarvestState
         |
         v
    FoodInventory

The package is opt-in and isolated from the V1/V2 runtime. It does not
implement dose, ingestion, population or regulatory age groups, UFOTRI
parameter activation, or CTEAS-Atmos coupling.

## food_v3 package

The package is src/cteas_ufotri/plant/food_v3:

- harvest_state.py defines immutable HarvestState and FoodInventory records;
- food_transfer_solver.py defines HarvestParameters, FoodTransferSolver,
  FoodTransferResult, and FoodTransferBalance;
- validation.py applies fail-closed identity, timestamp, provenance, unit,
  fraction, area, inventory, and provisional-parameter checks;
- __init__.py exposes the explicit public API.

HarvestState contains the required fields:

| Field | Contract |
|---|---|
| plant_identifier | Required source plant identity |
| crop_identifier | Required crop identity |
| growth_stage | Required harvest-stage label |
| harvest_fraction | Dimensionless OBT transfer fraction |
| harvest_inventory_bq | Total transferred activity in Bq |
| food_product_identifier | Stable product identity |
| timestamp | Timezone-aware UTC harvest time |
| provenance | Immutable source metadata |

HarvestState is frozen and exposes inventory() and product(). It contains no
dose, ingestion, population, or regulatory state. FoodInventory records total
food activity plus explicit OBT and TFWT components and exposes the same
inventory/product access boundary.

## Transfer equations and units

OBT source inventory and TFWT source inventory are public areal inventories in
Bq m^-2. An explicit harvest area converts them to total food activity:

    M_food,OBT [Bq]
      = f_h [1] * M_OBT [Bq m^-2] * A_h [m^2]

    M_food,TFWT [Bq]
      = f_w [1] * M_TFWT [Bq m^-2] * A_h [m^2]

The TFWT term is optional and is enabled only by an explicit
tfwt_harvest_fraction. Omission means that no TFWT component is transferred
in this event; it is not a hidden numeric production default.

HarvestParameters requires explicit plant/crop/stage/product identity,
harvest_fraction, harvest_area_m2, provenance, and provisional status. No
parameter database, config, trusted registry, or validated UFOTRI value is
read.

## Public source boundary

FoodTransferSolver reads OBTState.inventory() and TFWTState.inventory() only.
It does not inspect source inventory fields and does not mutate OBTState or
TFWTState. FoodTransferResult contains:

- HarvestState for the plant-to-food transfer event;
- FoodInventory for the product activity;
- FoodTransferBalance for source, component transfer, remaining inventory,
  and residual.

The balance is:

    OBT source + TFWT source
      = harvest transfer + remaining plant inventory + residual

The result supports explicit two-output unpacking as harvest state and food
inventory while retaining the auditable balance.

## Source and activation boundary

The only source additions are under plant/food_v3. Existing V3 OBT, TFWT,
soil, root, resistance, and pathway packages are not modified. V1/V2 plant,
soil, coupling, foodchain, and dose paths remain untouched. No configuration,
parameter, or trusted external-evidence registry file is changed.

## Deliberate exclusions

P6.5 does not implement:

- dose calculation or ingestion;
- population or regulatory age-group parameters;
- foodchain animal transfer;
- harvest mass/yield dynamics beyond the explicit area and fractions;
- validated UFOTRI harvest fractions;
- automatic mutation of plant source states;
- CTEAS-Atmos coupling or V3 physics validation.

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
