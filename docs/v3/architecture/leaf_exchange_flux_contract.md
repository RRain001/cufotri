# LeafExchangeFlux Contract

Status: `DESIGN_ONLY_NOT_IMPLEMENTED`; reviewed interface target for V3-P6.

## Purpose

The current `LeafExchangePhysics.step()` result is intentionally a framework
seam. It exposes aggregate accounting sufficient for P1 tests but does not
make the physical pathways independently auditable. P5.3 freezes a future
internal result shape without modifying `leaf_exchange/physics.py`.

## Future record

The future `LeafExchangeFlux` record contains the following rate fields:

| Field | Meaning | Unit and sign |
| --- | --- | --- |
| `air_to_leaf_flux` | Net HTO transfer across the atmospheric-to-leaf boundary | Bq/m2/s; positive into the leaf system |
| `stomatal_flux` | HTO transfer assigned to stomatal exchange | Bq/m2/s; positive into the leaf system |
| `cuticular_flux` | HTO transfer assigned to cuticular exchange | Bq/m2/s; positive into the leaf system |
| `tfwt_to_obt_flux` | Internal biochemical transfer from TFWT to OBT | Bq/m2/s; positive into OBT |
| `decay_flux` | Activity leaving the tracked leaf inventory by decay/turnover | Bq/m2/s; positive as a loss |

The record is rate-based. Integrating one interval of duration `delta_t`
produces an activity per declared leaf area in Bq/m2. The area basis, gross
versus net interpretation, reverse exchange sign behavior, and treatment of
turnover must be frozen by P6 together with the equations.

## Ownership and conservation

`air_to_leaf_flux` is the only external atmospheric boundary term. The
stomatal and cuticular fields are pathway diagnostics and must not be added as
additional atmospheric inputs unless their contract explicitly says they are
gross terms. `tfwt_to_obt_flux` is internal and must not be counted as a
boundary source. `decay_flux` is an output/loss term.

The future result must map to the plant dual-pathway ledger without creating a
second soil/root input. No field in this record implies root uptake.

## Non-implementation boundary

P5.3 does not add `LeafExchangeFlux`, does not alter the current
`LeafExchangePhysics` protocol, and does not import UFOTRI equations or
parameters. A P6 implementation requires reviewed formulas, parameter
provenance, dimensional checks, and a reference regression artifact.
