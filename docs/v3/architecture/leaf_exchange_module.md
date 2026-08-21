# V3-P1 Leaf Exchange Module

Status: `FRAMEWORK_COMPLETE`

Physics status: `PENDING_UFOTRI_PARAMETER_AND_FORMULA_MIGRATION`

UFOTRI numerical equivalence: `NOT_CLAIMED`

## Responsibility

The module establishes the executable boundary between atmospheric HTO
forcing, leaf TFWT, and leaf OBT. It owns only:

- immutable state and forcing records;
- parameter-database resolution and parameter provenance;
- one-step state advancement through an injected physics kernel;
- explicit activity inventories and a mass-balance ledger.

It does not replace the V2 `plant.leaf_exchange` path, modify V2
configuration, perform food-chain or soil coupling, calculate dose, import
UFOTRI legacy values, calibrate against experiments, or claim field or
regulatory validation.

## Package layout

```text
src/cteas_ufotri/leaf_exchange/
├── state.py       # LeafExchangeState and LeafExchangeForcing
├── parameters.py  # ParameterDatabase-only parameter bundle
├── physics.py     # replaceable physics protocol and test-only kernels
├── balance.py     # explicit interval ledger
└── model.py       # state/physics/ledger coordinator
```

## State and units

`LeafExchangeState` is immutable and contains no global or module-level
simulation state:

| Field | Contract |
|---|---|
| `hto_air_concentration` | `Bq m-3 air` |
| `air_temperature` | `K` |
| `relative_humidity` | fraction in `[0, 1]` |
| `tfwt_activity` | `Bq kg-1 fresh` |
| `obt_activity` | `Bq kg-1 dry` |
| `leaf_water_mass` | `kg` on the module leaf reference basis |
| `dry_matter_mass` | `kg` on the module leaf reference basis |
| `current_time` | `datetime` |
| `delta_t` | `s` |

The state converts TFWT and OBT concentrations to inventories using

```text
I_TFWT = tfwt_activity * leaf_water_mass
I_OBT  = obt_activity  * dry_matter_mass
I_leaf = I_TFWT + I_OBT
```

Every numeric field is finite; activities and inventories cannot be negative;
mass, temperature, humidity, and timestep domains are checked explicitly.

## Advance and physics seam

The canonical call is:

```python
new_state, balance = model.advance(state, forcing, dt)
```

The model delegates all numerical exchange behavior to
`LeafExchangePhysics.step(state, forcing, dt, parameters)`. The default
`FrameworkOnlyPhysics` fails closed because no reviewed UFOTRI kernel is
configured. `SyntheticLinearLeafExchangePhysics` and
`ZeroExchangePhysics` are marked `TEST_ONLY` and exist only for deterministic
framework tests. Replacing the reviewed implementation in `physics.py` does
not require changing state, parameter, coordinator, or ledger interfaces.

## Parameter dependency and provenance

Executable parameter values are resolved only through
`ParameterDatabase.get_entry()` in `LeafExchangeParameters.from_database()`.
The P1 role names are in the `leaf_exchange.*` namespace:

```text
leaf_exchange.tfwt_exchange_rate
leaf_exchange.obt_formation_rate
leaf_exchange.obt_decay_rate
leaf_exchange.air_to_tfwt_partition
```

The existing V3-P0 database remains unchanged and contains only interface
placeholders under its reviewed `leaf.*` declarations. It therefore cannot
drive P1 arithmetic. Until the parameter mapping is reviewed, a production
construction fails closed; deterministic tests use an explicitly synthetic,
`TEST_ONLY` parameter database and retain its SHA-256 package hash plus each
entry's provenance.

## Mass-balance contract

For one interval, all ledger quantities are integrated activity in Bq:

```text
closure_error =
    initial_inventory
  + atmospheric_input
  - leaf_exchange_flux
  - decay_loss
  - final_inventory
```

`atmospheric_input` is positive activity entering the leaf domain,
`leaf_exchange_flux` is positive activity leaving it, and TFWT-to-OBT transfer
is internal. The coordinator rejects non-finite or negative physics results
and fails closed if the ledger does not close within the declared tolerance.

## Validation boundary

The P1 tests cover initialization, immutable copying, invalid state values,
placeholder rejection, provenance, zero exchange, deterministic repeat,
timestep scaling, non-negative inventory protection, invalid parameters, and
ledger closure. These are interface and conservation tests only. They are not
UFOTRI equivalence tests, field validation, external experiment calibration,
or regulatory acceptance.

```text
Implementation status: Framework complete
Physics status: Pending UFOTRI parameter/formula migration
Validation status: Deterministic contract tests only
```
