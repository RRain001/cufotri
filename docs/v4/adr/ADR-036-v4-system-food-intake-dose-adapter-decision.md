# ADR-036: V4 food-intake-dose terminal endpoint adapter decision R1

## Status

`PASS_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_DECISION_AWAITING_EXACT_HEAD_GATE`

## Context

PR #31 merged the post-orchestration system review without tree drift at `1884bb791873d47d08ceb6300d51b6974dddf37d`. The opt-in V4 replay system now reaches authoritative endpoint `TFWTState` and `OBTState` values while preserving the frozen V3 default, the selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` split, and the existing soil/root/TFWT/OBT component equations.

The remaining north-star software gap is the terminal chain from those replay endpoint inventories to food, annual intake, and dose. The repository already contains V3 `FoodTransferSolver`, `FoodIntakeSolver`, and `DoseSolver`; therefore this stage must decide only how an opt-in V4 adapter may compose those existing public APIs without silently changing upstream physics, harvest semantics, basis semantics, or provenance.

This ADR authorizes no implementation on the present branch.

## Existing API facts

The decision is based on the exact merged software state, not on a proposed replacement model.

1. `FoodTransferSolver` consumes public `OBTState` and `TFWTState` inventories, requires a shared harvest timestamp, multiplies the area-normalized source inventories by explicit `harvest_area_m2`, and returns `FoodInventory`, `HarvestState`, and a food-transfer balance.
2. The food solver reports `remaining_plant_inventory_bq` but does **not** mutate or return depleted OBT/TFWT source states.
3. `FoodIntakeSolver` uses `FoodInventory [Bq] / food_product_mass_kg [kg] * annual_consumption_amount [kg/year]`.
4. `DoseSolver` uses annual intake and an explicit dose coefficient under `D = I * e` and checks age-group identity.
5. V3.1 `MassBasisContract` provides metadata and fail-closed comparison gates only. It implements no numerical fresh/dry/water/hydrogen conversion and no area conversion.
6. The replay endpoint remains normalized to `soil_surface_area`; its OBT and TFWT inventories are authoritative in `Bq m^-2` on that same support.

## Decision

Select an **opt-in terminal diagnostic endpoint adapter** for the future implementation stage.

The adapter will be a one-way composition/readout layer over a **completed replay endpoint**. It may call the existing food, intake, and dose solvers after additional fail-closed identity and basis checks, but it may not alter replay dynamics or component solver equations.

The selected future order is:

1. accept one completed V4 replay endpoint and an explicit terminal harvest request;
2. validate endpoint timestamp, plant/crop/growth-stage identity, common `soil_surface_area` support, product identity, and independent provenance;
3. validate the explicitly selected harvest mode;
4. perform one diagnostic food-transfer readout with the existing `FoodTransferSolver`;
5. validate food-product and consumption `MassBasisContract` values for direct comparison only;
6. perform one annual intake transform with the existing `FoodIntakeSolver`;
7. validate age group, radionuclide, pathway, and dose provenance;
8. perform one dose transform with the existing `DoseSolver`;
9. return the downstream states plus a composite audit record while leaving the upstream replay endpoint unchanged.

## Terminal harvest semantics

R1 freezes harvest as an explicit **terminal diagnostic event**.

- No harvest is executed automatically on each replay interval.
- The caller must explicitly request the harvest after a completed replay endpoint exists.
- The harvest event timestamp must equal the endpoint TFWT/OBT timestamp.
- The same environmental trajectory must not continue after this diagnostic harvest while pretending that the plant source inventory has been depleted.
- The food solver's reported remaining inventory is an audit quantity for the diagnostic event, not a replacement plant state.
- A future state-mutating harvest or repeated-harvest model requires a separate coupling/physics decision.

Because the readout does not deplete the replay state, the downstream food/intake/dose branch must not be inserted into the replay coupled mass ledger as an environmental sink. Its food-transfer balance may close internally, but no post-harvest environmental conservation claim is permitted in R1.

## Harvest modes

The future adapter request must make the harvest mode explicit; implicit interpretation of `tfwt_harvest_fraction` is not sufficient at the V4 boundary.

### `OBT_ONLY`

- `HarvestParameters.harvest_fraction` applies to OBT.
- `tfwt_harvest_fraction` must be `None`.
- Food TFWT inventory must be exactly zero.

### `OBT_PLUS_TFWT`

- `HarvestParameters.harvest_fraction` applies to OBT.
- `tfwt_harvest_fraction` must be explicitly supplied.
- Both OBT and TFWT contributions remain separately visible in `FoodInventory` and the audit ledger.

No mode may infer a TFWT fraction from the OBT fraction.

## Area and geometry semantics

Replay OBT/TFWT inventories remain authoritative on `soil_surface_area` in `Bq m^-2`.

The only R1 geometry operation is:

`source inventory [Bq m^-2 soil_surface_area] * harvest_area_m2 [m^2 of the same ground support] -> total source activity [Bq]`.

`harvest_area_m2` is therefore an explicit physical extent on the same ground/soil-surface support, not a conversion to leaf area, plant area, edible-area, or another normalization. Silent area conversion is forbidden.

