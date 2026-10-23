# P3 R3 — dynamic 1993 resistance to TFWT signed-flux compatibility

**Scope: real, opt-in state coupling, not the reconstructed 1993 original TFWT equation.** The source of the **resistance** is W. Raskob's [KfK 5194 (1993)](https://publikationen.bibliothek.kit.edu/270034158/3813483) Eq.(4)–(10) (P3 R1 [day/dry](P3_R1_CANOPY_MONTEITH.md), P3 R2 [night/rain](P3_R2_NIGHT_RAIN_CANOPY.md)). The signed concentration-to-inventory operator is explicitly the previously implemented **KfK 4605 (1990) Eq.(27)–(30) compatibility kernel** and V3 frozen TFWT balance; its use with 1993 resistances is a research bridge, *not proof this matches the original 1993 FORTRAN*. The full original 1993 TFWT exchange equations and numeric routing still require per-feature scientific audit.

## Physical computation and units

`src/cteas_ufotri/plant/kfk5194_1993_tfwt_compat.py` implements `advance_kfk5194_tfwt_compatibility` and `advance_kfk5194_tfwt_intervals`. Requires explicit `KFK5194_1993_V4` P1 source profile, a validated P3 R1/R2 canopy state, and the explicit exchange kernel `KFK4605_EQ27_30_COMPATIBILITY`. Every interval specifies air HTO [Bq/m³], air T [K], HTO liquid/vapour fractionation [-], duration [s]. Result records a signed leaf-to-inventory transfer [Bq/m²], updated plant TFWT [Bq/m² and Bq/kg water], and the V3 activity residual.

The fixed plant water content **must be per m² ground** `TFWTState.area_basis="ground_area"` because `r_c=r_st/LAI` is already an areal canopy resistance. The V3 default `plant_area` is **explicitly rejected** rather than silently treating a leaf-area inventory as ground-area inventory. No implied leaf-to-ground conversion or default LAI is introduced.

For each interval of duration `Δt`, reusing the verified legacy-compatible kernel:
`k=rho_v,sat / (alpha*W*r_total)`,
`C* = alpha*C_air/rho_v,sat`,
`C_new=C*+(C_old-C*) exp(-k*Δt)`,
and integrated signed leaf flux `F_Δt=W(C_new-C_old)`. Negative values represent leaf-to-air re-emission, not an extra simultaneous sink. The scalar resistance `r_total` comes exclusively from P3 1993 canopy result `r_av+r_bv+r_c`, validated at each step. At transition to the next hour, new meteorological forcing/resistance is chosen explicitly. The R3 bridge does not imply a continuously solved coupled atmospheric–canopy system.

## Validation and exclusions

Tests exercise positive air uptake, zero-air signed re-emission, rain/day/night transfer rates, night wet/dry invariance, multihour day→night→rain progression, time-step semigroup invariance under constant forcing, explicit ground-area units, conservative interval activity closure, invalid state/forcing rejection, legacy solver source isolation and provenance. No OBT, root uptake, soil, transpiration-linked **water-loss sink**, energy/TFWT water-content coupling, empirical field validation or full 1993 solver activation. Monteith ET and current TFWT water balance **are not auto-coupled**, since that would require a separately reviewed water-mass basis and root-water replenishment mechanism. P0 #126 remains OPEN; original executable-equivalence `NOT_ESTABLISHED`.
