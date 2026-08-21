# Plant Pathway Independent Review

Status: `PASS_WITH_ROOT_UPTAKE_DEFERRED`

## Frozen architecture

The reviewed topology is:

```text
AtmosphericHTOForcing
        |
        +--> Leaf uptake --> leaf TFWT --> leaf OBT
        |
        +--> Soil deposition --> Root uptake --> plant water --> OBT
                                      |
                                      v
                                  PlantState
                                      |
                                      v
                                  Food chain
```

Leaf and root paths remain independent until the plant integration state.
`leaf_exchange` owns leaf physics only, `soil` owns soil inventory only,
`PlantState` owns plant integration and convergence accounting, and
`food_chain` consumes the declared plant state.

## Source evidence

The existing V3 `food_chain.PlantState` is immutable and conserves explicit
total, TFWT, and OBT inventories. `PlantInputs` accepts leaf activity inputs
and retains root-zone values as a seam only. It explicitly does not convert
root-zone activity into root uptake. The V3 soil model exposes a read-only
`RootZoneActivity` seam with status `SEAM_ONLY_NO_ROOT_UPTAKE`.

The current state can therefore represent aggregate plant inventory, but it
does not yet preserve independent leaf/root pathway inventories or root-uptake
flux provenance. That is a P6 implementation requirement, not a P5.4 defect
in the ownership topology.

## Ownership checks

The following invalid ownerships remain prohibited:

```text
soil module owns plant = FORBIDDEN
leaf module owns soil = FORBIDDEN
root pathway consumes leaf flux as soil input = FORBIDDEN
```

The architecture supports the future branching sequence without modifying
`PlantState` today. P6 must add typed pathway outputs and an explicit
convergence ledger before enabling root uptake; the ledger must separate
atmospheric input, soil/root input, internal TFWT-to-OBT transfer, decay, and
final inventory.

## Soil-layer compatibility

V3 `SoilState` has exactly three ordered layers with IDs 1, 2, and 3. This is
structurally compatible with a future surface/root/deep representation, but
the current source freezes numeric layer identity rather than the semantic
labels `surface`, `root`, and `deep`. P6 must freeze that mapping and the root
uptake output basis. Adding those semantics must not make soil own
`PlantState`.

## Review conclusion

```text
PLANT_PATHWAY_TOPOLOGY = CONSISTENT
LEAF_ROOT_DOUBLE_COUNTING_GUARD = REQUIRED_AT_PLANT_SEAM
ROOT_UPTAKE_IMPLEMENTED = FALSE
PLANT_STATE_BREAKAGE = NOT_FOUND
```
