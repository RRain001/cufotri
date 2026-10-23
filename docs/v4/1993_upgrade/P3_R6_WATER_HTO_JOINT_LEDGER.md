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


## R6 R4 — layer-resolved soil-to-root withdrawal audit

The source-defined uptake fractions are now used not only to calculate `Croot`,
but to expose a **three-layer extensive mass and HTO flux ledger** for every
prescribed root-flow interval. For each soil depth `i`, prescribed root
delivery `R` [kg/(m² ground·s)], step `dt` [s], and layer liquid-water HTO
`Ci` [Bq/kg water]:

```text
WaterWithdrawal_i = f_i * R * dt                       [kg/m² ground]
HTOWithdrawal_i   = WaterWithdrawal_i * Ci              [Bq/m² ground]
Sum_i WaterWithdrawal_i = R * dt
Sum_i HTOWithdrawal_i = R * dt * Croot
```

The opt-in `kfk5194_1993_root_layer_withdrawals` returns a frozen, finite,
three-layer water/HTO record, with independently checked water and activity
residuals. The R6 root-boundary adapter also cross-checks the sum against the
**actual R6 leaf-model root input**. Agricultural (20/40/40) and grass
(40/60/0) hand-calculated numerical cases, zero uptake, malformed rates,
forged layer fractions and time-splitting are independently tested.

**This is a boundary withdrawal accounting model, not a soil-state balance
solver:** no layer inventory is mutated, the local available water/HTO
inventory is not validated and potential supply exhaustion is not checked.
No leakage of an atmospheric vapor term into soil/root water accounting is
allowed. Leaf-water instantaneous homogenization remains an explicit,
unverified *research hypothesis*, not a recovered original FORTRAN
transport mechanism. PR #152 stays Draft until scientific sign-off.


## R6 R5 — static soil capacity preflight (not original soil dynamics)

The 1993 p.15 source-weighted soil-to-root withdrawal ledger now has a **separate,
opt-in available-stock validation**, `kfk5194_1993_root_soil_capacity.py`.
It requires *externally supplied*, time-consistent **liquid-water** stores
`W_soil,i` [kg/m² ground] and **HTO** stores `I_soil,i` [Bq/m² ground] for
each of the source-defined 0–5 / 5–15 / 15–30 cm horizons, in addition to the
existing source-measured concentration `C_soil,i` [Bq/kg water].

The strict well-mixed, **static bucket preflight** checks, for each horizon:

```text
I_soil,i ≈ W_soil,i * C_soil,i  (user-provided soil stock consistency)
W_taken,i = f_i * R * dt <= W_soil,i
I_taken,i = W_taken,i * C_soil,i <= I_soil,i
W_rem,i = W_soil,i - W_taken,i
I_rem,i = I_soil,i - I_taken,i
sum(W_taken,i) == R*dt
sum(I_taken,i) == R*dt*C_root
```

It returns projected post-withdrawal stocks and separately audited total water
and isotope budget residuals. Both agricultural and grass source fractions
are checked; grass has exactly zero third-layer uptake and may legitimately
have zero available water/HTO in that layer. The capacity checker rejects
insufficient stock, bad units/nonphysical input, forged fraction or forged
withdrawal values, and inconsistent source concentration versus inventory.
Synthetic tests use independently hand-calculated water and activity values.

**Crucial science limits:** This is **not** a 1993-source-derived soil
water-content or HTO transport law. It does **not mutate soil state** and it
does not supply capillary rise, rainfall, infiltration, sorption, profile
re-equilibration, organic uptake or a future soil reservoir at the next time
step. The assumption of uniform concentration within each externally
provided depth bucket and the input inventory values are research choices,
not original FORTRAN defaults. Actual state advance belongs to P4 #130 and
requires independently reviewed mass-flux control-volume coupling; this
isolated preflight is only an early rejection gate. The root-to-leaf
instantaneous mixing limitation remains unchanged. PR #152 remains Draft.


## R6 R6 — explicit immutable soil-to-root-to-leaf time progression

For a **source-specified, finite set of three liquid soil-water buckets**, a
separate opt-in `kfk5194_1993_soil_root_transfer.py` permits an immutable
**extraction-only** progression from one stationary root/leaf interval to
the next. Each previous-step soil inventory is explicitly supplied to the
next call, after checking the three source-verified depth fractions, the
per-layer extraction ledger, available soil water and HTO, and the
*unchanged* P3 R6 `R=E` Belot-composite leaf dynamics.

Its control volumes are:

```text
soil water_i, after = soil water_i, before - f_i R dt
soil HTO_i, after   = soil HTO_i, before   - f_i R dt Csoil,i
leaf water, after   = leaf water, before  (explicit R=E)
leaf HTO, after     = leaf HTO, before + Belot_composite + root_HTO

Δ(sum soil water + leaf water) + plant_transpired_water = 0
Δ(sum soil HTO + leaf HTO) - signed_Belot_composite = 0
```

