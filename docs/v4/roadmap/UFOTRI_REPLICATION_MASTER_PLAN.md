# UFOTRI Replication Master Plan

## 1. Purpose

This document is the single roadmap and progress ledger for the post-RC1 effort to reconstruct the recoverable UFOTRI model from the available KfK 4605 manual and repository evidence.

It exists to prevent the replication work from being scattered across chat history, pull-request descriptions, ADRs, audit YAML files, and historical branches.

This document does **not** replace stage-specific ADRs, governance records, reports, tests, or validation evidence. It is the top-level control plane that records what remains, what is complete, why each item is required, and what evidence closes each item.

The governing distinction is:

- `V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE=TRUE`
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`
- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`

The frozen V4 RC1 baseline remains the stable fallback/default path. Replication-fidelity work must be developed as explicit post-RC1 compatibility/fidelity paths and must not silently rewrite RC1 behavior.

## 2. Source authority and claim boundary

Primary replication authority:

- available UFOTRI KfK 4605 manual;
- repository historical V1/V2 implementations;
- V3 manual/equation mappings and evidence records;
- frozen V4 RC1 implementation and its exact-head CI evidence;
- `UFOTRI_REPLICATION_GAP_AUDIT_R1`.

Unavailable original assets:

- original UFOTRI source code;
- original UFOTRI executable;
- original parameter-loader implementation;
- complete original executable regression suite.

Therefore the strongest target claim currently permitted is:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE`

The project must not claim exact original-executable numerical equivalence unless original executable/source regression material is recovered later.

## 3. Status vocabulary

Use only these top-level stage states in this roadmap:

- `COMPLETE` — merged to `main`, exact-head CI passed, and post-merge no-drift audit passed.
- `IN_PROGRESS` — an authorized branch/PR is actively being worked.
- `NOT_STARTED` — required work identified but no active implementation/reconciliation stage exists.
- `DEFERRED_EXTERNAL_DEPENDENCY` — required for full replication, but intentionally delayed because an external project/input is not ready.
- `BLOCKED_SOURCE_AMBIGUITY` — the manual/evidence is insufficient to choose a faithful implementation without inventing semantics.
- `OPTIONAL_EXTENSION` — scientifically interesting but not required to reproduce the recoverable UFOTRI manual mechanism.
- `NOT_APPLICABLE_TO_REPLICATION` — not part of the UFOTRI fidelity target.

A stage must not be marked `COMPLETE` merely because code exists. Completion requires the closure evidence defined in Section 5.

## 4. Current frozen baseline

### Foundation F0 — V4 internal software baseline

- Status: `COMPLETE`
- Stage: `V4_DEVELOPMENT_BASELINE_RC1`
- Merge SHA: `38f9d5f5a863e195e7140444829d0e674acca6fc`
- Meaning: selected V4 software chain is internally complete under controlled synthetic/replay forcing.
- Non-claims: no production readiness, no real CTEAS-Atmos binding, no empirical validation, no exact UFOTRI replication claim.

### Foundation F1 — Formal UFOTRI replication gap audit

- Status: `COMPLETE`
- Stage: `UFOTRI_REPLICATION_GAP_AUDIT_R1`
- PR: `#56`
- Certified head: `0a2f7ca78d7469827ea8e8f3cdac33023985ca62`
- Merge SHA: `84655b0989c7d4896dccbc89d575f81967d38091`
- Merge tree: `f13aa22c534c5a51f87e58c30d7972fec4747908`
- Result: 30 UFOTRI capabilities classified; manual-based functional replication remains incomplete.
- No-drift: `MERGE_TREE_DRIFT=FALSE`

## 5. Completion rule for every replication stage

Every required stage must record all of the following before this master plan can mark it `COMPLETE`:

1. exact stage identifier;
2. UFOTRI manual section/equation anchor;
3. implementation/reconciliation decision;
4. changed source files or explicit `NO_SOURCE_CHANGE` result;
5. stage tests and numerical/conservation checks;
6. exact certified head SHA;
7. exact-head Remediation and Protected CI result;
8. PR number;
9. merge SHA;
10. post-merge parent/tree/head-to-merge/main no-drift result;
11. remaining gap after the stage;
12. selected next authorized stage.

