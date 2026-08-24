# V3-P6.2B-2.5 Public Plant Pathway Interface Implementation Report

## Final status

```ini
P6_2B_INTEGRATION_STATUS = PASS
P6_2B_INTERFACE_FREEZE = PASS
P6_2B_2_5_STATUS = PASS_PUBLIC_PATHWAY_INTERFACE_FREEZE
UFOTRI_PARAMETER_IMPORTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
OBT_SOLVER = FALSE
ROOT_UPTAKE = FALSE
SOIL_COUPLING = FALSE
DOSE_CALCULATION = FALSE
V3_PHYSICS_READY = FALSE
```

## Baseline and ancestry

```text
INTEGRATION_BRANCH = codex/v3-p6-2b-integration
BASE_TFWT_BRANCH = codex/v3-p6-2b-2-tfwt-solver
P6_2B_1_ANCESTRY = PASS
P6_2B_2_ANCESTRY = PASS
LEGACY_V1_V2_PATH_MODIFIED = FALSE
DEFAULT_RUNTIME_CONNECTED = FALSE
```

The integration branch preserves both prior implementation histories. The
resistance package remains the only producer of `LeafExchangeFlux`, and the
TFWT package remains storage-only.

## Delivered interface

- `TFWTState.inventory()` exposes the area-normalized TFWT inventory.
- `TFWTState.activity_concentration()` exposes the fixed-water-basis TFWT
  concentration.
- `TFWTState.advance(dt, forcing)` consumes the signed P6.2B-1 flux through
  the existing storage solver.
- `plant/v3/pathway.py` connects atmospheric forcing, a precomputed
  `ResistanceState`, signed leaf flux, and TFWT state.
- `plant/v3/state.py` reserves an explicit `obt` slot as `None`; it does not
  implement `OBTState` or an OBT solver.
- `plant/v3/validation.py` rejects a non-empty reserved OBT slot.

## Toy acceptance boundary

The constant-forcing toy verifies that the resistance-to-flux-to-TFWT chain
increases inventory by the integrated signed leaf flux and that the residual
is below tolerance. A reverse-forcing case verifies the negative signed flux
direction and the absence of separate uptake/re-emission state.

## Forbidden changes checked

```text
UFOTRI numeric import or validated claim = NONE
ACTIVE parameter database = NONE
default config change = NONE
trusted registry change = NONE
plant/tfwt.py change = NONE
plant/leaf_exchange.py change = NONE
soil/root/dose/CTEAS-Atmos connection = NONE
OBT implementation = NONE
```

This stage freezes the public pathway boundary only. It does not establish
`V3_PHYSICS_READY`.
