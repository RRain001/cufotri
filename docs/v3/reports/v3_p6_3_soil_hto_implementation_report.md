# V3-P6.3 soil HTO transport implementation report

Status: `PASS_SOIL_HTO_IMPLEMENTED`

Branch: `codex/v3-p6-3-soil-hto`

Base: `codex/v3-p6-2c-obt-solver`

## Scope

This stage implements the first isolated soil HTO inventory pathway:

```text
Atmospheric deposition flux
             |
             v
      SoilStorageSolver
             ^
             |
Signed layer transport flux
             |
             v
       SoilState inventory
```

The new package is `src/cteas_ufotri/plant/soil_v3/`:

- `soil_state.py`: immutable layer inventory and soil-water concentration;
- `soil_solver.py`: deposition, signed transport, decay, and balance ledger;
- `validation.py`: fail-closed state, flux, time, provenance, unit, and
  half-life validation;
- `__init__.py`: explicit package exports.

The existing V1/V2 `src/cteas_ufotri/soil/` and `coupling/` implementations are
not imported or modified. No default configuration, parameter file, trusted
registry, foodchain, dose, root uptake, plant pathway, or CTEAS-Atmos coupling
was added.

## SoilState contract

`SoilState` contains:

| Field | Contract |
|---|---|
| `soil_identifier` | Required soil identity |
| `layer_id` | Required layer identity |
| `layer_depth_m` | Positive layer thickness in `m` |
| `soil_water_content` | Positive water depth basis in `m water` |
| `soil_water_inventory_bq_m2` | Authoritative HTO inventory in `Bq m^-2` |
| `soil_water_concentration` | Checked diagnostic in `Bq m^-3 water` |
| `timestamp` | Timezone-aware UTC state time |
| `provenance` | Immutable source metadata |

The concentration invariant is:

```text
soil_water_concentration [Bq m^-3 water]
  = soil_water_inventory_bq_m2 [Bq m^-2]
  / soil_water_content [m water]
```

State updates return a new immutable record and recompute concentration from
inventory. No root state, plant state, TFWT, or OBT field exists in
`SoilState`.

## Storage and transport equation

For one layer and one constant-flux interval:

```text
dM_s/dt = F_dep + F_transport - lambda_T M_s
lambda_T = ln(2) / T_half
```

Units are explicit:

```text
M_s                 Bq m^-2
F_dep/F_transport   Bq m^-2 s^-1
T_half              s
lambda_T            s^-1
```

`transport_flux_bq_m2_s` is signed relative to the current layer: positive
means transport into the layer and negative means transport out. This supports
a two-layer interface by sending `-F` to the donor and `+F` to the receiver.
P6.3 does not derive this interface from Richards flow, diffusion, percolation,
soil moisture movement, or atmospheric dispersion.

The linear equation is advanced analytically while input fluxes are held
constant. The returned `SoilStorageBalance` records deposition input,
transport input, transport loss, radioactive-decay loss, storage change, and
residual:

```text
deposition input + transport input
  = storage increase + transport loss + decay loss + residual
```

A step that would create a negative inventory fails closed.

## Public API boundary

The public state methods are:

```python
SoilState.inventory()
SoilState.concentration()
SoilState.advance(interval_seconds, forcing, parameters=...)
```

`SoilStorageSolver` reads the authoritative state only through
`inventory()` and `concentration()`. It consumes `SoilForcing` deposition and
signed transport fluxes and does not access TFWT/OBT or resistance fields.

## Parameter and activation boundary

`SoilParameters` requires an explicit `tritium_half_life_s`; no half-life is
read from configs or a UFOTRI parameter database. The resulting rate is
computed as `ln(2) / T_half` and is not a validated UFOTRI parameterization.

```text
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = TRUE
SOIL_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

## Deliberate exclusions

This stage does not implement or activate:

- root uptake, plant uptake, TFWT, or OBT transfer;
- foodchain or dose calculations;
- atmospheric dispersion or CTEAS-Atmos coupling;
- a complex hydrological, Richards-equation, diffusion, or percolation model;
- empirical, field, regulatory, or UFOTRI parameter validation;
- V1/V2 runtime or GUI integration.

Those remain future stages and are not implied by the software tests.
