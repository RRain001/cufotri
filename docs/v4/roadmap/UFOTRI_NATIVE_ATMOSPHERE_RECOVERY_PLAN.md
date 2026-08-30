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

Historical G4 evidence is not deleted or rewritten. It remains valid for the scope that G4 actually audited. The current whole-model claim is reopened until the UFOTRI-native atmospheric sequence below is closed.

Current state:

- `V4_SOFTWARE_DEVELOPMENT_BASELINE_COMPLETE=TRUE`
- `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=FALSE_PENDING_NATIVE_ATMOSPHERE_CLOSURE`
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

- Status: `AUTHORIZED_NOT_STARTED`
- Stage: `UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`
- Primary authority: KfK 4605 Section 2.1 plus KfK 4332, *UFOMOD - atmospheric dispersion and deposition*.
- Required recovery:
  - a trajectory starts at the source for each hourly start time;
  - one meteorological station represents the source region in MUSEMET;
  - meteorology is homogeneous within each hourly interval;
  - each trajectory stores successive horizontal coordinates relative to the source Cartesian system;
  - wind direction and wind speed of each subsequent hour advance the single precomputed segmented trajectory;
  - stability, precipitation and mixing-layer state remain attached to the corresponding segment;
  - travel-time / maximum-distance termination is explicit;
  - deterministic restart and coordinate invariance are tested.
- Forbidden:
  - do not substitute a multiple-puff model;
  - do not make all already-released plume elements instantaneously adopt a new wind direction;
  - do not use CTEAS-Atmos wind fields;
  - do not invent spatially varying meteorology absent from MUSEMET.
- Next stage after clean closure: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`.

### H3 — Native HT/HTO environmental forcing adapters

- Status: `NOT_STARTED`
- Stage: `UFOTRI_NATIVE_ATMOSPHERIC_FORCING_ADAPTER_R1`
- Dependency: H1 + H2.
- Required closure:
  - native HT concentration/deposition → existing typed E1 HT forcing;
  - native HT deposition → existing E2 soil HT→HTO conversion;
  - native HTO concentration/deposition/washout → existing HTO forcing contract;
  - no HT/HTO chemistry aliasing;
  - interval, units, spatial support and provenance preserved;
  - activity/deposition ledgers close across the adapter.
- Next stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`.

### H4 — Atmospheric-process reconciliation

- Status: `NOT_STARTED`
- Stage: `UFOTRI_NATIVE_ATMOSPHERIC_PROCESS_RECONCILIATION_R1`
- Dependency: H1-H3.
- Required topics:
  - recover/qualify the two HTO washout coefficient regimes if authoritative values are available;
  - replace the H1 controlled source-depletion approximation with the KfK 4332/MUSEMET relation where recoverable;
  - reconcile building-wake correction;
  - reconcile thermal-lift/effective-release-height treatment;
  - preserve source-limited boundaries where equations/numerics remain unavailable instead of inventing them.
- Atmospheric HT→HTO remains disabled for KfK 4605 unless separate versioned evidence proves otherwise.
- Next stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`.

### H5 — Native atmosphere → environmental chain → dose qualification

- Status: `NOT_STARTED`
- Stage: `UFOTRI_NATIVE_ATMOSPHERE_TO_DOSE_QUALIFICATION_R1`
- Dependency: H1-H4 plus already completed A-F internal environmental mechanisms.
- Required execution:
  - source term → native HT/HTO atmosphere;
  - species-specific deposition/washout;
  - HT soil conversion to HTO;
  - soil HTO transport and re-emission;
  - root + leaf exchange;
  - TFWT + OBT;
  - food chain;
  - inhalation/skin/ingestion dose;
  - secondary area-source feedback without double counting;
  - deterministic repeat, restart, timestep/partition checks and cross-module activity conservation;
  - explicit comparison against Canada/ITER benchmark contracts only to the extent supported by authoritative data.
- Completion of H5 allows a new final reconstruction gate.

### H6 — Corrected final reconstruction gate

- Status: `NOT_STARTED`
- Stage: `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R2`
- Dependency: H1-H5 complete.
- Required decision:
  - audit historical A-G stages plus H1-H5;
  - supersede G4 only as the current final-gate status, without rewriting G4 history;
  - restore `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE` only if no recoverable internal mechanism remains.

## 5. CTEAS-Atmos after H6

The future CTEAS-Atmos integration is retained, but its role is changed from replication blocker to optional higher-fidelity backend integration:

- `CTEAS_ATMOS_HTO_BACKEND_BINDING`
- `CTEAS_ATMOS_HT_BACKEND_BINDING`
- `CTEAS_ATMOS_END_TO_END_COMPATIBILITY`

These may be required for the broader CTEAS software product and real project applications, but they do not block standalone manual-based UFOTRI functional reconstruction.

## 6. Immediate next stage

`UFOTRI_NATIVE_HOURLY_TRAJECTORY_R1`

No production calibration, empirical site calibration, unrelated CTEAS-Atmos development, original-executable-equivalence claim, or optional ecological extension is authorized before the native-atmosphere sequence is closed.
