# UFOTRI manual-based functional reconstruction final gate R1

## Scope

This report records the candidate decision for `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE_R1`.

The stage is restricted to the internal recoverable manual-based reconstruction claim. It does not perform real CTEAS-Atmos integration, production parameter activation, calibration, empirical validation, or optional scientific extensions.

## Evidence audited

The G4 machine gate audits all 19 required internal A–G3 stages listed in the master roadmap:

- leaf Eq. (7)–(31) reconciliation, fidelity implementation and manual regression;
- OBT state-role reconstruction and numerical/conservation qualification;
- Eq. (33)–(37) soil hydrology and coupled water/HTO verification;
- continuous food-chain reconciliation, pasture roots, vegetable/grass, cow/milk/beef and public exposure;
- HT contract, HT→HTO soil conversion and HT-derived HTO/re-emission ownership;
- re-emission/area-source compatibility;
- Canada 1987 benchmark-contract reconstruction;
- ITER benchmark/tabulated-reference reconstruction;
- G3 cross-module fidelity qualification.

For each stage, G4 requires the roadmap `COMPLETE` status and no-drift record and independently verifies from Git history that the recorded certified head is a parent of the recorded merge commit, the merge commit is an ancestor of the G4 candidate, and the certified-head tree equals the merge tree.

G4 also re-executes the G3 aggregate machine gate rather than inventing a new model pipeline.

## Gap disposition

The final G3 matrix contains all 30 UFR entries with no unimplemented recoverable internal mechanism:

- `COMPLETE_INTERNAL`: 20;
- `RECONCILED_EXISTING_OPTION`: 1 (`UFR-16`, historical optional approximately 3 h root delay);
- `COMPLETE_WITH_SOURCE_LIMIT`: 3 (`UFR-12`, `UFR-27`, `UFR-28`);
- `DEFERRED_EXTERNAL_DEPENDENCY`: 4 (`UFR-01`, `UFR-03`, `UFR-04`, `UFR-05`);
- `BLOCKED_SOURCE_UNAVAILABLE`: 2 (`UFR-29`, `UFR-30`).

The deferred entries are real atmospheric transport/deposition/washout obligations. The blocked entries depend on unavailable original UFOTRI assets. Neither class is relabeled as implemented internal physics.

## Claim boundary

A successful G4 candidate supports eligibility for the internal flag:

`UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE=TRUE`

but only after exact-head CI, merge, post-merge no-drift audit, and a separate roadmap-status synchronization. The candidate itself leaves the roadmap flag false.

The following remain explicitly outside that claim and remain false, deferred, source-limited, or not established:

- real CTEAS-Atmos HTO/HT binding and full real-Atmos end-to-end replication;
- complete Eq. (44) rate recovery;
- Canada 1987 full numerical/empirical replay;
- ITER full atmospheric numerical replay and empirical validation;
- empirical site validation;
- physical-accuracy validation and production readiness;
- original UFOTRI parameter-loader/hidden-default recovery;
- original MUSEMET/ISOLA/UFOTRI executable numerical equivalence.

`UFOTRI_ORIGINAL_NUMERICAL_EQUIVALENCE=NOT_ESTABLISHED` remains the governing boundary.

## Candidate decision

The intended machine result is:

`PASS_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_FINAL_GATE`

only when every G4 gate passes. Until the candidate passes exact-head CI and post-merge no-drift audit, `UFOTRI_MANUAL_BASED_FUNCTIONAL_RECONSTRUCTION_COMPLETE` remains false in the control-plane roadmap.

## Candidate changes

Exactly five qualification artifacts are permitted:

1. ADR-078;
2. G4 governance YAML;
3. this report;
4. the G4 machine gate;
5. the focused G4 pytest file.

No `src/`, default, workflow, or roadmap change is part of this candidate.
