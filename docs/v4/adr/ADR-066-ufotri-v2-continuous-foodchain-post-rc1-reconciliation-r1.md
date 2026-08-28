# ADR-066 — UFOTRI V2 continuous food-chain to post-RC1 reconciliation R1

## Status

Candidate pending exact-head CI.

Stage: `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`

## Context

The post-RC1 replication roadmap requires reconciliation of two deliberately different downstream boundaries:

1. the historical V2 continuous ecological food-chain and dose path; and
2. the frozen V4 RC1 one-way terminal harvest → intake → dose diagnostic adapter.

The target is not to choose one and delete the other. The target is to identify which V2 mechanisms correspond to recoverable KfK 4605 roles, which V2 mechanisms are engineering/project extensions, which manual roles remain absent, and how a later opt-in UFOTRI compatibility path can coexist with the RC1 fallback/default.

Primary manual anchors are KfK 4605 Eq. (65)-(107), summarized in `docs/v2/manual_equation_inventory.md`.

## Frozen repository evidence

The annotated tag `ufotri-environmental-pathways-v2-candidate` resolves to commit:

`f097115cbfc052baa18f1e49a1207fa6b3523cff`

The tag object is:

`11eb90096b2c08a0b40c7cf7f2917d473535e8c7`

Three central V2 files are still byte-identical on current `main`:

- `src/cteas_ufotri/case.py` — blob `54c3155810a119b796dea0b1480e4a559fed5b0e`;
- `src/cteas_ufotri/foodchain/model.py` — blob `fc9b9a6b440fd0da8a00f93455c594607c3cc635`;
- `src/cteas_ufotri/dose/public.py` — blob `e7ac3c125dcb53583a3015b002e545cb2cfc8f91`.

This means the historical continuous implementation has not been lost. It is retained source that is no longer the V4 RC1 downstream default.

Current post-RC1 reference boundaries include:

- `plant/food_v3/food_transfer_solver.py` — blob `2061ed157df0b59fff194ad41034b5ae7f3ee7c7`;
- `exposure/intake_v3/intake_solver.py` — blob `1c0f6019d733183ba57265a96f41a4fcda909e04`;
- `v4_integration/food_intake_dose_endpoint.py` — blob `c715ec905904c1391095fc84c2465045815664ab`.

The RC1 adapter is explicitly terminal, one-way and non-mutating. It is not an environmental mass sink.

## Manual-to-V2 reconciliation

### Eq. (65)-(66): vegetable HTO/OBT

V2 `plant_food_outputs` projects plant TFWT and OBT into fresh-food concentration channels. This projection is useful and may be retained as an interface role, but it is not by itself sufficient to claim the complete manual vegetable compartment reconstruction.

Disposition:

`RETAINABLE_CONCENTRATION_PROJECTION_REQUIRES_D3_MANUAL_CLOSURE`

### Eq. (67)-(81): grass-atmosphere/soil

V2 preserves a continuous pasture concentration route and the driver feeds it into the animal pathway. However, the manual pasture root distribution `40/60/0` and the explicit grass/soil fidelity closure remain separate obligations.

Disposition:

`PARTIAL_TOPOLOGY_REQUIRES_D2_D3`

### Eq. (82)-(84): cow water/boundary losses

`AnimalState` and `step_animal` provide explicit HTO/OBT inventories, feed/drinking-water inputs and excretion/boundary outputs. The topology is useful, but representative support-area normalization and some intake quantities are project assumptions.

Disposition:

`RETAINABLE_TOPOLOGY_PARAMETER_SPLIT_REQUIRED`

### Eq. (85)-(91): milk HTO/OBT

V2 has separate milk HTO and OBT outputs and manual-converted transfer-rate candidates. These roles can be retained, but D4 must isolate manual rate provenance from project herd geometry and modern consumption assumptions.

Disposition:

`RETAINABLE_TOPOLOGY_MANUAL_RATE_PROVENANCE_REQUIRED`

### Eq. (92)-(97): cow OBT formation/turnover

V2's animal HTO/OBT two-pool topology contains formation and turnover terms consistent with the recoverable manual role. D4 still owes equation-level verification and parameter provenance qualification.

