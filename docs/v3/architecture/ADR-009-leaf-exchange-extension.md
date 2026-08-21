# ADR-009: Future Leaf Exchange Flux Decomposition

- Status: proposed for V3-P6
- Decision stage: V3-P5.2 readiness audit
- Scope: V3 Leaf Exchange only

## Context

The V3 Leaf Exchange framework already owns state, a forcing seam, parameter
resolution, a replaceable physics kernel, and a total activity ledger. Its
current result exposes a single leaf-exchange flux and does not distinguish
boundary-layer, stomatal, cuticular, TFWT-to-OBT, or decay pathways. Those
distinctions are required before a reviewed UFOTRI migration can be made
auditable without hiding source and sink ownership inside one aggregate value.

The repository's V2 plant implementation remains a separate legacy path. This
ADR does not import, copy, or reinterpret its formulas or numerical defaults.

## Decision

Keep all existing V3 P1-P5.1 interfaces unchanged during P5.2. For a future
P6 implementation, evaluate a typed result such as `LeafExchangeFluxes` with
the following conceptual fields:

| Field | Conceptual meaning | Ledger unit |
| --- | --- | --- |
| `atmospheric_uptake` | Net HTO entering the leaf system from the atmospheric boundary | Bq m^-2 s^-1 |
| `stomatal_flux` | HTO exchange assigned to stomatal pathway | Bq m^-2 s^-1 |
| `cuticular_flux` | HTO exchange assigned to cuticular pathway | Bq m^-2 s^-1 |
| `tfwt_obt_transfer` | Internal TFWT-to-OBT biochemical transfer | Bq m^-2 s^-1 |
| `decay_loss` | Radioactive or modelled loss leaving the tracked inventory | Bq m^-2 s^-1 |

The final shape, signs, and whether gross or net pathway fluxes are retained
must be frozen with the P6 equations and mass-balance contract. A result
object must not be treated as a validated UFOTRI model merely because it has
these field names.

## Rationale

1. Existing model and ledger contracts remain backward-compatible.
2. Separate pathway ownership prevents atmospheric, leaf-surface, and
   biochemical terms from being double-counted.
3. The decomposition creates a place to attach reviewed parameter provenance
   and independent regression checks.
4. Keeping this as a future ADR avoids introducing unreviewed equations or
   placeholder numerical values during a readiness audit.

## Consequences and P6 entry criteria

P6 must define the sign convention, reference area, time integration rule,
resistance and kinetic equations, parameter dimensional checks, and the
relationship between pathway fluxes and the existing total-inventory ledger.
It must also provide a reference case and an equivalence disposition before
any production status is assigned.

No `LeafExchangeFluxes` implementation is added by P5.2.
