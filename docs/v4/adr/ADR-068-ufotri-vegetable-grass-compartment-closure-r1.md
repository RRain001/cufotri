# ADR-068 — UFOTRI vegetable/grass compartment closure R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1`

## Context

D1 established that the retained V2 continuous ecological chain contains useful UFOTRI topology but cannot be activated wholesale because manual-derived rates are mixed with project biomass, support-area, intake and inventory-engineering assumptions. D2 separately closed the manual-direct pasture root allocation `(0.4, 0.6, 0.0)` for the three UFOTRI soil layers.

KfK 4605 Section 3.3.3 Eq. (65)-(66) defines vegetable plant OBT → plant HTO and plant HTO → plant OBT as a reversible pair. The manual assumes an OBT loss half-time of about 10 d and derives the forward coefficient from the stated organic/inorganic masses and hydrogen divisors. The already qualified short-term V4 `OBTSolver` instead exposes its `kr` contribution as an OBT `other_loss`; it does not return that activity to TFWT. Reusing it unchanged would therefore not be a literal Eq. (65) long-term food-chain implementation.

KfK 4605 Eq. (67)-(81) gives an equilibrium-oriented grass/soil/atmosphere transfer-rate system. Its physical roles overlap mechanisms that are already separately reconstructed in post-RC1 V4: UFOTRI leaf exchange, three-layer soil/hydrology, and D2 pasture root uptake. Creating a second rate-matrix soil/atmosphere solver in D3 would duplicate ownership and risk double counting.

Grass OBT Eq. (105-1)-(105-2) is outside D3. In particular Eq. (105-2) subtracts grass-OBT losses to cow/milk pathways before defining grass OBT → grass HTO, so its literal closure depends on D4 animal compartments.

## Decision

1. Add a new opt-in module `foodchain/ufotri_vegetable_grass_v4.py`; do not modify existing V2, RC1, `obt_v3`, or V4 integration source.
2. Implement Eq. (65)-(66) as a closed two-compartment analytic constant-rate system:
   - TFWT carries free plant HTO plus the exchangeable-OBT role established in B1;
   - OBTState carries non-exchangeable OBT;
   - no third exchangeable-OBT inventory is introduced;
   - OBT → HTO activity returns to TFWT and is not an external loss.
3. Require the caller to select the Eq. (66) forward-rate basis explicitly. D3 supports:
   - exact reconstruction from the manual's stated masses/divisors;
   - the manual-rounded `0.012 d^-1` value.
   There is no hidden selection and no claim about the unavailable original executable's choice.
4. Preserve Eq. (67)-(81) values as a typed reference/ownership map only. The map records the canonical 0–5/5–15/15–30 cm layers, D2 40/60/0 roots, and the manual reference rates while explicitly setting `reference_rates_activated=False`.
5. Keep ownership of the active physical mechanisms with the previously qualified modules:
   - leaf exchange → `plant.leaf_ufotri_v4`;
   - soil water/HTO transport → `plant.soil_ufotri_v4` + `plant.soil_v4`;
   - pasture root allocation → `plant.root_v4.pasture_profile`.
6. Defer grass OBT Eq. (105-1)-(105-2) and all cow/milk/beef transfers to D4.
7. Do not activate historical/project-specific crop biomass, edible fraction, LAI, phenology, grazing intake, animal support area, milk/beef or production assumptions.

## Numerical method

For constant rates `kf` and `kr` and total plant activity `T = H + O`:

```text
dO/dt = kf H - kr O
H = T - O
lambda = kf + kr
Oeq = kf/lambda * T
O(t+dt) = Oeq + (O(t)-Oeq) exp(-lambda dt)
H(t+dt) = T - O(t+dt)
```

This is an implementation choice for exact integration of the recovered two-box equation; it is not claimed to reproduce the unavailable original executable's discretization.

## Required D3 gates

- exact Eq. (65)-(66) analytic agreement;
- total activity conservation;
- positive HTO→OBT transfer from an HTO-only initial state;
- positive OBT→HTO return from an OBT-only initial state;
- deterministic repeat;
- two-half-step restart/semigroup equivalence;
- 24×1 h partition equivalence to one 24 h analytic step;
- zero-inventory stability;
- explicit forward-rate selection and preserved exact-vs-rounded numerical distinction;
- exact-profile equilibrium organic/inorganic specific-activity ratio of one;
- fail-closed metadata/time-step validation;
- Eq. (67)-(81) role-map/layer/root/rate evidence checks;
- confirmation that legacy Eq. (67)-(81) reference rates are not activated;
- confirmation that grass OBT Eq. (105) remains D4 work.

## Consequences

D3 may close the recoverable vegetable Eq. (65)-(66) compartment semantics and the grass Eq. (67)-(81) ownership/mapping boundary without adding a second soil or atmosphere solver. It does not complete cow/milk/beef, grass OBT Eq. (105), public exposure, production parameterization, empirical validation, real CTEAS-Atmos binding, or original-executable equivalence.

If exact-head CI and merge/no-drift pass, the authorized scoped claim is:

`UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE=COMPLETE`

The next stage is `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1` after a separate roadmap-status PR.
