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

- Phase status: `COMPLETE`

#### D1. V2 continuous food-chain to post-RC1 reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_V2_CONTINUOUS_FOODCHAIN_TO_POST_RC1_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: KfK 4605 Eq. (65)-(107), covering vegetable/grass, cow/milk, animal HTO/OBT and public exposure roles.
- Decision: reconciliation-only closure with `NO_EXISTING_SOURCE_CHANGE`. The historical V2 continuous ecological food-chain/dose implementation remains present byte-for-byte and provides recoverable continuous topology, but it is not directly activated because it mixes manual/manual-converted rates with modern inventory-closure engineering, project herd/intake geometry and later dose-coefficient extensions. The V4 RC1 terminal-harvest → annual-intake → food-dose adapter remains the stable default/fallback; later UFOTRI continuous work must be an opt-in parallel compatibility path.
- Frozen historical evidence: annotated tag `ufotri-environmental-pathways-v2-candidate`, tag object `11eb90096b2c08a0b40c7cf7f2917d473535e8c7`, resolves to commit `f097115cbfc052baa18f1e49a1207fa6b3523cff`. D1 machine tests verified current-vs-tag byte identity for `src/cteas_ufotri/case.py`, `src/cteas_ufotri/foodchain/model.py` and `src/cteas_ufotri/dose/public.py`.
- Key gap classification: Eq. (98) cow inhalation/skin uptake is genuinely absent from the retained V2 animal core and must be reconstructed in D4; human/public inhalation and skin dose terms must not be relabeled as animal uptake. Representative support-area normalization, beef product inventory/continuous herd turnover, several intake assumptions and distinct modern OBT dose coefficients remain project/application extensions rather than recovered original UFOTRI behavior.
- Changed source files: `NO_EXISTING_SOURCE_CHANGE`; D1 added only a machine reconciliation script, one independent pytest file, ADR-066, governance YAML and report.
- PR: `#72`
- Certified head: `1739f16abb3396a30799fe3c2bcda2ebb750517c`
- Certified tree: `a2fe9ed69cb4d84c5eb8f62b6ce1c81d07b79dab`
- Remediation CI: `33146466499` (#202) — `SUCCESS`
- Protected CI: `33146466511` (#213) — `SUCCESS`
- Protected merge-ref: `10b7a385e95ce41b8de463c4337d266e621ab7c4`
- Validation: portable `1520 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`. D1-specific tag resolution, byte-identity, Eq.98-gap, parameter-policy and RC1-boundary assertions passed inside the portable suite.
- Merge SHA: `1d09f65efb5bff70b65c9b4adfa41b2c09604739`
- Merge tree: `a2fe9ed69cb4d84c5eb8f62b6ce1c81d07b79dab`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `711819c4bf6b6bdd286f0ee7c970aeb53f631298` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: pasture root allocation, vegetable/grass manual compartment closure, cow/milk/beef Eq. (82)-(105-2) closure including Eq. (98), and Eq. (106)-(107) exposure reconciliation remain D2-D5.
- Next stage: `UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1`.
- Non-claims: no vegetable/grass completion, cow/milk/beef completion, exposure completion, calibration, empirical validation, production parameter activation, physical-accuracy claim, real CTEAS-Atmos binding, original numerical-discretization recovery or original-executable equivalence.

#### D2. Pasture root-profile fidelity

- Status: `COMPLETE`
- Stage: `UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY_R1`
- Replication requirement: `REQUIRED`
- Manual/evidence anchor: frozen V2 parameter-source audit records `grass_root_fractions=0.4;0.6;0.0` as `manual direct`, source `UFOTRI manual`, grade `A`, status `accepted`; the nutrient-crop `0.2;0.4;0.4` profile remains a separate manual-direct role.
- Decision: added a separate opt-in `src/cteas_ufotri/plant/root_v4/pasture_profile.py` that accepts an explicit total non-negative water-uptake flux and returns the existing `ThreeLayerRootWaterFluxForcingV4` with exact `(0.4, 0.6, 0.0)` allocation. It does not infer total uptake, ET or hydrology, and it does not replace the existing crop `20/40/40` profile globally.
- Changed source files: one new opt-in source file only, `src/cteas_ufotri/plant/root_v4/pasture_profile.py`; no pre-existing source file changed. D2 also added one machine script, one pytest file, ADR-067, governance YAML and report.
- Numerical closure: exact 40/60/0 fractions, exact L3 zero, unchanged 20/40/40 control, total-water identity, equal-concentration total-HTO equivalence, unequal-concentration `J=q_w C_w`, water/HTO ledger closure, typed forcing compatibility and fail-closed invalid input checks all pass.
- PR: `#74`
- Certified head: `e4d8a01452b4e8dd3475a3b64f53d661eaa3d5fb`
- Certified tree: `f83db84e2f1c9793d41724b3cc9ea0d792106226`
- Remediation CI: `33148130661` (#204) — `SUCCESS`
- Protected CI: `33148130577` (#215) — `SUCCESS`
- Protected merge-ref: `88b240e3b0e08582b9655cb0b379e77b8c6338a3`
- Validation: portable `1531 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`. D2-specific machine-gate execution and all profile/conservation assertions passed inside the portable suite.
- Merge SHA: `c849f3d328c6d59c73fb1d1de85bff57dc5ec1ce`
- Merge tree: `f83db84e2f1c9793d41724b3cc9ea0d792106226`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `d5d43092b9255f0a2a950196f68ad6b89b910bab` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: vegetable/grass compartment closure, cow/milk/beef closure including Eq. (98), and exposure reconciliation remain D3-D5. D2 does not activate project-specific pasture LAI, biomass, cutting, root-activity, feed-intake or total-uptake parameters.
- Next stage: `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1`.
- Scope claim: `UFOTRI_PASTURE_40_60_0_ROOT_PROFILE_FIDELITY=COMPLETE`.
- Non-claims: no production total root-water uptake, production pasture parameters, vegetable/grass compartment completion, cow/milk/beef completion, exposure completion, calibration, empirical validation, physical-accuracy claim, real CTEAS-Atmos binding or original-executable equivalence.

#### D3. Vegetable/grass compartment closure

- Status: `COMPLETE`
- Stage: `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE_R1`
- Replication requirement: `REQUIRED`
- Dependency: B1/B2, C1/C2, D1 and D2.
- Manual anchor: KfK 4605 Section 3.3.3 Eq. (65)-(66) for reversible vegetable plant HTO↔OBT and Section 3.4.1-3.4.2 Eq. (67)-(81) for the grass/soil/atmosphere compartment-role system; grass OBT Eq. (105-1)-(105-2) remains D4 scope because its reverse rate depends on cow/milk losses.
- Decision: added a separate opt-in long-term `foodchain/ufotri_vegetable_grass_v4.py` path. Vegetable Eq. (65)-(66) is represented as a conservative analytic two-compartment TFWT/non-exchangeable-OBT system in which OBT→HTO returns activity to TFWT. The caller must explicitly select either the exact Eq. (66) rate reconstructed from the manual's stated masses/divisors or the manual-rounded `0.012 d^-1`; no original-executable selection is inferred. Eq. (67)-(81) grass rates are retained as a typed reference/ownership map only and are not activated as a second transport solver; active leaf, soil/hydrology and root roles remain owned by the previously qualified Phase A/C/D2 paths.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/foodchain/ufotri_vegetable_grass_v4.py`; D3 also added one machine script, one pytest file, ADR-068, governance YAML and report. No pre-existing RC1, V2, `obt_v3`, V4 integration or roadmap source was changed in PR #76.
- Numerical closure: independent analytic agreement for exact and rounded Eq. (66) profiles, total HTO+OBT conservation, forward HTO→OBT transfer, reverse OBT→HTO return, deterministic repeat, restart/semigroup equivalence, 24×1 h partition equivalence, zero-inventory stability, exact-vs-rounded rate distinction, exact-profile equilibrium organic/inorganic specific-activity ratio of one, metadata/time-step fail-closed behavior, exact grass layer/root/reference-rate mapping, D2 40/60/0 preservation and explicit confirmation that Eq. (67)-(81) rates remain inactive all pass.
- PR: `#76`
- Certified head: `3d6967a3640d35b9374b1a80778db0487cff8d9d`
- Certified tree: `b73231b61816da88302959b47f9544abc1abdd66`
- Remediation CI: `33151263118` (#206) — `SUCCESS`
- Protected CI: `33151263149` (#217) — `SUCCESS`
- Protected merge-ref: `4b5af8ebca32f07bc6f749d2ed72c93336f62425`
- Validation: portable `1537 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `238bbcbc82f5c417dc33663bd47695f6b20426ed`
- Merge tree: `b73231b61816da88302959b47f9544abc1abdd66`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `50a82968959cb6a5cc2094cd97f7936ec08be7de` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: cow/milk/beef Eq. (82)-(105-2) closure including Eq. (98), grass OBT Eq. (105) completion through the animal-loss terms, and Eq. (106)-(107) exposure reconciliation remain D4-D5.
- Next stage: `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`.
- Scope claim: `UFOTRI_VEGETABLE_GRASS_COMPARTMENT_CLOSURE=COMPLETE`.
- Non-claims: no cow/milk/beef completion, no grass OBT Eq. (105) completion, no exposure completion, no production parameter activation, no calibration or empirical validation, no physical-accuracy/production-readiness claim, no real CTEAS-Atmos binding, no recovered original numerical discretization and no original-executable equivalence.

#### D4. Cow/milk/beef compartment closure

- Status: `COMPLETE`
- Stage: `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE_R1`
- Replication requirement: `REQUIRED`
- Dependency: D1 and D3.
- Manual anchor: KfK 4605 Eq. (82)-(105-2), including cow-water loss, milk HTO/OBT pathways, cow OBT turnover/formation, Eq. (98) atmosphere-to-cow HTO inhalation/skin uptake, grass-to-cow transfers, and grass HTO/OBT Eq. (105-1)-(105-2).
- Decision: added a separate opt-in `src/cteas_ufotri/foodchain/ufotri_cow_milk_beef_v4.py` activity-conserving compatibility path. Eq. (98) is an explicit animal atmosphere-column input and is not public dose. Manual rounded transfer rates are retained as written rather than renormalized to Eq. (82)/(92) half-time summaries. Eq. (86) OCR-heading ambiguity is retained, with `cow OBT -> milk OBT` selected from compartment indices, surrounding prose and the milk-production balance. Eq. (105-2) closes literally as `0.069-(0.0033+0.021+0.0017)=0.043 d^-1`. Project feed/drinking-water, support-area, edible-beef-mass and continuous herd-turnover assumptions are not activated. Explicit slaughter-to-beef is a caller-declared activity-conservation boundary only, not a recovered original algorithm.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/foodchain/ufotri_cow_milk_beef_v4.py`; D4 also added one machine script, one pytest file, ADR-069, governance YAML and report. No existing V2/RC1/D3/V4 integration, public-dose, roadmap or workflow file changed in PR #78.
- Numerical closure: Eq. (98) exact geometry (`4.875e-5 d^-1`) and manual-rounded value (`4.9e-5 d^-1`) are both visible; Eq. (82)/(92) rounded-rate tensions remain explicit; Eq. (105-2) identity closes; grass OBT receiver routes, milk HTO/OBT receivers, Eq. (83)/(84) external-boundary activity conservation, deterministic repeat, restart equivalence, hourly partition equivalence, timestep refinement (`3600→1800→900→450 s` toward `225 s`), zero-inventory stability, explicit slaughter-to-beef activity conservation, and fail-closed project feed/drinking-water and invalid-input checks all pass.
- PR: `#78`
- Certified head: `e5409ce264e1dfd71cd4246dc88f477cc4a6e074`
- Certified tree: `937104b21aa22a552e6b77d12d492d2ea0038b0e`
- Remediation CI: `33154304997` (#208) — `SUCCESS`
- Protected CI: `33154305054` (#219) — `SUCCESS`
- Protected merge-ref: `b70d3f3cc993ad2ab023d32a4dd3bbd7ac976eb9`
- Validation: portable `1560 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `27f057474b750e299e2e5234f73552df5b06d558`
- Merge tree: `937104b21aa22a552e6b77d12d492d2ea0038b0e`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `7f51cca82342601364e1cc074602e44c09554a83` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: public Eq. (106)-(107) inhalation/skin/ingestion exposure reconciliation remains D5. Production animal parameters, calibration, empirical validation and original-executable equivalence remain outside D4's claim.
- Next stage: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`.
- Scope claim: `UFOTRI_COW_MILK_BEEF_COMPARTMENT_CLOSURE=COMPLETE`.
- Non-claims: no public exposure completion; no project feed 50 kg/day, drinking water 50 L/day, 4000 m²/animal support area, 200 kg/head edible beef or `0.002 d^-1` continuous herd-turnover activation; no production parameter activation, calibration, empirical validation, physical-accuracy/production-readiness claim, real CTEAS-Atmos binding, recovered original numerical discretization or original-executable equivalence.

#### D5. Inhalation/skin/ingestion exposure reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Dependency: D1-D4.
- Manual anchor: KfK 4605 Section 4 and Eq. (106)-(107), including HTO inhalation with 50% skin absorption, QF=1, representative green-vegetable/beef/milk ingestion, and the historical treatment of ingested OBT with the selected HTO dose coefficient.
- Decision: added a separate opt-in `src/cteas_ufotri/dose/ufotri_manual_v4.py` manual-fidelity exposure path while leaving the retained modern `dose.public` application path unchanged. Eq. (106) is reconstructed literally as inhalation plus 50% skin absorption. Eq. (107) contains only green vegetable, beef and milk. HTO/OBT food activities remain separately visible upstream and are summed only before applying one selected manual coefficient. The named adult-reference helper exposes `1.7e-11 Sv/Bq`, but coefficient selection, breathing and consumption habits remain explicit/provenanced inputs. No implicit milk litre-to-kilogram conversion is performed.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/dose/ufotri_manual_v4.py`; D5 also added one machine script, one pytest file, ADR-070, governance YAML and report. No existing `dose.public`, V2/RC1, D3/D4, V4 integration, roadmap or workflow file changed in PR #80.
- Numerical/policy closure: Eq. (106) inhalation identity, skin=`0.5×inhalation`, total `1.5` multiplier and residual closure; Eq. (107) exact three-food identity and residual closure; separate upstream HTO/OBT diagnostics with the same selected manual dose coefficient; deterministic repeat; one-day versus 24-hourly and 96-quarter-hour exposure partition equivalence; zero-exposure zero-dose; controlled distinction between manual adult reference `1.7e-11 Sv/Bq` and retained modern adult HPA HTO `1.8e-11 Sv/Bq`; retention of the modern separate OBT ingestion coefficient; and fail-closed invalid timestep/concentration/policy/habit inputs all pass.
- PR: `#80`
- Certified head: `e34c41934b89e1e2d9af0b112e6a6a93033d5b22`
- Certified tree: `5a4a3905814a8ed9c51c1992aad2a247a8ccf356`
- Remediation CI: `33174142590` (#210) — `SUCCESS`
- Protected CI: `33174142585` (#221) — `SUCCESS`
- Protected merge-ref: `f80549ef2c439c3f431b25264bd3849cefbf5a46`
- Validation: portable `1576 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`. D5-specific Eq. (106)/(107), policy-boundary, partition-additivity and fail-closed assertions pass inside the portable suite.
- Merge SHA: `1ff801e5b9b118b5bac47eef4137301aa26fdf89`
- Merge tree: `5a4a3905814a8ed9c51c1992aad2a247a8ccf356`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `a888055ea9908e6d23cd5b06ca8c60b61c19dad9` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: `NONE_WITHIN_PHASE_D_FOOD_CHAIN_AND_EXPOSURE` for the recoverable manual-based food-chain/exposure semantics. Production exposure habits/coefficients, calibration, empirical validation and modern application policy remain separate and are not reclassified as original UFOTRI behavior.
- Next stage: `UFOTRI_HT_BRANCH_RECONCILIATION_R1`.
- Scope claim: `UFOTRI_INHALATION_SKIN_INGESTION_EXPOSURE_RECONCILIATION=COMPLETE`.
- Non-claims: no production exposure parameter activation, no project breathing/consumption habits promoted to recovered UFOTRI defaults, no modern HPA coefficient relabeling, no separate OBT dose coefficient relabeled as original UFOTRI behavior, no drinking-water/root-crop/grain addition to manual Eq. (107), no calibration, empirical validation, physical-accuracy/production-readiness claim, real CTEAS-Atmos binding or original-executable equivalence.

---

### Phase E — HT branch and HT→HTO environmental reconstruction

- Phase status: `IN_PROGRESS`
- Internal reconstruction status: `E1_E2_E3_COMPLETE`; E4/E5 remain `DEFERRED_EXTERNAL_DEPENDENCY` and therefore Phase E is not marked globally complete.

**HT is part of the replication target and is not omitted from this roadmap.**

The branch is split so that internal HT environmental mechanisms can progress independently, while real atmospheric transport remains deferred until CTEAS-Atmos is ready.

#### E1. HT branch contract and manual mapping

- Status: `COMPLETE`
- Stage: `UFOTRI_HT_BRANCH_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Manual anchor: KfK 4605 introduction/dispersion-module description and Section 2.2.3 soil/atmosphere exchange semantics, including explicit HT/T2 versus HTO chemical-form separation, soil/moisture dependence of HT deposition, rapid microorganism-mediated HT→HTO conversion after deposition, and benchmark HT/HTO deposition/diffusion/oxidation values.
- Decision: added a separate opt-in typed `src/cteas_ufotri/coupling/ht_v4.py` contract. `AtmosphericHTForcing` is distinct from the existing HTO forcing type; HT/T2 concentration is `Bq m-3`, surface HT deposition flux is `Bq m-2 s-1`, and interval-integrated deposited HT is `Bq m-2`. E1 preserves deposited material as chemically HT and creates zero HTO; E2 exclusively owns HT→HTO soil conversion. Synthetic/replay HT forcing is accepted, while real CTEAS-Atmos HT binding fails closed until E4. KfK benchmark values (`v_d,HT=0.05 cm/s`, atmospheric oxidation `0.5%/d`, HT soil diffusion `5.0e-2 cm2/s`, plus corresponding HTO benchmark values) remain evidence-visible but are not activated as global/production defaults.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/coupling/ht_v4.py`; E1 also added one machine script, one pytest file, ADR-071, governance YAML and report. No existing HTO/V2/RC1/V4 integration, roadmap or workflow file changed in PR #82.
- Contract/numerical closure: explicit HT/T2 species and rejection of HTO/DT/total-tritium aliases; exact unit contracts; UTC interval validation; finite/non-negative inputs; deposition-flux time integration; four-interval partition equivalence; HT chemical-identity preservation at the soil boundary; zero E1 HTO creation; explicit E1/E2/E3/E4 ownership; distinct HT/HTO forcing fields/types; benchmark evidence visibility without activation; and fail-closed real Atmos binding all pass.
- PR: `#82`
- Certified head: `762e9b9b5cdd0f12610fa73b0e1c2d590585553c`
- Certified tree: `3aed0b8d8f62800fe18013763e54d5d4296357a6`
- Remediation CI: `33178907829` (#216) — `SUCCESS`
- Protected CI: `33178907771` (#227) — `SUCCESS`
- Protected merge-ref: `e109525ae7fc5f38de1f68a5e6034c7fa21b8090`
- Validation: portable `1597 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `a71a6859f10413038b642009081ea5c730e0a2c3`
- Merge tree: `3aed0b8d8f62800fe18013763e54d5d4296357a6`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `34ee72b061f393ae082e93df5d60f7f89c01cf34` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: E2 must reconstruct the soil HT→HTO conversion/oxidation mechanism and conservation ledger; E3 secondary HTO re-emission and E4 real CTEAS-Atmos HT binding remain separate later scopes.
- Next stage: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`.
- Scope claim: `UFOTRI_HT_BRANCH_RECONCILIATION=COMPLETE`.
- Non-claims: no HT→HTO conversion implementation, no HT-derived HTO re-emission, no real HT transport/binding, no benchmark parameter production activation, no calibration, empirical validation, physical-accuracy/production-readiness claim, original numerical-discretization recovery or original-executable equivalence.

#### E2. HT→HTO soil conversion/oxidation reconstruction

- Status: `COMPLETE`
- Stage: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION_R1`
- Replication requirement: `REQUIRED`
- Dependency: E1.
- Manual anchor: KfK 4605 secondary-model soil balances Eq. (1)-(2) plus Section 2.2.3 soil/atmosphere exchange. The soil state is HTO; atmospheric HT contributes directly through the effective deposition term, while deposited HT is described as being transformed very rapidly by microorganism activity and only the transformed part remains in soil.
- Decision: added the isolated opt-in `src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py` compatibility path. E2 consumes the reviewed E1 `HTSoilDepositionBoundary` and maps the accepted deposited HT activity directly to soil HTO on a 1:1 activity basis. No independent soil-HT kinetic pool, microbial half-time, generic oxidation rate, or tunable conversion fraction is invented. Generated HTO is added to, not substituted for, primary HTO in the existing `ThreeLayerSoilForcing.surface_deposition_flux_bq_m2_s`; the projection keeps primary HTO, HT-derived HTO, combined HTO and upstream HT/T2 provenance separately visible.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/coupling/ht_to_hto_soil_v4.py`; E2 also added one machine script, one pytest file, ADR-072, governance YAML and report. No existing E1, HTO, soil/hydrology/root/TFWT/OBT, V2/RC1/V4 integration, roadmap or workflow file changed in PR #84.
- Conservation/numerical closure: exact `HT input - generated HTO - residual HT = 0`; generated HTO equals accepted deposited HT and residual independent soil HT is zero; generated flux integrates to the generated amount; one-hour versus four-quarter-hour partition additivity; explicit HT/T2 provenance retention; additive primary-HTO + HT-derived-HTO projection; existing L1 soil HTO inventory/global-balance integration; zero direct L2/L3 injection; benchmark non-activation; absence of atmospheric HT oxidation and E3 re-emission; and fail-closed type/time/interval contracts all pass.
- PR: `#84`
- Certified head: `4c2011bbe7d6c39503edbe1f8c4c3a09d4fcbc25`
- Certified tree: `7f547ba0d5d44a3bd67b867ff5ed8704cc5fdd04`
- Remediation CI: `33182342401` (#218) — `SUCCESS`
- Protected CI: `33182342345` (#229) — `SUCCESS`
- Validation: portable `1612 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `5c35aa95c61d221b73f4df0da698b9e5ea1c747e`
- Merge tree: `7f547ba0d5d44a3bd67b867ff5ed8704cc5fdd04`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `e6b9b1769a29bf0c0ede922892a057fe729cbb48` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: E3 must reconcile HT-derived HTO re-emission/secondary-feedback ownership and provenance without double counting. E4 real CTEAS-Atmos HT binding remains a separate deferred external dependency.
- Next stage: `UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1`.
- Scope claim: `UFOTRI_HT_TO_HTO_SOIL_CONVERSION=COMPLETE`.
- Non-claims: no E3 secondary HTO re-emission completion, no atmospheric HT oxidation, no real HT atmospheric binding, no production benchmark parameter activation, no calibration, empirical validation, physical-accuracy/production-readiness claim, original numerical-discretization recovery or original-executable equivalence.

#### E3. HT-derived HTO re-emission and secondary-feedback reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Dependency: E2.
- Manual anchor: KfK 4605 plant Eq. (27)-(31) exchange/re-emission, Section 2.2.3 soil/atmosphere exchange and topsoil-only direct soil re-emission role, Eq. (38)-(44) soil re-emission terminology, and the Eq. (4) secondary area-source role.
- Decision: reconciliation-only closure with `NO_EXISTING_SOURCE_CHANGE`. Existing Phase-A signed leaf exchange owns the recoverable plant release role and the V4 three-layer soil core owns the explicit L1 `surface_reemission_hto_loss_bq_m2_s` inventory-loss boundary. Historical V1/V2 delayed area-source/point-equivalent feedback is retained only as topology evidence and is not activated. The historical Eq. (44) engineering reconstruction remains provisional/source-limited. After primary and HT-derived HTO are aggregated in the current soil/plant inventories, later aggregate re-emission may not be labeled `HT_DERIVED_HTO` without explicit origin proof; mixed/unresolved origin must remain explicit and silent proportional source splitting is forbidden.
- Activity/provenance closure: re-emission is first an environmental inventory loss. A later atmospheric secondary-source adapter may consume the same accounted activity as source handoff but must not create a second environmental activity term. E2's primary/HT-derived input provenance remains visible before soil aggregation; the current aggregate soil/TFWT state is not falsely treated as origin-resolved. Phase F retains source geometry, emission height, delay/time discretization, area-source/equivalent representation, provenance-aware adapter implementation and any origin-aware sidecar required for auditable HT-derived attribution.
- Changed source files: `NO_EXISTING_SOURCE_CHANGE`; E3 added only `scripts/v4/check_ufotri_ht_derived_hto_reemission_secondary_feedback_reconciliation_r1.py`, `tests/v4/test_ufotri_ht_derived_hto_reemission_secondary_feedback_reconciliation_r1.py`, ADR-073, governance YAML and report. Existing source, workflow and roadmap files were unchanged in PR #86.
- Qualification: manual topsoil/plant roles, Eq. (44) source limits, historical delayed-feedback topology, aggregate-feedback non-promotion, V4 L1 re-emission sink reuse, Phase-A signed leaf-release reuse, E2 pre-aggregation provenance, post-aggregation HT-derived fail-closed attribution, mixed-origin policy, Phase-F numerical ownership and no-source-change assertions all pass.
- PR: `#86`
- Certified head: `3214741fbb77ef0b1189aa8b25d258bdf48eb3c1`
- Certified tree: `571029e887fea7672020a40785a34793ed9ff7a5`
- Remediation CI: `33186224164` (#220) — `SUCCESS`
- Protected CI: `33186224152` (#231) — `SUCCESS`
- Validation: portable `1619 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `ef11dc4d90478aa4ee3fc1dabefd1cb99a4d2d3d`
- Merge tree: `571029e887fea7672020a40785a34793ed9ff7a5`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `29102a20fc69ebe3bc3226482c62f363f3976c41` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: Phase F must implement/reconcile the provenance-aware secondary atmospheric source adapter and the recoverable re-emission/area-source numerical compatibility boundary. Complete Eq. (44) rate recovery remains source-limited rather than silently invented. E4/E5 real CTEAS-Atmos dependencies remain separately deferred.
- Next stage: `UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1`.
- Scope claim: `UFOTRI_HT_DERIVED_HTO_REEMISSION_SECONDARY_FEEDBACK_RECONCILIATION=COMPLETE`.
- Non-claims: no complete Eq. (44) numerical recovery, no origin-resolved environmental tracer, no Phase-F area-source implementation, no real CTEAS-Atmos binding, no production parameter activation, no calibration, empirical validation, physical-accuracy/production-readiness claim, recovered original numerical discretization or original-executable equivalence.

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

- Phase status: `COMPLETE`
- Scope claim: `UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION=COMPLETE` under controlled synthetic/replay/manual-compatible forcing only.

#### F1. Re-emission/area-source reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_REEMISSION_AREA_SOURCE_RECONCILIATION_R1`
- Replication requirement: `REQUIRED`
- Dependency: E3.
- Manual anchor: KfK 4605 Section 2.2.1 Eq. (4)-(6), including rectangular area-source semantics, selected centre-point representation, Eq. (5) initial lateral widening, Eq. (6) reduced-time Gaussian concentration, common soil/plant source height and hour-N→hour-N+1 secondary-model cadence.
- Decision: added an isolated opt-in `src/cteas_ufotri/coupling/reemission_area_source_v4.py` compatibility adapter while leaving historical `case.py`, `config.py`, legacy Gaussian functions and default YAML unchanged. The same activity already accounted as an environmental soil/plant re-emission loss is handed to the secondary atmospheric source with an explicit `environmental_loss = routed + unrouted` ledger. Soil and plant remain distinct source channels until concentration superposition. Eq. (5) uses `sigma_y0=width/4.3`; the visible printed Eq. (6) is reproduced literally with `sigma_y*sigma_z` in the denominator and `sigma_yg` only in the lateral exponential, without claiming that this proves the unavailable original-executable normalization. Phase-A `max(0.8H,1m)` source-height semantics are reused; fallout/washout factors remain explicit. Hourly handoff accumulates activity over exactly 3600 s and exposes it in the following source hour for time steps that exactly divide one hour. `HT_DERIVED_HTO` attribution requires explicit origin proof; mixed origin remains fail closed.
- Changed source files: one new opt-in source file, `src/cteas_ufotri/coupling/reemission_area_source_v4.py`; F1 also added one machine script, one pytest file, ADR-074, governance YAML and report. No pre-existing source/default/roadmap/workflow file changed in PR #89.
- Qualification: printed Eq. (5)/(6) identities, minimum/common source height, explicit fallout/washout factors, soil/plant separate-source superposition, first-hour-zero and hour-N→N+1 timing, 300 s/600 s timestep activity invariance, environmental-loss/source-handoff ledger closure, mixed-origin preservation, explicit HT-derived provenance proof, invalid-input fail-closed behavior and legacy/default non-promotion all pass.
- PR: `#89` (`#88` was closed unmerged only because the connector draft→Ready mutation was schema-incompatible; the candidate was unchanged and #89 independently reran exact-head CI).
- Certified head: `a971814ccda46246268e9398d9ca58790413d224`
- Certified tree: `44ac94944fbe87a9d9131e74cf0358b5c9635aaa`
- Remediation CI: `33222301744` (#227) — `SUCCESS`
- Protected CI: `33222301754` (#238) — `SUCCESS`
- Validation: portable `1628 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `43b1b0d09fe1c6a041a88b0448a784c4603c1570`
- Merge tree: `44ac94944fbe87a9d9131e74cf0358b5c9635aaa`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `e1a3f1ffd94ee91daf5385d21f1076d1d549e630` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: `NONE_WITHIN_PHASE_F_REEMISSION_AREA_SOURCE_COMPATIBILITY` for the recoverable internal/manual-compatible handoff and area-source semantics. Complete Eq. (44) rate recovery remains source-limited; E4/E5 real CTEAS-Atmos dependencies remain deferred; benchmark validation remains Phase G.
- Next stage: `UFOTRI_CANADA_1987_BENCHMARK_RECONSTRUCTION_R1`.
- Non-claims: no complete Eq. (44) recovery, no real CTEAS-Atmos binding, no empirical benchmark validation yet, no production parameter activation, no physical-accuracy/production-readiness claim and no original MUSEMET/ISOLA/UFOTRI executable equivalence.

---

### Phase G — UFOTRI benchmark reconstruction and final replication gate

#### G1. Canada 1987 benchmark reconstruction

- Status: `COMPLETE`
- Stage: `UFOTRI_CANADA_1987_BENCHMARK_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED_AS_VALIDATION`
- Manual anchor: KfK 4605 Section 5.2 and Figures 21-28.
- Decision: source-limited benchmark-contract reconstruction only. Recoverable static inputs, eight observable families, unit conversions, qualitative historical comparison intent, Figure 28 `175 m` prose versus `180 m` caption/TOC ambiguity, and replay blockers are frozen without inventing missing values. Markdown chart-helper values are not promoted to authoritative raw measured/calculated arrays.
- Changed source files: `NO_PRODUCTION_SOURCE_CHANGE`; G1 added ADR-075, governance/report artifacts, one machine gate and one focused pytest file. No `src/`, default, workflow or roadmap file changed in PR #91.
- PR: `#91`
- Certified head: `5cff21a0b3e7e1cb46592602662c767d9d5ace4e`
- Certified tree: `60712fdf32231af8c5cd5e28882bd1894ed53561`
- Remediation CI: `33286810982` (#234) — `SUCCESS`
- Protected CI: `33286810988` (#245) — `SUCCESS`
- Protected merge-ref: `d306b99eaef94275ac9729afffdd3e3cf8d6a50c`
- Validation: `PASS_SOURCE_LIMITED_CANADA_1987_BENCHMARK_RECONSTRUCTION`; portable `1634 passed, 1 skipped, 57 deselected, 1 warning`; frozen/current-boundary `375 passed`; sensitivity screening `PASS_SOFTWARE_SCREENING`; root split `PASS_SELECTION`; soil-root-TFWT-OBT `PASS_INTEGRATION`; replay orchestration `PASS_REPLAY_ORCHESTRATION_SOFTWARE_INTEGRATION`; food/intake/dose adapter `PASS_FOOD_INTAKE_DOSE_ADAPTER_SOFTWARE_INTEGRATION`.
- Merge SHA: `6101346f18b87faafb55417e03b08a4f911148ac`
- Merge tree: `60712fdf32231af8c5cd5e28882bd1894ed53561`
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `9b1d6ff34b7306175601e9257fdddf393a4e8d3c` and the certified head; certified-head tree equals merge tree; remote `main` equals the merge SHA.
- Remaining gap: Canada 1987 full numerical replay and empirical validation remain source-limited by the absent underlying reference /44 raw report/data, hourly meteorology, exact release-clock alignment, hourly precipitation allocation, authoritative measured/calculated series, Canada-specific sigma numerical provenance, complete Eq. (44) recovery and original/real atmospheric numerical binding. `CANADA_1987_FULL_NUMERIC_REPLAY_READY=FALSE` and `CANADA_1987_EMPIRICAL_VALIDATION_COMPLETE=FALSE` remain explicit.
- Next stage: `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`.
- Non-claims: no Canada empirical reproduction, no pointwise RMSE from chart transcription, no production-readiness/physical-accuracy claim and no original MUSEMET/UFOTRI executable equivalence.

#### G2. ITER benchmark reconstruction

- Status: `NOT_STARTED`
- Stage: `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`
- Replication requirement: `REQUIRED_AS_VALIDATION`
- Goal: reproduce the recoverable ITER comparison/benchmark case described or referenced by the manual/evidence set, preserving case distinctions and source ambiguities instead of flattening them into one assumed scenario.

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

1. `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`
2. deferred real HT/HTO Atmos reconciliation when CTEAS-Atmos is ready
3. final cross-module fidelity qualification
4. `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE` gate

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

- [x] V2 continuous food-chain reconciliation — PR #72, merge `1d09f65efb5bff70b65c9b4adfa41b2c09604739`, no-drift PASS
- [x] Pasture 40/60/0 root profile — PR #74, merge `c849f3d328c6d59c73fb1d1de85bff57dc5ec1ce`, no-drift PASS
- [x] Vegetable/grass closure — PR #76, merge `238bbcbc82f5c417dc33663bd47695f6b20426ed`, no-drift PASS
- [x] Cow/milk/beef closure — PR #78, merge `27f057474b750e299e2e5234f73552df5b06d558`, no-drift PASS
- [x] Inhalation/skin/ingestion exposure reconciliation — PR #80, merge `1ff801e5b9b118b5bac47eef4137301aa26fdf89`, no-drift PASS

### HT and secondary HTO

- [x] HT branch contract/manual mapping — PR #82, merge `a71a6859f10413038b642009081ea5c730e0a2c3`, no-drift PASS
- [x] HT→HTO soil conversion — PR #84, merge `5c35aa95c61d221b73f4df0da698b9e5ea1c747e`, no-drift PASS
- [x] HT-derived HTO re-emission/secondary feedback — PR #86, merge `ef11dc4d90478aa4ee3fc1dabefd1cb99a4d2d3d`, no-drift PASS
- [x] Re-emission/area-source compatibility — PR #89, merge `43b1b0d09fe1c6a041a88b0448a784c4603c1570`, no-drift PASS
- [ ] Real HT atmospheric transport / CTEAS-Atmos binding — deferred external dependency
- [ ] End-to-end HT→HTO compatibility with real Atmos — deferred external dependency

### Benchmarks / final gate

- [x] Canada 1987 benchmark contract reconstruction — PR #91, merge `6101346f18b87faafb55417e03b08a4f911148ac`, no-drift PASS; full numerical/empirical replay remains source-limited
- [ ] ITER benchmark — `UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`
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

`UFOTRI_ITER_BENCHMARK_RECONSTRUCTION_R1`

G1 is complete as a source-limited benchmark-contract reconstruction under exact-head CI and merge/no-drift evidence. The recoverable Canada static inputs, eight observable families, qualitative historical comparison objective, unit conversions and Figure 28 175/180 m ambiguity are now frozen without promoting chart-helper values or invented inputs to ground truth. Canada full numerical replay remains explicitly not ready because eight primary/source/numerical blockers remain unresolved; this does not erase the required benchmark obligation or imply empirical validation. G2 is now authorized to reconstruct the ITER benchmark from the manual's Section 5.3/Appendix B evidence while preserving the distinct HT/HTO, stability, wind, mixing-layer, release-height/building-wake and model-comparison cases. Real CTEAS-Atmos HT/HTO binding remains deferred, complete Eq. (44) rate recovery remains source-limited, and `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE` remains unchanged.