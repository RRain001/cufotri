# P3 R6 — opt-in coupled leaf-water and HTO ledger (source-limited)

**Status: physically computed, exact mathematical integration under declared research assumptions; scientific validation and original FORTRAN equivalence not established.** This phase follows [P3 R5 fixed-LAI leaf-to-ground inventory](P3_R5_LEAF_GROUND_AREA_BUDGET.md), [P3 R4 KfK5194 (1993) leaf HTO Eqs.(1)–(3)](P3_R4_1993_PRINTED_LEAF_EQ1_3.md) and [P3 R1 Eq.(11) Monteith ET](P3_R1_CANOPY_MONTEITH.md). Normative manual: [KfK 5194 (1993)](https://publikationen.bibliothek.kit.edu/270034158/3813483).

## Physical terms, separate evidence and hypotheses

The direct 1993 *leaf-level* gas exchange rate is derived from Eq.(1)–(4) and projected onto a **homogeneous, fixed-LAI, leaf-water-only** ground-area pool:

`a = LAI * rho_v,sat / (alpha * r_g)` in kg/(m² ground·s), with source-1993 leaf resistance `r_g [s/m]`, `LAI [m² leaf/m² ground]`, vapour density `rho_v,sat [kg/m³]`, fractionation factor `alpha [-]`; equilibrium HTO in leaf water is `C_eq=alpha*C_air/rho_v,sat [Bq/kg water]`.

The rate of **plant** transpiration `E [kg/m² ground/s]` is supplied by the previously implemented Eq.(11) Monteith plant component; **soil ET is not charged to the leaf-water store**. The model requires separately explicit external root-delivered water `R [kg/m² ground/s]` and its HTO concentration `C_root [Bq/kg]`.

Assuming (A) externally delivered root water is instantaneously mixed into leaf water, (B) transpired HTO leaves at contemporaneous homogeneous leaf concentration with **no additional transpiration isotope fractionation**, and (C) the leaf gas-exchange source can be distinguished from and added to the transpiration isotope sink, the two inventory equations are:

- Water: `dW/dt = R - E` [kg/(m² ground·s)].
- Leaf HTO: `dI/dt = a*(C_eq-C) + R*C_root - E*C` [Bq/(m² ground·s)], `C=I/W`.

**A–C are explicit research coupling hypotheses, not printed 1993 FORTRAN behavior. In particular, hypothesis C may double count atmosphere–leaf isotope exchange relative to the original complete leaf-vapour representation; requires independent scientific review before any default or production use.** The formula does not implement mechanistic root hydraulics, transit times, isotope fractionation of transpiration, water stress feedback or soil–plant multi-physics.

## Analytic interval integrator and activity ledger

For interval-constant external fluxes, leaf resistance, LAI and air forcing, `W_1=W_0+(R-E)*dt` must remain **strictly positive**. Let `K=a+R`, `C_star=(a*C_eq+R*C_root)/K`, and `L=integral(dt/W(t))`. With `beta=R-E`, `L=ln(W_1/W_0)/beta` if beta differs from zero and `L=dt/W_0` otherwise. The exact solution is:

`C_1=C_0+(C_star-C_0)*(1-exp(-K*L))`.

For separate signed air, root and transpired HTO entries, integrate the concentration:

`J=integral_0^dt C(t)dt=C_star*dt+(C_0-C_star)*(W_0/(a+E))*(1-exp(-(a+E)*L))` [Bq·s/kg].

Then `Air=a*(C_eq*dt-J)` (signed), `Root=R*C_root*dt`, `ET_HTO=E*J`; the budget requires `I_1-I_0=Air+Root-ET_HTO`. Both the water and HTO budgets are verified independently with finite tolerances. For **zero root water and zero ET**, the solution reduces exactly to P3 R5 / printed 1993 Eq.(1)–(3) at constant leaf-water mass. `expm1` and `log1p` stabilize close-to-equilibrium, small-step and equal-root/ET cases.

`src/cteas_ufotri/plant/kfk5194_1993_water_hto_joint.py` provides the opt-in `advance_kfk5194_water_hto_joint` API with required typed `KFK5194_1993_V4` profile, R1 daytime/dry canopy and typed Monteith output, explicit forcing and explicit `WELL_MIXED_NO_ET_FRACTIONATION` hypothesis. The pool is `TFWTState.area_basis="ground_area"`, with contents exclusively **leaf water**. Invalid area, isotope provenance, negative root flux, zero water, mixed-LAI Monteith output or potential water exhaustion fail closed. Output includes a frozen state, water/HTO ledger and methodological provenance.

## Tests, known gaps and exit criteria

Independent tests cover Monteith plant-only ET, exact equal root-water and ET analytical result, P3 R5 equivalence with zero water flux, zero-air reemission plus transpiration HTO removal, infinitesimal ODE slope, two half-step equivalence, water exhaustion, invalid forcings, source/area/hypothesis gates and default 1990 CLI/solver non-activation. Synthetic forcing is not historical default data.

**No full 1993 runtime activation**, no verified 1993 executable numerical parity, no field validation, no mechanistic root transport/soil/OBT, no dynamic LAI/growth. P0 issue #126 stays OPEN. Scientific review must resolve the possible air/ET isotope double-counting and evaluate transpiration fractionation *before* coupling the new source term to the production model. Do not merge a scientific implementation based on CI alone.