If a stage only performs reconciliation and concludes that existing code is already faithful, it may close with `NO_SOURCE_CHANGE`, but it still requires CI and merge/no-drift evidence.

## 6. Master replication sequence

### Phase A — UFOTRI leaf-exchange fidelity

- Phase status: `COMPLETE`
- Scope claim: `UFOTRI_LEAF_EQ7_31_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION=COMPLETE`
- Non-claims: no empirical validation, no production readiness, no real CTEAS-Atmos binding, no whole-model UFOTRI completion, and no original-executable equivalence.

#### A1. UFOTRI Eq. (7)-(31) reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_LEAF_EQ7_31_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: Eq. (7)-(31), leaf/canopy aerodynamic, boundary, stomatal/canopy and meteorological exchange relations.
- Decision: `SOURCE_CHANGES_REQUIRED=TRUE`; historical V2 is manual-informed but not a clean UFOTRI compatibility implementation; generic empirical Leaf R5 is not required for replication.
- Changed source files: `NO_SOURCE_CHANGE`; this stage added governance/report/test artifacts only.
- PR: `#58`
- Certified head: `04d9a10808132f85a52c27a93c22d5829e2c97e9`
- Remediation CI: `33136146835` — `SUCCESS`
- Protected CI: `33136146838` — `SUCCESS`
- Protected merge-ref: `b6e3839fe0908471a7ded6c0ecac64443f098575`
- Validation: portable `1454 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; all five existing V4 machine gates PASS.
- Merge SHA: `6aa1c3858265758927984f2be93b0450e1d1a9e3`
- Merge tree: `e61581dbd03cd0ac9b88b624840bb18afc60adfc`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `cc39a710ed3d59fb894cb5029f96cdeab624faf6` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA.
- Remaining gap: implement the smallest opt-in manual-fidelity path selected by A1, then close manual regression in A3.
- Next stage: `UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`.

#### A2. Leaf fidelity implementation required by A1

- Status: `COMPLETE`
- Stage: `UFOTRI_LEAF_EQ7_31_FIDELITY_IMPLEMENTATION_R1`
- Replication requirement: `REQUIRED_BY_A1`
- Dependency: A1.
- Manual anchor: Eq. (7)-(31), including recovered canopy/day-night/rain rules, Eq. (18), Eq. (21), Eq. (22)-(25), Eq. (27)-(31), and the recovered vegetation geometry relations.
- Decision: implemented a separate opt-in `plant/leaf_ufotri_v4` compatibility path; RC1 and historical V2 defaults remain unchanged. Daytime-rain `r_c=0` is preserved exactly and is not replaced by epsilon. The Golder Monin-Obukhov route is explicitly identified as a literature approximation, not recovered original UFOTRI source logic.
- Changed source files: new `src/cteas_ufotri/plant/leaf_ufotri_v4/{__init__.py,model.py,resistance_state.py}` only; no pre-existing RC1/V2 source file changed. ADR/governance/report and two V4 test files were also added.
- PR: `#60`
- Certified head: `c23b442c1061287a4f8fd9d8856d5c870b930e71`
- Certified tree: `220423b79b4b1a678fa90a2a2bce3d0abaf51b7d`
- Remediation CI: `33138592669` — `SUCCESS`
- Protected CI: `33138592661` — `SUCCESS`
- Validation: portable `1472 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `881a1fff98cf28e19e789249872f58e97d38ea3d`
- Merge tree: `220423b79b4b1a678fa90a2a2bce3d0abaf51b7d`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `4ff6fc0d6fd5a5f93f8b65fc05c11d3e3b8ed507` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: deterministic manual-role regression/benchmark closure for the selected compatibility path; no empirical or original-executable equivalence has been established.
- Next stage: `UFOTRI_LEAF_EQ7_31_MANUAL_REGRESSION_CLOSURE_R1`.
- Forbidden scope remains in force: no generic empirical Leaf R5 physiology, no parameter calibration, no production activation, no real CTEAS-Atmos binding, and no silent replacement of RC1 leaf behavior.

#### A3. Leaf manual-regression/benchmark closure

- Status: `COMPLETE`
- Stage: `UFOTRI_LEAF_EQ7_31_MANUAL_REGRESSION_CLOSURE_R1`
- Replication requirement: `REQUIRED`
- Dependency: A1 and A2.
- Manual anchor: KfK 4605 Section 2.2.2, including Eq. (12)-(14), Eq. (18), Eq. (21)-(25), Eq. (27)-(31), representative day/night stomatal resistances, LAI, rain/soil-water rules, geometry relations, and the stated long-duration interval additivity property.
- Decision: deterministic manual-semantic regression closes the recoverable leaf fidelity scope. A3 found and corrected one A2 manual-literal defect: Eq. (23)-(24) stability corrections must use actual height `z`, while the logarithmic term alone uses `z-d`. Neutral Eq. (22) remains unchanged.
- Changed source files: only opt-in `src/cteas_ufotri/plant/leaf_ufotri_v4/model.py`; RC1 and historical V2 source paths were not changed. ADR/governance/report and one independent manual-regression test file were added.
- PR: `#62`
- Certified head: `ff0e4e399ac3a864328c1298ed84bae1ba0c4752`
- Certified tree: `682aac573b8ec66e5f0d0029bbebf3b61535456a`
- Remediation CI: `33139484014` — `SUCCESS`
- Protected CI: `33139483922` — `SUCCESS`
- Validation: portable `1482 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `cf33d25d9af55be66066bb8fee038c19541898c2`
- Merge tree: `682aac573b8ec66e5f0d0029bbebf3b61535456a`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `61248e4abdfe80e9bce41e898e6c8d159caaa9d5` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: `NONE_WITHIN_PHASE_A_LEAF`; Canada 1987/ITER empirical benchmark obligations remain in Phase G and are not part of A3 closure.
- Next stage: `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`.

---

### Phase B — UFOTRI OBT compartment fidelity

#### B1. Exchangeable/non-exchangeable OBT reconstruction

- Status: `NOT_STARTED`
- Stage: `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED`
- Current state: RC1 retains a reduced aggregate `k_f/k_r` OBT inventory.
- Required fidelity target:
  - reconstruct the manual distinction between exchangeable and non-exchangeable tritium/OBT where recoverable;
  - retain the reduced RC1 OBT path as fallback/reference;
  - map plant/crop OBT semantics into later food-chain compartments.
- Important boundary:
  - `GENERIC_MULTI_POOL_OBT=OPTIONAL_EXTENSION`;
  - only the narrow manual-supported compartment structure is replication-required.

#### B2. OBT compartment conservation and numerical integration

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: B1.
- Required checks:
  - mass/inventory conservation;
  - deterministic repeat;
  - restart equivalence;
  - timestep refinement;
  - compatibility with TFWT/root operator split;
  - explicit comparison against reduced RC1 OBT behavior.

---

### Phase C — UFOTRI soil hydrology fidelity

#### C1. Eq. (33)-(37) soil-hydrology reconstruction

- Status: `NOT_STARTED`
- Stage: `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: Eq. (33)-(37), soil water potential and Darcy/Richards transport.
- Current state:
  - V4 three-layer soil inventories and signed transport are implemented;
  - interlayer water fluxes are supplied by the caller rather than generated from the UFOTRI hydrologic closure.
