# UFOTRI HT-derived HTO Re-emission and Secondary-feedback Reconciliation R1

Stage: `UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1`

Candidate status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

## 1. Result

E3 is a reconciliation stage, not a new re-emission physics implementation.

The audit finds that the repository already contains the necessary semantic roles for conservative soil/plant HTO loss, while the historical V1/V2 path also demonstrates a delayed secondary-atmosphere feedback topology. However, the advanced Eq. (44) soil-reemission relation remains incompletely recovered from the manual, and the historical secondary-feedback implementation does not preserve primary-HTO versus HT-derived-HTO origin after environmental mixing.

The selected E3 disposition is therefore:

`NO_EXISTING_SOURCE_CHANGE`

with explicit ownership/provenance rules and a fail-closed handoff to Phase F.

## 2. Manual evidence

The recoverable manual roles are:

- plant HTO exchange/re-emission through Eq. (27)-(31);
- soil/atmosphere re-emission in Section 2.2.3;
- direct soil re-emission only from the top soil layer;
- a secondary atmospheric area-source role;
- Eq. (44-1)/(44-2) REEM/DIFF/ZT terminology and reference behaviors.

The available evidence does not recover enough executable detail to claim a complete advanced Eq. (44) implementation.

## 3. Historical V1/V2 topology

`src/cteas_ufotri/reemission/fluxes.py` contains:

- a basic evaporation/transpiration mass-flux route;
- a configurable Eq. (44-1)/(44-2) **engineering reconstruction**.

`src/cteas_ufotri/coupling/integrator.py` removes soil and plant re-emission from the environmental inventories and includes those losses in the mass-boundary ledger.

`src/cteas_ufotri/case.py` then:

1. stores `diag.total_reemission_bq_m2_s` in a delay queue;
2. reads the lagged value on a later step;
3. maps it through either a rectangular area source or a point-equivalent source;
4. adds the resulting `secondary` air concentration to the `primary` concentration.

This is strong evidence for the historical software topology, but not evidence that the current geometry, delay, or provisional Eq. (44) rate is exact original UFOTRI executable behavior.

## 4. Eq. (44) remains source-limited

The frozen V2 advanced-reemission closure plan records:

- `LIMITATION = M_REEM_MANUAL_FIDELITY`;
- rain-start 3% validation: `PARTIAL`;
- concentration-dependent DIFF validation: `PARTIAL`.

The same record explicitly states that:

- the released engineering function has no rain/rain-start input;
- the later DIFF mapping is not fully demonstrated;
- the historical candidate is a non-negative outward loss and does not represent concentration-gradient reversal.

E3 therefore does not promote `ufotri_empirical_soil_reemission_bq_m2_s` to a manual-exact or production path.

## 5. Post-RC1 roles that can be reused

### 5.1 Plant

Phase A's `leaf_ufotri_v4` already provides signed Eq. (27)-(30) exchange and the Eq. (31) zero-air re-emission diagnostic. A negative signed leaf exchange is the required plant-to-air activity-loss role.

The same compatibility module also exposes the recoverable vegetation area-source emission-height geometry for later use; it does not itself perform atmospheric source integration.

### 5.2 Soil

The three-layer V4 soil core already accepts:

`ThreeLayerSoilForcing.surface_reemission_hto_loss_bq_m2_s`

and removes this activity only from L1. The loss is included explicitly in the global external HTO loss ledger.

Thus E3 does not need a second soil storage solver. What remains missing is a source-authorized function that generates the correct manual Eq. (44) loss magnitude.

## 6. Primary HTO versus HT-derived HTO provenance

E2 retains, in its projection record:

- primary HTO surface flux;
- HT-derived HTO surface flux;
- their combined soil-input flux;
- upstream HT/T2 source kind/species/provenance/support.

But the current `ThreeLayerSoilState` stores one HTO inventory per layer. Once the two input fluxes are summed and advanced, the soil state does not retain an origin partition. Downstream TFWT is likewise an aggregate activity state unless a separate origin-aware accounting layer is introduced.

Therefore E3 freezes the following rule:

> Aggregate later HTO re-emission is not automatically HT-derived HTO.

An `HT_DERIVED_HTO` label requires explicit origin proof. Otherwise the origin remains mixed/unresolved. E3 forbids inventing a proportional split merely to make the lineage close.

This prevents a provenance error that would otherwise survive all ordinary total-activity conservation tests.

## 7. Double-counting rule

Environmental re-emission is first a loss from soil/plant inventory. A later atmospheric feedback adapter may route that same activity into a secondary atmospheric source.

It must not count the routed activity again as a new environmental production term.

The Phase-F adapter therefore needs an explicit identity between:

- accounted environmental re-emission loss;
- activity routed into the secondary atmospheric source;
- any explicitly unrouted remainder.

For a fully routed event:

`reemission loss = secondary-source handed-off activity`.

## 8. Phase-F handoff

Phase F retains the numerical compatibility work:

- choose/reconcile area-source or equivalent representation;
- source footprint and geometry;
- vegetation emission height where applicable;
- feedback delay and time discretization;
- conversion from re-emission flux/activity to atmospheric source forcing;
- origin-aware sidecar/accounting if an HT-derived label must survive soil/plant mixing;
- no-double-counting integration with atmospheric feedback.

The E3 roadmap-sync must freeze the exact next stage identifier; this report intentionally does not invent it.

## 9. Changed-file boundary

The intended E3 PR changes no existing source file. It adds only:

- this report;
- ADR-073;
- E3 governance YAML;
- one machine reconciliation script;
- one independent pytest file.

No existing V1/V2/RC1/V4 source path, roadmap, or workflow is modified in the E3 implementation PR.

## 10. Claim boundary

If exact-head CI and merge/no-drift succeed, the permitted claim is only:

`UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION=COMPLETE`

This does not establish:

- complete manual Eq. (44) soil re-emission numerics;
- an origin-resolved environmental tracer;
- Phase-F area-source numerical compatibility;
- real CTEAS-Atmos binding;
- empirical validation;
- physical accuracy or production readiness;
- original UFOTRI executable equivalence.
