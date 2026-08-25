# V3 P6.2B Public Plant Pathway Interface

Status: `P6_2B_INTERFACE_FREEZE = PASS`

## Scope

This interface freeze connects the already isolated V3 resistance subsystem to
the P6.2B-2 TFWT storage state:

```text
AtmosphericHTOForcing
        |
        v
ResistanceState [precomputed by P6.2B-1]
        |
        v
LeafExchangeFlux
        |
        v
TFWTState
        |
        v
OBTState [future interface only; not implemented]
```

The public facade is under `src/cteas_ufotri/plant/v3/`. It consumes an
already validated `ResistanceState`; it does not reconstruct the resistance
chain, perform a parameter lookup, or connect to the default runtime.

The existing V1/V2 modules remain at `plant/leaf_exchange.py` and
`plant/tfwt.py`. The new package names preserve those import paths and keep
this work in an independent V3 namespace.

## Frozen public API

`TFWTState` exposes the following stable methods:

| Method | Contract |
|---|---|
| `inventory()` | Returns TFWT inventory in `Bq m^-2` |
| `activity_concentration()` | Returns TFWT concentration in `Bq kg^-1 water` |
| `advance(dt, forcing)` | Consumes a signed `LeafExchangeFlux` and returns the next `TFWTState` |

`V3PlantPathway.advance(...)` is the minimal end-to-end facade. It computes one
signed leaf flux from the supplied atmospheric forcing and frozen resistance,
then passes that flux through the public TFWT state API.

## Numerical contract

The P6.2B-1 resistance chain supplies:

```text
r_tot = r_a + r_b + r_c
g_ex = 1 / r_tot
F_leaf = g_ex * (C_air - C_equilibrium)
```

The P6.2B-2 storage boundary then applies:

```text
dI_TFWT/dt = F_leaf
              - F_water_loss
              - F_transformation
```

The current facade does not calculate water-loss or transformation terms.
They remain explicit optional storage-equation inputs. No OBT inventory is
created, and no second re-emission or uptake field is generated.

## Toy validation

The integration toy uses `r_a = 10`, `r_b = 20`, `r_c = 30 s m^-1`,
`C_air = 60 Bq m^-3`, and zero equilibrium concentration. Therefore
`g_ex = 1/60 m s^-1` and `F_leaf = 1 Bq m^-2 s^-1`. Three 10-second intervals
produce 30 `Bq m^-2` of TFWT inventory from an initially empty state. The
inventory residual is checked against a `1e-12 Bq m^-2` tolerance. Reverse
forcing is also checked: a negative signed flux decreases TFWT without
creating a separate re-emission field.

## Activation and limitations

```ini
P6_2B_INTERFACE_FREEZE = PASS
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
OBT_SOLVER = FALSE
ROOT_UPTAKE = FALSE
SOIL_COUPLING = FALSE
DOSE_CALCULATION = FALSE
V3_PHYSICS_READY = FALSE
```

No UFOTRI numeric value is imported or promoted to `ACTIVE`. The facade is an
auditable interface and storage test, not validated production plant physics.
P6.2C is the next stage for the OBT solver contract.
