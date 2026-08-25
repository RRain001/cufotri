# V3-P6.2C OBT solver implementation report

Status: `PASS_OBT_SOLVER_IMPLEMENTED`

Branch: `codex/v3-p6-2c-obt-solver`

Base: `codex/v3-p6-2b-integration`

## Scope

This stage implements the first isolated V3 TFWT-to-OBT inventory pathway:

```text
TFWTState public API
        |
        v
PlantBiologicalForcing
        |
        v
OBTSolver
        |
        v
OBTState + OBTStorageBalance
```

The package is located at `src/cteas_ufotri/plant/obt_v3/` and contains:

- `obt_state.py`: immutable inventory-based OBT state;
- `obt_solver.py`: provisional first-order formation/turnover solver and
  biological forcing boundary;
- `validation.py`: fail-closed units, timestamps, state, rate, and forcing
  validation;
- `__init__.py`: explicit package exports.

No V1/V2 plant module, default configuration, parameter file, trusted registry,
foodchain, dose, soil, or CTEAS-Atmos path was changed or connected.

## State contract

`OBTState` contains the required plant identity and growth metadata,
`obt_inventory_bq_m2`, `obt_concentration`, `timestamp`, and `provenance`. The
authoritative quantity is the area-normalized inventory in `Bq m^-2`.
Concentration is checked on an explicit fresh-plant-mass basis:

```text
obt_concentration [Bq kg^-1 fresh]
  = obt_inventory_bq_m2 [Bq m^-2]
  / plant_mass_kg_m2 [kg fresh m^-2]
```

The state has no TFWT/OBT ratio field. Updates create a new immutable state and
recompute the checked concentration from the updated inventory.

## Dynamic equation and numerical contract

The provisional equation is:

```text
dM_OBT/dt = kf_eff M_TFWT - kr M_OBT
```

where `kf_eff` and `kr` have unit `s^-1`, both inventories have unit
`Bq m^-2`, and the resulting rates have unit `Bq m^-2 s^-1`. Therefore every
integrated balance term has unit `Bq m^-2`:

```text
TFWT loss = OBT formation
OBT increase = OBT formation - other loss
TFWT loss = OBT increase + other loss
```

For one interval, TFWT inventory and biological forcing are held constant. The
linear equation is advanced analytically, which keeps non-negative OBT storage
for non-negative inputs and produces an auditable formation/loss balance.

`PlantBiologicalForcing.is_daylight` selects the explicit day or night
formation multiplier. Optional temperature, photosynthetic activity, and
growth-stage fields are reserved but do not affect P6.2C arithmetic.

## TFWT boundary

`OBTSolver` reads only:

```python
tfwt_state.inventory()
tfwt_state.activity_concentration()
```

It does not read TFWT internal fields, timestamps, water content, resistance
components, boundary resistance, canopy resistance, or exchange coefficients.
Resistance is therefore not recomputed in this stage.

## Parameter and validation boundary

`OBTParameters` requires explicit `kf_s` and `kr_s` values. The day/night
multipliers are explicit provisional test controls. No value is imported from
the UFOTRI validated parameter database, and no production lookup or trusted
registry activation is present.

```text
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = TRUE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

The rates and multipliers are not a validated UFOTRI parameterization. They are
an interface-level first implementation and must be replaced or accepted only
through a later parameter/evidence contract.

## Deliberate exclusions

This stage does not implement or activate:

- soil HTO, root uptake, or re-emission;
- foodchain or dose calculations;
- annual forcing integration or crop harvest transfer;
- UFOTRI database lookup or trusted external evidence;
- default V1/V2 runtime or GUI integration;
- empirical, field, regulatory, or UFOTRI validation.

Those remain future stages and are not implied by the passing software tests.
