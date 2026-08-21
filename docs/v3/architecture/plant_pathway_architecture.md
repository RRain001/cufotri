# Plant Dual-Pathway Architecture

Status: `V3-P5.3_INTERFACE_FROZEN`; no root uptake or UFOTRI plant physics is
implemented by this stage.

## Frozen topology

```text
CTEAS-Atmos
      |
      v
AtmosphericHTOForcing
      |
      +--------------------+
      |                    |
 Leaf pathway        Soil/Root pathway
      |                    |
      +---------+----------+
                v
            PlantState
                |
                v
            Food chain
```

Leaf absorption and root absorption are independent paths. They may converge
only at the plant integration state and its explicitly owned activity ledger.
They must not be merged at the atmospheric or soil boundary.

## Leaf pathway ownership

```text
Atmospheric HTO
      -> leaf exchange
      -> TFWT
      -> OBT
```

`leaf_exchange` owns leaf physics and leaf-level flux accounting only. It
receives `AtmosphericHTOForcing`; it does not own soil inventory, root uptake,
or the final food-chain state.

## Root pathway ownership

```text
Soil HTO inventory
      -> root-uptake interface
      -> plant water
      -> OBT
```

`soil` owns soil inventory only. The root-uptake interface is a future seam;
P2 currently exposes a read-only root-zone activity seam and performs no root
uptake. Root uptake must not be inferred from a leaf flux.

## Plant integration state

`PlantState` is the integration state that can receive independent leaf and
root pathway outputs. It owns aggregate plant inventory and the convergence
ledger, not leaf equations or soil inventory. The existing V3-P3
`food_chain.PlantState` remains an immutable framework state; P5.3 freezes the
ownership interpretation without changing its fields or behavior.

The following ownerships are forbidden:

```text
soil module owns plant       = FORBIDDEN
leaf module owns soil        = FORBIDDEN
root pathway consumes leaf flux as soil input = FORBIDDEN
```

The convergence ledger must distinguish atmospheric input, soil/root input,
internal TFWT-to-OBT transfer, decay/turnover, and final inventory. This is
required to prevent double counting when both paths are active.

## P6 entry criteria

P6 must freeze the root-uptake flux units and sign, temporal alignment,
plant-area basis, crop/growth-stage applicability, and the cross-module mass
ledger before connecting the two paths to production physics. No V2 coupled
integrator is used as a substitute for this V3 contract.
