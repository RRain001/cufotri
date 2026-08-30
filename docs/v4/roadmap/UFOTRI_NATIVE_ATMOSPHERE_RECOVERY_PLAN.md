# UFOTRI Native Atmosphere Recovery Plan

Status: `POST_G4_AUTHORITATIVE_CORRECTION_ACTIVE`

Authority date: 2026-08-30

Base after H1 merge: `main@1962da0e360aa7eec760f5f4c298c65df8eb4d37`

## 1. Purpose and precedence

This document is the authoritative post-G4 correction to the atmospheric portion of `UFOTRI_REPLICATION_MASTER_PLAN.md`.

The historical master plan remains the record of why G4 was previously closed. A later architecture/source review demonstrated that one recoverable internal mechanism had been incorrectly classified as wholly external: UFOTRI's own primary atmospheric dispersion model based on modified MUSEMET.

Where the historical master plan states any of the following, this later correction supersedes that statement for current work:

- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE` as a current whole-model status;
- `NO_IMMEDIATE_INTERNAL_REPLICATION_STAGE`;
- all primary HT/HTO atmospheric transport is owned by CTEAS-Atmos;
- E4 is the only route by which real atmospheric HT/HTO transport can enter the replication sequence.

Historical G4 evidence is not deleted or rewritten. It remains valid for the scope that G4 actually audited. The current whole-model claim was reopened until the UFOTRI-native atmospheric sequence below was closed by H6 R2.

Current state:

- `V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE=TRUE`
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`
- `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`
- `CTEAS_ATMOS_BACKEND=DEFERRED_OPTIONAL_HIGHER_FIDELITY_BACKEND`

## 2. Corrected architecture

Standalone fidelity route:

`UFOTRI source term`
→ `UFOTRI-native MUSEMET/Gaussian primary atmosphere`
→ `HT / HTO air concentrations and deposition`
→ `HT soil deposition → HT→HTO soil conversion`
→ `three-layer soil HTO`
→ `root uptake + leaf exchange`
→ `TFWT`
→ `OBT`
→ `vegetable/grass/cow/milk/beef`
→ `inhalation + skin + ingestion dose`

Secondary feedback remains:

`soil/plant HTO re-emission`
→ `UFOTRI area-source secondary atmosphere`
→ downstream environmental chain.

Future optional backend route:

`CTEAS-Atmos HT/HTO products`
→ `typed backend adapter`
→ same UFOTRI environmental interfaces.

CTEAS-Atmos must not be required to execute or qualify the standalone UFOTRI-native route.

## 3. Atmospheric HT→HTO chemical boundary

KfK 4605 Section 2.2 explicitly states that atmospheric conversion of tritium gas to HTO is not included in the program because conversion is slow. Appendix B separately prints an ITER input `Oxidation rate in air = 0.5 %/d`.

The KfK 4605 fidelity route therefore freezes:

`ATMOSPHERIC_HT_TO_HTO_CONVERSION=DISABLED`

and preserves `0.5 %/d` only as conflicting benchmark/version evidence.

This must not be confused with soil conversion:

`SOIL_HT_TO_HTO_CONVERSION=COMPLETE`

from the already-merged E2 stage.

If a later authoritative UFOTRI version proves that atmospheric oxidation became active, that behavior must be implemented as a separately versioned compatibility option rather than retroactively changing the KfK 4605 path.

## 4. Native atmosphere sequence

### H1 — Native primary atmosphere core

