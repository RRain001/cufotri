# V4 system food-intake-dose adapter decision R1 review

## Result

`PASS_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_AWAITING_CLOSURE_GATE`

Base: `1884bb791873d47d08ceb6300d51b6974dddf37d`

Branch: `codex/v4-system-food-intake-dose-adapter-decision-r1`

This is a control-plane/interface decision only. No production source, solver equation, replay orchestration, numerical coupling, parameter activation, calibration, Leaf R5, OBT redesign, hydrology, or real CTEAS-Atmos binding is changed.

## Why this is now the correct next stage

The upstream replay seam is already closed through Atmos/replay -> baseline leaf exchange -> three-layer soil/root -> TFWT/OBT. The remaining system connectivity gap is the downstream endpoint readout into food, intake, and dose. The repository already has V3 solvers for all three stages, so replacing their equations would be unnecessary scope expansion.

The smallest safe next architecture is an opt-in terminal endpoint adapter that composes the existing solvers while adding system-level identity, basis, and provenance gates.

## Software facts confirmed

- `FoodTransferSolver` reads public OBT/TFWT inventories and multiplies them by explicit `harvest_area_m2` before applying explicit transfer fractions.
- It reports remaining inventory but does not mutate OBT/TFWT source states.
- `FoodIntakeSolver` evaluates `FoodInventory [Bq] / food_product_mass [kg] * annual consumption [kg/year]`.
- `DoseSolver` evaluates `intake * dose coefficient`, and checks the age group.
- The dose solver does not by itself cross-check its radionuclide or pathway identifier against the upstream chain.
- V3.1 basis governance allows direct comparison only for identical mass/tissue/area bases and performs no numerical cross-basis conversion.
- Replay OBT/TFWT inventories are endpoint inventories on `soil_surface_area`.

## Frozen R1 architecture

Selected architecture: `OPT_IN_TERMINAL_DIAGNOSTIC_ENDPOINT_ADAPTER`.

The future adapter may run only against a completed replay endpoint and only after an explicit terminal harvest request. It will execute one diagnostic food transfer, one annual intake transform, and one dose transform, then return downstream states and a composite audit record.

It must not modify the upstream replay endpoint.

## Harvest semantics

R1 harvest is terminal and diagnostic. It is not an every-step sink and it does not create a depleted plant state.

Therefore:

- no automatic harvest per replay interval;
- no continuation of the same trajectory after harvest while treating plant inventory as depleted;
- no claim that the downstream readout closes the environmental mass ledger after harvest;
- a future repeated/state-mutating harvest model requires a separate decision.

Two explicit modes are frozen:

- `OBT_ONLY`: `tfwt_harvest_fraction=None`, zero TFWT food contribution;
- `OBT_PLUS_TFWT`: explicit independent `tfwt_harvest_fraction` is required.

The TFWT fraction may never be inferred from the OBT fraction.

## Area and mass-basis semantics

The only allowed geometry operation is the existing same-support multiplication:

`Bq m^-2 on soil_surface_area * explicit harvest_area_m2 -> total Bq`.

This is not permission to convert to leaf area, plant area, edible area, or another area normalization.

Before the intake calculation, R1 requires two V3.1 `MassBasisContract` records: one for food-product mass and one for consumption mass. Both must refer to the same food product, use `HARVEST_PRODUCT` tissue scope with the same product identifier, use `NOT_APPLICABLE` area basis, and pass direct comparison with identical mass/tissue/area bases.

Cross-basis numerical conversion remains forbidden. Evidence metadata alone cannot create a fresh/dry/water/hydrogen numerical relation that the software does not implement.

## Identity checks to be added by the future adapter

The future system boundary must fail closed on mismatches in:

- OBT/TFWT timestamp;
- plant identifier;
- crop identifier;
- growth stage;
- harvest request identities;
- food-product identity across harvest, mass-basis, and consumption records;
- age group across consumption and dose;
- radionuclide: exactly `H-3`;
- pathway: exactly `food-ingestion`.

No alias guessing or silent normalization is authorized.

## Provenance

Replay, harvest, food-product basis, consumption basis, consumption parameters, and dose parameters remain independently provenanced. The future adapter must preserve those domains in a composite audit record instead of replacing them with one synthetic provenance value.

## Time interpretation

The harvest/food event is anchored at the replay endpoint timestamp. The annual intake period is an exposure-period transform of that terminal product concentration. It is not evidence that the environmental model or harvest process was simulated continuously for a year.

## First exact-head certification

The first attempted head `604b6a4ec2b3f025e2fa10ec024bb753f9a5f9e4` was not certified: Protected run `33033492314` rejected a brittle exact-string governance assertion. Remediation `33033492312` passed, and no production/runtime/physics failure was observed. The branch was rewritten to preserve a one-clean-commit decision history.

Certified decision head: `8b94002dbfbdd1a2278f95a345ba488d98e06474`.

Evidence:

- Protected `33033725862`: SUCCESS;
- Remediation `33033725958`: SUCCESS;
- portable: `1259 passed, 1 skipped, 57 deselected`;
- frozen/current: `327 passed`;
- `PASS_SOFTWARE_SCREENING`;
- `PASS_SELECTION`;
- `PASS_INTEGRATION`;
- `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`.

The decision is therefore content-complete and first-head certified. This closure records that evidence only; it does not implement the adapter.

## Future implementation acceptance requirements

A later implementation may be authorized only after this governance-only closure passes a second exact-head Protected + Remediation CI and the PR merges by expected head without tree drift.

That future implementation must prove direct-chain equivalence, endpoint immutability, both harvest modes, internal food balance closure, timestamp preservation, fail-closed identities, fail-closed basis mismatch, absence of cross-basis conversion, deterministic repeat, and independent provenance retention.

## Hard holds

Still HOLD / FALSE:

- endpoint adapter implementation on this decision branch;
- state-mutating or repeated harvest;
- continuous food-chain kinetics;
- numerical mass-basis conversion;
- area-basis conversion;
- parameter activation/calibration;
- Leaf R5;
- OBT redesign;
- full hydrology/plant-water dynamics;
- real CTEAS-Atmos binding;
- empirical validation or physical-accuracy claim.

If the closure exact-head gates and no-drift merge pass, the next isolated stage is `V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_IMPLEMENTATION_R1`.
