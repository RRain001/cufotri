# V3 P7.8A Physics Redesign Prioritization Report

Date: 2026-08-24
Branch: `codex/v3-p7-8a-physics-redesign-prioritization`
Baseline: `codex/v3-p7-7b-synthetic-benchmark` at `9490c21`

## Disposition

```ini
P7_8A_STATUS = PASS_PHYSICS_REDESIGN_PRIORITIZATION
REDESIGN_ITEMS_REVIEWED = TRUE
PRIORITY_MATRIX_COMPLETE = TRUE
ROADMAP_DEFINED = TRUE
IMPLEMENTATION_STARTED = FALSE
SOLVER_CHANGES = FALSE
COUPLING_CHANGES = FALSE
ACTIVE_PARAMETERS = 0
CALIBRATION_STARTED = FALSE
UFOTRI_ACTIVE_DATABASE = FALSE
V3_PHYSICS_READY = FALSE
```

This stage converts the P7.6C-3 feasibility and P7.6D adoption decisions
into a ranked physics roadmap. It does not select parameter values, change an
equation, reopen P7.5/P7.5B, or authorize P7.8B implementation.

## Evidence boundary

The review used:

- P7.6C-3 physics-gap and validation-feasibility reports;
- the complete P7.6D decision registry and four-work-package priority matrix;
- the P7.7A validation framework and its fail-closed scenario gate;
- the P7.7B synthetic benchmark, conservation, stability, and independent
  review reports;
- the current V3 interfaces for leaf exchange, TFWT, OBT, soil, root, food,
  intake, and dose.

P7.7B demonstrates deterministic software behavior, ledger bookkeeping,
restart equivalence, and refinement behavior for synthetic inputs. It is not
environmental evidence, empirical validation, calibration, regulatory dose
validation, or UFOTRI equivalence. No P7.6D redesign is therefore promoted by
the benchmark result.

## Evaluation method

Each item was assessed against five decision questions:

| Criterion | Meaning in P7.8A |
|---|---|
| Scientific importance | Effect on environmental tritium behavior and pathway interpretation |
| Dose-pathway importance | Potential influence on plant, food, intake, or dose output |
| Model inadequacy | Whether the frozen V3 state/equation cannot represent the target mechanism |
| Validation availability | Whether the required matched observations and metadata are realistically identifiable |
| Engineering/coupling cost | State ownership, interface, pipeline, conservation, and numerical-boundary consequences |

Priority is an ordinal governance decision, not a fitted score. `CRITICAL`
means that the gap is a central blocker with high scientific and pathway
consequence; it does not mean that implementation is authorized. `DEFERRED`
means that the question is scientifically relevant but should wait for a
better data or boundary contract. `REJECTED` means that the proposed action
must not be implemented in any future stage.

## Subsystem decisions

| Subsystem | Frozen baseline | P7.8A decision | Reason |
|---|---|---|---|
| Leaf exchange | `r_a + r_b + r_c`, with derived `g_ex` | `KEEP_CURRENT_V3`; stage relation is a redesign | Components are sufficiently defined for scoped validation; stage-dependent physics is not defined |
| TFWT | Storage with explicit leaf/root, water-loss, and transformation fluxes | `KEEP_CURRENT_V3`; dynamic water turnover is deferred | Current basis and flux boundary can be validated with limitations |
| OBT | Reduced first-order `kf/kr` storage with day/night selector | `REDESIGN_REQUIRED`; reduced model remains a baseline | Missing biological state, day/night normalization, activity, mass basis, and temperature relation |
| Soil | One-layer storage with signed transport input and decay | `KEEP_CURRENT_V3`; hydrology is deferred | Current boundary is explicit; hydraulic/multi-layer redesign lacks the required data and coupling contract |
| Root uptake | `J_root = k_root * C_soil` effective-velocity boundary | `REDESIGN_REQUIRED` | Rate/layer/transpiration semantics do not map to the current one-layer velocity |
| Environmental food transfer | Event transfer of separate OBT and TFWT inventories | `REDESIGN_REQUIRED` | Continuous and event product representations are not interchangeable |
| Consumption | Annual scenario input and product-mass conversion | `KEEP_EXTERNAL_LAYER` | Consumption is not environmental physics |
| Dose | External `D = I_food * e` assessment layer | `KEEP_EXTERNAL_LAYER` | Dose requirements do not justify environmental-physics redesign |

## Ranked redesign items

The nine `REDESIGN_REQUIRED` records are the complete P7.6D blocking set. The
rank is refined below without changing the source decision.

