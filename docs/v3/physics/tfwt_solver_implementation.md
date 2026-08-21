# V3-P6.2B-2 TFWT Dynamic Solver Implementation

Status: `TFWT_STORAGE_ONLY_NOT_PRODUCTION_PHYSICS`

## Scope

This stage adds a new V3 TFWT storage pathway:

```text
LeafExchangeFlux [P6.2B-1, already computed]
        |
        v
TFWTStorageSolver
        |
        v
updated TFWTState
```

The solver does not recompute resistance, access atmospheric dispersion, read
ERA5, activate a parameter database, or connect the default V1/V2 runtime. It
does not implement OBT, root uptake, soil feedback, foodchain, dose, or
CTEAS-Atmos coupling.

The repository already has the V1/V2 file
`src/cteas_ufotri/plant/tfwt.py`. To preserve that import path, the new V3
package is isolated at:

```text
src/cteas_ufotri/plant/tfwt_v3/
    __init__.py
    tfwt_state.py
    tfwt_solver.py
    validation.py
```

## TFWTState

`TFWTState` contains:

| Field | Unit | Contract |
|---|---|---|
| `plant_identifier` | controlled string | Required plant identity |
| `crop` | controlled string | Crop metadata for future parameter lookup |
| `growth_stage` | controlled string | Growth-stage metadata for future parameter lookup |
| `tfwt_concentration_bq_kg_water` | `Bq kg^-1 water` | Non-negative TFWT concentration |
| `tfwt_inventory_bq_m2` | `Bq m^-2` | Non-negative area-normalized TFWT inventory |
| `water_content_kg_m2` | `kg water m^-2` | Positive fixed water basis in P6.2B-2 |
| `time` | timezone-aware UTC | State timestamp |
| `provenance` | immutable metadata | Source id/version, artifact SHA-256, spatial reference, temporal resolution |

The state invariant is:

```text
I_TFWT = C_TFWT * W_p
```

No OBT, root, soil, dose, edible-product, or atmospheric state is stored.

## Storage equation

The solver consumes the signed P6.2B-1 flux directly:

```text
dI_TFWT/dt = F_leaf_exchange
              - F_water_loss
              - F_transformation
```

At fixed plant water content:

```text
dC_TFWT/dt = (1 / W_p)
              * (F_leaf_exchange
                 - F_water_loss
                 - F_transformation)
```

All fluxes are `Bq m^-2 s^-1`, inventory changes are `Bq m^-2`, and the
interval is seconds. Positive `F_leaf_exchange` increases TFWT; negative
`F_leaf_exchange` decreases TFWT. Water-loss and transformation are explicit
non-negative external rate arguments. They are not calculated by this stage,
and the transformation term does not create OBT state.

Each step returns an auditable `TFWTStorageBalance` containing integrated leaf
input, water loss, transformation, storage change, and residual. A step that
would create negative inventory fails closed.

## Parameter and activation boundary

The TFWT solver has no direct parameter lookup. Resistance parameters remain
behind the P6.2B-1 structural P6.1 seam, which calls
`lookup(..., production=False)` and rejects missing or ACTIVE values. This
stage adds no parameter file, no numeric UFOTRI value, no default, and no
trusted registry entry.

```ini
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = FALSE
UFOTRI_DATABASE_ACTIVE = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
V3_PHYSICS_READY = FALSE
```

## Non-production limitation

This is a storage-equation implementation and interface test, not complete
validated plant physics. Water content is fixed, the solver does not determine
resistance or plant-water equilibrium, and no experimental evidence is used.
P6.2B-3 or a later scope must not add OBT or root/soil terms without a new
contract and independent review.