- Required outcome:
  - reconstruct the UFOTRI-specific water-potential/flux mechanism;
  - couple it to the existing three-layer HTO inventory solver;
  - preserve explicit flux interfaces for RC1/replay compatibility.
- Important boundary:
  - this is **not** authorization for an unconstrained general-purpose Richards/Darcy hydrology package;
  - implement only the manual-required UFOTRI fidelity scope unless later evidence explicitly authorizes an extension.

#### C2. Coupled water/HTO hydrology verification

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: C1.
- Required checks:
  - water balance;
  - HTO balance;
  - signed upward/downward transport;
  - lower-boundary behavior;
  - root sink coupling;
  - dry/wet limiting cases;
  - restart and timestep refinement.

---

### Phase D — UFOTRI food-chain and exposure reconciliation

#### D1. V2 continuous food-chain to post-RC1 reconciliation

- Status: `NOT_STARTED`
- Stage: `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Current state:
  - historical V2 contains vegetable/grass/animal/milk/beef and exposure functionality;
  - V4 RC1 uses a simpler terminal-harvest food→intake→dose adapter.
- Required outcome:
  - map historical V2 compartments to UFOTRI manual roles;
  - identify which historical components can be retained, which require migration, and which are project-specific replacements;
  - create an optional UFOTRI continuous-ingestion compatibility path without removing the RC1 terminal-harvest project boundary.

#### D2. Pasture root-profile fidelity

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Manual target: pasture root distribution `40/60/0` where specified by the manual.
- Current state: controlled crop profile `20/40/40` exists for nutrient crops.
- Dependency: C1/C2 interfaces must remain compatible.

#### D3. Vegetable/grass compartment closure

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: B1/B2 and D1.

#### D4. Cow/milk/beef compartment closure

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: D1 and D3.
- Required checks: feed/drinking-water inputs, animal HTO/OBT inventories, milk transfer, slaughter/beef inventory, excretion/loss accounting.

#### D5. Inhalation/skin/ingestion exposure reconciliation

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: D1-D4.
- Goal: reconcile the recoverable UFOTRI exposure pathways with the post-RC1 dose interfaces without asserting obsolete dose coefficients as modern production defaults.

---

### Phase E — HT branch and HT→HTO environmental reconstruction

**HT is part of the replication target and is not omitted from this roadmap.**

The branch is split so that internal HT environmental mechanisms can progress independently, while real atmospheric transport remains deferred until CTEAS-Atmos is ready.

#### E1. HT branch contract and manual mapping

- Status: `NOT_STARTED`
- Stage: `UFOTRI_HT_BRANCH_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Goal:
  - identify the recoverable manual states, units, interfaces, deposition/oxidation semantics, and coupling boundaries for HT;
  - distinguish HT concentration/flux inputs from HTO inputs;
  - define synthetic/replay-compatible interfaces so internal HT process development does not wait for real Atmos.