| Rank | Registry item | Priority | Scientific/dose consequence | Coupling | Recommended stage |
|---:|---|---|---|---|---|
| 1 | `R1_OBT_DAYLIGHT_FORMATION_STATE` | `CRITICAL` | Direct control of dose-relevant OBT formation | `NO_IMPACT` at design stage | V3.2 |
| 2 | `R2_OBT_NIGHTTIME_FORMATION_STATE` | `CRITICAL` | Integrated day/night OBT burden cannot be interpreted without it | `NO_IMPACT` at design stage | V3.2 |
| 3 | `R3_OBT_PHOTOSYNTHETIC_FORCING_STATE` | `CRITICAL` | Potentially controls organic binding and propagates to food OBT | `INTERFACE_CHANGE_ONLY` | V3.2 |
| 4 | `R6_ROOT_LAYERED_UPTAKE_STATE` | `CRITICAL` | Soil-to-plant bridge; errors propagate to TFWT, OBT, food, and dose | `NUMERICAL_COUPLING_REDESIGN_REQUIRED` | V4 |
| 5 | `R4_OBT_PLANT_MASS_BASIS` | `HIGH` | Controls concentration comparability and plant-product interpretation | `INTERFACE_CHANGE_ONLY` | V3.1 design contract |
| 6 | `R5_OBT_TEMPERATURE_RESPONSE` | `HIGH` | Can be confounded with formation/turnover rates | `INTERFACE_CHANGE_ONLY` | V3.2 |
| 7 | `R7_FOOD_OBT_EVENT_CONTINUOUS_BOUNDARY` | `HIGH` | Direct plant-to-food OBT and dose boundary | `NUMERICAL_COUPLING_REDESIGN_REQUIRED` | V4 |
| 8 | `R8_FOOD_TFWT_EVENT_CONTINUOUS_BOUNDARY` | `HIGH` | Direct plant-water/product-water and intake boundary | `NUMERICAL_COUPLING_REDESIGN_REQUIRED` | V4 |
| 9 | `R9_LEAF_PHENOLOGY_RESISTANCE` | `MEDIUM` | Affects applicability and possibly exchange, but current chain remains usable | `INTERFACE_CHANGE_ONLY` | V3.1 |

The detailed record, including required validation data, prerequisites,
forbidden shortcuts, and exit evidence, is
`docs/v3/physics/p7_8a_redesign_priority_registry.yaml`.

## What can wait

Two extensions are deliberately not promoted to the nine blocking redesigns:

1. Dynamic TFWT water turnover, growth, and dilution waits for a matched plant
   water-balance dataset and an explicit decision about water-state ownership.
2. Soil hydraulic transport, evaporation, and multi-layer water coupling wait
   for layer-resolved hydrology and a soil-root numerical-boundary review.

These are recorded as `DEFERRED`, not as hidden implementation tasks. The
current signed soil transport and explicit TFWT flux interfaces remain the
validation-feasible baseline under their declared limitations.

## What must never be implemented

The registry permanently rejects four shortcuts or scope expansions:

- importing an unreviewed, reconstructed, synthetic, or reference UFOTRI
  value as a runtime parameter;
- converting a root rate into a V3 velocity with an assumed layer depth;
- converting a continuous food-chain rate into a harvest fraction by time
  scaling;
- redesigning environmental physics to satisfy an external dose-coefficient
  or reporting requirement.

These are `REJECTED`, not low-priority future work. A redesign record cannot
move directly from `REDESIGN_REQUIRED` or `DEFERRED` to `ACTIVE` or
`VALIDATED`; the intermediate design, validation, review, and explicit
implementation artifacts listed in the registry gate are mandatory.

## Scope conclusion

P7.8A answers the planning questions as follows:

1. Scientifically necessary redesigns are the nine P7.6D blockers, led by OBT
   formation scope, layered root uptake, and the plant-product boundary.
2. Highest benefit is expected from the OBT day/night/activity state and the
   soil-to-plant root representation because they control central pathway
   behavior; this is a prioritization judgment, not a performance claim.
3. Dynamic TFWT/soil hydrology extensions and stage refinement can wait behind
   baseline contracts and data readiness.
4. Root, food, and deferred soil-hydrology work can affect numerical coupling;
   OBT and leaf work currently affect interfaces only or remain internal.
5. The four rejected shortcuts are not implementation candidates.

No statement in this report changes `CURRENT_V3_MODEL = FROZEN` or
`V3_PHYSICS_READY = FALSE`.