`Belot_composite` already accounts for diffusion and transpiration-related
isotope loss (1993 printed p.7), so there is **no duplicate -E*C isotope sink**.
Every value is normalized to m² ground. Soil and leaf states require an
**identical UTC timestamp**; the returned immutable states carry the same
updated time; no root transport delay is silently assumed. **Changing
atmospheric/plant forcing from one interval to the next is allowed only
through new explicitly provided forcing, not through implicit interpolation.**
Independent tests cover agricultural/pasture groups, soil-layer water/HTO
removal, both cross-control-volume residuals, two 1800-s intervals versus one
3600-s interval, depleted soil rejection, soil/leaf clock mismatch and
opt-in / default-path isolation.

**Strict limitations:** This is a conservative *arithmetic extraction-only*
model, **not** UFOTRI 4.0's original soil transport model. No rainfall,
recharge, vertical diffusion, capillary movement, evapotranspiration from
soil, soil sorption, radioactive decay, growing plant biomass, OBT, root
hydraulics or lag is supplied. If no other physical process updates the
soil pools, their depletion is artificial over long durations. Therefore
these results **must not** be used as calibrated soil-plant predictions or
a production full-1993 solver. The root-to-leaf homogeneous instant mixing
is a **required research hypothesis, not source-established parity**.
P3 #129 / P4 #130 and P0 #126 stay open, and PR #152 stays Draft pending
independent scientific review.


## R6 R7 — six-hour explicit forcing transaction (no soil physics added)

`advance_kfk5194_1993_extraction_only_soil_root_leaf_intervals` takes
a nonempty **ordered tuple** of explicitly typed, piecewise constant
atmospheric/Monteith/root forcing intervals and one initial soil/leaf
state at the same UTC clock. It executes only the existing source-limited
R6 R6 single-interval operator. **Each result's immutable, depleted soil
and leaf inventories become the next interval's starting inventories**.
There is no hidden meteorological interpolation, root delay, recharge,
soil vertical motion or implicit correction of depleted source buckets.

The returned `KFK5194SoilRootLeafSeries` includes all interval records,
initial/final states, cumulative transpired water and signed composite
Belot and root HTO, and explicitly checks the six-hour telescoping
conservation relations:

```
sum_i Δt_i = t_final - t_initial
Δ(sum soil water + leaf water) + Σ_i plant_transpired_water_i = 0
Δ(sum soil HTO + leaf HTO) - Σ_i Belot_composite_HTO_i = 0
Σ_i root_water_input_i = Σ_i plant_transpired_water_i  (fixed R=E)
```

Independent numerical tests cover six consecutive 3600-second steps for
both source-defined crop classes with changing air HTO forcing, signed
release/uptake, agreement with separately replayed one-step operators,
invalid forcing sequence and failure of a second-hour extraction when a
first-layer inventory becomes inadequate. **They only establish mathematical
consistency of this declared extraction-only research operator**, not an
original 1993 UFOTRI multi-hour hydrological integration algorithm.


## P3 R6 research authorization — option A (2026-10-23)

**Project-owner decision:** the root-water-to-leaf instantaneous homogeneous
mixing approximation **may be used only in explicit, opt-in research and
numerical tests** as `INSTANT_HOMOGENEOUS_LEAF_MIXING_RESEARCH`. This permits
continuing controlled model construction and uncertainty tests. It is **not**
scientific validation of the approximation, an original UFOTRI 4.0
mechanism, a release-ready switch, or a waiver of independent review.

**Accepted engineering/testing scope (not a scientific pass):**
- Typed historical `KFK5194_1993_V4` source profile, dry-day
  fixed-leaf-water `R=E`, root composition per KfK5194 printed p.15,
  source composite Belot exchange per printed pp.3,7 without extra `-E*C`.
- **All three research switches remain explicit:** fixed-water Belot
  hypothesis, instantaneous root→leaf mixing hypothesis, and
  extraction-only/no-recharge soil inventory hypothesis. Each cannot be
  supplied implicitly or replaced by a string matching the enum name.
- Independent root water/HTO ledger, three-layer extraction capacity
  preflight, signed Belot exchange, consecutive-hour inventory budgets,
  failure on insufficient soil supply or nonphysical clock, paired
  zero-air Eq.(3) and energy/water unit checks. Exact-current-HEAD
  Python, Docker, Protected Integration, Remediation CI must pass.
- The 1990 default path and real soil/OBT/food-chain/dose calculations
  **may not** select this mode implicitly or call it a validated 1993
  historical solver. No automatic merger / Ready transition.

**Open independent scientific questions:** actual root-water transit time,
possible storage/exchange pools between root and leaf, justified
mixing timescale versus hourly simulation step, isotope fractionation
during plant transport, coupling of Belot transpiration composite sink to
root input without double-counting, and applicability outside fixed
`R=E`, one-sided fixed LAI, and homogeneous soil buckets. To assess
these, the next studies should run sensitivity tests against an explicit
*separate* candidate lag/mixing model, if credible evidence is obtained,
and retain clear source provenance; no instantaneous-mixing assumption
can be certified by algebraic conservation alone.

**Hard merge gate for PR #152:** independent scientific approval of the
chosen root→leaf compartment/flux formulation with primary source
or experimentally justified evidence, as well as all latest-head CI,
version-specific numerical regression, and a decision on
`SOURCE_LIMITED` behavior. Until that sign-off, retain **Draft,
unmerged**, do not enable the default or claim KfK5194 original
FORTRAN numerical parity (`NOT_ESTABLISHED`). P0 #126, P3 #129
and P4 #130 remain Open.