#### E2. HT→HTO soil conversion/oxidation reconstruction

- Status: `NOT_STARTED`
- Stage: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`
- Replication requirement: `REQUIRED`
- Dependency: E1.
- Scope:
  - HT deposition/entry to soil as supported by the manual;
  - microbial/soil conversion of HT to HTO;
  - resulting HTO entry into the existing soil inventory system;
  - conservation ledger linking HT loss to HTO gain where physically defined.
- This stage can use controlled synthetic HT forcing and does **not** require real CTEAS-Atmos output.

#### E3. HT-derived HTO re-emission and secondary-feedback reconciliation

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: E2.
- Goal:
  - reconcile soil/plant re-emission and area-source feedback behavior from historical implementations with the UFOTRI manual;
  - distinguish primary atmospheric HTO from secondary HTO generated after HT oxidation;
  - preserve mass provenance across HT→HTO→atmosphere/plant pathways.

#### E4. Separate HT atmospheric transport and real CTEAS-Atmos binding

- Status: `DEFERRED_EXTERNAL_DEPENDENCY`
- Replication requirement: `REQUIRED_FOR_FULL_REPLICATION`
- Dependency: independent CTEAS-Atmos project maturity.
- Deferred scope:
  - real HT atmospheric transport;
  - real deposition/forcing products;
  - production-quality Atmos→UFOTRI binding.
- Important rule:
  - E4 being deferred must **not** block E1-E3 synthetic/manual reconstruction work;
  - no HTO atmospheric surrogate may be silently relabeled as real HT transport.

#### E5. End-to-end HT→HTO→plant/food/dose compatibility test

- Status: `DEFERRED_EXTERNAL_DEPENDENCY`
- Replication requirement: `REQUIRED_FOR_FULL_REPLICATION`
- Dependency: E2/E3 plus E4 when real Atmos integration is eventually available.
- A synthetic/manual E5 precursor may be run earlier, but it must not be labeled real Atmos validation.

---

### Phase F — Re-emission and atmosphere/area-source compatibility

#### F1. Re-emission/area-source reconciliation

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Goal:
  - reconcile historical soil/plant re-emission code with recoverable UFOTRI semantics;
  - define how secondary HTO returns to atmospheric forcing without double counting;
  - make source provenance explicit for primary release versus secondary environmental feedback.
- Real CTEAS-Atmos numerical binding remains deferred, but internal compatibility can be tested with replay/synthetic atmosphere adapters.

---

### Phase G — UFOTRI benchmark reconstruction and final replication gate

#### G1. Canada 1987 benchmark reconstruction

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED_AS_VALIDATION`
- Goal: reconstruct the recoverable manual benchmark inputs, observables, timing, and comparison metrics without inventing missing values.
- Missing/ambiguous inputs must remain explicitly unresolved rather than silently filled.

