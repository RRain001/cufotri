# ADR-067: UFOTRI pasture 40/60/0 root-profile fidelity R1

## Status

Accepted for D2 candidate implementation.

## Stage

`UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1`

## Context

The post-RC1 V4 root core already separates two questions that must remain separate:

1. how much total plant water uptake is supplied during an interval; and
2. how that explicit total is distributed among the 0-5, 5-15 and 15-30 cm soil layers.

The existing opt-in UFOTRI crop profile implements the manual 20/40/40 allocation and intentionally does not infer total uptake from meteorology, soil state, a transfer constant or hidden hydrology.

The historical V2 parameter-source audit independently records:

- `grass_root_fractions = 0.4;0.6;0.0`, source type `manual direct`, source `UFOTRI manual`, source grade `A`, status `accepted`;
- `root_crop_root_fractions = 0.2;0.4;0.4`, also `manual direct` and `accepted`.

The 40/60/0 evidence therefore belongs to the grass role in the UFOTRI second ingestion system. The D2 roadmap uses the term "pasture" because this grass state feeds the pasture/grass-to-cow pathway. This naming must not be interpreted as validating the repository's project-specific pasture phenology, biomass, cutting schedule or root-activity parameters.

## Decision

Add a separate opt-in module:

`src/cteas_ufotri/plant/root_v4/pasture_profile.py`

with the exact fractions:

`(q_w,L1, q_w,L2, q_w,L3) = q_w,total * (0.4, 0.6, 0.0)`.

The API accepts an explicit non-negative total water-uptake flux in `m s^-1`, validates it through the same root-v4 unit/input contract used by the 20/40/40 path, and returns the same `ThreeLayerRootWaterFluxForcingV4` type.

Selection is explicit through the pasture-specific API. There is no global profile switch and no replacement of the existing 20/40/40 constants/functions.

## Compatibility decision

No change is made to:

- `root_v4/ufotri_profile.py`;
- `root_v4/root_solver.py`;
- `root_v4/ufotri_eq39.py`;
- C1/C2 soil hydrology;
- the selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` operator ordering;
- V3 or RC1 defaults.

Because both profiles return `ThreeLayerRootWaterFluxForcingV4`, the existing root solver still evaluates `J_root,i = q_w,i C_w,i` and the same water/HTO conservation ledgers. C1/C2 signed hydrology remains external to the root-profile allocation.

## Numerical qualification

D2 must prove:

- exact pasture fractions `(0.4, 0.6, 0.0)` and exact L3 zero;
- existing crop fractions remain `(0.2, 0.4, 0.4)`;
- both profiles preserve the same explicit total water-uptake flux;
- zero input remains zero;
- negative, non-finite and wrong-unit inputs fail closed;
- typed forcing preserves identity, UTC timestamp, provenance and interval-start semantics;
- with equal layer HTO concentrations, changing only the profile changes layer allocation but not total HTO transfer;
- with unequal concentrations, each layer still obeys `J=q_w C_w` and total HTO transfer equals the sum of layer transfers;
- root water and HTO ledgers remain closed.

## Source boundary

The manual-direct evidence supports only the root-distribution fractions. D2 does not activate project-specific values for pasture LAI, biomass, cutting, root activity, feed intake, hydrology or total water demand.

The manual does not establish that every crop should use 40/60/0, and D2 must not reinterpret it that way.

## Allowed claim after exact-head merge/no-drift

`UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY=COMPLETE`

This claim means only that the manual-direct grass/pasture layer allocation is available and numerically qualified through the existing root-v4 contract.

## Non-claims

D2 does not establish:

- production total root-water uptake;
- production pasture parameters;
- calibration;
- empirical validation;
- physical accuracy;
- vegetable/grass compartment closure;
- cow/milk/beef closure;
- real CTEAS-Atmos binding;
- original UFOTRI executable equivalence.
