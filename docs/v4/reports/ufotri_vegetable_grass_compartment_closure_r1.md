# UFOTRI vegetable/grass compartment closure R1

Stage: `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1`

Candidate status: `PENDING_EXACT_HEAD_CI`

## 1. Result

D3 reconstructs the recoverable long-term vegetable HTO/OBT compartment semantics from KfK 4605 Eq. (65)-(66) as a separate opt-in conservative two-compartment solver and closes the Eq. (67)-(81) grass/soil ownership mapping without activating a duplicate equilibrium-rate transport system.

The frozen RC1 path, historical V2 source, existing `obt_v3` solver and existing V4 soil-root-TFWT-OBT integrator are unchanged.

## 2. Why source code is required

Eq. (65) is not merely an OBT disappearance term. It is explicitly `plant OBT -> plant HTO`. Historical V2 reflects this topology by adding OBT turnover back to plant TFWT.

The already qualified short-term `OBTSolver` instead reports `kr` as `other_loss` from the OBT inventory. That boundary remains valid for B1/B2's controlled short-term profiles, but reusing it unchanged for the long-term ingestion equations would lose activity externally instead of returning it to TFWT.

D3 therefore adds a separate long-term compatibility solver rather than changing the frozen short-term solver.

## 3. Vegetable Eq. (65)-(66)

Manual evidence:

```text
Eq.65: t15,14 = ln(2)/10 d^-1        plant OBT -> plant HTO
M_OBT = 0.1 kg m^-2
M_HTO = 0.4 kg m^-2
water-H divisor = 9
organic-H divisor = 13
Eq.66: t14,15 ~= 0.012 d^-1          plant HTO -> plant OBT
```

B1 already established the state-role boundary:

```text
free plant HTO + exchangeable OBT role -> TFWTState
non-exchangeable OBT                  -> OBTState
separate exchangeable OBT pool        -> FALSE
```

D3 preserves that boundary.

Two forward-rate descriptions are retained explicitly:

1. exact Eq. (66) reconstruction from the stated masses/divisors;
2. the manual-rounded `0.012 d^-1` value.

The caller must choose one by identifier. There is no automatic preference and no claim that the unavailable original executable selected either representation.

The reverse rate is Eq. (65), `ln(2)/10 d^-1`, for both profiles.

## 4. Conservative analytic solver

For total plant activity `T = H + O` and constant rates:

```text
dO/dt = kf H - kr O
H = T - O
lambda = kf + kr
Oeq = kf/lambda * T
O1 = Oeq + (O0-Oeq) exp(-lambda dt)
H1 = T - O1
```

The numerical method exactly integrates the recovered constant-rate two-box equation and keeps Eq. (65) internal to the pair. It is an implementation choice, not a recovered original UFOTRI discretization.

The exact Eq. (66) profile reproduces the manual equilibrium requirement that organic and inorganic plant compartments have equal specific tritium activity when the stated hydrogen inventories are used.

## 5. Grass Eq. (67)-(81)

The manual's second food-chain area uses:

- soil layers 0–5, 5–15 and 15–30 cm;
- pasture root allocation 40/60/0;
- equilibrium-derived reference transfer rates for grass/atmosphere/soil exchange.

Those physical roles now already have post-RC1 owners:

```text
leaf/atmosphere exchange -> plant.leaf_ufotri_v4
soil water/HTO transport -> plant.soil_ufotri_v4 + plant.soil_v4
pasture root allocation  -> plant.root_v4.pasture_profile
```

D3 therefore records Eq. (67)-(81) as a typed reference/ownership map with the manual values, but `reference_rates_activated=False`. No second soil, hydrology or atmosphere solver is added.

This is deliberate. Eq. (67)-(81) rates were equilibrium-derived under historical fixed inventories/conditions; silently activating them alongside the already reconstructed dynamic mechanisms would double count pathways and promote historical reference assumptions into production behavior.

## 6. Grass OBT boundary

Grass OBT is not closed in D3.

Eq. (105-1) gives the grass HTO -> OBT formation role, but Eq. (105-2) defines grass OBT -> HTO only after subtracting organic-grass losses to cow and milk routes. Those animal transfer pathways belong to Eq. (82)-(105-2) and are D4 scope.

Therefore:

`GRASS_OBT_EQ105_COMPLETED=FALSE`

D3 does not invent a reverse grass OBT rate independent of the D4 animal chain.

## 7. Project assumptions excluded

The V2 parameter audit classifies many downstream quantities as project assumptions, including crop biomass/yield, edible fraction, LAI/phenology, feed and drinking-water intake, animal support area and beef turnover. None is activated by D3.

The manual grass masses and Eq. (67)-(81) rates are retained as historical manual reference evidence, not as a production parameter packet.

## 8. Machine qualification

The D3 machine gate requires:

- independent analytic one-day state agreement for exact and rounded Eq. (66) profiles;
- total HTO+OBT activity conservation;
- forward HTO -> OBT behavior;
- reverse OBT -> HTO return into TFWT;
- zero external loss in the closed pair;
- deterministic repeat;
- 24 h = 12 h + restart + 12 h semigroup equivalence;
- 24 h = 24 x 1 h partition equivalence;
- zero-inventory stability;
- exact-vs-rounded profile distinction;
- exact-profile equilibrium specific-activity ratio = 1;
- metadata and interval fail-closed tests;
- exact grass layer/root mapping;
- Eq. (67)-(81) reference-rate mapping;
- `reference_rates_activated=False`;
- D2 root profile unchanged;
- Eq. (105) remains D4.

## 9. Candidate source set

New files only:

- `src/cteas_ufotri/foodchain/ufotri_vegetable_grass_v4.py`;
- `scripts/v4/run_ufotri_vegetable_grass_compartment_closure_r1.py`;
- `tests/v4/test_ufotri_vegetable_grass_compartment_closure_r1.py`;
- `docs/v4/adr/ADR-068-ufotri-vegetable-grass-compartment-closure-r1.md`;
- `docs/v4/governance/ufotri_vegetable_grass_compartment_closure_r1.yaml`;
- this report.

No roadmap modification is part of the D3 implementation PR.

## 10. Candidate claim and non-claims

If exact-head Remediation and Protected CI pass and merge/no-drift is verified, D3 may claim:

`UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE=COMPLETE`

This scoped claim means vegetable Eq. (65)-(66) has a conservative opt-in long-term compartment implementation and grass Eq. (67)-(81) has a non-duplicating role/reference closure against the already reconstructed leaf/soil/root paths.

It does not mean any of the following:

- grass OBT Eq. (105) complete;
- cow/milk/beef complete;
- public exposure complete;
- project crop/animal parameters are UFOTRI production defaults;
- calibration or empirical validation;
- physical-accuracy or production-readiness claim;
- real CTEAS-Atmos binding;
- original numerical-discretization recovery;
- original-executable equivalence.

After D3 merge/no-drift and a separate roadmap-status PR, the next authorized stage is:

`UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`.