#### G2. ITER benchmark reconstruction

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED_AS_VALIDATION`
- Goal: reproduce the recoverable ITER comparison/benchmark case described or referenced by the manual/evidence set.

#### G3. Cross-module fidelity qualification

- Status: `NOT_STARTED`
- Replication requirement: `REQUIRED`
- Dependency: completed internal phases plus available deferred Atmos/HT items as required by benchmark scope.
- Required checks:
  - deterministic repeat;
  - restart equivalence;
  - timestep refinement;
  - cross-module mass conservation;
  - HT/HTO provenance conservation;
  - plant/soil/food inventory accounting;
  - explicit comparison of RC1 fallback versus UFOTRI fidelity path;
  - all remaining manual-gap matrix entries resolved or explicitly source-blocked.

#### G4. Final UFOTRI manual-based reconstruction gate

- Status: `NOT_STARTED`
- Target flag: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE`
- Gate may become `TRUE` only if:
  - all recoverable manual-required internal mechanisms are complete;
  - all required reconciliations are merged and no-drift audited;
  - benchmark obligations are closed to the extent permitted by available evidence;
  - remaining unresolved items are only those provably blocked by unavailable original assets rather than missing implementation work;
  - no exact-original-executable equivalence claim is made without original regression material.

## 7. Candidate extensions that are not automatically replication requirements

These may be scientifically useful later, but they must not be confused with UFOTRI fidelity work:

- empirical Leaf R5 model beyond recovered Eq. (7)-(31) semantics — `OPTIONAL_EXTENSION`;
- generic precursor-rich multi-pool OBT model beyond manual exchangeable/non-exchangeable structure — `OPTIONAL_EXTENSION`;
- unconstrained modern full Richards/Darcy hydrology framework beyond UFOTRI Eq. (33)-(37) needs — `OPTIONAL_EXTENSION`;
- calibration to production data — outside the replication-development gate;
- modernized dose coefficients/consumption datasets — production/application layer, not evidence of original UFOTRI fidelity.

## 8. Production and Atmos boundaries

Production inputs are intentionally not required to progress the internal manual-reconstruction phases.

The following remain separate from this roadmap's internal replication-development completion:

- real production-case input packet;
- real CTEAS-Atmos HTO binding;
- real CTEAS-Atmos HT binding;
- empirical site validation;
- production calibration;
- physical-accuracy/production-readiness claim.

Synthetic, replay, and manual benchmark inputs may be used for software/fidelity reconstruction, but their provenance must remain explicit and they must not be presented as real production validation.

## 9. Current priority order

Unless a reconciliation stage exposes a hard dependency that requires re-ordering, the selected sequence is:

