# UFOTRI V2 Continuous Food-chain to Post-RC1 Reconciliation R1

Stage: `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`

Candidate status: `PENDING_EXACT_HEAD_CI`

## 1. Result in one sentence

The historical V2 continuous plant→pasture→animal→milk/beef→dose path is still present byte-for-byte in the repository and contains substantial recoverable UFOTRI topology, but it is not safe to activate as a single block because it mixes manual-derived rates, explicit modern inventory-closure engineering, project geometry/intake assumptions and later dose-coefficient extensions; the frozen RC1 terminal-harvest endpoint therefore remains the default while D2-D5 reconstruct an opt-in continuous compatibility path by compartment.

## 2. Frozen evidence

The V2 candidate is anchored to annotated tag `ufotri-environmental-pathways-v2-candidate`, tag object `11eb90096b2c08a0b40c7cf7f2917d473535e8c7`, resolving to commit `f097115cbfc052baa18f1e49a1207fa6b3523cff`.

The D1 machine gate verifies byte identity between that tag and the current checkout for:

- `src/cteas_ufotri/case.py` — `54c3155810a119b796dea0b1480e4a559fed5b0e`;
- `src/cteas_ufotri/foodchain/model.py` — `fc9b9a6b440fd0da8a00f93455c594607c3cc635`;
- `src/cteas_ufotri/dose/public.py` — `e7ac3c125dcb53583a3015b002e545cb2cfc8f91`.

Therefore D1 does not need to restore or copy historical source before reconciliation.

## 3. Continuous V2 semantics

`case.run_short_case` updates the ecological system at every time step. The retained chain calls plant edible/concentration projection, `plant_food_outputs`, `step_animal`, `step_beef_product`, and `calculate_public_dose_step`.

The public dose function explicitly scales daily habits by `dt_s / 86400`, so the V2 public-dose path is a continuous per-step accumulation path rather than a single terminal readout.

The animal model includes:

- body HTO inventory;
- body OBT inventory;
- pasture/feed HTO input;
- pasture/feed OBT input;
- drinking-water HTO input;
- HTO↔OBT formation/turnover roles;
- HTO/OBT milk outputs;
- HTO/OBT excretion;
- slaughter outputs.

The beef-product extension adds explicit produced/stored/consumed HTO and OBT inventories and edible-mass accounting.

## 4. Why direct V2 activation is rejected

### 4.1 Manual balances are not the same as V2 ledgers

The manual equation inventory records that UFOTRI food-chain parameters are equilibrium-oriented daily transfer rates and that the available manual balances are explicitly imperfect.

V2 deliberately strengthens these paths into conservative inventories using explicit boundary losses for harvest, milk, slaughter, excretion, deep loss and product consumption.

This is desirable software engineering, but it is not evidence that the original executable used the same state variables, limiter, operator ordering or boundary ledger.

### 4.2 Manual and project parameters are mixed

The V2 parameter-source audit supports several animal rates as manual/manual-converted candidates, including milk production, HTO/OBT excretion, milk transfer and cow OBT formation/turnover.

It also identifies project assumptions such as representative feed/water intake, 4000 m² per animal support area, beef edible mass and continuous herd turnover.

Direct activation would therefore silently promote project assumptions into the UFOTRI fidelity path.

### 4.3 Eq. (98) is a real missing animal role

KfK 4605 Eq. (98) concerns cow inhalation/skin uptake. `foodchain.model.step_animal` does not contain that route.

The inhalation and skin terms in `dose.public` are human/public dose terms and cannot be reused as animal uptake without changing their physical meaning.

D4 must close Eq. (98) explicitly.

### 4.4 Public dose coefficient policy differs from the manual

The manual inventory records one adult HTO coefficient and treatment of ingested OBT as HTO.

V2 supports age-specific modern HTO coefficients and a distinct OBT ingestion coefficient. Those are useful modern application inputs, but they are not evidence of the original UFOTRI coefficient policy.

D5 must preserve both provenance and the distinction between manual-fidelity behavior and modern application behavior.

## 5. Manual-role disposition matrix

| Manual role | Eq. | D1 disposition | Next owner |
|---|---|---|---|
| Vegetable HTO/OBT | 65-66 | Retain concentration projection; full manual closure still required | D3 |
| Grass atmosphere/soil | 67-81 | Partial topology; root/grass closure incomplete | D2/D3 |
| Cow water/boundary loss | 82-84 | Retainable topology; parameter split required | D4 |
| Milk HTO/OBT | 85-91 | Retainable topology; manual-rate provenance required | D4 |
| Cow OBT formation/turnover | 92-97 | Retainable topology; equation-level verification required | D4 |
| Cow inhalation/skin uptake | 98 | Missing from V2 animal core | D4 |
| Grass→cow / grass balance | 99-105-2 | Retain continuous coupling; parameter split required | D4 |
| Public inhalation + skin | 106 | Retain pathway topology; parameter policy correction required | D5 |
| Public ingestion | 107 | Retain pathway topology; manual/modern coefficient modes must be separated | D5 |
| RC1 terminal endpoint | project boundary | Keep unchanged as stable default/fallback | retained |

## 6. Post-RC1 boundary

The current `V4FoodIntakeDoseEndpointAdapter` deliberately:

- reads a completed V4 replay endpoint;
- performs a one-event terminal harvest;
- converts the food inventory into an annual intake state;
- computes food-ingestion dose;
- does not mutate the source endpoint;
- is not an environmental mass sink;
- performs no implicit area or mass-basis conversion.

This boundary remains valid for project use even when a continuous UFOTRI compatibility path is later added.

The intended architecture is therefore parallel, not replacement:

```text
V4 environmental state
  ├─ RC1 default/fallback: terminal harvest → annual intake → food dose
  └─ opt-in UFOTRI fidelity: continuous plant/grass → cow/milk/beef → pathway dose
```

## 7. D1 source decision

`NO_EXISTING_SOURCE_CHANGE`

D1 adds only a machine reconciliation gate, independent pytest assertions, ADR-066, governance YAML and this report.

No existing V2, V3 or V4 source is modified and no parameter is activated.

## 8. Authorized downstream partition

After D1 exact-head merge/no-drift and a separate roadmap sync, the food-chain work is partitioned as:

1. `UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1` — close manual pasture root allocation without contaminating nutrient-crop 20/40/40 behavior;
2. `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1` — close Eq.65-81 plant/grass roles against the already reconstructed TFWT/OBT/soil interfaces;
3. `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1` — reconstruct Eq.82-105-2, including the missing Eq.98 animal route and parameter provenance separation;
4. `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1` — reconcile Eq.106-107 manual dose semantics with modern application coefficients without rewriting the original claim.

## 9. Candidate claim

If exact-head CI and merge/no-drift pass, D1 may claim:

`UFOTRI_V2_CONTINUOUS_FOODCHAIN_POST_RC1_RECONCILIATION=COMPLETE`

This means only that the retained V2 chain has been provenance-locked and semantically reconciled sufficiently to authorize staged fidelity work.

It does not mean vegetable/grass, cow/milk/beef, or exposure fidelity is complete.

## 10. Hard boundaries

The following remain false:

- calibration;
- empirical validation;
- physical-accuracy claim;
- production parameter activation;
- modern dose coefficients as original UFOTRI values;
- separate OBT ingestion coefficient as original UFOTRI behavior;
- beef product inventory/continuous herd turnover as recovered original algorithm;
- animal support-area normalization as recovered original algorithm;
- real CTEAS-Atmos binding;
- original executable equivalence.
