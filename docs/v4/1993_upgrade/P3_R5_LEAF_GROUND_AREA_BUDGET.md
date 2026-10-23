# P3 R5 — conservative constant-LAI leaf-to-ground HTO exchange budget

**Physical implementation**, grounded in the official [KfK 5194 (1993)](https://publikationen.bibliothek.kit.edu/270034158/3813483) leaf exchange Eq.(1)–(3), printed p.3, and its leaf/canopy resistance Eq.(4) and Eq.(10), printed pp.4–5. Builds directly on the [P3 R4 original-1993 equation implementation](P3_R4_1993_PRINTED_LEAF_EQ1_3.md), *not* the mixed-edition [P3 R3 compatibility model](P3_R3_TFWT_COMPAT_COUPLING.md).

## Explicit geometric and water-pool assumptions

For homogeneous leaf HTO concentration, single-sided LAI fixed over a meteorological interval, and a specified **leaf-water-only** reservoir per ground area, the change of extensive basis is:

- `LAI = m² leaf/m² ground`;
- `W_leaf [kg/m² leaf] = W_ground,leaf [kg/m² ground] / LAI`;
- `I_leaf [Bq/m² leaf] = I_ground,leaf [Bq/m² ground] / LAI`;
- `ΔI_ground,leaf [Bq/m² ground] = LAI × ΔI_leaf [Bq/m² leaf]`;
- `C_leaf [Bq/kg water] = C_ground,leaf [Bq/kg water]`.

A fixed LAI is a **declared research canopy homogenization**, not an established original FORTRAN algorithm. No multiple-leaf-layer inference or two-leaf-face assumption is introduced. `TFWTState.area_basis` must be explicitly `ground_area`, with `KFK5194GroundWaterPool.LEAF_WATER_ONLY` supplied separately. A `plant_area` or `leaf_area` state is rejected by this *ground projection* API. This projection is **not** a conversion of stems, fruits or roots.

## Actual model addition

The opt-in `kfk5194_1993_ground_leaf_budget.py` constructs an intermediate leaf-area TFWT state, integrates the **1993 Eq.(1)–(3)** HTO absorption/re-emission with the P3 R1/R2 **leaf** resistance, and projects the signed leaf transfer, extensive water and inventory back to ground area. It checks `I_after-I_before-ΔI_ground≈0` and concentration invariance. A multihour helper accepts interval-specific meteorology or day/night/rain branch changes while requiring a **constant LAI**.

## Deliberate limits

Any mismatch or variation in LAI is rejected, because growth, new-leaf water, senescence, redistribution and TFWT growth dilution demand their own mass and activity budget. **Monteith ET is not a plant-water loss sink in R5**, and root-water replenishment is not implicitly applied. Water-content per ground area is fixed during this isolated air–leaf HTO exchange. Consequently this code does **not** yet constitute a complete hydrologically dynamic atmospheric–soil–plant model.

Unit tests check independent direct Eq.(1)–(3) hand calculations and fixed LAI scaling, reverse signed HTO emission, LAI=1 identity, timestep semigroup, hourly activity telescoping, rejected incompatible pools and changing LAI, legacy CLI/source isolation, and original-executable `NOT_ESTABLISHED` provenance. No historical numerical-executable parity, observational validation or full 1993 runtime activation is claimed. P0 #126 stays open.
