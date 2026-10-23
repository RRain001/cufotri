# P3 R6 — opt-in coupled leaf-water and HTO ledger (source-limited)

**Status: physically computed, exact mathematical integration under declared research assumptions; scientific validation and original FORTRAN equivalence not established.** This phase follows [P3 R5 fixed-LAI leaf-to-ground inventory](P3_R5_LEAF_GROUND_AREA_BUDGET.md), [P3 R4 KfK5194 (1993) leaf HTO Eqs.(1)–(3)](P3_R4_1993_PRINTED_LEAF_EQ1_3.md) and [P3 R1 Eq.(11) Monteith ET](P3_R1_CANOPY_MONTEITH.md). Normative manual: [KfK 5194 (1993)](https://publikationen.bibliothek.kit.edu/270034158/3813483).

## Physical terms, separate evidence and hypotheses

The direct 1993 *leaf-level* gas exchange rate is derived from Eq.(1)–(4) and projected onto a **homogeneous, fixed-LAI, leaf-water-only** ground-area pool:

`a = LAI * rho_v,sat / (alpha * r_g)` in kg/(m² ground·s), with source-1993 leaf resistance `r_g [s/m]`, `LAI [m² leaf/m² ground]`, vapour density `rho_v,sat [kg/m³]`, fractionation factor `alpha [-]`; equilibrium HTO in leaf water is `C_eq=alpha*C_air/rho_v,sat [Bq/kg water]`.

The rate of **plant** transpiration `E [kg/m² ground/s]` is supplied by the previously implemented Eq.(11) Monteith plant component; **soil ET is not charged to the leaf-water store**. The model requires separately explicit external root-delivered water `R [kg/m² ground/s]` and its HTO concentration `C_root [Bq/kg]`.

## Fixed-water composite Belot and root-water hypothesis

The original KfK5194 (1993) printed page 7 states that the Belot leaf HTO re-emission loss already includes diffusion and transpiration-related isotope loss. Therefore the previous equation with an additional -E*C isotope sink was scientifically inconsistent and has been removed.

The revised source-limited control volume is a homogeneous fixed-LAI leaf-water pool per ground area: W [kg/m2 ground], I [Bq/m2 ground], C=I/W [Bq/kg]. With a=LAI*rho/(alpha*r_g) [kg/(m2 ground s)] and Ceq=alpha*Cair/rho [Bq/kg], the equations are:

- Water: dW/dt=R-E=0, requiring root delivery R exactly equal to Monteith plant transpiration E.
- Leaf HTO: dI/dt=a*(Ceq-C)+R*Croot. The composite Belot exchange is signed and includes the transpiration-associated isotope loss. No extra -E*C is added.

This is an explicit research assumption for instantaneous root isotope delivery and mixing, not original 1993 FORTRAN numerical equivalence. A dynamic-water model is rejected until an independently justified flux partition is available.

For interval-constant forcing, k=a/W, Cstar=Ceq+R*Croot/a, f=1-exp(-k*dt). The exact solution is C1=C0+(Cstar-C0)*f. The integral J=int(C dt)=Cstar*dt+(C0-Cstar)*f/k. Signed Belot=a*(Ceq*dt-J) and Root=R*Croot*dt, with I1-I0=Belot+Root. Water closes by R*dt-E*dt=0. An additional ET HTO sink is identically zero.

Source limitation: The printed manual supports the composite Belot loss and root replenishment conceptual role but does not establish this exact combined root isotope transport equation. Original binary parity, root mixing and fractionation remain NOT_ESTABLISHED; soil, OBT, dynamic water and full 1993 runtime are not implemented.

## Tests, known gaps and exit criteria

Independent tests cover independent fixed-water analytic oracles, zero-air Eq.(3) decay, changing Monteith E without spurious additional isotope loss, signed Belot exchange, R=E enforcement, two half-steps, invalid forcing/profile/area, and frozen 1990 default non-activation. Scientific review is still required before merging. P0 #126 remains OPEN.
## R6 R3 source-defined 3-layer root-water HTO boundary (printed p.15)

The official **KfK 5194 (1993) printed p.15 / PDF index 24** explicitly defines the composition of root-delivered water from three soil horizons (0–5, 5–15, 15–30 cm). For agricultural crops, water fractions are **0.20 / 0.40 / 0.40**; for pasture grass, **0.40 / 0.60 / 0.00**. This is a published fraction-of-water-uptake statement, not a dry-soil or total-H-to-HTO concentration transfer factor. The effective root-water-specific HTO concentration can therefore be calculated as a flux-weighted source boundary:

```
Croot,crop  = 0.20*Csoil_0_5 + 0.40*Csoil_5_15 + 0.40*Csoil_15_30
Croot,grass = 0.40*Csoil_0_5 + 0.60*Csoil_5_15
```

All `Csoil` are concentrations in **soil liquid water** [Bq/kg water] at the same source time/ground-area context. No assumption about HTO soil depth transport, pore-water equilibration, time interpolation or root transport delay is made here.

`kfk5194_1993_root_soil_boundary.py` implements a typed source-verified plant-group selector and fail-closed three-layer input boundary. Its optional adapter to the R6 **fixed-water** solver alters **only** `Croot`, preserving the supplied Monteith `E` and required `R=E`. Coupling requires a *second explicit* `INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH` hypothesis, because **the manual supports the root uptake depth fractions but does not establish instantaneous uniform mixing in all leaf water**. Neither this bridge nor synthetic examples establish original FORTRAN parity. Independent tests verify both fractional vectors, weighted-concentration hand oracles, the unused grass third layer, root activity input and zero extra ET isotope sink, and reject incomplete/nonphysical soil data or unacknowledged mixing.

**Scientific exit gate unchanged:** PR remains Draft; actual leaf mixing / transport lag, root/soil state integration and 1993 original executable behavior require independent evidence and review before any production solver activation or merge.
