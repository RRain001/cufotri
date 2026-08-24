# V3-P6.2B-1 Leaf-Exchange Resistance Subsystem Implementation

Status: `IMPLEMENTED_TESTABLE_SUBSYSTEM_NOT_PRODUCTION_PHYSICS`

## Scope

This stage implements only the typed resistance subsystem:

```text
AtmosphericHTOForcing
        |
        v
ResistanceChain (r_a + r_b + r_c)
        |
        v
exchange_velocity (g_ex)
        |
        v
LeafExchangeFlux (signed placeholder)
```

The implementation does not solve TFWT dynamics, OBT formation, root uptake,
soil coupling, atmospheric dispersion, or dose. It is not connected to the
default V1/V2 runtime path.

## Package boundary

The main branch already contains the V1/V2 module
`src/cteas_ufotri/plant/leaf_exchange.py`. Replacing it with a package named
`plant/leaf_exchange/` would alter the legacy import path and violate the
regression boundary. The new subsystem therefore lives in:

```text
src/cteas_ufotri/plant/leaf_exchange_resistance/
    __init__.py
    resistance.py
    types.py
    validation.py
```

The existing V1/V2 file is unchanged.

## Implemented contract

`ResistanceState` contains:

- `aerodynamic_resistance` (`r_a`, `s m^-1`);
- `boundary_layer_resistance` (`r_b`, `s m^-1`);
- `canopy_resistance` (`r_c`, `s m^-1`);
- `total_resistance` (`s m^-1`);
- `exchange_velocity` (`g_ex`, `m s^-1`).

The chain is computed only after exact unit-token validation:

```text
r_tot = r_a + r_b + r_c
g_ex  = 1 / r_tot
```

Zero, negative, non-finite, non-numeric, and wrongly labelled values fail
closed. No centimetre/metre or other implicit conversion is performed.

`AtmosphericHTOForcing` validates UTC time, HTO concentration, temperature,
relative humidity, optional wind/radiation/boundary-layer fields, day/night
state, and immutable provenance. It does not read ERA5, call CTEAS-Atmos, or
derive missing weather.

`LeafExchangeFlux` contains one authoritative signed field in
`Bq m^-2 s^-1`: positive is air-to-leaf and negative is leaf-to-air. No
separate uptake and re-emission fields are emitted, so the same boundary flux
cannot be counted twice.

## ParameterDatabase seam

The P6.1 `ParameterDatabase` implementation is on an unmerged branch and is
not copied into this main-based implementation branch. `resistance.py`
therefore consumes its structural public seam:

```python
lookup(name, coordinates, production=False) -> float
```

`ResistanceChain.from_parameter_database` passes explicit crop,
growth-stage, temperature, humidity, and optional period coordinates. It
rejects missing/null values, catches unavailable lookup errors as
`MissingParameterError`, rejects `ACTIVE` provenance, and never supplies a
fallback. The current branch adds no database file, no numeric UFOTRI value,
and no production registry entry.

## Relationship to P6.2A

The signed flux and resistance symbols follow the P6.2A equation contract.
This stage stops before the P6.2A TFWT inventory equation, TFWT-to-OBT
formation, day/night OBT rates, and plant conservation solver. Explicit
component values used in unit tests are test inputs only; they are not UFOTRI
manual values and are not validation evidence.

## Limitations and next phase

This is a testable interface subsystem, not production leaf physics. It does
not determine aerodynamic, boundary-layer, or canopy resistance from wind,
temperature, humidity, radiation, or crop physiology. Those parameterized
relations require the future evidence-backed table, interpolation policy,
uncertainty, and lifecycle gate. P6.2B-2 may add the TFWT dynamic solver only
after preserving this fail-closed boundary.

```ini
LEAF_EXCHANGE_RESISTANCE_IMPLEMENTED = TRUE
LEAF_EXCHANGE_SOLVER = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
LEAF_EXCHANGE_COMPLETE = FALSE
TFWT_SOLVER = FALSE
OBT_SOLVER = FALSE
V3_PHYSICS_READY = FALSE
```
