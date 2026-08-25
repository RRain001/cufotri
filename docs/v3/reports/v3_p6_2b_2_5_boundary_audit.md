# V3-P6.2B-2.5 Public Plant Pathway Boundary Audit

Status: `PASS_INTERFACE_SCOPE_ONLY`

| Audit item | Result | Evidence boundary |
|---|---|---|
| P6.2B-1 resistance history preserved? | PASS | Integration branch contains the resistance commit as an ancestor |
| P6.2B-2 TFWT history preserved? | PASS | Integration branch contains the TFWT solver commit as an ancestor |
| TFWT public API frozen? | PASS | `inventory()`, `activity_concentration()`, and `advance(dt, forcing)` are present |
| Forcing reaches TFWT through one signed flux? | PASS | `V3PlantPathway` calls `signed_leaf_exchange_flux` and `TFWTState.advance` |
| Resistance recalculated in the facade? | PASS | Facade accepts `ResistanceState`; no chain or coefficient calculation is present |
| OBT implemented early? | PASS | `obt` is reserved as `None`; validation rejects a non-empty slot |
| Root/soil/dose/atmosphere connected? | PASS | No imports or runtime registration were added |
| UFOTRI value imported or activated? | PASS | No database lookup, numeric parameter, or `ACTIVE` entry was added |
| V1/V2/default behavior changed? | PASS | Legacy paths and default config are asserted unchanged |
| Toy inventory conservation closes? | PASS | Three constant-forcing intervals have residual below `1e-12 Bq m^-2` |

The scope is deliberately limited to the public interface and TFWT storage
boundary. It is not a validated complete plant model.
