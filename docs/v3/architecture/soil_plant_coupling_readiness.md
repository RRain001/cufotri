# Soil-Plant Coupling Readiness Audit

Status: `PASS_ARCHITECTURE_READY`; no soil, root-uptake, or plant physics is
implemented by P5.2.

## Current V3 separation

The V3 P1 Leaf Exchange framework and P2 Soil Layer framework are separate
modules. P2 has a fixed three-layer state and a read-only `RootZoneActivity`
seam; it does not implement root uptake. Atmospheric deposition is supplied
to P2 as an external flux and is not derived from air concentration.

The repository also contains a V2 coupled integrator with legacy plant, soil,
leaf, root, re-emission, and OBT pathways. That path is not silently re-used
as the V3 coupling contract and is unchanged by this audit.

## Future coupling graph

```text
AtmosphericHTOForcing
          |
          +--> V3 Leaf Exchange --> leaf TFWT --> leaf OBT
          |
          +--> V3 Soil Layer -----> Root Uptake --> plant/root TFWT and OBT
```

Leaf uptake and root uptake are independent branches from the same typed
forcing context. A later plant-level ledger must define where the branches
converge, how atmospheric input is allocated, and how internal transfers are
excluded from boundary-flux totals. It must prevent the same HTO inventory
from being counted once through leaf uptake and again through soil input.

## Missing contracts before physical migration

1. A shared typed plant state that can consume leaf and root outputs without
   coupling V3 to the V2 positional integrator.
2. A root-uptake flux contract with units, direction, time integration, and
   layer ownership.
3. Temporal alignment between atmospheric forcing, soil deposition, root
   uptake, leaf exchange, and plant biochemical conversion.
4. A cross-module activity ledger with explicit boundary and internal terms.
5. Crop and growth-stage applicability semantics for both leaf and root
   pathways.

The fixed V3 three-layer representation is retained as a framework contract.
P5.2 does not add a three-layer soil implementation, root uptake equations, or
plant coupling code.
