# ADR-031: V4 soil-root-TFWT-OBT integration R1

Status: Accepted after implementation-head machine gate; closure-head CI required before merge

## Context

The merged operator-split decision selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` for the first opt-in V4 integration of the three-layer soil and root cores with the existing TFWT and OBT inventory solvers.

This stage exists to connect already-authorized software components without expanding the physical model. In particular, R1 does not authorize a transpiration model, Richards/Darcy hydrology, plant-water storage, area conversion, UFOTRI reference-profile activation, Leaf R5, food/intake/dose integration, or real CTEAS-Atmos binding.

## Frozen interval semantics

For one interval `[t_n, t_n+1]`:

1. validate a composite interval-start state containing three-layer soil, TFWT, and OBT;
2. require one identical declared area basis across all three reservoirs;
3. compute one non-mutating `root_v4` transfer plan from `S_n` and explicit external `q_w,i` forcing;
4. advance OBT using interval-start TFWT only;
5. reject the interval if OBT formation would consume more TFWT than exists at interval start;
6. apply the same root plan once as the soil root-water/HTO sink;
7. reconcile endpoint TFWT as interval-start TFWT minus TFWT-to-OBT formation plus the interval-integrated root HTO transfer;
8. require root-plan identity, plant HTO conservation, soil conservation, and coupled soil+plant HTO conservation to close.

The base soil forcing must have zero root-extraction slots. The integrator alone inserts the transfer-plan fluxes. This makes duplicate root application fail closed.

## Area and water boundaries

R1 does not infer that `plant_area == soil_surface_area`. It accepts integration only when soil, TFWT, and OBT already declare the same area basis. A future geometry adapter is required before distinct bases can be coupled.

The root water transfer is applied to the soil storage sink because it is the carrier for `J_root,i = q_w,i C_w,i`. R1 does not add that water to TFWT water content and therefore does not claim coupled plant-water conservation. TFWT water content remains the existing fixed storage basis.

## Parameter boundary

The production integration object requires an explicit soil solver and an explicit OBT solver. It defines no soil half-life, OBT `kf/kr`, root-water flux, UFOTRI root fraction, or delay default.

Synthetic test and machine-harness values are labelled `TEST_ONLY`; they do not become validated or active parameters. The H-3-scale half-life used by the synthetic machine harness is a numerical-conditioning fixture only, not a runtime default or parameter activation.

## Restart contract

The opt-in composite state is JSON round-trippable from authoritative soil, TFWT, and OBT inventories plus their existing provenance and basis metadata. Restart must reproduce a direct multi-step run exactly under the same explicit forcing sequence.

## Machine evidence

Implementation head `966ac71c590b8a0e850d9d9ec01b5bdcef285116` passed the protected exact-head gate in run `33028178452`:

- portable suite: `1216 passed`, `1 skipped`, `57 deselected`;
- frozen-boundary suite: `295 passed`;
- sensitivity screening: `PASS_SOFTWARE_SCREENING`;
- operator-split gate: `PASS_SELECTION`;
- integration machine result: `PASS_INTEGRATION`;
- deterministic repeat: PASS;
- restart equivalence: PASS;
- root-pulse post-OBT semantics: PASS;
- maximum root-plan identity residual: `0 Bq m^-2`;
- maximum plant residual: `4.44e-16 Bq m^-2`;
- maximum soil residual: `4.16e-17 Bq m^-2`;
- maximum coupled residual: `4.88e-15 Bq m^-2`.

The closure commit changes governance/report/test assertions only. Its new exact head must pass the same protected CI before the PR can be marked Ready or merged.

A passing synthetic gate is software integration evidence only. It is not empirical or physical validation. No subsequent stage is authorized by this ADR.
