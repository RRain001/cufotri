# ADR-083 — UFOTRI Native Atmosphere to Dose Qualification R1

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`

## Context

H1-H4 now provide an internally reconstructed UFOTRI-native atmospheric route through typed HT/HTO transport, hourly trajectory semantics, environmental forcing adapters and the recoverable KfK 4332/KfK 5194 source-depletion/washout relations.

The repository already contains qualified environmental solvers and manual-fidelity compatibility modules for HT soil conversion, three-layer soil HTO, root uptake, leaf exchange, TFWT/OBT, vegetable/grass, cow/milk/beef, re-emission area sources and Eq. (106)-(107) public exposure.

H5 therefore qualifies composition across those boundaries. It does not create a replacement whole-model production pipeline and does not reopen completed component equations.

## Decision 1 — native atmosphere enters the existing environmental contract

H5 adds `compose_native_atmosphere_replay_input` in:

`src/cteas_ufotri/v4_integration/native_atmosphere_to_dose_v4.py`.

For one interval:

- native HTO air concentration remains atmospheric HTO;
- primary HTO dry/local-explicit wet deposition remains the primary HTO soil-surface input;
- native HT deposition is mapped through the existing H3 E1 contract and E2 1:1 deposited-HT→soil-HTO activity conversion;
- primary HTO and HT-derived HTO surface fluxes are summed only at the aggregate soil-HTO forcing boundary;
- their pre-aggregation provenance remains separately visible in the H5 sidecar ledger;
- atmospheric HT→HTO generation remains exactly zero.

This is an explicit composition seam, not a new soil, plant or dose solver.

## Decision 2 — wet plume loss is not relabelled as a local deposition flux

KfK 5194 washout is exercised in H5 through the H4 reconciled atmosphere.

A nonzero atmospheric HTO wet source loss is still a plume/source `Bq s-1` ledger term. H3/H5 fail closed if the caller attempts to continue to a local environmental surface forcing without separately supplying a local `Bq m-2 s-1` wet deposition flux.

The H5 controlled wet test supplies an explicit qualification-only local wet flux to prove the mapping contract. It does not derive that flux from the plume source loss and therefore does not claim spatial closure that the recovered source does not support.

## Decision 3 — replay orchestration is the conservative state-composition backbone, not a false claim of Eq. (27)-(30) numerical identity

The existing V4 replay orchestrator owns the already-reviewed cross-module operator split and activity ledger for soil/root/leaf/TFWT/OBT.

H5 supplies it with an A-stage Eq. (7)-(25) resistance state where the frozen positive-component RC1 resistance contract can represent that state exactly.

However, the replay orchestrator's signed leaf flux is not the same numerical operator as the A-stage exact interval integration of UFOTRI Eq. (27)-(30). H5 therefore independently evaluates `ufotri_eq27_30_analytic_interval_transfer` against the same native HTO atmospheric concentration and resistance state, but explicitly does **not** require or claim numerical equality between those two discretisations.

The original UFOTRI Monin-Obukhov estimator remains unrecovered. The H5 controlled resistance state uses the already-declared `GOLDER_1972_APPROXIMATION` literature estimator and never labels it original UFOTRI logic.

## Decision 4 — re-emission handoff is conservative and delayed, without double counting

H5 debits a controlled explicit soil re-emission flux through the existing `ThreeLayerSoilForcing.surface_reemission_hto_loss_bq_m2_s` boundary.

The same already-accounted loss is handed to `HourlyReemissionHandoffBuffer`. H5 requires:

`environmental loss activity = routed secondary-source activity + unrouted activity`.

For the controlled fully routed case, the unrouted term is zero.

The source becomes active only in the following source hour. Its atmospheric concentration is then added as an explicit secondary-air contribution. H5 does not add a second environmental inventory source or implicit deposition term when performing that atmospheric routing.

Because environmental soil HTO is already aggregated after primary HTO and HT-derived HTO inputs mix, the H5 re-emission event is labelled `UNRESOLVED_HTO_ORIGIN`; it is not falsely promoted to `HT_DERIVED_HTO` without an origin proof.

## Decision 5 — food and public-dose qualification uses the recovered manual path

H5 exercises:

- the D3 reversible vegetable HTO↔OBT compatibility solver;
- the D4 grass/cow/milk/beef compartment solver;
- explicit slaughter-to-beef activity transfer;
- D5 Eq. (106) inhalation plus 50% skin absorption;
- D5 Eq. (107) green-vegetable, beef and milk ingestion.

D4 intentionally has no default edible beef mass and D5 requires Bq/kg. H5 therefore uses explicit synthetic `kg m-2` mass bases only inside the machine qualification fixture to project area-normalized inventories to specific activity. Those values are not source parameters, not defaults, not production bindings and not empirical data.

## Decision 6 — partition, restart and pre-existing fidelity gates remain part of acceptance

H5 directly qualifies:

- deterministic repeat;
- state serialization/restart equivalence;
- interval-constant native surface-flux integration under `1 h` versus `2 x 0.5 h` partition;
- hourly F1 re-emission routing under `1 h` versus `2 x 0.5 h` partition;
- manual exposure integral partition equivalence;
- cross-module soil/plant/root activity conservation.

It also re-executes the already-merged manual hydrology, F1 area-source, Canada benchmark-contract and ITER benchmark-contract machine gates. This preserves their original claim boundaries rather than restating their results as new H5 validation.

## Benchmark boundary

Canada 1987 remains a source-limited benchmark-contract reconstruction; H5 does not claim full numerical or empirical replay.

ITER remains a qualified tabulated/reference contract; H5 does not claim complete atmospheric numerical replay or empirical validation.

## Acceptance

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION`

After exact-head CI, expected-head merge and merge-tree/no-drift certification, a separate roadmap-only sync may mark H5 complete and authorize:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`.

## Non-claims

H5 does not establish original UFOTRI leaf discretisation identity, the original Monin-Obukhov estimator, plume-wet-loss/local-flux spatial closure, origin-resolved mixed soil HTO, complete building-wake or plume-rise equivalence, Canada empirical reproduction, ITER full atmospheric replay, CTEAS-Atmos binding, production parameters, calibration, empirical validation, physical accuracy, or original UFOTRI executable numerical equivalence.
