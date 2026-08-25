# V3 P7.7B Conservation Report

## Result

All executed ledgers closed within the declared `1e-12` tolerance. The
maximum absolute residual recorded for every case was exactly `0.0` in the
registry.

| Case | Ledger source | Maximum absolute residual | Verdict |
| --- | --- | ---: | --- |
| radioactive decay | `SoilStorageBalance` | `0.0 Bq m^-2` | PASS |
| leaf exchange → TFWT | `TFWTStorageBalance` | `0.0 Bq m^-2` | PASS |
| TFWT → OBT | `OBTStorageBalance` | `0.0 Bq m^-2` | PASS |
| Soil → Root | `RootUptakeBalance` | `0.0 Bq m^-2` | PASS |
| end-to-end pathway | soil/root/TFWT/OBT/food pipeline ledgers | `0.0` in each native unit | PASS |

The runner audits the balances returned by existing solvers. It does not
replace, rewrite, or recompute production ledgers with a benchmark-specific
equation. The end-to-end audit covers soil, root, TFWT, OBT, and food balances;
intake and dose remain endpoint readouts under the frozen pipeline contract.

## Boundary

Ledger closure demonstrates implementation bookkeeping consistency for these
synthetic inputs only. It does not demonstrate mass continuity for an
environmental system, field data agreement, or physical parameter validity.
