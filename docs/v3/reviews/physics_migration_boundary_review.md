# Physics Migration Boundary Independent Review

Status: `PASS_WITH_P6_PHYSICS_PREREQUISITES`

## Leaf Exchange boundary

The current V3 `LeafExchangePhysics.step()` protocol returns aggregate
inventories and ledger terms. It is intentionally fail-closed by default and
the available synthetic kernel is explicitly test-only.

The future `LeafExchangeFlux` design can express the pathway outputs needed by
the P6 sequence:

```text
air HTO
  -> boundary resistance
  -> leaf water
  -> TFWT
  -> OBT
```

The fields `air_to_leaf_flux`, `stomatal_flux`, `cuticular_flux`,
`tfwt_to_obt_flux`, and `decay_flux` provide an auditable output decomposition.
They do not themselves encode the boundary-resistance equation, leaf-water
state law, or kinetic parameterization. `LeafExchangeFlux` is therefore
sufficient as a future flux/result seam, but not sufficient by itself to
claim physics migration.

P6 must freeze the resistance equation, area basis, gross/net and reverse-flux
signs, time integration, parameter provenance, and mapping into the plant
ledger. No `LeafExchangeFlux` class is implemented by P5.4.

## Soil and PlantState boundary

The current V3 soil state has exactly three ordered layers, IDs 1, 2, and 3,
and a read-only root-zone seam. It accepts externally supplied deposition and
does not derive deposition or root uptake. This does not require changing
`PlantState` merely to represent a future surface/root/deep soil inventory.

The interface remains safe only if P6 keeps the following ownership:

```text
soil layers -> soil inventory and root-zone output
root uptake -> typed plant-pathway input
PlantState -> plant integration and convergence ledger
```

P6 must assign the semantic labels surface/root/deep to layer IDs, define the
root-uptake flux basis and timing, and prevent direct soil mutation of plant
inventory. A three-layer implementation cannot be introduced by silently
reinterpreting the current read-only seam.

## Review conclusion

```text
LEAF_EXCHANGE_FLUX_SEAM = SUFFICIENT_FOR_P6_DESIGN
LEAF_EXCHANGE_PHYSICS = NOT_IMPLEMENTED
SOIL_THREE_LAYER_COMPATIBILITY = STRUCTURAL_ONLY
PLANT_STATE_INTERFACE_BREAK_REQUIRED = FALSE
P6_EQUATIONS_AND_TYPED_ROOT_FLUX = REQUIRED
```
