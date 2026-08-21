# ADR-010: Plant Dual-Pathway Model

- Status: accepted as an interface freeze for V3-P5.3
- Scope: V3 leaf, soil/root, plant integration, and food-chain boundaries
- Implementation status: design only; no production behavior change

## Context

Atmospheric HTO can reach a plant through a leaf pathway and a soil/root
pathway. Treating both as one undifferentiated plant input would obscure
ownership, allow double counting, and make later UFOTRI validation unable to
identify the source of a mismatch.

The V3 P1-P3 frameworks already provide separate leaf, soil, and plant seams.
The P2 root-zone seam is read-only and does not perform root uptake. The V2
coupled integrator is a separate legacy path and is not the V3 contract.

## Decision

Freeze the following ownership model:

1. `AtmosphericHTOForcing` is the atmospheric boundary record.
2. `leaf_exchange` owns leaf physics only and emits leaf-pathway outputs.
3. `soil` owns soil inventory only and emits a future root-zone/root-uptake
   output; it does not own `PlantState`.
4. `PlantState` owns the integration state and convergence ledger.
5. `food_chain` consumes the declared plant state; it does not reconstruct
   atmospheric or soil inputs.

Leaf and root pathways remain independent until the plant integration seam.
The ledger must keep boundary inputs and internal TFWT-to-OBT transfers
separate.

The following ownerships are explicitly forbidden:

```text
soil module owns plant = FORBIDDEN
leaf module owns soil = FORBIDDEN
```

## Consequences

- Leaf physics cannot read or mutate soil inventory.
- Soil physics cannot write plant inventory directly.
- Root uptake cannot be represented as a leaf-exchange side effect.
- A future plant step must accept typed pathway outputs with compatible time,
  area, unit, and provenance metadata.
- Existing V2 behavior remains outside this decision and unchanged.

## P6 entry criteria

Before implementation, P6 must freeze the root-uptake equation, pathway flux
signs, shared plant-area basis, temporal synchronization, double-counting
guard, and reference regression cases. This ADR does not implement any of
those equations.
