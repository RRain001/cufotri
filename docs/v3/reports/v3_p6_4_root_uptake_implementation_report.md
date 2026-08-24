# V3-P6.4 root uptake and Soil-Plant coupling implementation report

Status: PASS_ROOT_UPTAKE_IMPLEMENTED

Branch: codex/v3-p6-4-root-uptake

Base: d38ae03536b5e9fd027012f0b2e68402310551c7

## Scope

This stage closes the first typed Soil -> Root -> TFWT transfer boundary:

    SoilState
        |
        v
    RootUptakeSolver
        |
        v
    RootFlux
        |
        v
    TFWTStorageSolver
        |
        v
    TFWTState

The implementation is opt-in and remains separate from the V1/V2 runtime.
It does not activate the UFOTRI parameter database, change configuration
defaults, connect foodchain or dose, or connect CTEAS-Atmos.

## New root_v3 package

The package is src/cteas_ufotri/plant/root_v3:

- root_state.py defines the immutable RootState transfer record;
- root_solver.py defines RootUptakeForcing, explicit RootParameters,
  RootUptakeSolver, and the source-inventory ledger;
- validation.py applies fail-closed identifier, time, provenance, unit, and
  provisional-parameter checks;
- __init__.py exposes the frozen public API.

RootState contains the required fields:

| Field | Contract |
|---|---|
| plant_identifier | Required plant identity |
| root_zone_identifier | Required root-zone identity |
| uptake_inventory_bq_m2 | Integrated transfer inventory in Bq m^-2 |
| uptake_flux_bq_m2_s | Instantaneous transfer flux in Bq m^-2 s^-1 |
| timestamp | Timezone-aware UTC end time of the interval |
| provenance | Immutable source metadata |

RootState is frozen and exposes inventory() and flux(). RootFlux is the
semantic public alias for this state-bearing flux record. It contains no
TFWT, OBT, foodchain, dose, or whole-plant compartment fields.

## Root equation and dimensional contract

For one constant-concentration interval:

    J_root = k_root * C_soil

The dimensional contract is:

| Quantity | Unit |
|---|---|
| C_soil from SoilState.concentration() | Bq m^-3 water |
| k_root | m s^-1 |
| J_root | Bq m^-2 s^-1 |
| J_root times interval | Bq m^-2 |

The coefficient must be supplied explicitly through RootParameters or the
k_root_m_s constructor argument. It is required to carry the status
provisional. There is no hidden default, UFOTRI lookup, config lookup, or
production activation.

RootUptakeSolver reads the soil inventory and concentration through the public
SoilState methods. If the requested interval transfer exceeds the source soil
inventory, the operation fails closed rather than creating negative source
activity.

## Root-to-TFWT boundary

TFWTStorageSolver retains the existing leaf exchange input and accepts an
optional root_uptake_flux argument containing RootFlux. The TFWT solver alone
updates TFWT inventory and concentration. Its TFWTStorageBalance now records
root_uptake_input_bq_m2 and includes the root transfer in the conservation
residual. TFWTState.advance forwards the same typed boundary.

The root module does not import or modify TFWTState or OBTState. It only emits
the RootFlux consumed by the storage solver.

## Source and activation boundary

The only production-source changes are:

- new plant/root_v3 files;
- the optional RootFlux input and ledger field in plant/tfwt_v3.

No source under the V1/V2 plant, soil, coupling, foodchain, dose, or
configuration paths was changed. No parameters file or trusted external
evidence registry was changed.

## Deliberate exclusions

P6.4 does not implement:

- root geometry, root density, soil-water flow, diffusion, or competition;
- a calibrated or validated UFOTRI root uptake coefficient;
- automatic mutation of the source SoilState;
- foodchain, harvest, dose, or CTEAS-Atmos coupling;
- empirical, field, regulatory, or full V3 physics validation.

The P6.4 status therefore does not imply V3 physics readiness.

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
