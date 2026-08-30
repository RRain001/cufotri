# UFOTRI Native Atmosphere to Dose Qualification R1

Stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`

Status: `CANDIDATE_PENDING_EXACT_HEAD_CI`

Base: `main@7a70c49dde2edcb54adc0b826c4a6d99ba0e5ada`

## 1. Objective

H5 qualifies the corrected standalone north-star route after H1-H4:

`native source`
→ `UFOTRI-native HT/HTO atmosphere`
→ `species-specific deposition/washout`
→ `HT deposition → E2 soil HTO`
→ `three-layer soil HTO + re-emission`
→ `root + leaf transfer`
→ `TFWT + OBT`
→ `vegetable / grass / cow / milk / beef`
→ `inhalation + skin + ingestion dose`
→ `delayed secondary area-source feedback`.

The stage is qualification/composition work. It does not create a new production pipeline or change previously frozen solver equations.

## 2. Native atmospheric boundary

H5 uses H4 `transport_straight_segment_reconciled` for both chemical species.

The controlled dry route uses explicit manual/benchmark-compatible dry deposition velocities only as qualification inputs. They are not activated production parameters.

The HTO and HT source-depletion ledgers must close independently and atmospheric HT→HTO generation must remain zero.

A separate wet HTO probe enables the recovered KfK 5194 power-law washout. Because that creates a nonzero plume/source wet-loss term, H3 must reject environmental projection unless a distinct local wet surface flux is supplied. H5 proves both the fail-closed branch and the explicit-local-flux branch. It never computes the latter by dividing or geometrically redistributing the plume `Bq s-1` loss.

## 3. H3/E2 composition into the environmental chain

The new H5 composition seam:

`compose_native_atmosphere_replay_input`

performs only the following mappings:

- HTO air → existing `AtmosphericHTOForcing`;
- HTO surface deposition → primary soil HTO flux;
- HT air/deposition → existing E1 typed HT forcing;
- deposited HT → E2 generated soil HTO flux;
- aggregate soil HTO flux = primary HTO + HT-derived HTO;
- primary and HT-derived fluxes retained separately in the H5 sidecar ledger.

The aggregate soil state still carries one HTO inventory. H5 does not infer a hidden origin split after environmental mixing.

## 4. Soil, root, leaf, TFWT and OBT

The main conservative state-composition backbone is the already-qualified `V4ReplayInputSystemOrchestrator`.

The H5 controlled case supplies:

- explicit L1→L2 and L2→L3 water/HTO transport terms;
- an explicit top-layer re-emission loss;
- explicit root-water uptake with 20/40/40 layer fractions;
- the recovered A-stage Eq. (7)-(25) resistance chain;
- daylight biological forcing;
- native HTO concentration and primary+HT-derived surface deposition.

The replay orchestrator must close soil/root identities, plant activity balance and coupled soil+plant balance.

The A-stage exact Eq. (27)-(30) interval leaf transfer is evaluated separately against the same native HTO air concentration and resistance state. This is a deliberate cross-check rather than a false equality assertion: the replay signed-flux operator and the exact Eq. (27)-(30) interval operator are different numerical compositions.

The controlled Eq. (7)-(25) resistance uses `GOLDER_1972_APPROXIMATION` because the original UFOTRI Monin-Obukhov estimator remains unavailable.

## 5. Secondary re-emission feedback

The controlled soil re-emission flux is first debited by the three-layer soil forcing boundary. The corresponding integrated environmental loss over the source footprint is then handed to the F1 hourly buffer.

Acceptance requires:

- zero active secondary source during the source hour;
- the same activity becoming the next-hour secondary source;
- routed activity equal to the already-accounted environmental loss for the fully routed test;
- zero unrouted activity;
- no second environmental loss or direct surface-deposition term created by the handoff.

The next-hour F1 Eq. (5)/(6) concentration is passed to H5 as an explicit secondary HTO air concentration. It may affect subsequent leaf exchange, but the H5 adapter does not add it again as an independent soil inventory input.

The source origin is `UNRESOLVED_HTO_ORIGIN`, because primary HTO and HT-derived HTO have already mixed in the soil state. H5 does not invent a proportional origin split.

## 6. Food chain and manual public exposure

The H5 controlled endpoint is further qualified through the already-reconstructed manual modules:

1. D3 reversible vegetable HTO↔OBT exchange;
2. D4 grass/cow/milk/beef transfer;
3. explicit slaughter-to-beef activity transfer;
4. D5 Eq. (106) inhalation and skin absorption;
5. D5 Eq. (107) green-vegetable, beef and milk ingestion.

The D3, D4 and slaughter activity ledgers must close.

D5 requires food specific activity in Bq/kg, while the reconstructed plant/animal states are area-normalized. H5 therefore declares three positive synthetic qualification masses locally in the machine fixture and uses them only to form a terminal Bq/kg readout. These masses are not added to configuration, parameter databases, defaults or production bindings.

The manual adult reference dose coefficient is the already-reconstructed D5 reference policy, not a production receptor policy.

Acceptance requires positive inhalation, skin and ingestion contributions, exactly 50% skin/inhalation relation, and Eq. (106)/(107) residual closure.

## 7. Determinism, restart and partition checks

H5 directly tests:

- deterministic repeat of the first native-driven environmental interval;
- JSON state serialization/restart before the second interval;
- equal native aggregate surface-flux rate for 1 h and 0.5 h contexts under interval-constant transport;
- equal integrated surface activity for one 1 h interval versus two 0.5 h partitions;
- equal one-hour F1 routed activity/flux under 1 h versus two 0.5 h steps;
- equal D5 exposure integrals under 1 h versus two 0.5 h steps.

H5 does not demand whole-state equality under arbitrary timestep subdivision of every operator split. The existing coupled hydrology numerical gate is re-executed for the already-qualified timestep-refinement claim.

## 8. Existing fidelity gates re-executed

The H5 machine gate re-executes:

- coupled water/HTO hydrology verification;
- F1 re-emission/area-source reconciliation;
- Canada 1987 benchmark-contract reconstruction;
- ITER benchmark-contract reconstruction.

This is evidence that H5 has not broken those qualified boundaries; it does not upgrade their scientific claims.

## 9. Benchmark comparison boundary

Canada 1987:

- benchmark contract remains qualified;
- full numerical replay remains source-limited;
- empirical validation remains false.

ITER:

- benchmark/reference tables remain qualified;
- full atmospheric numerical replay remains false;
- empirical validation remains false.

No chart transcription, missing-input fill or original-executable equivalence is introduced by H5.

## 10. Candidate scope

The H5 implementation PR is intended to contain exactly:

- one new composition module;
- one machine qualification script;
- one focused pytest file;
- this report;
- ADR-083;
- one governance ledger.

It does not modify the native-atmosphere recovery roadmap, workflows, defaults, existing component solvers, parameter databases or CTEAS-Atmos integration.

## 11. Expected result and next stage

Expected machine result:

`PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION`

Only after exact-head Remediation/Protected CI, expected-head merge and no-drift certification may a separate roadmap-only sync mark H5 complete and authorize:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`.

## 12. Non-claims

H5 does not claim original Eq. (27)-(30) discretisation identity for replay orchestration, recovery of the original Monin-Obukhov estimator, wet plume-loss/local-flux spatial equivalence, exact Eq. (44) re-emission-rate generation, origin-resolved mixed soil HTO, complete building-wake/plume-rise numerics, Canada empirical reproduction, ITER full atmospheric replay, CTEAS-Atmos binding, production parameter readiness, calibration, empirical validation, physical accuracy, or original UFOTRI executable numerical equivalence.
