# V3-P6.2B-1 Resistance Subsystem Implementation Report

## Final status

```ini
P6_2B_1_STATUS = PASS_RESISTANCE_SUBSYSTEM_IMPLEMENTED
LEAF_EXCHANGE_RESISTANCE_IMPLEMENTED = TRUE
LEAF_EXCHANGE_COMPLETE = FALSE
LEAF_EXCHANGE_SOLVER = FALSE
TFWT_SOLVER = FALSE
OBT_SOLVER = FALSE
V3_PHYSICS_READY = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
```

The implementation is limited to a testable resistance subsystem. It does not
enter the TFWT dynamic equation, OBT formation, root uptake, soil coupling,
atmospheric dispersion, dose, or the default V1/V2 runtime.

## Baseline and branch

```text
BASE = origin/main@6671f5793d04842bf2ceae4904f3c0cf30a0d7e0
BRANCH = codex/v3-p6-2b-1-resistance-subsystem
P6_2A_HISTORY_MODIFIED = FALSE
MAIN_MODIFIED = FALSE
```

The existing V1/V2 `src/cteas_ufotri/plant/leaf_exchange.py` file is retained
unchanged. Because a file and a package cannot safely occupy the same import
path, the new package is isolated at
`src/cteas_ufotri/plant/leaf_exchange_resistance/`.

## Implemented surface

| Surface | Result |
|---|---|
| `ResistanceState` | Stores `r_a`, `r_b`, `r_c`, total resistance, and exchange velocity with explicit units |
| Resistance sum | `r_tot = r_a + r_b + r_c` |
| Exchange coefficient | `g_ex = 1 / r_tot` |
| Unit validation | Exact `s m^-1`, `m s^-1`, `Bq m^-3`, and `Bq m^-2 s^-1` tokens; no conversion |
| Invalid resistance | Zero, negative, non-finite, and non-numeric values fail closed |
| `AtmosphericHTOForcing` | UTC, air HTO, temperature, humidity, optional wind/radiation/boundary layer, day/night, provenance |
| `LeafExchangeFlux` | One signed boundary field; positive air-to-leaf, negative leaf-to-air |
| ParameterDatabase seam | Structural P6.1 `lookup(..., production=False)` protocol; missing/null and ACTIVE fail closed |

The P6.1 database implementation and its placeholder parameter file remain on
the unmerged P6.1 branch. No database, trusted registry, default, or UFOTRI
numeric value is copied into this branch.

## Explicit exclusions

There is no implementation of atmospheric dispersion, ERA5 access, TFWT
storage/dynamics, TFWT-to-OBT transfer, root uptake, soil exchange, re-emission
state evolution, dose, or production activation. The signed flux function only
multiplies an already supplied atmospheric-equivalent concentration difference
by `g_ex`; it does not compute that concentration from plant state.

## Verification summary

The new unit, integration, and architecture tests pass. Existing
`tests/unit`, `tests/integration`, and `tests/regression` suites also pass.
One pre-existing NumPy/netCDF binary-compatibility warning is emitted by the
ERA5 reader unit test; it does not fail the suite and is unrelated to this
package.
