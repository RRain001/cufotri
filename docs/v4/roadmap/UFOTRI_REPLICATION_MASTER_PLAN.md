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

- Phase status: `COMPLETE`
- Completed scope: plant exchangeable/non-exchangeable state-role semantics, recoverable first-order HTO↔OBT transfer topology, and controlled conservation/numerical qualification for both recoverable manual rate contexts.
- Remaining source boundary: original day/night formation multipliers and exact original executable parameter selection remain unresolved because the original source/executable is unavailable; these do not block recoverable manual-based Phase B closure. No empirical, production, physical-accuracy, or original-executable-equivalence claim is made.

#### B1. Exchangeable/non-exchangeable OBT reconstruction

- Status: `COMPLETE`
- Stage: `UFOTRI_OBT_E_N_COMPARTMENT_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: KfK 4605 Section 2.2.6 and Section 3.3.3 Eq. (65)-(66).
- Decision: no independent exchangeable-OBT inventory is created because the manual explicitly treats exchangeable OBT together with free plant HTO. In the opt-in UFOTRI semantic path, `TFWTState` represents free HTO plus the exchangeable-OBT role and `OBTState` represents non-exchangeable OBT. The existing first-order `kf*M_TFWT-kr*M_OBT` topology is supported by Eq. (65)-(66) and the manual statement that ingestion transfer paths/rates are adapted to hourly dispersion-module time steps. Generic multi-pool OBT remains an optional extension, not a replication requirement.
- Rate reconciliation: Section 2.2.6 gives daily-average `kf=0.0006 h^-1`, `kr=0.003 h^-1`; Eq. (66)/24 reconstructs approximately `0.0004998658 h^-1` and Eq. (65)/24 approximately `0.0028881133 h^-1`. The forward and loss differences are approximately 20.0% and 3.9%, respectively. Both manual contexts are retained with distinct provenance; the original executable's parameter selection is not recovered. Normalized day/night formation multipliers also remain unresolved.
- Changed source files: new opt-in `src/cteas_ufotri/plant/obt_ufotri_v4/{__init__.py,model.py}` only; existing `obt_v3`, `tfwt_v3`, `food_v3`, V4 integration and RC1 defaults were not modified. ADR-062, governance/report artifacts and one independent B1 test file were added.
- PR: `#64`
- Certified head: `842151a857fa62f0e9df1f6142ad3c552af516d2`
- Certified tree: `37a26cc3066deebb84767e9082f32a46ba199cee`
- Remediation CI: `33140638373` — `SUCCESS`
- Protected CI: `33140638399` — `SUCCESS`
- Protected merge-ref: `1194c58830554669e88fb96aab822596933ab2b1`
- Validation: portable `1493 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `f98b9d54300d53736c25ebf3bf5502f67cf89f07`
- Merge tree: `37a26cc3066deebb84767e9082f32a46ba199cee`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `0756ddb4777819a58278b73c37209169c2318ee0` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: numerical/conservation qualification of the reconstructed roles, including explicit comparison of the Section-2.2.6 controlled daily-average profile with the Eq. (65)-(66)-derived profile. B1 does not recover the original day/night multiplier pair or exact original executable parameter selection.
- Next stage: `UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1`.

#### B2. OBT compartment conservation and numerical integration

- Status: `COMPLETE`
- Stage: `UFOTRI_OBT_COMPARTMENT_CONSERVATION_NUMERICAL_INTEGRATION_R1`
- Replication requirement: `REQUIRED`
- Dependency: B1.
- Manual anchor: KfK 4605 Section 2.2.6 and Section 3.3.3 Eq. (65)-(66).
- Decision: qualification-only closure using two explicit manual rate contexts under identical controlled forcing: `SECTION_2_2_6_DAILY_AVERAGE_CONTROLLED_BASELINE` (`kf=0.0006 h^-1`, `kr=0.003 h^-1`) and `EQ65_66_DERIVED_HOURLY_COMPARISON` (`kf≈0.0004998658 h^-1`, `kr≈0.0028881133 h^-1`). Neither comparison profile is promoted to recovered original-executable truth. Constant day/night multipliers `1/1` are used only for controlled numerical comparison; original diurnal multipliers remain unresolved.
- Changed source files: `NO_EXISTING_SOURCE_CHANGE`; B2 adds only `scripts/v4/run_ufotri_obt_compartment_conservation_numerical_integration_r1.py`, `tests/v4/test_ufotri_obt_compartment_conservation_numerical_integration_r1.py`, ADR-063, governance and report artifacts. Existing `obt_v3`, `tfwt_v3`, V4 integrator, selected operator split and RC1/V3 defaults are unchanged.
- Numerical closure: both rate profiles pass conservation, deterministic repeat, restart equivalence, timestep refinement (`3600→1800→900→450 s` against `225 s`), nonzero OBT formation, independent constant-TFWT analytic oracle and zero-TFWT pure OBT decay. Section-2.2.6 profile exactly reproduces the frozen controlled baseline; no third exchangeable-OBT inventory is introduced; the two manual profiles retain a nonzero controlled numerical consequence without physical-validity ranking.
- PR: `#66`
- Certified head: `e98cd4d0429302fbc08d3c8fccda09e1c14c6418`
- Certified tree: `0b6ed18cb952b3f8e5cfb4c121d02fcd0f7f64d3`
- Remediation CI: `33141481585` — `SUCCESS`
- Protected CI: `33141481600` — `SUCCESS`
- Protected merge-ref: `9595555e425c60ee1a2d3cd3f53bf43efdd913f6`
- Validation: portable `1499 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `cb26e9f3d245e31a4597b4f8e6a4abd93d004f28`
- Merge tree: `0b6ed18cb952b3f8e5cfb4c121d02fcd0f7f64d3`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `b86886d5a87409f76dadd76ad3f5d2c19b3cd520` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: `NONE_WITHIN_PHASE_B_OBT` for recoverable manual-based state roles and controlled numerical qualification. Original day/night formation multipliers and exact original executable parameter selection remain source-blocked and are not reconstructed by B2.
- Next stage: `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`.
- Non-claims remain: no empirical validation, calibration, production parameter activation, real CTEAS-Atmos binding, generic multi-pool OBT, physical-accuracy claim, or original-executable numerical equivalence.

---

### Phase C — UFOTRI soil hydrology fidelity

- Phase status: `COMPLETE`
- Completed scope: recoverable Eq. (33)-(37) hydrologic mechanism, opt-in signed inter-layer water/HTO flux closure compatible with the frozen three-layer inventory core, and controlled multi-step coupled numerical qualification across lower-boundary, root, TFWT and OBT interfaces.
- Scope claim: `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_NUMERICAL_QUALIFICATION=COMPLETE` for the recoverable manual-based mechanism under controlled/provenanced constitutive inputs.
- Remaining source boundary: original UFOTRI constitutive curves and exact original numerical discretization remain unavailable; Phase C does not convert those source gaps into invented production parameters or an original-executable-equivalence claim.

#### C1. Eq. (33)-(37) soil-hydrology reconstruction

- Status: `COMPLETE`
- Stage: `UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: KfK 4605 Section 2.2.3 Eq. (33)-(37), including additive soil-water potential, one-dimensional continuity, Darcy flux, the matric-potential/conductivity Richards form and the vegetation root sink role.
- Decision: added an opt-in `plant/soil_ufotri_v4` closure that generates only the two internal signed water/HTO interface fluxes and projects them into the unchanged `ThreeLayerSoilForcing` contract. Eq. (37) root uptake remains external through `root_v4`. No original UFOTRI constitutive curve or original numerical discretization was invented.
- Constitutive boundary: callers must supply versioned/provenanced tabulated `Theta -> (Psi_m, K)` evidence; piecewise-linear interpolation is allowed only within the supplied domain and extrapolation fails closed. Harmonic-mean interface conductivity and layer-centre gradients are explicitly labeled implementation choices rather than recovered original UFOTRI source behavior.
- Changed source files: new `src/cteas_ufotri/plant/soil_ufotri_v4/{__init__.py,model.py}` only; no pre-existing `soil_v4`, `root_v4`, V4 integration or RC1/replay source file changed. Machine script, two C1 test files, ADR-064, governance and report artifacts were added.
- Numerical closure: independent Eq. (33) and Eq. (35) identities, downward gravity drainage, upward capillary-direction transport, signed upwind HTO donor selection, constitutive interpolation/no-extrapolation, malformed-table rejection, boundary/root preservation, inter-layer double-count rejection and one-step frozen soil water/HTO conservation all pass. The machine-visible C1 gate is executed under pytest.
- PR: `#68`
- Certified head: `19316b61dcdf3eb036c8fb0882f2d15919b284a2`
- Certified tree: `de5f3742bcfef9fff2e09980b2cf76937d936f2f`
- Remediation CI: `33142454886` — `SUCCESS`
- Protected CI: `33142454941` — `SUCCESS`
- Protected merge-ref: `043e63d77d73eaceda314610923157ad996f3afa`
- Validation: portable `1510 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `62d720d46ca6e52b328f985226d68d84ce278fc8`
- Merge tree: `de5f3742bcfef9fff2e09980b2cf76937d936f2f`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `d1a89246db1b2847c3a9fc04488f6cf303bb8477` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: full dynamic/coupled hydrology qualification remains C2; original executable constitutive curves and exact numerical discretization remain unavailable source boundaries and are not claimed recovered.
- Next stage: `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1`.
- Non-claims: no production soil parameters, calibration, empirical validation, physical-accuracy claim, generic production Richards solver, real CTEAS-Atmos binding or original-executable numerical equivalence.

#### C2. Coupled water/HTO hydrology verification

- Status: `COMPLETE`
- Stage: `UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1`
- Replication requirement: `REQUIRED`
- Dependency: C1.
- Decision: qualification-only closure with `NO_EXISTING_SOURCE_CHANGE`. At each interval the merged C1 hydrology closure is recomputed from the current three-layer soil state, projected into the frozen `ThreeLayerSoilForcing` contract, coupled to explicit `root_v4` uptake, and advanced through the existing `V4SoilRootTFWTOBTIntegrator`. No second soil solver, second hydrology solver, production parameter activation or RC1 default-path change is introduced.
- Controlled inputs: synthetic, explicit and provenance-bearing gravity, capillary and dry/wet hydraulic profiles only. The dry `K=0` endpoint uses a documented numerical-zero tolerance `|q| <= 1.0e-24 m/s` solely to absorb a measured floating-point reconstruction residual of `7.401486830834377e-26 m/s`; this is approximately fifteen orders of magnitude below the controlled `~1e-9 m/s` transport scale and does not alter equations, constitutive inputs, conservation tolerances or refinement criteria.
- Changed source files: `NO_EXISTING_SOURCE_CHANGE`; C2 adds only `scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py`, `tests/v4/test_ufotri_coupled_water_hto_hydrology_verification_r1.py`, ADR-065, governance and report artifacts. Existing `soil_ufotri_v4`, `soil_v4`, `root_v4`, TFWT/OBT, V4 integration and RC1/replay source paths remain unchanged.
- Numerical closure: per-step and cumulative water/HTO ledgers, downward gravity transport, upward capillary transport including a multi-step trajectory, wet/dry limits, lower-boundary water/HTO loss, exact root water/HTO transfer identity, dynamic hydrology recomputation, selected `PRESERVE_V3_POST_OBT_ROOT_GAIN` ordering, deterministic repeat, JSON restart equivalence and timestep refinement (`3600→1800→900→450 s` toward a `225 s` comparison reference) all pass.
- PR: `#70`
- Certified head: `a1c0c6759108cd8da716af71c3e38142ca10fc00`
- Certified tree: `7a14d4edb6c92fc78e6fb269161367f95a7ed42f`
- Remediation CI: `33144651653` (#200) — `SUCCESS`
- Protected CI: `33144651659` (#211) — `SUCCESS`
- Protected merge-ref: `be9af53b68ae54aeff6876e47a3fbea5580fffbc`
- Validation: portable `1515 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `881f2ab06ef6df3e8e3f4ed5b2c6ddf46aa6e37b`
- Merge tree: `7a14d4edb6c92fc78e6fb269161367f95a7ed42f`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `95681af4c22bb3ec1de00bf3d67f002288edb0c6` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: `NONE_WITHIN_PHASE_C_SOIL_HYDROLOGY` for recoverable manual-based mechanism plus controlled numerical qualification. Original constitutive curves and exact original discretization remain source-blocked and are not claimed recovered.
- Next stage: `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`.
- Non-claims: no production hydraulic parameters, production hydrology readiness, calibration, empirical validation, physical-accuracy claim, real CTEAS-Atmos binding, original constitutive-curve recovery, original numerical-discretization recovery or original-executable equivalence.

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

1. `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`
2. pasture / vegetable / grass / cow / milk / beef / exposure closure
3. `UFOTRI_HT_BRANCH_RECONCILIATION_R1`
4. `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`
5. HT-derived HTO re-emission/secondary-feedback reconciliation
6. re-emission/area-source reconciliation
7. Canada 1987 benchmark reconstruction
8. ITER benchmark reconstruction
9. deferred real HT/HTO Atmos reconciliation when CTEAS-Atmos is ready
10. final cross-module fidelity qualification
11. `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE` gate

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

- [x] Exchangeable/non-exchangeable reconstruction — PR #64, merge `f98b9d54300d53736c25ebf3bf5502f67cf89f07`, no-drift PASS
- [x] OBT conservation/numerical integration closure — PR #66, merge `cb26e9f3d245e31a4597b4f8e6a4abd93d004f28`, no-drift PASS

### Soil hydrology

- [x] Eq. (33)-(37) UFOTRI hydrology reconstruction — PR #68, merge `62d720d46ca6e52b328f985226d68d84ce278fc8`, no-drift PASS
- [x] Coupled water/HTO verification — PR #70, merge `881f2ab06ef6df3e8e3f4ed5b2c6ddf46aa6e37b`, no-drift PASS

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

`UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`

D1 must reconcile the historical V2 continuous food-chain implementation against the UFOTRI manual and the post-RC1 terminal-harvest boundary before any migration or new compatibility code is authorized. The first obligation is semantic: map vegetable, grass, pasture, animal, milk, beef and exposure compartments/rates to recoverable manual roles; identify which historical V2 components are retainable, which require migration or correction, and which are project-specific replacements. The RC1 terminal-harvest food→intake→dose adapter remains the stable fallback/default and must not be silently removed. No historical V2 parameter is promoted to a modern production default merely because its compartment topology is retained.