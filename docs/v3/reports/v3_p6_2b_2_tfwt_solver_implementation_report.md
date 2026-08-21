# V3-P6.2B-2 TFWT Solver Implementation Report

## Final status

```ini
P6_2B_2_STATUS = PASS_TFWT_SOLVER_IMPLEMENTED
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = FALSE
UFOTRI_DATABASE_ACTIVE = FALSE
UFOTRI_PARAMETER_IMPORTED = FALSE
V3_PHYSICS_READY = FALSE
LEAF_EXCHANGE_COMPLETE = FALSE
```

The V3 TFWT solver is a storage-only pathway consuming a precomputed signed
`LeafExchangeFlux`. It does not recalculate resistance and does not enter the
legacy V1/V2 path.

## Baseline and isolation

```text
BASE = codex/v3-p6-2b-1-resistance-subsystem@5ac5d57
BRANCH = codex/v3-p6-2b-2-tfwt-solver
LEGACY_TFWT_FILE_MODIFIED = FALSE
DEFAULT_RUNTIME_CONNECTED = FALSE
```

Because the main branch already contains `plant/tfwt.py`, the new V3 package
is `plant/tfwt_v3/` rather than replacing the legacy module.

## Delivered implementation

- `TFWTState` with plant/crop/stage metadata, TFWT concentration, inventory,
  fixed water basis, UTC timestamp, and provenance;
- `TFWTStorageSolver` with the storage equation
  `dI/dt = F_leaf - F_water_loss - F_transformation`;
- `TFWTStorageBalance` with integrated terms and conservation residual;
- explicit rejection of invalid intervals, negative loss terms, inconsistent
  states, and negative resulting inventory;
- direct consumption of the existing P6.2B-1 `LeafExchangeFlux` field only;
- no OBT, root, soil, foodchain, dose, atmosphere, or database activation.

## Required gates

```text
P6_2B_2_STATUS = PASS_TFWT_SOLVER_IMPLEMENTED
LEAF_RESISTANCE = TRUE
TFWT_SOLVER = TRUE
OBT_SOLVER = FALSE
UFOTRI_DATABASE_ACTIVE = FALSE
V3_PHYSICS_READY = FALSE
```