1. `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`
2. OBT conservation/numerical closure
3. `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`
4. coupled water/HTO hydrology verification
5. `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`
6. pasture / vegetable / grass / cow / milk / beef / exposure closure
7. `UFOTRI_HT_BRANCH_RECONCILIATION_R1`
8. `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`
9. HT-derived HTO re-emission/secondary-feedback reconciliation
10. re-emission/area-source reconciliation
11. Canada 1987 benchmark reconstruction
12. ITER benchmark reconstruction
13. deferred real HT/HTO Atmos reconciliation when CTEAS-Atmos is ready
14. final cross-module fidelity qualification
15. `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE` gate

The order after A1 may be changed only by an explicit governance decision that records the dependency and preserves completed evidence.

## 10. Progress checklist

### Foundation

- [x] V4 RC1 internal software baseline frozen
- [x] UFOTRI replication gap audit R1

### Leaf

- [x] Eq. (7)-(31) reconciliation — PR #58, merge `6aa1c3858265758927984f2be93b0450e1d1a9e3`, no-drift PASS
- [x] UFOTRI Eq. (7)-(31) fidelity implementation — PR #60, merge `881a1fff98cf28e19e789249872f58e97d38ea3d`, no-drift PASS
- [x] Leaf manual-regression closure — PR #62, merge `cf33d25d9af55be66066bb8fee038c19541898c2`, no-drift PASS

### OBT

- [ ] Exchangeable/non-exchangeable reconstruction
- [ ] OBT conservation/numerical integration closure

### Soil hydrology

- [ ] Eq. (33)-(37) UFOTRI hydrology reconstruction
- [ ] Coupled water/HTO verification

### Food chain / exposure

- [ ] V2 continuous food-chain reconciliation
- [ ] Pasture 40/60/0 root profile
- [ ] Vegetable/grass closure
- [ ] Cow/milk/beef closure
- [ ] Inhalation/skin/ingestion exposure reconciliation

### HT and secondary HTO

- [ ] HT branch contract/manual mapping
- [ ] HT→HTO soil conversion
- [ ] HT-derived HTO re-emission/secondary feedback
- [ ] Re-emission/area-source compatibility
- [ ] Real HT atmospheric transport / CTEAS-Atmos binding — deferred external dependency
- [ ] End-to-end HT→HTO compatibility with real Atmos — deferred external dependency

### Benchmarks / final gate

- [ ] Canada 1987 benchmark
- [ ] ITER benchmark
- [ ] Cross-module fidelity qualification
- [ ] `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE`

## 11. Update protocol

After each stage merges, update this document in a small roadmap-status PR. Do not rewrite historical completion evidence.

For the completed stage, record:

```text
Status: COMPLETE
PR: #<number>
Certified head: <sha>
Merge SHA: <sha>
Validation: <exact machine result>
No-drift: PASS
Remaining gap: <explicit remaining work or NONE>
Next stage: <stage id>
```

If the stage is blocked by missing/ambiguous manual evidence, record the blocker and leave the checkbox open.

If a stage proves that a planned implementation is unnecessary because existing code is already manual-faithful, mark the reconciliation stage complete and change the implementation item to `NOT_APPLICABLE_TO_REPLICATION`; do not write code merely to satisfy a checklist.

## 12. Immediate next stage

`UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`

B1 must first reconcile KfK 4605 Section 2.2.6 against the existing `obt_v3` solver and UFOTRI baseline. The manual explicitly states that exchangeable organically bound tritium is in equilibrium with free plant HTO and need not be distinguished from free HTO in the model; therefore B1 must not introduce a generic exchangeable/non-exchangeable multi-pool structure merely to satisfy the stage name. The distinct replication target is the recoverable non-exchangeable organic-tritium behavior, including the daily-average incorporation rate of approximately `0.06% per hour`, the reported day/night asymmetry where recoverable, and the mean organic-tritium loss rate of approximately `0.3% per hour`. Missing normalized day/night multipliers must remain unresolved rather than being invented.
