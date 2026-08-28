# ADR-074 — UFOTRI re-emission/area-source reconciliation R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1`

## Context

E3 closed ownership and provenance for secondary HTO re-emission without activating an atmospheric feedback solver. It established that soil/plant re-emission is first an environmental inventory loss and that any later atmospheric source consumes that same accounted activity rather than creating a second activity term. It also froze the rule that aggregate HTO cannot be relabeled `HT_DERIVED_HTO` after mixing without explicit origin proof.

F1 must now recover the available KfK 4605 secondary area-source semantics while preserving the frozen RC1/V2 defaults and keeping real CTEAS-Atmos binding deferred.

## Manual evidence

KfK 4605 Section 2.2.1 provides a recoverable reduced-time area-source algorithm:

1. concentrations from source hour N are transferred to the secondary model and modified in hour N+1;
2. soil and plant secondary releases are area sources;
3. rectangular area sources are preferred;
4. the selected practical approximation is a single point in the centre of the area source with an initial lateral plume width;
5. Eq. (5) uses `sigma_yg = sqrt(sigma_y^2 + sigma_y0^2)` with `sigma_y0 = width / 4.3`;
6. Eq. (6) is applied separately to soil and plant and the resulting plumes are linearly superposed;
7. Eq. (4) states a common effective source height for soil and plant sources.

Phase A separately recovered vegetation geometry `z0=0.1H`, `d=0.6H`, and `FLQH=0.8H` with a minimum area-source emission height of 1 m. The existing `leaf_ufotri_v4` helper exposes that height specifically for later re-emission coupling.

## Historical implementation audit

The retained V1/V2 path demonstrates useful topology but not manual-exact area-source numerics:

- `case.py` delays aggregate `diag.total_reemission_bq_m2_s` by a configured interval;
- `area_source` mode calls `rectangular_area_source_concentration`, which performs midpoint quadrature over a uniform rectangle;
- `point_equivalent` mode uses a ground-level point source;
- the legacy path then computes `air = primary + secondary`;
- default feedback rectangle, area and 3600 s delay are historical/project configuration and remain untouched.

The current rectangular quadrature is a reasonable engineering route, but it is not the manual-selected centre-point + Eq. (5) initial-widening approximation. It therefore remains historical compatibility behavior rather than being relabeled original UFOTRI.

## Decision

F1 requires a source addition but no modification of existing default sources:

`NEW_OPT_IN_SOURCE_MODULE_REQUIRED = TRUE`

`EXISTING_DEFAULT_SOURCE_CHANGE = FALSE`

The new module is `src/cteas_ufotri/coupling/reemission_area_source_v4.py`.

### 1. Environmental-loss handoff

`AccountedReemissionLoss` represents an activity flux already removed from an environmental inventory. `HourlySecondarySource` carries the same activity across the atmospheric boundary. Its ledger enforces:

`environmental_loss_activity = routed_activity + unrouted_activity`.

For the fully routed F1 compatibility path, `unrouted_activity = 0`.

No environmental inventory is incremented by this handoff.

### 2. Provenance

The handoff keeps explicit origin classes. A request to label activity `HT_DERIVED_HTO` requires an `origin_proof_id`. If primary and HT-derived activity are mixed within a source hour, the routed source becomes `MIXED_HTO_ORIGIN`; no proportional split is inferred.

This directly preserves the E3 fail-closed rule.

### 3. Source-hour timing

`HourlyReemissionHandoffBuffer` implements the recoverable `hour N -> hour N+1` cadence. It accumulates Bq over one complete 3600 s source hour and exposes that activity as a uniform source flux in the following source hour.

The numerical time step must exactly divide 3600 s. This avoids hidden rounding and makes integrated routed activity invariant for compatible `dt` values such as 600 s and 300 s.

This is a manual compatibility mode, not evidence that every original UFOTRI event-boundary detail has been recovered.

### 4. Area-source representation

`ManualAreaSourceGeometry` requires explicit rectangle length and width and one common effective source height. The helper `from_canopy_height` reuses the Phase-A recovered `max(0.8H, 1 m)` area-source height.

`eq5_effective_sigma_y_m` implements the recovered Eq. (5) widening using `width / 4.3`.

`eq6_equivalent_area_source_concentration_bq_m3` uses the total rectangle source strength `surface_flux * area`, the centre-relative receptor coordinates, Eq. (5) lateral widening and the explicit common source height.

Fallout and washout multipliers are explicit arguments. F1 does not silently import a depletion parameterization into the fidelity path.

### 5. Soil/plant separation and superposition

Soil and plant secondary source handoffs remain separate. Eq. (6) is evaluated separately and only the resulting air concentrations are added. A helper may then add the already-computed primary air concentration to the summed secondary concentration.

### 6. Preserved boundaries

F1 does not:

- modify `case.py`, `config.py`, `configs/default_parameters.yaml`, or the legacy Gaussian functions;
- activate the new adapter as a default;
- implement or promote the provisional Eq. (44) engineering re-emission rate;
- reconstruct rain-start/DIFF behavior that remains source-limited;
- bind to real CTEAS-Atmos;
- start Canada 1987 or ITER benchmark work;
- activate production parameters.

## Qualification requirements

The F1 gate must prove:

- manual `N -> N+1` timing and rectangular centre-source semantics are present;
- Eq. (5) uses the exact recoverable `width/4.3` rule;
- Eq. (6) controlled calculations are finite/positive and use explicit source height/depletion factors;
- soil and plant sources remain distinct until concentration superposition;
- 600 s and 300 s time steps produce identical routed hourly activity and mean source flux for the same loss history;
- the first source hour has zero lagged secondary forcing;
- routed activity closes exactly against the already-accounted environmental loss;
- mixed origin remains mixed and HT-derived attribution without proof fails closed;
- legacy feedback behavior/default configuration remains present and is not promoted to original UFOTRI;
- no Eq. (44), real Atmos, benchmark, empirical-validation, physical-accuracy, production-readiness or original-executable-equivalence claim is made.

## Consequence

If exact-head CI, locked-head merge and post-merge no-drift pass, the scoped F1 claim may become:

`UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION=COMPLETE`

This means the recoverable internal secondary-source handoff and area-source compatibility boundary is reconstructed. It does not mean the original MUSEMET/ISOLA executable, complete Eq. (44), real Atmos coupling, benchmark validation or production fidelity has been recovered.