After total food activity is formed, the food/intake mass-basis contracts are not area-normalized and must use V3.1 `AreaBasisKind.NOT_APPLICABLE` for R1.

## Mass/tissue/product basis semantics

The future adapter must require **two explicit V3.1 contracts**:

1. a food-product mass-basis contract governing `food_product_mass_kg`;
2. a consumption mass-basis contract governing `annual_consumption_amount`.

Before intake arithmetic, the adapter must call the semantic equivalent of `require_direct_comparison` and fail closed unless mass basis, tissue scope, and area basis are identical.

For R1:

- both contracts must identify the same `food_product_identifier`;
- both must use `TissueScopeKind.HARVEST_PRODUCT` with an explicit matching product identifier;
- both must use `AreaBasisKind.NOT_APPLICABLE`;
- `food_product_mass_kg` is interpreted on the declared food-product mass basis;
- `annual_consumption_amount` is interpreted on the declared consumption mass basis;
- cross-basis conversion is forbidden even when evidence metadata exists, because V3.1 contains no reviewed numerical conversion relation.

Thus a fresh-mass consumption rate may not be multiplied by a dry-mass food concentration unless a later stage implements and independently reviews an explicit numerical conversion relation.

## Identity gates

The future adapter must add system-level checks that are not all enforced by the individual V3 solvers.

Required exact identities are:

- endpoint OBT and TFWT timestamps;
- endpoint OBT and TFWT plant identifier;
- endpoint OBT and TFWT crop identifier;
- endpoint OBT and TFWT growth stage;
- harvest request plant/crop/growth-stage identifiers against the endpoint;
- food-product identifier across harvest, food inventory, both mass-basis contracts, and consumption parameters;
- age-group identifier across consumption and dose parameters;
- dose radionuclide identifier exactly `H-3` for this HTO/OBT pathway;
- dose pathway identifier exactly `food-ingestion` in R1.

No fuzzy matching, alias guessing, case folding, or nearest-category substitution is authorized.

## Provenance ownership

Provenance must remain domain-specific.

- replay endpoint provenance remains upstream evidence and is not overwritten;
- harvest parameters own harvest-event/product provenance;
- each mass-basis contract owns basis provenance;
- consumption parameters own consumption-data provenance;
- dose parameters own dose-coefficient provenance.

The existing V3 states carry the local stage provenance supplied to their solver. The future V4 adapter must therefore return a separate composite audit record that preserves references/fingerprints for all upstream and downstream provenance domains. It must not forge one synthetic provenance object and attach it to every stage.

## Time semantics

The food event timestamp is the replay endpoint timestamp. Intake and dose may retain that timestamp as the provenance anchor of the evaluated harvest product.

The `annual` intake period is an exposure-period transform applied to a terminal food-product concentration. It is **not** a statement that the environmental replay, plant dynamics, or harvest transfer were simulated continuously for one year.

## Parameter status and scientific interpretation

R1 does not activate or validate any endpoint parameter.

Existing harvest fractions, TFWT harvest fractions, annual consumption amounts, product masses, and dose coefficients remain explicit scenario/provisional inputs under their current API rules. The earlier synthetic sensitivity screen demonstrated computational dependence only; it does not provide physical uncertainty ranges, calibration, or parameter validation.

## Future implementation acceptance gates

If and only if this decision later passes both exact-head gate rounds and merges without tree drift, a new isolated implementation branch may be authorized. That implementation must demonstrate at least:

1. exact composition equivalence to direct `FoodTransferSolver -> FoodIntakeSolver -> DoseSolver` calls for identical valid inputs;
2. upstream replay endpoint object/value immutability before and after the diagnostic readout;
3. explicit `OBT_ONLY` and `OBT_PLUS_TFWT` mode tests;
4. food-transfer internal balance closure;
5. exact endpoint timestamp preservation;
6. fail-closed plant/crop/growth-stage/product/age/radionuclide/pathway identity tests;
7. fail-closed mass/tissue/area-basis mismatch tests;
8. explicit proof that cross-basis conversion is not performed;
9. deterministic repeat;
10. independent provenance retention for replay, harvest, basis, consumption, and dose domains;
11. no change to V3 default behavior, replay orchestration equations, selected operator split, or upstream conservation ledgers.

## Non-authorization

This decision does not authorize on the current branch:

- production endpoint-adapter implementation;
- state-mutating or repeated harvest;
- continuous food-chain transfer kinetics;
- fresh/dry/water/hydrogen numerical conversion;
- area-basis conversion;
- parameter activation or calibration;
- Leaf R5/dynamic stomata;
- OBT physics redesign;
- full soil hydrology or plant-water dynamics;
- real CTEAS-Atmos binding;
- empirical validation or physical-accuracy claims.

The frozen V3 default, merged V4 replay orchestration, component equations, `PRESERVE_V3_POST_OBT_ROOT_GAIN`, and `ACTIVE_PARAMETERS=0` remain unchanged.

If this decision closes through both exact-head gates and a no-drift merge, the only newly authorized next stage is `V4_SYSTEM_FOOD_INTAKE_DOSE_ADAPTER_IMPLEMENTATION_R1` on a new isolated branch.