Disposition:

`RETAINABLE_TOPOLOGY_MANUAL_RATE_PROVENANCE_REQUIRED`

### Eq. (98): cow inhalation/skin uptake

This manual animal-uptake role is not present in `foodchain.model.step_animal`.

The inhalation and skin terms in `dose.public.calculate_public_dose_step` are public dose terms and must not be relabeled as cow uptake.

Disposition:

`MISSING_IN_V2_ANIMAL_CORE_REQUIRES_D4`

### Eq. (99)-(105-2): grass-to-cow and grass balance

The V2 driver continuously connects pasture food concentrations to animal feed inputs. That coupling topology is useful. However, feed quantity, support area and beef herd turnover include project assumptions rather than recoverable original-UFOTRI truth.

Disposition:

`RETAINABLE_CONTINUOUS_COUPLING_PARAMETER_SPLIT_REQUIRED`

### Eq. (106): public inhalation + skin dose

V2 explicitly reports inhalation and skin components. The pathway topology is useful, but modern age-specific dose coefficients are application-layer evidence, not original UFOTRI parameter evidence.

Disposition:

`RETAINABLE_PATHWAY_TOPOLOGY_PARAMETER_POLICY_CORRECTION_REQUIRED`

### Eq. (107): public ingestion dose

V2 continuously accumulates drinking-water, plant, milk and meat ingestion dose. The manual inventory records that original UFOTRI used one adult HTO coefficient and treated ingested OBT as HTO. V2's separate modern OBT ingestion coefficient is therefore a project/literature extension and cannot be presented as manual-exact.

Disposition:

`RETAINABLE_PATHWAY_TOPOLOGY_PARAMETER_POLICY_CORRECTION_REQUIRED`

## Manual balance versus V2 engineering closure

The available manual describes food-chain parameters as equilibrium-oriented daily transfer rates and explicitly imperfect balances.

V2 strengthened this into auditable inventory closure by representing harvest, milk, slaughter, excretion, deep loss and product consumption as boundaries. That engineering choice is valuable for a modern compatibility implementation, but it is not evidence that the original UFOTRI executable used the same ledger/discretization.

Therefore:

`HISTORICAL_V2_MASS_CLOSURE_IS_ORIGINAL_UFOTRI_ALGORITHM=FALSE`

## Parameter provenance split

Manual/manual-converted candidates include the recorded cow milk production and animal transfer/loss rates, subject to later equation-level verification.

Project/application extensions include, among others:

- 50 kg fresh/day feed intake;
- 50 L/day animal drinking water;
- 4000 m²/animal support-area normalization;
- 200 kg/head edible beef mass;
- 0.002 d⁻¹ continuous herd turnover;
- age-specific modern dose coefficients;
- separate modern OBT ingestion dose coefficient;
- RC1 terminal harvest/annual-consumption inputs.

No D1 decision activates any of these as production or original-UFOTRI parameters.

## Decision

D1 is a reconciliation-only stage:

`D1_EXISTING_SOURCE_CHANGE=FALSE`

No historical V2 code is directly activated in V4 by this stage.

Later UFOTRI food-chain work must be an explicit:

`OPT_IN_PARALLEL_COMPATIBILITY_PATH`

The frozen V4 RC1 terminal endpoint remains available and unchanged as the stable project fallback/default.

The next implementation/reconciliation partition is:

1. `UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1`;
2. `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1`;
3. `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`;
4. `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`.

## Consequences

This stage permits the claim that historical V2 continuous food-chain code has been located, provenance-locked and semantically partitioned against the manual and RC1 boundaries.

It does not permit claims of:

- completed vegetable/grass fidelity;
- completed cow/milk/beef fidelity;
- completed exposure fidelity;
- original UFOTRI numerical discretization recovery;
- original executable equivalence;
- empirical validation;
- calibration;
- production parameter activation;
- physical accuracy;
- real CTEAS-Atmos binding.

If exact-head CI and no-drift merge pass, the permitted stage claim is:

`UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RECONCILIATION=COMPLETE`
