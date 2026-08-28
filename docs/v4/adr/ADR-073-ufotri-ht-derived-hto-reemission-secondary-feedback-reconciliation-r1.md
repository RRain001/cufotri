# ADR-073 — UFOTRI HT-derived HTO re-emission and secondary-feedback reconciliation R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1`

## Context

E1 established a chemically explicit HT/T2 forcing and deposition boundary. E2 then mapped the activity accepted by that boundary directly into soil HTO on the recoverable KfK 4605 Eq. (1)/(2) basis. E2 deliberately stopped before secondary HTO re-emission.

E3 must decide what can be called a recovered UFOTRI re-emission/secondary-feedback mechanism without either:

1. promoting the historical V1/V2 engineering reconstruction beyond its evidence;
2. double counting a loss as both an environmental boundary and a new independent source;
3. relabeling mixed primary/HT-derived HTO as HT-derived after the sources have been aggregated;
4. implementing the Phase-F atmosphere/area-source numerical adapter prematurely.

## Evidence audit

### Manual roles

KfK 4605 establishes all of the following recoverable roles:

- re-emission is part of the soil/atmosphere exchange system;
- only HTO in the top soil layer directly participates in soil re-emission;
- soil re-emission may be linked to soil-water evaporation or represented by an exchange-rate approximation;
- plant re-emission is represented by the Eq. (27)-(31) exchange/equilibration system;
- the manual exposes a secondary area-source concept for atmospheric transport.

The manual does **not**, in the available evidence, fully recover every executable detail of the advanced Eq. (44-1)/(44-2) REEM/DIFF/ZT relation.

### Historical V1/V2 implementation

The retained historical path contains two useful but distinct layers:

1. environmental inventory losses:
   - soil re-emission is removed from soil HTO;
   - plant transpiration/leaf release is removed from plant HTO;
   - both are counted in the environmental mass-boundary ledger;
2. atmospheric feedback topology:
   - `diag.total_reemission_bq_m2_s` is delayed;
   - the lagged total is mapped through either an area-source or point-equivalent Gaussian route;
   - secondary concentration is added to primary concentration.

This proves a historical topology. It does not prove that its current configurable Eq. (44) engineering reconstruction or its particular source geometry/numerics is exact original UFOTRI behavior.

### Existing post-RC1 roles

The already qualified post-RC1 path contains the reusable semantic boundaries needed for later fidelity work:

- `leaf_ufotri_v4` implements signed Eq. (27)-(30) leaf exchange and exposes the Eq. (31) zero-air re-emission diagnostic; negative signed exchange is a plant-to-air loss role;
- `ThreeLayerSoilForcing.surface_reemission_hto_loss_bq_m2_s` is an explicit HTO loss from L1 and enters the global soil external-loss ledger;
- E2 preserves primary HTO and HT-derived HTO as separate input-flux diagnostics before writing their sum into `ThreeLayerSoilForcing.surface_deposition_flux_bq_m2_s`.

No second plant or soil storage solver is required merely to represent these roles.

## Source ambiguity that remains open

The historical advanced soil-reemission mode is not promoted.

The frozen V2 validation record explicitly leaves both of these at `PARTIAL`:

- rain-start 3% behavior;
- concentration-dependent DIFF behavior.

It further records that the released engineering function has no rain/rain-start argument, that full manual mapping was not demonstrated, and that concentration-gradient reversal is not represented.

Therefore E3 does not invent missing state transitions, modifiers, equilibrium conventions, or a replacement rate law.

## Decision

E3 closes as a reconciliation-only stage with:

`NO_EXISTING_SOURCE_CHANGE`

and the following ownership rules.

### 1. Plant re-emission ownership

The recoverable plant re-emission role remains owned by the Phase-A UFOTRI Eq. (27)-(31) leaf compatibility path. E3 does not add a second transpiration or leaf-release solver.

### 2. Soil re-emission ownership

The post-RC1 three-layer soil core already owns conservative storage and the explicit L1 re-emission-loss boundary. E3 does not add a second soil inventory solver.

The numerical generation of a manual-fidelity Eq. (44) soil re-emission rate remains unresolved by source evidence and must fail closed until that relation is either recovered or explicitly classified as an engineering extension.

### 3. Secondary-feedback ownership

E3 recognizes the historical delayed-feedback topology as useful compatibility evidence, but does not activate its area-source or point-equivalent Gaussian numerical path.

The later atmospheric source mapping, source geometry, emission height, delay semantics and source integration are Phase-F responsibilities.

### 4. Primary versus HT-derived HTO provenance

E2 can distinguish the two incoming HTO fluxes:

`primary HTO input + HT-derived HTO input = combined HTO input`.

Once the sum is advanced into the current aggregate soil HTO inventory, the state no longer contains two origin-resolved HTO inventories. The same is true for downstream aggregate TFWT after mixing.

Therefore:

- an aggregate soil/plant HTO re-emission flux must **not** be labeled `HT_DERIVED_HTO` merely because an HT-derived input occurred earlier;
- `HT_DERIVED_HTO` may be used only when an explicit origin-aware accounting record proves that the released activity belongs to that lineage;
- otherwise the feedback must remain `MIXED_HTO_ORIGIN` (or an equivalently explicit unresolved/mixed classification);
- no proportional source split may be invented silently.

This is the key E3 fail-closed provenance rule.

### 5. Activity accounting and double counting

A re-emission amount is first an environmental inventory loss. A future atmospheric secondary-source adapter may consume the **same accounted loss** as source input, but must not add a second environmental activity creation term.

The ledger identity required for later integration is conceptually:

`environmental inventory loss = secondary-source activity handed to atmosphere + explicitly unresolved/unrouted remainder`.

For a fully routed compatibility event the remainder is zero. This is an interface/accounting identity, not a new physical production term.

### 6. Phase boundary

E3 authorizes no atmospheric Gaussian/area-source code change. Phase F retains:

- area-source versus other source representation selection;
- source area/geometry and emission height;
- delay and time-discretization compatibility;
- numerical concentration feedback;
- provenance-aware source-adapter implementation;
- any required origin-aware sidecar needed to make an `HT_DERIVED_HTO` attribution auditable.

Real CTEAS-Atmos output is not required for E3 and remains separately deferred.

## Qualification

The E3 machine/pytest gate must prove that:

- the manual topsoil and plant-reemission roles are visible;
- Eq. (44) remains provisional rather than silently upgraded;
- historical delayed area-source and point-equivalent feedback topology exists;
- historical feedback consumes aggregate total re-emission;
- the V4 soil core exposes a conservative L1 re-emission sink;
- the Phase-A leaf path exposes signed Eq. (27)-(31) release behavior;
- E2 preserves input provenance before aggregation but writes a combined soil flux;
- aggregate later re-emission cannot be labeled HT-derived without explicit origin proof;
- Phase F remains the owner of atmospheric area-source numerical compatibility;
- no empirical-validation, physical-accuracy, production-readiness or original-executable-equivalence claim is made.

## Consequences

If exact-head CI, locked-head merge and post-merge no-drift pass, the scoped E3 claim may become:

`UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION=COMPLETE`

This means the ownership, source-evidence, provenance and no-double-counting rules are reconciled. It does **not** mean that a complete Eq. (44) soil re-emission rate, origin-resolved environmental tracer, Phase-F area-source adapter, real atmospheric binding, empirical validation or exact original executable behavior has been recovered.