- Status: `COMPLETE`
- Stage: `UFOTRI_NATIVE_PRIMARY_ATMOSPHERE_CORE_R1`
- PR: `#100`
- Certified head: `728728067640e692e57f7a9875e390706517982a`
- Merge SHA: `1962da0e360aa7eec760f5f4c298c65df8eb4d37`
- Merge tree: `e15bd6d5613652e567925f1679e6efdce92bdda4`
- Exact-head Remediation CI: `33299247438` — `SUCCESS`
- Exact-head Protected CI: `33299247451` — `SUCCESS`
- Protected synthetic merge-ref: `c3221eac1d45c50bec1488ac5f263f20ae274717`
- Portable suite: `1667 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- No-drift: `MERGE_TREE_DRIFT=FALSE`
- Recovered: typed HT/HTO, exact Mol A-F coefficients, sigma power laws, `sigma_z<=0.8h`, wind-height power law, straight-segment Gaussian role, <=1h release slicing, species-specific dry deposition, HT wet-deposition fail-closed, explicit HTO washout input, source-depletion ledger, atmospheric oxidation conflict preservation.
- Source boundary: original MUSEMET source-depletion discretisation not yet claimed recovered.
- Next stage: `UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`.

### H2 — Hourly bent/segmented MUSEMET trajectory

- Status: `COMPLETE`
- Stage: `UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`
- PR: `#102`
- Certified head: `f39d8491ba4b5335d9d7a5a6170d96ec9c51dc31`
- Certified tree: `0449a206422b2012d567c0dded99e0ce67824ae6`
- Merge SHA: `5e1d079a75ee1b58657b5804331a308c6aea298a`
- Merge tree: `0449a206422b2012d567c0dded99e0ce67824ae6`
- Exact-head Remediation CI: `33301029851` (#254) — `SUCCESS`
- Exact-head Protected CI: `33301029855` (#265) — `SUCCESS`
- Protected synthetic merge-ref: `9a76d90ba63e63da8d19122681e48685d046f47c`
- Portable suite: `1680 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- Validation: `PASS_UFOTRI_NATIVE_HOURLY_TRAJECTORY`; one trajectory starts at each hourly source time; later winds bend only subsequent straight segments; per-segment stability/precipitation/mixing-layer state is retained; meteorological FROM direction is converted explicitly to the downwind TO vector; radial source-distance and travel-time termination, deterministic restart and rigid coordinate-frame invariance are qualified.
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `e36288b7423892119d0027b848e647af6e3cc2f5` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA.
- Non-claims: no multiple-puff substitution, no spatially varying meteorology, no CTEAS-Atmos wind field, no H3 forcing adapter, no H4 process closure and no original MUSEMET numerical equivalence.
- Next stage: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`.

### H3 — Native HT/HTO environmental forcing adapters

- Status: `COMPLETE`
- Stage: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`
- PR: `#104`
- Certified head: `db9b97c56f98bb6c5c2340bb1ed5edde6dcea114`
- Certified tree: `8bb9ada4dfc3c1599d0efbcee265b55a8c648fa8`
- Merge SHA: `c64f377f779253099a12583e90b6a92cc03e01af`
- Merge tree: `8bb9ada4dfc3c1599d0efbcee265b55a8c648fa8`
- Exact-head Remediation CI: `33302177645` (#256) — `SUCCESS`
- Exact-head Protected CI: `33302177603` (#267) — `SUCCESS`
- Protected synthetic merge-ref: `af3e61df921e9a5a4a1d16f619e5ab6d5e9eccef`
- Portable suite: `1692 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- Validation: `PASS_UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER`; native HT is mapped to the existing E1 HT contract with explicit `UFOTRI_NATIVE` provenance and then through the existing E2 soil HT→HTO conversion; native HTO is mapped into the existing P7 HTO forcing; interval, units, spatial support and provenance remain explicit; source-depletion and E2 activity ledgers close.
- Wet-deposition boundary: H1 wet source loss remains a plume/source ledger term in Bq/s and is not relabelled as a local Bq m^-2 s^-1 flux; a local wet surface flux must be supplied explicitly when wet source loss is nonzero.
- Chemical boundary: atmospheric HT→HTO remains disabled for the KfK 4605 route; crossed HT/HTO adapters and generated atmospheric HTO fail closed; `REAL_CTEAS_ATMOS` remains fail-closed and distinct from `UFOTRI_NATIVE`.
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `297bd85500f268cc0114f9f41b3904a8a66ca5ee` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA.
- Non-claims: no H4 washout-parameter recovery, source-depletion reconstruction, building-wake or thermal-lift equivalence, CTEAS-Atmos binding, production parameter activation, calibration, empirical validation, or original executable numerical equivalence.
- Next stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`.

### H4 — Atmospheric-process reconciliation

- Status: `COMPLETE`
- Stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`
- PR: `#106`
- Certified head: `3ca2e6ae152d7d1fe2e3cbd17f4a5dca49514c54`
- Certified tree: `6c21213961b586c8057815b840d7df008fb0238b`
- Merge SHA: `caa36cd56222cad739bc0ca264d74db5463b4b2a`
- Merge tree: `6c21213961b586c8057815b840d7df008fb0238b`
- Exact-head Remediation CI: `33303660781` (#258) — `SUCCESS`
- Exact-head Protected CI: `33303660733` (#269) — `SUCCESS`
- Protected synthetic merge-ref: `c4be3edc1c924981f3265f6d301989da0814ccce`
- Portable suite: `1704 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- Validation: `PASS_UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION`; KfK 4332 Eq. (2.20) dry source depletion is reconstructed by direct-equation deterministic regularised quadrature, Eq. (2.27) wet depletion is applied multiplicatively, and the H4+ authoritative transport is `transport_straight_segment_reconciled` while the H1 controlled approximation remains historical evidence only.
- KfK 5194 washout: `IWASH=0` recovers the HTO classes `6e-5/1e-4/4e-4 s^-1` with `REGTIM=0.5/0.75/0.72`; `IWASH=1` recovers `lambda=9e-5*I^0.6`; HT wet deposition remains zero.
- Source-limited boundaries: the `IWASH=1` power-law `REGTIM` numeric default is not invented; `Lp>30` lift-off semantics are preserved but Eq. (3.22) numerical evaluation remains source-limited because the recovered rendering is OCR-ambiguous; complete building-wake and `PLRISE/RISEFX` plume-rise numerics remain source-limited. No Briggs/AERMOD/CALPUFF/CTEAS-Atmos surrogate is inserted.
- Chemical boundary: atmospheric HT→HTO remains disabled for the KfK 4605 route.
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `85adef07d15cd319384db41ed8668dcd59e9832a` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA.
- Non-claims: no original MUSEMET closed-form three-case numerical equivalence, numeric Eq. (3.22) equivalence, complete building-wake/plume-rise equivalence, CTEAS-Atmos binding, production parameter activation, calibration, empirical validation, or original executable numerical equivalence.
- Next stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`.

### H5 — Native atmosphere → environmental chain → dose qualification

- Status: `COMPLETE`
- Stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`
- PR: `#108`
- Certified head: `42aceec5328895ad80eac9b9840b7828371837d9`
- Certified tree: `3737dc663bc93d7258a7715fb5199867d32c0dba`
- Merge SHA: `e23896e0bfcb94582a5226d56df6073582d167e5`
- Merge tree: `3737dc663bc93d7258a7715fb5199867d32c0dba`
- Exact-head Remediation CI: `33306266651` (#261) — `SUCCESS`
- Exact-head Protected CI: `33306266650` (#272) — `SUCCESS`
- Protected synthetic merge-ref: `267fe7e7499d652846083ab38dcf6a1c9f96d678`
- Portable suite: `1708 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- Validation: `PASS_UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION`; the H4 reconciled native atmosphere is composed through the H3 forcing adapters and E2 deposited-HT→soil-HTO conversion into the existing soil/root/leaf/TFWT/OBT orchestration, then through the recovered food and Eq. (106)/(107) exposure paths.
- Conservation/restart: primary HTO and HT-derived HTO origins remain explicit pre-aggregation; atmospheric and E2 ledgers close; deterministic repeat, restart, interval partition, secondary-hour routing and exposure partition checks pass; F1 re-emission is handed off only after the environmental loss is accounted and is not double counted.
- Wet-deposition boundary: plume wet source loss remains distinct from local surface wet flux; the controlled H5 wet case supplies an explicit local qualification flux rather than inferring spatial closure.
- Leaf boundary: A-stage manual Eq. (27)-(30) transfer is independently cross-checked, but the replay leaf operator is not claimed numerically identical to the original interval discretisation; the original Monin-Obukhov estimator remains unrecovered.
- Benchmark boundary: Canada and ITER benchmark contracts are requalified only within their existing source-limited/reference scopes; no full numerical or empirical replay is claimed.
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `7a70c49dde2edcb54adc0b826c4a6d99ba0e5ada` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA.
- Non-claims: no original UFOTRI leaf-discretisation identity, original Monin-Obukhov estimator, plume-wet-loss/local-flux spatial equivalence, origin-resolved mixed soil HTO, complete building-wake/plume-rise equivalence, Canada empirical reproduction, ITER full atmospheric replay, CTEAS-Atmos binding, production parameter activation, calibration, empirical validation, physical-accuracy claim, or original executable numerical equivalence.
- Next stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`.

### H6 — Corrected final reconstruction gate

- Status: `COMPLETE`
- Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`
- PR: `#110`
- Certified head: `c5e4951d75445b74347a89be1f4368f89cca75dc`
- Certified tree: `170e600bef80794d636a62b113d8fbd9ba44124a`
- Merge SHA: `0cdaaa4c526fdf632360219cc26a70934ad33507`
- Merge tree: `170e600bef80794d636a62b113d8fbd9ba44124a`
- Exact-head Remediation CI: `33307016094` (#265) — `SUCCESS`
- Exact-head Protected CI: `33307016067` (#276) — `SUCCESS`
- Protected synthetic merge-ref: `0934b962812a6a085a57c0230af98961db083d7f`
- Portable suite: `1711 passed, 1 skipped, 57 deselected, 1 warning`
- Frozen/current-boundary suite: `375 passed`
- Existing five V4 integration gates: `PASS`
- Validation: `PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`.
- Qualification: H1-H5 machine gates were re-executed; the historical G3 aggregate gate was re-executed; historical G4 evidence was preserved without rewriting its original scope; the H4/H5 source-limited boundaries and non-claims remained explicit.
- No-drift: `MERGE_TREE_DRIFT=FALSE`; merge parents are `23ca602fe136a805d9be268acf33194b8ce9fd35` and the certified head; certified-head tree equals merge tree; head→merge files are empty; remote `main` equals the merge SHA at H6 closure.
- Claim: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE` is now permitted for the standalone manual-based reconstruction scope.
- Non-claims: `UFOTRI_MANUAL_BASED_FUNCTIONAL_REPLICATION_COMPLETE=FALSE`; `UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED`; CTEAS-Atmos binding remains optional/deferred; production readiness, calibration, empirical validation and physical-accuracy validation are not claimed.

## 5. CTEAS-Atmos after H6

The future CTEAS-Atmos integration is retained, but its role is changed from replication blocker to optional higher-fidelity backend integration:

- `CTEAS_ATMOS_HTO_BACKEND_BINDING`
- `CTEAS_ATMOS_HT_BACKEND_BINDING`
- `CTEAS_ATMOS_END_TO_END_COMPATIBILITY`

These may be required for the broader CTEAS software product and real project applications, but they do not block standalone manual-based UFOTRI functional reconstruction.

## 6. Immediate next stage

`NO_IMMEDIATE_INTERNAL_MANUAL_RECONSTRUCTION_STAGE`

The standalone manual-based UFOTRI reconstruction sequence is closed. No new internal reconstruction stage is authorized. Production calibration, empirical site validation, original-executable numerical equivalence, optional ecological extensions, and CTEAS-Atmos higher-fidelity backend integration remain separate future workstreams and must not be silently promoted into the completed reconstruction claim.
